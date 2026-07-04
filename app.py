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
            st.error("You are not currently logged in.")

    if st.session_state.current_user:
        st.info(f"Logged in as: **{st.session_state.current_user}**")

def log_workout_tab():
    st.subheader("Log a Workout")
    name = st.text_input("Name:", value=st.session_state.current_user or "", key="workout_entry_name", disabled=True)
    exercise = st.text_input("Exercise:", key="workout_entry_exercise")
    
    col1, col2 = st.columns(2)
    with col1:
        sets = st.number_input("Sets:", min_value=0, value=3, step=1, key="workout_entry_sets")
        weight = st.number_input("Weight (lb):", min_value=0.0, value=0.0, step=5.0, key="workout_entry_weight")
    with col2:
        reps = st.number_input("Reps:", min_value=0, value=10, step=1, key="workout_entry_reps")
        duration = st.number_input("Duration (min):", min_value=0.0, value=0.0, step=1.0, key="workout_entry_duration")
        
    rest_time = st.number_input("Rest Time (seconds):", min_value=0, value=60, step=5, key="workout_entry_rest")

    if st.button("Log Workout", key="workout_submit_action_button"):
        if not name.strip():
            st.error("Please log in first.")
        else:
            log_workout(name.strip(), exercise.strip(), sets, reps, weight, duration, rest_time)
            mark_active(name.strip())

def dashboard_tab():
    st.subheader("Dashboard — Everyone's Stats")
    if st.button("Refresh Dashboard", key="dashboard_manual_refresh_btn"):
        st.rerun()

    workouts = get_all_workouts()
    if not workouts:
        st.info("No logged workouts found.")
        return

    by_person = {}
    for w in workouts:
        by_person.setdefault(w.get("name", "Unknown"), []).append(w)

    for person, entries in by_person.items():
        total_sets = sum(int(e.get("sets", 0) or 0) for e in entries)
        with st.expander(f"{person} — {len(entries)} workouts logged"):
            st.write(f"**Total Sets Tracked:** {total_sets}")
            for entry in entries:
                st.write(f"- {entry.get('exercise')}: {entry.get('sets')} sets x {entry.get('reps')} reps @ {entry.get('weight')} lbs (Rest: {entry.get('rest_time', 'N/A')}s)")

def active_users_tab():
    st.subheader("Who's Active Right Now")
    if st.button("Refresh Active List", key="active_users_manual_refresh_btn"):
        st.rerun()

    active = get_active_users()
    if not active:
        st.info("No active users online.")
        return

    for user in active:
        user_name = user.get("task_name", "Anonymous User")
        st.write(f" 🔥 **{user_name}** is actively crushing it")

# 6. Main App Layout Router (Auth Guarded)
if st.session_state.current_user is None:
    tab1, = st.tabs(["Login"])
    with tab1:
        login_tab()
        st.warning("Please log in to unlock the rest of the application features.")
else:
    tab1, tab2, tab3, tab4 = st.tabs(["Login Status", "Log Workout", "Dashboard", "Active Users"])
    with tab1:
        login_tab()
    with tab2:
        log_workout_tab()
    with tab3:
        dashboard_tab()
    with tab4:
        active_users_tab()       
