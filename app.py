import streamlit as st
from google import genai
from google.genai import types
import json
import pandas as pd

# 1. Page Configuration (Must be first)
st.set_page_config(page_title="Student Finance AI", page_icon="💰", layout="wide")

# 2. Sidebar for API Key & Budget
with st.sidebar:
    st.header("🔑 Setup")
    
    # Try to get key from secrets, otherwise ask user
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("API Key loaded from secrets!")
    else:
        api_key = st.text_input("Enter Gemini API Key", type="password")
        st.info("Get a free key at [Google AI Studio](https://aistudio.google.com/)")

    st.divider()
    st.header("🎯 Monthly Goal")
    budget_goal = st.number_input("Monthly Budget (₹)", min_value=1, value=5000)

# Initialize Session State
if "expenses" not in st.session_state:
    st.session_state.expenses = []

# Initialize Client only if API Key exists
client = None
if api_key:
    try:
        client = genai.Client(api_key=api_key, http_options=types.HttpOptions(api_version="v1beta"))
    except Exception as e:
        st.error(f"Client error: {e}")

# 3. Main UI
st.title("💸 Student Finance AI Advisor")
st.markdown("Track your daily spending and let AI find your saving opportunities.")

# Input Form
with st.container(border=True):
    with st.form("expense_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            date = st.date_input("Date")
        with col2:
            amount = st.number_input("Amount (₹)", min_value=1)
        with col3:
            desc = st.text_input("What did you buy?")
        
        if st.form_submit_button("Add Expense"):
            if desc:
                st.session_state.expenses.append({"date": str(date), "amount": amount, "desc": desc})
                st.rerun()

# 4. Analysis & Charts
if st.session_state.expenses:
    df = pd.DataFrame(st.session_state.expenses)
    df['date'] = pd.to_datetime(df['date'])
    
    # Summary Metrics
    total_spent = df['amount'].sum()
    remaining = budget_goal - total_spent
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Spent", f"₹{total_spent}")
    m2.metric("Remaining", f"₹{remaining}", delta=remaining)
    m3.metric("Expenses Count", len(df))

    st.divider()

    col_a, col_b = st.columns([1, 1])
    
    with col_a:
        st.subheader("📋 Expense Log")
        st.dataframe(df, use_container_width=True)

    with col_b:
        st.subheader("📊 Spending Trend")
        chart_data = df.groupby("date")["amount"].sum()
        st.bar_chart(chart_data)

    # 5. AI Advisor Section
    st.divider()
    if st.button("🤖 Get AI Financial Advice", type="primary"):
        if not client:
            st.warning("Please provide an API Key in the sidebar first!")
        else:
            prompt = f"""
            Role: Strict Student Financial Advisor.
            Current Budget: ₹{budget_goal}
            Expense Data: {json.dumps(st.session_state.expenses)}
            
            Task: 
            1. Summarize spending.
            2. Identify the single biggest waste of money.
            3. Give 3 specific hacks for a student to save ₹500 next month based on this data.
            """
            
            with st.spinner("AI is calculating your savings..."):
                try:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt
                    )
                    st.success("Advisor Insight:")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"AI Error: {e}")

    if st.button("🗑️ Clear All Data"):
        st.session_state.expenses = []
        st.rerun()
else:
    st.info("Start by adding an expense above!")

