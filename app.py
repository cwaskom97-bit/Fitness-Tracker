import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta

# 1. Page Configuration (Browser Tab Title and Icon)
st.set_page_config(page_title="RunItBack", page_icon="🏃‍♂️", layout="centered")

# Global App Header (Shows on every page/tab at the very top)
st.title("RunItBack 🏃‍♂️")

TIMEOUT_MINUTES = 10

# Mobile styling tweak
st.markdown("""
<style>
div.stButton > button {
width: 100%;
height: 3em;
font-size: 1.05em;
border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# 2. Database Initialization
@st.cache_resource
def get_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_client()

# 3. Session State
if "current_user" not in st.session_state:
    st.session_state.current_user = None

# 4. Database Interactions (Silent error handling to prevent blank UI blocks)
def mark_active(name):
    try:
        supabase.table("tasks").upsert({"task_name": name, "task_date": datetime.utcnow().date().isoformat()}).execute()
    except Exception as e:
        pass

def mark_inactive(name):
    try:
        supabase.table("tasks").delete().eq("task_name", name).execute()
    except Exception as e:
        pass

def get_active_users():
    try:
        cutoff = (datetime.utcnow() - timedelta(minutes=TIMEOUT_MINUTES)).date().isoformat()
        res = supabase.table("tasks").select("*").gte("task_date", cutoff).execute()
        return res.data if hasattr(res, 'data') else []
    except Exception as e:
        return []

def get_all_workouts():
    try:
        res = supabase.table("Completions").select("*").execute()
        return res.data if hasattr(res, 'data') else []
    except Exception as e:
        return []

def log_workout(name, exercise, sets, reps, weight, duration, rest_time):
    try:
        supabase.table("Completions").insert({
            "name": name, 
            "exercise": exercise or "Unspecified", 
            "sets": sets, 
            "reps": reps, 
            "weight": weight, 
            "duration": duration,
            "rest_time": rest_time
        }).execute()
        st.success("Workout saved to database!")
    except Exception as e:
        st.error(f"Database Error: {e}")

# 5. Interface Tabs
def login_tab():
    st.subheader("Login / Registration")
    name = st.text_input("Your name", key="user_login_input_field")
    col1, col2 = st.columns(2)

    if col1.button("Log In", key="action_login_btn"):
        if name.strip():
            st.session_state.current_user = name.strip()
            mark_active(name.strip())
            st.success(f"Logged in as {name.strip()}")
            st.rerun()
        else:
            st.error("Please enter a name.")

    if col2.button("Log Out", key="action_logout_btn"):
        if st.session_state.current_user:
            mark_inactive(st.session_state.current_user)
            st.success(f"{st.session_state.current_user} logged out.")
            st.session_state.current_user = None
            st.rerun()
        else:
