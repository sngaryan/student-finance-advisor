import streamlit as st

# Initialize guest mode state
if "guest_mode" not in st.session_state:
    st.session_state.guest_mode = False

# --- 1. STYLING ---
st.markdown("""
    <style>
    .auth-card {
        text-align: center;
        padding: 3rem;
        border-radius: 20px;
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        margin: 2rem auto;
        max-width: 500px;
    }
    .stButton>button {
        border-radius: 10px;
        height: 3em;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. AUTH LOGIC ---
is_authorized = st.user.is_logged_in or st.session_state.guest_mode

if not is_authorized:
    # --- BEAUTIFUL LOGIN PAGE ---
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    st.title("💰 Student Finance AI")
    st.write("Personalized budgeting powered by Gemini 3 Flash")
    st.write("---")
    
    # Original Login Button
    if st.button("🔐 Log in with Google", type="primary", use_container_width=True):
        st.login()
            
    st.write("OR")
    
    # Guest Access
    if st.button("👤 Continue as Guest", use_container_width=True):
        st.session_state.guest_mode = True
        st.rerun()
        
    st.caption("Guest mode does not save data permanently.")
    st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- REDIRECT TO APP.PY ---
    
    # Top bar for Logout/Exit
    with st.sidebar:
        st.write(f"Logged in as: **{st.user.name if st.user.is_logged_in else 'Guest'}**")
        if st.user.is_logged_in:
            if st.button("Log out"):
                st.logout()
        else:
            if st.button("Exit Guest Mode"):
                st.session_state.guest_mode = False
                st.rerun()
        st.divider()

    # This line "calls" your dashboard code from app.py
    try:
        import app
        # If your app.py has a main function, call it here: app.main()
    except Exception as e:
        st.error(f"Could not load the dashboard: {e}")