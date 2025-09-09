import streamlit as st
import pandas as pd
import altair as alt
from io import StringIO

st.set_page_config(page_title="My Fit Pod — Revenue Dashboard", page_icon="💪", layout="wide")

st.markdown("# My Fit Pod — 3-Month Revenue Snapshot")
st.caption("Income breakdown for Berkhamsted and Aylesbury (June–August 2025)")

# ========= EMBED YOUR CSV CONTENTS BELOW =========
# Open each CSV on your computer, Select All → Copy → Paste between the triple quotes

# Berkhamsted — June
berko_jun_csv = """PASTE CSV CONTENT HERE
Date,Item,Quantity Sold,Amount Inc Tax
...your actual rows...
"""

# Berkhamsted — July
berko_jul_csv = """PASTE CSV CONTENT HERE
Date,Item,Quantity Sold,Amount Inc Tax
...your actual rows...
"""

# Berkhamsted — August
berko_aug_csv = """PASTE CSV CONTENT HERE
Date,Item,Quantity Sold,Amount Inc Tax
...your actual rows...
"""

# Aylesbury — June
ayles_jun_csv = """PASTE CSV CONTENT HERE
Date,Item,Quantity Sold,Amount Inc Tax
...your actual rows...
"""

# Aylesbury — July
ayles_jul_csv = """PASTE CSV CONTENT HERE
Date,Item,Quantity Sold,Amount Inc Tax
...your actual rows...
"""

# Aylesbury — August
ayles_aug_csv = """PASTE CSV CONTENT HERE
Date,Item,Quantity Sold,Amount Inc Tax
...your actual rows...
"""

# ========= DO NOT EDIT BELOW THIS LINE =========

def _ensure_filled(txt, label):
    if not txt.strip() or "PASTE CSV CONTENT HERE" in txt:
        st.stop()
        raise ValueError(f"{label} is empty. Paste the full CSV in that triple-quoted block.")

def load_embedded():
    # Validate all six blocks are filled
    _ensure_filled(berko_jun_csv, "Berkhamsted June")
    _ensure_filled(berko_jul_csv, "Berkhamsted July")
    _ensure_filled(berko_aug_csv, "Berkhamsted August")
    _ensure_filled(ayles_jun_csv, "Aylesbury June")
    _ensure_filled(ayles_jul_csv, "Aylesbury July")
    _ensure_filled(ayles_aug_csv, "Aylesbury August")

    def parse_one(txt, gym, month):
        df = pd.read_csv(StringIO(txt))
        # Expect exactly these four columns
        needed = ["Date", "Item", "Quantity Sold", "Amount Inc Tax"]
        missing = [c for c in needed if c not in df.columns]
        if missing:
            raise ValueError(f"Missing {missing} in embedded CSV for {gym} {month}.")
        df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
        df["gym"], df["month"] = gym, month
        return df

    frames = [
        parse_one(berko_jun_csv, "Berkhamsted", "June"),
        parse_one(berko_jul_csv, "Berkhamsted", "July"),
        parse_one(berko_aug_csv, "Berkhamsted", "August"),
        parse_one(ayles_jun_csv, "Aylesbury", "June"),
        parse_one(ayles_jul_csv, "Aylesbury", "July"),
        parse_one(ayles_aug_csv, "Aylesbury", "August"),
    ]
    all_df = pd.concat(frames, ignore_index=True)
    # Clean up
    all_df["Item"] = all_df["Item"].astype(str).str.strip()
    return all_df

df = load_embedded()

# -------- Sidebar filters
st.sidebar.header("Filters")
gyms = sorted(df["gym"].dropna().unique().tolist())
sel_gyms = st.sidebar.multiselect("Gyms", gyms, default=gyms)

months_order = ["June","July","August"]
sel_months = st.sidebar.multiselect("Months", months_order, default=months_order)

items = sorted(df["Item"].dropna().unique().tolist())
sel_items = st.sidebar.multiselect("Items (raw)", items, default=items)

filtered = df[
    df["gym"].isin(sel_gyms) &
    df["month"].isin(sel_months) &
    df["Item"].isin(sel_items)
].copy()

# -------- KPIs
total_rev = filtered["Amount Inc Tax"].sum()
total_sessions = filtered["Quantity Sold"].sum()
mr = filtered.groupby(["gym","month"], as_index=False)["Amount Inc Tax"].sum()
avg_monthly_rev = mr["Amount Inc Tax"].mean() if not mr.empty else 0.0

c1, c2, c3 = st.columns(3)
c1.metric("Total Revenue (selected)", f"£{total_rev:,.2f}")
c2.metric("Avg Monthly Revenue", f"£{avg_monthly_rev:,.2f}")
c3.metric("Total Sessions (selected)", f"{int(total_sessions):,}")

st.divider()

# -------- Total revenue by gym (bar)
st.subheader("Total Revenue by Gym (Selected Period)")
rev_by_gym = filtered.groupby("gym", as_index=False)["Amount Inc Tax"].sum().rename(columns={"Amount Inc Tax":"Revenue"})
chart1 = alt.Chart(rev_by_gym).mark_bar().encode(
    x=alt.X("gym:N", title="Gym"),
    y=alt.Y("Revenue:Q", title="Revenue (£)"),
    tooltip=[alt.Tooltip("gym:N"), alt.Tooltip("Revenue:Q", format="£,.2f")]
).properties(height=300)
st.altair_chart(chart1, use_container_width=True)

# -------- Monthly revenue trend (line)
st.subheader("Monthly Revenue Trend by Gym")
filtered["month"] = pd.Categorical(filtered["month"], categories=months_order, ordered=True)
monthly = filtered.groupby(["month","gym"], as_index=False)["Amount Inc Tax"].sum().rename(columns={"Amount Inc Tax":"Revenue"})
chart2 = alt.Chart(monthly).mark_line(point=True).encode_
