import streamlit as st
import pandas as pd
import altair as alt
from io import StringIO

# ──────────────────────────────────────────────────────────────────────────
# APP SETUP
# ──────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="My Fit Pod — Revenue Dashboard", page_icon="💪", layout="wide")
st.markdown("# My Fit Pod — 3-Month Revenue Snapshot")
st.caption("Income breakdown for Berkhamsted and Aylesbury (June–August 2025)")

# ──────────────────────────────────────────────────────────────────────────
# 🔽 PASTE YOUR SIX CSVs BETWEEN THE TRIPLE QUOTES
#   → Include the header row: Date,Item,Quantity Sold,Amount Inc Tax
#   → No extra quotes inside; plain text only.
#   → If any block is empty, the app will show a red error and stop.
# ──────────────────────────────────────────────────────────────────────────

# Berkhamsted — June
berko_jun_csv = """PASTE CSV CONTENT HERE
Date,Item,Quantity Sold,Amount Inc Tax
"""

# Berkhamsted — July
berko_jul_csv = """PASTE CSV CONTENT HERE
Date,Item,Quantity Sold,Amount Inc Tax
"""

# Berkhamsted — August
berko_aug_csv = """PASTE CSV CONTENT HERE
Date,Item,Quantity Sold,Amount Inc Tax
"""

# Aylesbury — June
ayles_jun_csv = """PASTE CSV CONTENT HERE
Date,Item,Quantity Sold,Amount Inc Tax
"""

# Aylesbury — July
ayles_jul_csv = """PASTE CSV CONTENT HERE
Date,Item,Quantity Sold,Amount Inc Tax
"""

# Aylesbury — August
ayles_aug_csv = """PASTE CSV CONTENT HERE
Date,Item,Quantity Sold,Amount Inc Tax
"""

# ──────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────
NEEDED_COLS = ["Date", "Item", "Quantity Sold", "Amount Inc Tax"]

def _ensure_filled(txt: str, label: str):
    """Show a visible error if a CSV block is empty or still has the placeholder."""
    if not txt.strip() or "PASTE CSV CONTENT HERE" in txt:
        st.error(f"❌ **{label}** CSV block is empty.\n\nOpen that CSV on your computer, copy **all rows (including the header)**, and paste it between the triple quotes.")
        st.stop()

def _parse_one(txt: str, gym: str, month: str) -> pd.DataFrame:
    """Parse one embedded CSV string, normalize headers, coerce types, add gym/month."""
    try:
        df = pd.read_csv(StringIO(txt))
    except Exception as e:
        st.error(f"❌ Could not read embedded CSV for **{gym} {month}**: {e}")
        st.stop()

    # Normalize headers: strip whitespace, accept case-insensitive matches
    df.columns = [c.strip() for c in df.columns]
    cmap = {}
    for want in NEEDED_COLS:
        match = next((c for c in df.columns if c.strip().lower() == want.lower()), None)
        if not match:
            st.error(f"❌ Missing column **{want}** in embedded CSV for **{gym} {month}**.\nFound columns: {list(df.columns)}")
            st.stop()
        cmap[want] = match

    df = df[[cmap[c] for c in NEEDED_COLS]].copy()
    df.columns = NEEDED_COLS

    # Types
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    df["Quantity Sold"] = pd.to_numeric(df["Quantity Sold"], errors="coerce")
    df["Amount Inc Tax"] = pd.to_numeric(df["Amount Inc Tax"], errors="coerce")

    # Add labels
    df["gym"], df["month"] = gym, month
    return df

@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    # Ensure blocks filled
    _ensure_filled(berko_jun_csv, "Berkhamsted — June")
    _ensure_filled(berko_jul_csv, "Berkhamsted — July")
    _ensure_filled(berko_aug_csv, "Berkhamsted — August")
    _ensure_filled(ayles_jun_csv, "Aylesbury — June")
    _ensure_filled(ayles_jul_csv, "Aylesbury — July")
    _ensure_filled(ayles_aug_csv, "Aylesbury — August")

    frames = [
        _parse_one(berko_jun_csv,  "Berkhamsted", "June"),
        _parse_one(berko_jul_csv,  "Berkhamsted", "July"),
        _parse_one(berko_aug_csv,  "Berkhamsted", "August"),
        _parse_one(ayles_jun_csv,  "Aylesbury",   "June"),
        _parse_one(ayles_jul_csv,  "Aylesbury",   "July"),
        _parse_one(ayles_aug_csv,  "Aylesbury",   "August"),
    ]
    df = pd.concat(frames, ignore_index=True)
    df["Item"] = df["Item"].astype(str).str.strip()
    return df

# ──────────────────────────────────────────────────────────────────────────
# LOAD + DEBUG PREVIEW (you can delete the expander later)
# ──────────────────────────────────────────────────────────────────────────
df = load_data()

with st.expander("🔍 Debug (temporary): data preview"):
    st.write({"rows": int(len(df)), "gyms": sorted(df["gym"].unique().tolist()), "months": sorted(df["month"].unique().tolist())})
    st.dataframe(df.head(10))

# ──────────────────────────────────────────────────────────────────────────
# FILTERS
# ──────────────────────────────────────────────────────────────────────────
st.sidebar.header("Filters")
gyms = sorted(df["gym"].dropna().unique().tolist())
sel_gyms = st.sidebar.multiselect("Gyms", gyms, default=gyms)

months_order = ["June", "July", "August"]
sel_months = st.sidebar.multiselect("Months", months_order, default=months_order)

items = sorted(df["Item"].dropna().unique().tolist())
sel_items = st.sidebar.multiselect("Items (raw)", items, default=items)

filtered = df[
    df["gym"].isin(sel_gyms) &
    df["month"].isin(sel_months) &
    df["Item"].isin(sel_items)
].copy()

# ──────────────────────────────────────────────────────────────────────────
# KPIs
# ──────────────────────────────────────────────────────────────────────────
total_rev = float(filtered["Amount Inc Tax"].sum())
total_sessions = float(filtered["Quantity Sold"].sum())

mr = filtered.groupby(["gym", "month"], as_index=False)["Amount Inc Tax"].sum()
avg_monthly_rev = float(mr["Amount Inc Tax"].mean()) if not mr.empty else 0.0

c1, c2, c3 = st.columns(3)
c1.metric("Total Revenue (selected)", f"£{total_rev:,.2f}")
c2.metric("Avg Monthly Revenue", f"£{avg_monthly_rev:,.2f}")
c3.metric("Total Sessions (selected)", f"{int(total_sessions):,}")

st.divider()

# ──────────────────────────────────────────────────────────────────────────
# CHARTS
# ──────────────────────────────────────────────────────────────────────────

# Total revenue by gym (bar)
st.subheader("Total Revenue by Gym (Selected Period)")
rev_by_gym = filtered.groupby("gym", as_index=False)["Amount Inc Tax"].sum().rename(columns={"Amount Inc Tax": "Revenue"})
chart1 = alt.Chart(rev_by_gym).mark_bar().encode(
    x=alt.X("gym:N", title="Gym"),
    y=alt.Y("Revenue:Q", title="Revenue (£)"),
    tooltip=[alt.Tooltip("gym:N"), alt.Tooltip("Revenue:Q", format="£,.2f")]
).properties(height=300)
st.altair_chart(chart1, use_container_width=True)

# Monthly revenue trend (line)
st.subheader("Monthly Revenue Trend by Gym")
filtered["month"] = pd.Categorical(filtered["month"], categories=months_order, ordered=True)
monthly = filtered.groupby(["month", "gym"], as_index=False)["Amount Inc Tax"].sum().rename(columns={"Amount Inc Tax": "Revenue"})
chart2 = alt.Chart(monthly).mark_line(point=True).encode(
    x=alt.X("month:O", title="Month", sort=months_order),
    y=alt.Y("Revenue:Q", title="Revenue (£)"),
    color="gym:N",
    tooltip=["month:N", "gym:N", alt.Tooltip("Revenue:Q", format="£,.2f")]
).properties(height=320)
st.altair_chart(chart2, use_container_width=True)

# Sessions per month by Item (stacked bar)
st.subheader("Session Breakdown per Month (Raw Item)")
sessions = filtered.groupby(["month", "Item"], as_index=False)["Quantity Sold"].sum().rename(columns={"Quantity Sold": "Sessions"})
chart3 = alt.Chart(sessions).mark_bar().encode(
    x=alt.X("month:O", title="Month", sort=months_order),
    y=alt.Y("Sessions:Q", title="Sessions"),
    color=alt.Color("Item:N", title="Item"),
    tooltip=["month:N", "Item:N", "Sessions:Q"]
).properties(height=380)
st.altair_chart(chart3, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────
# TABLES + DOWNLOAD
# ──────────────────────────────────────────────────────────────────────────
st.subheader("Details")
t1, t2 = st.tabs(["Monthly Revenue Table", "Session Breakdown Table"])

with t1:
    st.dataframe(monthly.sort_values(["month", "gym"]))

with t2:
    pivot = sessions.pivot(index="Item", columns="month", values="Sessions").fillna(0).astype(int)
    st.dataframe(pivot)

st.download_button(
    "Download filtered transactions (CSV)",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="filtered_transactions.csv",
    mime="text/csv"
)
