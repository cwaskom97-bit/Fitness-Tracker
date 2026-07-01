
import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta

# Fixed the syntax error on page config
st.set_page_config(page_title="Workout Tracker", page_icon="🏋️", layout="centered")

TIMEOUT_MINUTES = 10

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

# ---------- Data helpers matching your real database ----------
def mark_active(name):
# Maps to your actual 'tasks' table columns: task_name and task_date
try:
supabase.table("tasks").upsert({
"task_name": name,
"task_date": datetime.utcnow().date().isoformat()
}).execute()
except Exception as e:
st.error(f"Error marking active: {e}")

def mark_inactive(name):
try:
supabase.table("tasks").delete().eq("task_name", name).execute()
except Exception as e:
st.error(f"Error logging out: {e}")

def get_active_users():
# Queries your actual 'tasks' table safely
try:
cutoff = (datetime.utcnow() - timedelta(minutes=TIMEOUT_MINUTES)).date().isoformat()
res = supabase.table("tasks").select("*").gte("task_date", cutoff).execute()
return sorted(res.data, key=lambda r: r.get("task_date", ""), reverse=True)
except Exception as e:
st.error(f"Error fetching active users: {e}")
return []

def log_workout(name, exercise, sets, reps, weight, duration):
# Maps to your actual capitalized 'Completions' table
try:
supabase.table("Completions").insert({
"name": name,
"exercise": exercise or "Unspecified",
"sets": sets,
"reps": reps,
"weight": weight,
"duration": duration
}).execute()
except Exception as e:
st.error(f"Database error saving workout: {e}")

def get_all_workouts():
try:
res = supabase.table("Completions").select("*").execute()
return res.data
except Exception as e:
st.error(f"Error downloading dashboard data: {e}")
return []

# ---------- Tab Components ----------
def login_tab():
    st.subheader("Login")
    name = st.text_input("Your name", key="login_name_input")
    col1, col2 = st.columns(2)
    if col1.button("Log In", key="login_btn_action"):
        if name.strip():
            st.session_state.current_user = name.strip()
            mark_active(name.strip())
            st.success(f"Logged in as {name.strip()}")
            st.rerun()
else:
st.error("Enter a name first.")

if col2.button("Log Out", key="logout_btn_action"):
    if st.session_state.current_user:
        mark_inactive(st.session_state.current_user)
        st.success(f"{st.session_state.current_user} logged out.")
        st.session_state.current_user = None
        st.rerun()
else:
    st.error("You're not logged in.")

if st.session_state.current_user:
    st.info(f"Currently logged in as: **{st.session_state.current_user}**")

def log_workout_tab():
    st.subheader("Log a Workout")
    name = st.text_input("Name:", value=st.session_state.current_user or "", key="workout_name_input")
    exercise = st.text_input("Exercise:", key="workout_exercise_input")
    sets = st.number_input("Sets:", min_value=0, value=3, step=1, key="workout_sets_input")
    reps = st.number_input("Reps:", min_value=0, value=10, step=1, key="workout_reps_input")
    weight = st.number_input("Weight (lb):", min_value=0.0, value=0.0, step=5.0, key="workout_weight_input")
    duration = st.number_input("Duration (min):", min_value=0.0, value=0.0, step=1.0, key="workout_duration_input")

if st.button("Log Workout", key="submit_workout_btn"):
    if not name.strip():
        st.error("Enter a name first.")
else:
    log_workout(name.strip(), exercise.strip(), sets, reps, weight, duration)
    mark_active(name.strip())
    st.success(f"Logged workout successfully!")

def dashboard_tab():
    st.subheader("Dashboard — Everyone's Stats")
    if st.button("Refresh Dashboard", key="refresh_dashboard_data_btn"):
        st.rerun()

workouts = get_all_workouts()
if not workouts:
    st.info("No workouts logged in Completions table yet.")
    return

by_person = {}
for w in workouts:
    by_person.setdefault(w.get("name", "Unknown"), []).append(w)

for person, entries in by_person.items():
    total_sets = sum(int(e.get("sets", 0) or 0) for e in entries)
    total_reps = sum(int(e.get("sets", 0) or 0) * int(e.get("reps", 0) or 0) for e in entries)

        with st.expander(f"{person} — {len(entries)} entry/entries"):
            st.write(f"Total sets completed: {total_sets}")
            st.write(f"Estimated reps completed: {total_reps}")

def active_users_tab():
    st.subheader(f"Who's Active Right Now (last {TIMEOUT_MINUTES} min)")
    if st.button("Refresh Active Users", key="final_unique_refresh_active_users"):
        st.rerun()

    active = get_active_users()
    if not active:
        st.info("No one is currently listed in the active tasks log.")
        return

    for user in active:
        user_name = user.get("task_name", "Anonymous User")
        st.write(f"🟢 **{user_name}** — Checked in")

# ---------- App Router Layout ----------
tab1, tab2, tab3, tab4 = st.tabs(["Login", "Log Workout", "Dashboard", "Active Users"])
with tab1:
    login_tab()
with tab2:
    log_workout_tab()
with tab3:
    dashboard_tab()
with tab4:
    active_users_tab()
