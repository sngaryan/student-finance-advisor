import streamlit as st
from google import genai
from google.genai import types
import json
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="Student Finance AI", layout="wide")

# 2. Initialize Client (v1beta is the most compatible for Flash models)
try:
    client = genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"],
        http_options=types.HttpOptions(api_version="v1beta")
    )
except Exception as e:
    st.error(f"Failed to initialize AI Client: {e}")

st.title("💸 Student Expense & Savings Advisor")

# 3. Initialize Session State
if "expenses" not in st.session_state:
    st.session_state.expenses = []

# 4. Input Form
with st.container(border=True):
    st.subheader("➕ Add New Expense")
    with st.form("expense_form", clear_on_submit=True):
        col1, col2, col3 = st.columns([2, 2, 3])
        with col1:
            date = st.date_input("Date")
        with col2:
            amount = st.number_input("Amount (₹)", min_value=1)
        with col3:
            desc = st.text_input("Description (e.g., Lunch, Bus)")
        
        submitted = st.form_submit_button("Add to List")
        if submitted and desc:
            st.session_state.expenses.append({
                "date": str(date), 
                "amount": amount, 
                "desc": desc
            })
            st.rerun()

# 5. Display Table
if st.session_state.expenses:
    df = pd.DataFrame(st.session_state.expenses)
    st.subheader("📋 Your Expenses")
    st.dataframe(df, use_container_width=True)

    # 6. AI Analysis with Auto-Fallback Logic
    if st.button("🤖 Analyze with AI", type="primary"):
        prompt = f"Student Finance Advisor. Analyze these expenses and give 3 saving tips: {json.dumps(st.session_state.expenses)}"
        
        # List of models to try in order of reliability
        models_to_try = ["gemini-1.5-flash-latest", "gemini-2.0-flash", "gemini-1.5-flash"]
        success = False

        with st.spinner("AI is thinking..."):
            for model_id in models_to_try:
                try:
                    response = client.models.generate_content(
                        model=model_id,
                        contents=prompt
                    )
                    st.success(f"Analysis Complete (using {model_id})")
                    st.markdown(response.text)
                    success = True
                    break # Stop once we get a response
                
                except Exception as e:
                    err_msg = str(e)
                    # If it's a 404, just try the next model silently
                    if "404" in err_msg:
                        continue
                    # If it's a 429, tell the user to wait
                    elif "429" in err_msg:
                        st.warning(f"Model {model_id} is busy (Quota Hit). Trying next...")
                        continue
                    else:
                        st.error(f"Unexpected error with {model_id}: {e}")
                        break
            
            if not success:
                st.error("❌ All AI models are currently unavailable. Please wait 60 seconds and try again.")

    if st.button("🗑️ Clear All"):
        st.session_state.expenses = []
        st.rerun()

else:
    st.info("Add an expense to get started!")