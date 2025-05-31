import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pathlib
import plotly.graph_objects as go
import plotly.express as px


# Set the directory to the current file's location
dir = str(pathlib.Path(__file__).parent.resolve()) + '\\' 

st.title("Technical Challenge Fundraising Dashboard")

# Load data
@st.cache_data
def load_data():
    df = pd.read_excel(dir + "combined_df.xlsx")
    df.rename(columns={"CREATED_AT": "created_at", 
    "DONATION_TYPE": "donation_type", 
    "CC_TYPE": "cc_type", 
    "DESIGNATION_ID": "designation_id", 
    "DESIGNATED_VALUE": "designated_value", 
    "DESIGNATION_NAME": "desination_name"}, inplace=True)
    return df

df = load_data()
print("\nDescribe:\n", df.describe(include='all'))

# Prepare date features
df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
df["year"] = df["created_at"].dt.year.astype(int)
df["month"] = df["created_at"].dt.to_period("M").astype(int)
df["year_month"] = (df["created_at"].dt.to_period("M").dt.to_timestamp())

print(len(df))

# sidebar filter list
year_opts = sorted(df["year"].unique())
df = df[df["year"].isin(year_opts)]

st.sidebar.header("Filters")

# Sidebar options for filtering
st.sidebar.markdown("Select filters to narrow down the data displayed in the dashboard.")
year_opts = ["All"] + sorted(df["year"].unique())
cc_type_opts = ["All"] + sorted(df["cc_type"].dropna().unique())
designation_opts = ["All"] + sorted(df["desination_name"].dropna().unique())
donation_type_opts = ["All"] + sorted(df["donation_type"].dropna().unique())

selected_year = st.sidebar.selectbox("Year", year_opts)
selected_cc = st.sidebar.selectbox("Payment Method", cc_type_opts)
selected_designation = st.sidebar.selectbox("Fund", designation_opts)
selected_donation = st.sidebar.selectbox("Donation Type", donation_type_opts)

# Filter the dataframe based on selections
df_filtered = df.copy()
if selected_year != "All":
    df_filtered = df_filtered[df_filtered["year"] == selected_year]
if selected_cc != "All":
    df_filtered = df_filtered[df_filtered["cc_type"] == selected_cc]
if selected_designation != "All":
    df_filtered = df_filtered[df_filtered["desination_name"] == selected_designation]
if selected_donation != "All":
    df_filtered = df_filtered[df_filtered["donation_type"] == selected_donation]



# 1. Year-over-Year Trends by Month# 1. Year-over-Year Trends by Month# 1. Year-over-Year Trends by Month# 1. Year-over-Year Trends by Month# 1. Year-over-Year Trends by Month# 1. Year-over-Year Trends by Month
st.header("1-Year-over-Year Trends (by Year-Month)")
st.subheader("- Actionable Insights")
st.markdown("""
- **Feb, Sep, and Dec ramping up dramatically.** Be ready a month ahead and allocate more resources for the upcoming events for the school.
- **Feb and Sep spikes** guessing due to school semesters starting/Homecoming events pops up.
- **Comparing Donations on December 2023 to December 2022,** Trending up **+76% increase in giving.** A sign to be watched since could be a repetitive patern for other schools. Move-fast to have tax benefits for donors.
- **Monitor Apr-Aug Yearly.** These months show relatively low givings. Maybe due to slow planning around the school for other events, final, summer break, or graduation.
""")

# 1a)graph: Monthly Trends
monthly = (df_filtered.groupby("year_month")["designated_value"].sum().sort_index())
yoy = monthly.pct_change(periods=12) * 100
trend = pd.DataFrame({"total": monthly,"YoY % change": yoy}).reset_index()

st.caption("Monthly Total Contributions Over Time")
st.line_chart(trend.set_index("year_month")["total"], use_container_width=True) # Line chart of total contributions by month

# 1b) Table: Monthly Trends
trend["total_fmt"] = trend["total"].apply(lambda x: f"${x:,.2f}") # Format total contributions
trend["year_month"] = trend["year_month"].dt.strftime("%Y-%m") # Format year_month to YYYY-MM
trend["yoy_fmt"] = trend["YoY % change"].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "") # Format YoY percentage change
display_df = trend[["year_month", "total_fmt", "yoy_fmt"]].rename(columns={"year_month": "Month", "total_fmt":"Total Contributions", "yoy_fmt": "YoY % Change"}) # Rename columns for display

st.caption("Monthly Contributions Table")
st.dataframe(display_df, hide_index=True, use_container_width=True)

# 1c) Graph: Monthly Trends by Year
month_labels = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}

# Create pivot table for monthly contributions by year
pivot = (df_filtered.assign(month_num=df_filtered["created_at"].dt.month)
    .groupby(["month_num", "year"])["designated_value"]
    .sum()
    .unstack("year")
    .sort_index())

# Add month number for sorting
pivot["month"] = pivot.index.map(month_labels)

# Reorder columns to ensure month order is maintained
df_melted = pivot.reset_index().melt(
    id_vars=["month_num", "month"],
    value_vars=pivot.columns[:-1],
    var_name="Year",
    value_name="Total")

df_melted = df_melted.dropna(subset=["Total"]) # Drop rows with NaN in Total to avoid gaps in the line chart

# Convert month_num to categorical for proper ordering
fig = px.line(
    df_melted,
    x="month",
    y="Total",
    color="Year",
    markers=True,
    category_orders={"month": list(month_labels.values())},  # Keep month order
    title="Monthly Giving Trends"
)

fig.update_traces(connectgaps=False) # Do not connect missing points
    
# Format y-axis as dollar
fig.update_layout(
    yaxis_tickformat="$,.0f",
    xaxis_title="Month",
    yaxis_title="Total Giving ($)")

st.plotly_chart(fig, use_container_width=True)

st.divider()

# 2. Spikes & Dips in Monthly Contributions# 2. Spikes & Dips in Monthly Contributions# 2. Spikes & Dips in Monthly Contributions# 2. Spikes & Dips in Monthly Contributions# 2. Spikes & Dips in Monthly Contributions# 2. Spikes & Dips in Monthly Contributions
st.header("2-Spikes & Dips in Monthly Contributions")
st.subheader("- Actionable Insights")
st.markdown("""
- **Spikes in Feb, Sep, and Dec.** Could be large campaigns before school semester starts or year-end giving""")

monthly = df_filtered.groupby("year_month")["designated_value"].sum() # Group by year_month and sum contributions
monthly_df = monthly.to_frame().reset_index() # Convert to DataFrame
monthly_df["std"] = monthly_df["designated_value"].std() # Calculate standard deviation of contributions
threshold = monthly_df["std"].iloc[0] * 1  # 1 standard deviations
spikes = monthly_df[monthly_df["designated_value"] > monthly_df["designated_value"].mean() + threshold] # Identify spikes where contributions are above mean + threshold
dips = monthly_df[monthly_df["designated_value"] < monthly_df["designated_value"].mean() - threshold] # Identify dips where contributions are below mean - threshold

st.write("**Spikes:**")
st.dataframe(spikes[["year_month", "designated_value"]],  hide_index=True, use_container_width=True)
st.write("**Dips:**")
st.dataframe(dips[["year_month", "designated_value"]],  hide_index=True, use_container_width=True)

st.divider()

# 3. Top & Bottom Funds by Total Value# 3. Top & Bottom Funds by Total Value# 3. Top & Bottom Funds by Total Value# 3. Top & Bottom Funds by Total Value# 3. Top & Bottom Funds by Total Value# 3. Top & Bottom Funds by Total Value
st.header("3-Top & Bottom Funds by Total Value")
st.subheader("- Actionable Insights")
st.markdown("""
- **Top 5:** Making sure these funds have the best support from GiveCampus it's our driver. Also find pattern to replicate their success to other funds.
- **Bottom 5:** Maybe merge these funds with similar ones. helping donors to make better choices.
""")

print(len(df))
df["designated_value"] = df["designated_value"].astype(float)
fund_totals = df_filtered.groupby("desination_name")["designated_value"].sum() # Group by fund name and sum contributions
sorted_totals = fund_totals.sort_values(ascending=False)

# Top 5
top5 = sorted_totals.head(5)
top5.index = pd.CategoricalIndex(top5.index, categories=top5.index.tolist(), ordered=True) # Sort index to maintain order in bar chart
st.subheader("Top 5 Funds by Total Value")
st.bar_chart(top5)

# Bottom 5
bottom5 = sorted_totals.tail(5).sort_values(ascending=True)
bottom5.index = pd.CategoricalIndex(bottom5.index, categories=bottom5.index.tolist(), ordered=True)
st.subheader("Bottom 5 Funds by Total Value")
st.bar_chart(bottom5)

st.divider()

# 4. Donation Type & Payment Method Behavior# 4. Donation Type & Payment Method Behavior# 4. Donation Type & Payment Method Behavior# 4. Donation Type & Payment Method Behavior# 4. Donation Type & Payment Method Behavior# 4. Donation Type & Payment Method Behavior
st.header("4-Donation Type & Payment Method")
st.subheader("- Actionable Insights")
st.markdown("""
- **Potential from matching.** Encourage school to invite companies to match contributions.
""")

# 4A Collapse to gift‐level so count = unique gifts
gift_df = (df_filtered.groupby(["CONTRIBUTION_ID","donation_type"])["designated_value"].sum().reset_index(name="gift_value")) # Group by contribution ID and donation type, summing designated values to get unique gifts

# 4A Aggregate per payment method
cc_stats = (
    gift_df
    .groupby("donation_type")["gift_value"]
    .agg(Sum="sum", Count="count", Mean="mean", StdDev="std")
    .sort_values(by="Sum", ascending=False)
)

# 4A Add Subtotal row
subtotal = pd.DataFrame(cc_stats.sum(numeric_only=True)).T
subtotal.index = ["Subtotal"]
cc_stats = pd.concat([cc_stats, subtotal])
cc_stats.index.name = "Donation Type"

# 4A Format columns
cc_stats["Sum"]    = cc_stats["Sum"].map(lambda x: f"${x:,.2f}")
cc_stats["Mean"]   = cc_stats["Mean"].map(lambda x: f"${x:,.2f}")
cc_stats["StdDev"] = cc_stats["StdDev"].map(lambda x: f"${x:,.2f}")
cc_stats["Count"]  = cc_stats["Count"].astype(int)

# 4A Display
st.table(cc_stats)
donation_type_totals = (
    df_filtered
    .groupby("donation_type")["designated_value"]
    .sum()
    .sort_values(ascending=False))

# Donut Chart
donut_payment_type = go.Figure(
    data=[go.Pie(
        labels=donation_type_totals.index,
        values=donation_type_totals.values,
        hole=0.4,
        hoverinfo="label+percent+value",
        textinfo="label+percent")])

donut_payment_type.update_layout(title="Donation Type Distribution")
st.plotly_chart(donut_payment_type, use_container_width=True)


# 4B Payment Method Analysis
st.subheader("**By Payment Method**")

# 4B Collapse to gift‐level so count = unique gifts
gift_df = (df_filtered.groupby(["CONTRIBUTION_ID","cc_type"])["designated_value"].sum().reset_index(name="gift_value"))

# 4B Aggregate per payment method
cc_stats = (
    gift_df
    .groupby("cc_type")["gift_value"]
    .agg(Sum="sum", Count="count", Mean="mean", StdDev="std")
    .sort_values(by="Sum", ascending=False)
)

# 4B Add Subtotal row
subtotal = pd.DataFrame(cc_stats.sum(numeric_only=True)).T
subtotal.index = ["Subtotal"]
cc_stats = pd.concat([cc_stats, subtotal])
cc_stats.index.name = "Payment Method"

# 4B Format columns
cc_stats["Sum"]    = cc_stats["Sum"].map(lambda x: f"${x:,.2f}")
cc_stats["Mean"]   = cc_stats["Mean"].map(lambda x: f"${x:,.2f}")
cc_stats["StdDev"] = cc_stats["StdDev"].map(lambda x: f"${x:,.2f}")
cc_stats["Count"]  = cc_stats["Count"].astype(int)

# 4B Display
st.table(cc_stats)

# Aggregate by unique gifts
payment_method_counts = (
    df_filtered
    .groupby("cc_type")["designated_value"]
    .sum()
    .sort_values(ascending=False))

# 5B Donut Chart
donut_payment_type = go.Figure(
    data=[go.Pie(
        labels=payment_method_counts.index,
        values=payment_method_counts.values,
        hole=0.4,
        hoverinfo="label+percent+value",
        textinfo="label+percent")])

donut_payment_type.update_layout()
st.plotly_chart(donut_payment_type, use_container_width=True)

st.divider()

# 5. Distribution of Contribution Amounts# 5. Distribution of Contribution Amounts# 5. Distribution of Contribution Amounts# 5. Distribution of Contribution Amounts# 5. Distribution of Contribution Amounts# 5. Distribution of Contribution Amounts
st.header("5-Distribution of Contribution Amounts")
st.subheader("- Actionable Insights")
st.markdown("""
- **Small contributions bucket is the big players, but large contributions bucket should not be forgotten.**  
Tier-benefits for contributions <=$250.  
Focus on growing contributions on 250-1000.  
Large contributions require relationship-building and personalized attention.
""")
# Filter out zero or null values for clean distribution
value_data = df_filtered[df_filtered["designated_value"] > 0]

low = value_data[value_data["designated_value"] <= 1000]
high = value_data[value_data["designated_value"] > 1000]

# Then plot both separately with different bins
# Plot small contributions with donation type coloring
fig_low = px.histogram(
    low,
    x="designated_value",
    color="donation_type",
    nbins=50,
    title="Small Contributions (≤ $1,000)",
    barmode="stack", 
    labels={"designated_value": "Contribution Amount ($)"}
)

# Plot large contributions with donation type coloring
fig_high = px.histogram(
    high,
    x="designated_value",
    color="donation_type",
    nbins=30,
    title="Large Contributions (> $1,000)",
    barmode="stack",  
    labels={"designated_value": "Contribution Amount ($)"})

st.plotly_chart(fig_low, use_container_width=True)
st.plotly_chart(fig_high, use_container_width=True)