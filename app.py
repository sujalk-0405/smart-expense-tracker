import streamlit as st
import pandas as pd
import plotly.express as px


def load_and_clean_data(file):
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    df["Category"] = df["Category"].astype(str).str.strip()

    return df.dropna(subset=["Date", "Amount"])


st.set_page_config(
    page_title="Smart Expense Tracker",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Smart Daily Expense Tracker")

st.markdown("""
### 📝 How to use this app
1. Download the expense template and fill your monthly expenses.
2. Upload the file to see spending analysis and insights.
3. Optionally, upload a previous month file to compare expenses.
🔒 No login required. Your data is not stored.
""")

with open("expenses_sample.xlsx", "rb") as file:
    st.download_button(
        label="📥 Download Expense Template",
        data=file,
        file_name="expense_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

uploaded_file = st.file_uploader(
    "Upload your expense Excel or CSV file",
    type=["xlsx", "csv"]
)

if uploaded_file:
    df = load_and_clean_data(uploaded_file)

    required_columns = {"Date", "Category", "Amount"}
    if not required_columns.issubset(df.columns):
        st.error("File must contain Date, Category, and Amount columns.")
        st.stop()

    total_spent = df["Amount"].sum()
    avg_daily_spend = df.groupby(df["Date"].dt.date)["Amount"].sum().mean()
    top_category = df.groupby("Category")["Amount"].sum().idxmax()

    col1, col2, col3 = st.columns(3)
    col1.metric("💸 Total Spent", f"₹{total_spent:,.0f}")
    col2.metric("📊 Avg Daily Spend", f"₹{avg_daily_spend:,.0f}")
    col3.metric("🔥 Top Category", top_category)

    st.divider()
    st.subheader("📊 Category-wise Spending")

    category_summary = (
        df.groupby("Category")["Amount"]
        .sum()
        .reset_index()
        .sort_values(by="Amount", ascending=False)
    )

    fig_category = px.bar(
        category_summary,
        x="Category",
        y="Amount",
        text="Amount",
        title="Spending by Category"
    )
    st.plotly_chart(fig_category, use_container_width=True)

    st.subheader("📈 Daily Spending Trend")

    daily_summary = (
        df.groupby(df["Date"].dt.date)["Amount"]
        .sum()
        .reset_index(name="Total")
    )

    fig_daily = px.line(
        daily_summary,
        x="Date",
        y="Total",
        markers=True,
        title="Daily Expense Trend"
    )
    st.plotly_chart(fig_daily, use_container_width=True)

    st.subheader("🧠 Smart Insights")

    insights = [
        f"You spent the most on **{top_category}** this month.",
        "Your average daily spending is relatively high. Consider reviewing discretionary expenses."
        if avg_daily_spend > 300
        else "Your average daily spending is under control."
    ]

    highest_day = daily_summary.loc[daily_summary["Total"].idxmax()]
    insights.append(
        f"Your highest spending day was **{highest_day['Date']}** with ₹{highest_day['Total']:,.0f} spent."
    )

    for insight in insights:
        st.write("•", insight)

else:
    st.info("Please upload an expense file to begin analysis.")

st.divider()
st.header("📅 Month-to-Month Comparison")

col_left, col_right = st.columns(2)

with col_left:
    current_file = st.file_uploader(
        "Upload CURRENT month expense file",
        type=["xlsx", "csv"],
        key="current_month"
    )

with col_right:
    previous_file = st.file_uploader(
        "Upload PREVIOUS month expense file",
        type=["xlsx", "csv"],
        key="previous_month"
    )

if current_file and previous_file:
    current_df = load_and_clean_data(current_file)
    previous_df = load_and_clean_data(previous_file)

    current_total = current_df["Amount"].sum()
    previous_total = previous_df["Amount"].sum()
    difference = current_total - previous_total
    percentage_change = (difference / previous_total) * 100 if previous_total else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Current Month Total", f"₹{current_total:,.0f}")
    c2.metric("Previous Month Total", f"₹{previous_total:,.0f}")
    c3.metric("Change", f"₹{difference:,.0f}", f"{percentage_change:+.1f}%")

    st.subheader("📊 Category-wise Comparison")

    current_categories = current_df.groupby("Category")["Amount"].sum().reset_index()
    previous_categories = previous_df.groupby("Category")["Amount"].sum().reset_index()

    comparison = pd.merge(
        current_categories,
        previous_categories,
        on="Category",
        how="outer",
        suffixes=("_Current", "_Previous")
    ).fillna(0)

    comparison["Difference"] = (
        comparison["Amount_Current"] - comparison["Amount_Previous"]
    )

    fig_compare = px.bar(
        comparison,
        x="Category",
        y=["Amount_Current", "Amount_Previous"],
        barmode="group",
        title="Current vs Previous Month by Category"
    )
    st.plotly_chart(fig_compare, use_container_width=True)

    st.subheader("🧠 Comparison Insights")

    highest_increase = comparison.loc[comparison["Difference"].idxmax()]
    highest_decrease = comparison.loc[comparison["Difference"].idxmin()]

    st.write(
        f"• Highest increase: **{highest_increase['Category']}** "
        f"(+₹{highest_increase['Difference']:,.0f})"
    )
    st.write(
        f"• Highest decrease: **{highest_decrease['Category']}** "
        f"(₹{highest_decrease['Difference']:,.0f})"
    )

else:
    st.info("Upload both current and previous month files to see comparison.")
