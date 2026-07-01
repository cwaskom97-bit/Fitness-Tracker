import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta

"Workout Tracker", page_icon="🏋️", layout="centered")


TIMEOUT_MINUTES = 10 # how long someone stays "active" without activity

# ---------- Mobile-friendly styling ----------
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

# ---------- Supabase connection ----------
@st.cache_resource
def get_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_client()

# ---------- Session state ----------
if "current_user" not in st.session_state:
    st.session_state.current_user = None

# ---------- Data helpers ----------
def mark_active(name):
# Using your 'tasks' table to track user activity cleanly
    supabase.table("tasks").upsert({
        "task_name": name,
        "task_date": datetime.utcnow().date().isoformat()
    }).execute()

def mark_inactive(name):
    supabase.table("tasks").delete().eq("task_name", name).execute()

def get_active_users():
    cutoff = (datetime.utcnow() - timedelta(minutes=TIMEOUT_MINUTES)).date().isoformat()
    res = supabase.table("tasks").select("*").gte("task_date", cutoff).execute()
    return sorted(res.data, key=lambda r: r.get("task_date", ""), reverse=True)

def log_workout(name, exercise, sets, reps, weight, duration):
# Matches your exact capitalization for the 'Completions' table
supabase.table("Completions").insert({
    "name": name,
    "exercise": exercise or "Unspecified",
    "sets": sets,
    "reps": reps,
    "weight": weight,
    "duration": duration
}).execute()

def get_all_workouts():
    res = supabase.table("Completions").select("*").execute()
    return res.data

# ---------- Login tab ----------
def login_tab():
    st.subheader("Login")
    name = st.text_input("Your name", key="login_name")
    col1, col2 = st.columns(2)
    if col1.button("Log In"):
     if name.strip():
        st.session_state.current_user = name.strip()
        mark_active(name.strip())
        st.success(f"Logged in as {name.strip()}")
        st.rerun()
    else:
        st.error("Enter a name first.")
if col2.button("Log Out"):
    if st.session_state.current_user:
        mark_inactive(st.session_state.current_user)
        st.success(f"{st.session_state.current_user} logged out.")
        st.session_state.current_user = None
        st.rerun()
     else:
         st.error("You're not logged in.")

if st.session_state.current_user:
    st.info(f"Currently logged in as: **{st.session_state.current_user}**")

# ---------- Log Workout tab ----------
def log_workout_tab():
    st.subheader("Log a Workout")

    name = st.text_input("Name:", value=st.session_state.current_user or "", key="unique_tab_name_input")
    exercise = st.text_input("Exercise:", key="tab_exercise_input")
    sets = st.number_input("Sets:", min_value=0, value=3, step=1, key="tab_sets_input")
    reps = st.number_input("Reps:", min_value=0, value=10, step=1, key="tab_reps_input")
    weight = st.number_input("Weight (lb):", min_value=0.0, value=0.0, step=5.0, key="tab_weight_input")
    duration = st.number_input("Duration (min):", min_value=0.0, value=0.0, step=1.0, key="tab_duration_input")

if st.button("Log Workout", key="tab_log_workout_btn"):
    if not name.strip():
        st.error("Enter a name first.")
else:
    log_workout(name.strip(), exercise.strip(), sets, reps, weight, duration)
    mark_active(name.strip()) # Logging counts as activity
    st.success(f"Logged for {name.strip()}: {exercise or 'Unspecified'} — {sets}x{reps} @ {weight}lb, {duration} min")

# ---------- Dashboard tab (everyone's full stats) ----------
def dashboard_tab():
    st.subheader("Dashboard — Everyone's Stats")
    if st.button("Refresh Dashboard", key="tab_refresh_dashboard_btn"):
        st.rerun()

workouts = get_all_workouts()
if not workouts:
    st.info("No workouts logged yet.")
    return

by_person = {}
for w in workouts:
    by_person.setdefault(w.get("name", "Unknown"), []).append(w)

for person, entries in by_person.items():
    total_sets = sum(int(e.get("sets", 0)) for e in entries)
    total_reps = sum(int(e.get("sets", 0)) * int(e.get("reps", 0)) for e in entries)
    total_volume = sum(int(e.get("sets", 0)) * int(e.get("reps", 0)) * float(e.get("weight", 0.0)) for e in entries)
    total_duration = sum(float(e.get("duration", 0.0)) for e in entries)

with st.expander(f"{person} — {len(entries)} workout(s)"):
    st.write(f"Total sets: {total_sets}")
    st.write(f"Total reps: {total_reps}")
    st.write(f"Total volume (sets × reps × weight): {total_volume:.1f} lbs")
    st.write(f"Total duration: {total_duration:.1f} min")

# ---------- Active Users tab (only currently online) ----------
def active_users_tab():
    st.subheader(f"Who's Active Right Now (last {TIMEOUT_MINUTES} min)")
    if st.button("Refresh Active Users", key="unique_refresh_active_users_action_btn"):
        st.rerun()

active = get_active_users()
if not active:
    st.info("No one is currently active.")
    return

for user in active:
    user_name = user.get("task_name", "Anonymous User")
    st.write(f"🟢 **{user_name}** — Active today")

# ---------- Router Layout ----------
tab1, tab2, tab3, tab4 = st.tabs(["Login", "Log Workout", "Dashboard", "Active Users"])
with tab1:
    login_tab()
with tab2:
    log_workout_tab()
with tab3:
    dashboard_tab()
with tab4:
    active_users_tab()
