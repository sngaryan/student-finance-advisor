import streamlit as st
from google import genai
from google.genai import types
import pandas as pd
import json

# 1. Page Configuration
st.set_page_config(page_title="Student Finance AI", page_icon="💰", layout="wide")

# 2. Sidebar Setup
with st.sidebar:
    st.header("🔑 Setup")
    api_key = st.secrets.get("GEMINI_API_KEY") or st.text_input("Enter API Key", type="password")
    budget_goal = st.number_input("Monthly Budget (₹)", min_value=1, value=5000)
    
    st.divider()
    if st.button("🗑️ Reset Everything"):
        st.session_state.expenses = []
        st.session_state.messages = []
        st.rerun()

# Initialize Session State
if "expenses" not in st.session_state:
    st.session_state.expenses = []
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. Main UI - Expense Entry
st.title("💸 Student Finance AI Advisor")

with st.container(border=True):
    with st.form("expense_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1: date = st.date_input("Date")
        with col2: amount = st.number_input("Amount (₹)", min_value=1)
        with col3: desc = st.text_input("Description")
        if st.form_submit_button("Add Expense"):
            if desc:
                st.session_state.expenses.append({"date": str(date), "amount": amount, "desc": desc})
                st.rerun()

# 4. COMPACT DASHBOARD (Side-by-Side Layout)
if st.session_state.expenses:
    df = pd.DataFrame(st.session_state.expenses)
    total_spent = df['amount'].sum()
    remaining = budget_goal - total_spent
    
    # Small metrics at the top
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Spent", f"₹{total_spent}")
    m2.metric("Remaining", f"₹{remaining}", delta=f"{remaining}")
    m3.metric("Entries", len(df))

    # Side-by-side Table and Chart
    col_left, col_right = st.columns([1, 1]) # Split 50/50
    
    with col_left:
        st.subheader("📋 History")
        st.dataframe(df, use_container_width=True, height=250)
    
    with col_right:
        st.subheader("📊 Trend")
        # Creating a smaller, compact bar chart
        st.bar_chart(df.set_index('date')['amount'], height=250)
    
    st.divider()

    # 5. CHAT INTERFACE
    st.subheader("💬 Chat with Gemini 3 Flash")
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about your savings..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        if not api_key:
            st.error("Please add an API Key in the sidebar.")
        else:
            with st.chat_message("assistant"):
                history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                data_summary = f"Expenses: {json.dumps(st.session_state.expenses)}"
                full_query = f"Data: {data_summary}\nHistory: {history}\nUser: {prompt}"

                try:
                    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(api_version="v1beta"))
                    # 1. Define the rules for the AI (Do this before the response line)
                    sys_instruct = "You are a savvy Indian Student Financial Advisor. ALWAYS use Indian Rupees (₹) and never use Dollars ($). Provide advice relevant to Indian students (e.g., canteen costs, local metro/bus, Indian savings schemes)."

                    # 2. Update your API call using the variable you just created
                    response = client.models.generate_content(
                        model="gemini-3-flash",
                        config=types.GenerateContentConfig(system_instruction=sys_instruct),
                        contents=f"Context: {json.dumps(st.session_state.expenses)}\nUser: {prompt}"
                    )
                    
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception:
                    st.error("⚠️ API Error. See fallback below.")

    # 6. EXTERNAL FALLBACK
    with st.expander("🚀 Manual Chat (Copy-Paste)"):
        backup_text = f"Analyze my expenses:\n{df.to_string(index=False)}\nTotal: ₹{total_spent}. Give me advice."
        st.code(backup_text, language="text")
        st.link_button("Open Gemini Website", "https://gemini.google.com/app", use_container_width=True)

else:
    st.info("Add an expense to see your dashboard!")
