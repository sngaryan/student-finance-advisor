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
    
    # We wrap this in try/except so the app doesn't crash if secrets.toml is missing
    try:
        secret_key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        secret_key = None

    # If NO secret is found, show the manual input box
    if not secret_key:
        api_key = st.text_input("Enter API Key", type="password", key="manual_api_key")
    else:
        api_key = secret_key
        st.success("✅ API Key loaded from Secrets")

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

# --- 3. MAIN UI - TOP BUDGET DASHBOARD ---
st.title("💸 Student Finance AI Advisor")

# High-visibility Budget Goal section
with st.container(border=True):
    st.subheader("🎯 Monthly Budget Goal")
    c1, c2, c3 = st.columns([2, 1, 1])
    
    with c1:
        budget_goal = st.number_input("Set your limit (₹)", min_value=1, value=5000, step=500)
    
    # Calculate totals immediately for the header
    total_spent = pd.DataFrame(st.session_state.expenses)['amount'].sum() if st.session_state.expenses else 0
    remaining = budget_goal - total_spent
    
    with c2:
        st.metric("Total Spent", f"₹{total_spent}")
    with c3:
        st.metric("Left to Spend", f"₹{remaining}", delta=f"{remaining}", delta_color="normal" if remaining >= 0 else "inverse")

    # Add a visual progress bar
    if budget_goal > 0:
        progress = min(total_spent / budget_goal, 1.0)
        st.progress(progress, text=f"{int(progress*100)}% of budget used")

st.divider()

# --- 4. PERMANENT ADD EXPENSE FORM (Always Visible) ---
st.subheader("➕ Add New Expense")
with st.container(border=True):
    with st.form("expense_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1: date = st.date_input("Date")
        with col2: amount = st.number_input("Amount (₹)", min_value=1)
        with col3: desc = st.text_input("Description (e.g., Canteen, Metro)")
        
        if st.form_submit_button("Add to List"):
            if desc:
                st.session_state.expenses.append({"date": str(date), "amount": amount, "desc": desc})
                st.rerun()

# --- 5. COMPACT ANALYTICS & CHAT (Shows only if data exists) ---
if st.session_state.expenses:
    df = pd.DataFrame(st.session_state.expenses)
    
    # Side-by-side Table and Chart
    col_left, col_right = st.columns([1, 1]) 
    
    with col_left:
        st.subheader("📋 History")
        st.dataframe(df, use_container_width=True, height=250)
    
    with col_right:
        st.subheader("📊 Spending Trends")
        st.bar_chart(df.set_index('date')['amount'], height=250)
    
    st.divider()

    # 6. CHAT INTERFACE WITH GEMINI 3 FLASH
    st.subheader("💬 Chat with Gemini and analyse")
    
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
                try:
                    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(api_version="v1beta"))
                    sys_instruct = "You are a savvy Indian Student Financial Advisor. ALWAYS use Indian Rupees (₹) and never use Dollars ($). Provide advice relevant to Indian students."

                    # Gemini 3 Flash with dynamic thinking
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        config=types.GenerateContentConfig(
                            system_instruction=sys_instruct,
                            thinking_config=types.ThinkingConfig(include_thoughts=True)
                        ),
                        contents=f"Data: {json.dumps(st.session_state.expenses)}\nUser: {prompt}"
                    )
                    
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception:
                    st.error("⚠️ API Error. Use the fallback below.")

    # 7. EXTERNAL FALLBACK
    with st.expander("🚀 Manual Chat (Copy-Paste)"):
        backup_text = f"Analyze my expenses in ₹: {df.to_string(index=False)}\nTotal: ₹{total_spent}."
        st.code(backup_text, language="text")
        st.link_button("Open Gemini Website", "https://gemini.google.com/app", use_container_width=True)

else:
    st.info("Start by setting your budget and adding your first expense above!")

