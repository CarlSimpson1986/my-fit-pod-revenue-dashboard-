import streamlit as st
import pandas as pd
import altair as alt
import re, glob, os

st.set_page_config(page_title="My Fit Pod — Revenue Dashboard", page_icon="💪", layout="wide")

st.markdown("# My Fit Pod — 3-Month Revenue Snapshot")
st.caption("Income breakdown for Berkhamsted and Aylesbury (June–August 2025)")

@st.cache_data
def load_data(data_path: str = "data"):
    """
    Loads all CSVs in ./data, infers gym & month from filename, parses dates.
    Expected CSV cols: Date, Item, Quantity Sold, Amount Inc Tax (others ignored).
    Works with filenames like:
      - berko.jun.25.csv / Berkhamsted.jul.25.csv / Aylesbury.aug.25.csv (case-insensitive)
    """
    month_map = {
        "jan":"January","feb":"February","mar":"March","apr":"April","may":"May",
        "jun":"June","jul":"July","aug":"August","sep":"September","oct":"October",
        "nov":"November","dec":"December"
    }
    rows = []
    for fp in glob.glob(os.path.join(data_path, "*.csv")):
        fn = os.path.basename(fp).lower()

        # Infer gym from filename
        gym = "Berkhamsted" if "berk" in fn else ("Aylesbury" if "ayles" in fn else None)

        # Infer month from filename
        m_short = next((m for m in month_map if re.search(rf"\b{m}\b", fn)), None)
        month_name = month_map.get(m_short, None)

        try:
            df = pd.read_csv(fp)
        except Exception as e:
            # show a soft warning but keep going
            st.warning(f"Could not load {fp}: {e}")
            continue

        needed = ["Date", "Item", "Quantity Sold", "Amount Inc Tax"]
        missing = [c for c in needed if c not in df.columns]
        if missing:
            st.warning(f"{fp} missing columns: {missing}")
            continue

        # Parse date like '30/06/2025 19:25' (UK format)
        df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
        df["gym"] = gym if gym else df.get("gym", None)
        df["month"] = month_name if month_name else df["Date"].dt.month_name()

        rows.append(df)

    if not rows:
        return pd.DataFrame(columns=["Date","Item","Quantity Sold","Amount Inc Tax","gym","month"])

    all_df = pd.concat(rows, ignore_index=True)
    all_df["Item"] = all_df["Item"].astype(str).str.strip()
    all_df["gym"] = all_df["gym"].fillna("Unknown")
    all_df["month"] = all_df["month"].astype(str)
    return all_df

df = load_data("data")

if df.empty:
    st.error("No data found. Add your CSVs to the `data/` folder.")
    st.stop()

# -------- Sidebar filters
st.sidebar.header("Filters")
gyms = sorted(df["gym"].dropna().unique().tolist())
sel_gyms = st.sidebar.multiselect("Gyms", gyms, default=gyms)

months_order = ["June","July","August","September","October","November","December","January","February","March","April","May"]
months = [m for m in months_order if m in df["month"].unique().tolist()]
sel_months = st.sidebar.multiselect("Months", months, default=months)

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
chart2 = alt.Chart(monthly).mark_line(point=True).encode(
    x=alt.X("month:O", title="Month", sort=months_order),
    y=alt.Y("Revenue:Q", title="Revenue (£)"),
    color="gym:N",
    tooltip=["month:N","gym:N", alt.Tooltip("Revenue:Q", format="£,.2f")]
).properties(height=320)
st.altair_chart(chart2, use_container_width=True)

# -------- Sessions per month by Item (stacked bar)
st.subheader("Session Breakdown per Month (Raw Item)")
sessions = filtered.groupby(["month","Item"], as_index=False)["Quantity Sold"].sum().rename(columns={"Quantity Sold":"Sessions"})
chart3 = alt.Chart(sessions).mark_bar().encode(
    x=alt.X("month:O", title="Month", sort=months_order),
    y=alt.Y("Sessions:Q", title="Sessions"),
    color=alt.Color("Item:N", title="Item"),
    tooltip=["month:N","Item:N","Sessions:Q"]
).properties(height=380)
st.altair_chart(chart3, use_container_width=True)

# -------- Details tabs
st.subheader("Details")
t1, t2 = st.tabs(["Monthly Revenue Table", "Session Breakdown Table"])

with t1:
    st.dataframe(monthly.sort_values(["month","gym"]))

with t2:
    pivot = sessions.pivot(index="Item", columns="month", values="Sessions").fillna(0).astype(int)
    st.dataframe(pivot)

# -------- Download filtered transactions
st.download_button(
    "Download filtered transactions (CSV)",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="filtered_transactions.csv",
    mime="text/csv"
)
