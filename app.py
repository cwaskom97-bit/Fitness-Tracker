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

# 4. Database Interactions
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

def delete_workout(workout_id):
    try:
        supabase.table("Completions").delete().eq("id", workout_id).execute()
        st.success("Workout deleted successfully!")
        st.rerun()
    except Exception as e:
        st.error(f"Failed to delete workout: {e}")

# 5. Interface Tabs
def login_tab():
    st.subheader("Login / Registration")
    
    if not st.session_state.current_user:
        col_first, col_last = st.columns(2)
        with col_first:
            first_name = st.text_input("First Name", key="user_first_name")
        with col_last:
            last_name = st.text_input("Last Name", key="user_last_name")
            
        if st.button("Log In", key="login_btn"):
            if not first_name.strip() or not last_name.strip():
                st.error("Please enter both your first and last name.")
            else:
                full_name = f"{first_name.strip()} {last_name.strip()}"
                st.session_state.current_user = full_name
                mark_active(full_name)
                st.success(f"Successfully logged in as {full_name}")
                st.rerun()
    else:
        st.info(f"Logged in as: **{st.session_state.current_user}**")
        if st.button("Log Out", key="action_logout_btn"):
            mark_inactive(st.session_state.current_user)
            st.session_state.current_user = None
            st.success("Logged out successfully.")
            st.rerun()

def log_workout_tab():
    st.subheader("Log a Workout")
    name = st.text_input("Account:", value=st.session_state.current_user or "", key="workout_entry_name", disabled=True)
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
                col_data, col_action = st.columns([4, 1])
                with col_data:
                    st.write(f"- {entry.get('exercise')}: {entry.get('sets')} sets x {entry.get('reps')} reps @ {entry.get('weight')} lbs (Rest: {entry.get('rest_time', 'N/A')}s)")
                
                if entry.get("name") == st.session_state.current_user:
                    with col_action:
                        if st.button("❌ Delete", key=f"del_{entry.get('id')}"):
                            delete_workout(entry.get('id'))

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
