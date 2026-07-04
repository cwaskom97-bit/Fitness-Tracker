import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta
    
    # 1. Page Configuration
    st.set_page_config(page_title=
    "Workout Tracker", page_icon="", layout="centered")
    
    
    
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
    
    # 4. Database Interactions (Matching your actual tables)
    def mark_active(name):
        try:
            supabase.table("tasks").upsert({"task_name": name, "task_date": datetime.utcnow().date().isoformat()}).execute()
        except Exception as e:
            st.error(f"  Login Error (tasks table): {e}")
    
    def mark_inactive(name):
        try:
            supabase.table("tasks").delete().eq("task_name", name).execute()
        except Exception as e:
            st.error(f"  Logout Error (tasks table): {e}")
    
    def get_active_users():
        try:
            cutoff = (datetime.utcnow() - timedelta(minutes=TIMEOUT_MINUTES)).date().isoformat()
            res = supabase.table("tasks").select("*").gte("task_date", cutoff).execute()
            return res.data if hasattr(res, 'data') else []
        except Exception as e:
            st.error(f"  Error fetching active users: {e}")
            return []
    
    def get_all_workouts():
        try:
            res = supabase.table("Completions").select("*").execute()
            return res.data if hasattr(res, 'data') else []
        except Exception as e:
            st.error(f"  Dashboard Error (Completions table): {e}")
            return []
    
    def log_workout(name, exercise, sets, reps, weight, duration):
        try:
            supabase.table("Completions").insert({"name": name, "exercise": exercise or "Unspecified", "sets": sets, "reps": reps, "weight": weight, "duration": duration}).execute()
            st.success("Workout saved to database!")
        except Exception as e:
            st.error(f"  Workout Error (Completions table): {e}")
    
    state.current_user)
    st.success(f"{st.session_state.current_user} logged out.")
    
    user}**")
    
    current_user or "", key="workout_entry_name")
    
    button"):
    
    
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
            with st.expander(f"{person} — {len(entries)} entries"):
                st.write(f"Total Sets: {total_sets}")
    
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
            st.write(f" **{user_name}** is online")
    
    # 6. Main App Layout Router
    tab1, tab2, tab3, tab4 = st.tabs(["Login", "Log Workout", "Dashboard", "Active Users"])
    with tab1:
        login_tab()
    with tab2:
        log_workout_tab()
    with tab3:
        dashboard_tab()
    with tab4:
        active_users_tab()
