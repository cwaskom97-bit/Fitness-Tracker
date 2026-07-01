
import streamlit as st
import json
import os
from datetime import datetime

DATA_FILE = "workout_data.json"

# Maintain active users across the web session
if "active_users" not in st.session_state:
    st.session_state.active_users = set()

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Load data at start of app run
data_now = load_data()

st.title("🏋️‍♂️ Fitness and Messaging Tracker")

# Recreating your 3 Jupyter Tabs inside the web browser
tab1, tab2, tab3 = st.tabs(["Log Workout", "Dashboard", "Active Users"])

# --- TAB 1: LOG WORKOUT PANEL ---
with tab1:
    st.header("Log a Workout")

name_input = st.text_input("Name:", key="log_name").strip()
exercise_input = st.text_input("Exercise:", key="log_exercise").strip()
sets_input = st.number_input("Sets:", min_value=1, value=3)
reps_input = st.number_input("Reps:", min_value=1, value=10)
weight_input = st.number_input("Weight (lb):", min_value=0.0, value=0.0, step=0.5)
duration_input = st.number_input("Duration (min):", min_value=0.0, value=0.0, step=1.0)

if st.button("Log Workout"):
# 1. Gather the inputs into the 'entry' dictionary right her
  entry = {
"exercise": exercise_input or "Unspecified",
"sets": int(sets_input),
"reps": int(reps_input),
"weight": float(weight_input),
"duration_min": float(duration_input),
"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

# 2. Make sure the dictionary exists in session state
if "data_now" not in st.session_state:
    st.session_state.data_now = {}

if name_input not in st.session_state.data_now:
    st.session_state.data_now[name_input] = []

# 3. Append and save cleanly on separate lines
# 1. First, create the entry with all the workout details
entry = {
"exercise": exercise_input or "Unspecified",
"sets": int(sets_input),
"reps": int(reps_input),
"weight": float(weight_input),
"duration_min": float(duration_input),
"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
}

# 2. Make sure the tracking dictionary exists in session state
if "data_now" not in st.session_state:
    st.session_state.data_now = {}

# 3. Make sure the user's name has a list waiting for entries
if name_input not in st.session_state.data_now:
    st.session_state.data_now[name_input] = []

# 4. Now append the entry and save!
st.session_state.data_now[name_input].append(entry)
save_data(st.session_state.data_now)

st.success("Workout logged successfully!")
# Initialize the dictionary if it doesn't exist yet
if "data_now" not in st.session_state:
    st.session_state.data_now = {}

# ... your other code ...

# When logging the workout (Line 73 area):
if name_input not in st.session_state.data_now:
    st.session_state.data_now[name_input] = []

st.session_state.data_now[name_input].append(entry)
save_data(st.session_state.data_now)
st.session_state.active_users.add(name_input)
st.success(f"Logged for {name_input}: {entry['exercise']} ({entry['sets']}x{entry['reps']})")

# --- TAB 2: DASHBOARD PANEL ---
with tab2:
    st.header("Dashboard — Everyone's Stats")

if st.button("Refresh Dashboard"):
    st.rerun()

if not st.session_state.data_now:
    st.info("No workouts logged yet.")
else:
    for person, entries in st.session_state.data_now.items():
        total_sets = sum(e["sets"] for e in entries)
    total_reps = sum(e["sets"] * e["reps"] for e in entries)
    total_volume = sum(e["sets"] * e["reps"] * e["weight"] for e in entries)
    total_duration = sum(e["duration_min"] for e in entries)

with st.expander(f"🏅 {person} ({len(entries)} workouts)", expanded=True):
    col1, col2 = st.columns(2)
with col1:
    st.write(f"**Total Sets:** {total_sets}")
st.write(f"**Total Reps:** {total_reps}")
with col2:
    st.write(f"**Total Volume:** {total_volume:.1f} lbs")
st.write(f"**Total Duration:** {total_duration:.1f} min")

# --- TAB 3: ACTIVE USERS PANEL ---
with tab3:
    st.header("Who's Logged In")

if not st.session_state.active_users:
    st.info("No one has logged a workout yet this session.")
else:
    st.warning(f"=== {len(st.session_state.active_users)} user(s) currently active ===")
for person in sorted(st.session_state.active_users):
    entries = st.session_state.data_now.get(person, [])
total_sets = sum(e["sets"] for e in entries)
total_reps = sum(e["sets"] * e["reps"] for e in entries)
total_volume = sum(e["sets"] * e["reps"] * e["weight"] for e in entries)
total_duration = sum(e["duration_min"] for e in entries)

st.markdown(f"### 👤 {person}")
st.text(f" Workouts logged: {len(entries)}")
st.write(f"Total sets: {total_sets} | Total reps: {total_reps}")
st.write(f"Total volume: {total_volume:.1f} | Total duration: {total_duration:.1f} min")

import streamlit as st
from supabase import create_client, Client
from datetime import date, timedelta

st.set_page_config(page_title="Team Workout Tracker", page_icon="🏀", layout="centered")

# ---------- Mobile-first styling ----------
st.markdown("""
<style>
    div.stButton > button {
        width: 100%;
        height: 3.2em;
        font-size: 1.1em;
        border-radius: 12px;
    }
    div.stCheckbox > label {
        font-size: 1.15em;
    }
    .stTextInput > div > div > input {
        font-size: 1.1em;
        height: 2.8em;
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
COACH_PIN = st.secrets.get("COACH_PIN", "0000")
TODAY = date.today()

# ---------- Session state ----------
if "player" not in st.session_state:
    st.session_state.player = None
if "is_coach" not in st.session_state:
    st.session_state.is_coach = False

# ---------- Data helpers ----------
def get_players():
    res = supabase.table("players").select("name").execute()
    return sorted([r["name"] for r in res.data])

def get_player_pin(name):
    res = supabase.table("players").select("pin").eq("name", name).execute()
    return res.data[0]["pin"] if res.data else None

def create_player(name, pin):
    supabase.table("players").insert({"name": name, "pin": pin}).execute()

def get_tasks_for_date(d):
    res = supabase.table("tasks").select("*").eq("task_date", str(d)).execute()
    return res.data

def add_task(d, task_name):
    supabase.table("tasks").insert({"task_date": str(d), "task_name": task_name}).execute()

def delete_task(task_id):
    supabase.table("tasks").delete().eq("id", task_id).execute()

def get_completions(player_name, task_ids):
    if not task_ids:
        return []
    res = supabase.table("completions").select("task_id").eq("player_name", player_name).in_("task_id", task_ids).execute()
    return [r["task_id"] for r in res.data]

def toggle_completion(player_name, task_id, done):
    if done:
        supabase.table("completions").upsert({"player_name": player_name, "task_id": task_id}).execute()
    else:
        supabase.table("completions").delete().eq("player_name", player_name).eq("task_id", task_id).execute()

def get_week_completions():
    week_start = TODAY - timedelta(days=TODAY.weekday())
    tasks_res = supabase.table("tasks").select("id, task_date").gte("task_date", str(week_start)).execute()
    task_ids = [t["id"] for t in tasks_res.data]
    if not task_ids:
        return {}
    comp_res = supabase.table("completions").select("player_name, task_id").in_("task_id", task_ids).execute()
    counts = {}
    for c in comp_res.data:
        counts[c["player_name"]] = counts.get(c["player_name"], 0) + 1
    return counts

def get_player_streak(player_name):
    comp_res = supabase.table("completions").select("task_id").eq("player_name", player_name).execute()
    task_ids = [c["task_id"] for c in comp_res.data]
    if not task_ids:
        return 0
    tasks_res = supabase.table("tasks").select("id, task_date").in_("id", task_ids).execute()
    completed_dates = set(t["task_date"] for t in tasks_res.data)
    streak, d = 0, TODAY
    while str(d) in completed_dates:
        streak += 1
        d -= timedelta(days=1)
    return streak

def get_today_completion_matrix():
    players = get_players()
    tasks = get_tasks_for_date(TODAY)
    task_ids = [t["id"] for t in tasks]
    if not task_ids:
        return players, tasks, {}
    comp_res = supabase.table("completions").select("player_name, task_id").in_("task_id", task_ids).execute()
    matrix = {}
    for c in comp_res.data:
        matrix.setdefault(c["player_name"], set()).add(c["task_id"])
    return players, tasks, matrix

# ---------- Login screen ----------
def login_screen():
    st.title("🏀 Team Login")
    players = get_players()
    mode = st.radio("Are you...", ["Returning player", "New player", "Coach"], horizontal=True)

    if mode == "Returning player":
        if not players:
            st.info("No players yet — add yourself as a new player.")
            return
        name = st.selectbox("Your name", players)
        pin = st.text_input("Your 4-digit PIN", type="password", max_chars=4)
        if st.button("Log In"):
            if pin == get_player_pin(name):
                st.session_state.player = name
                st.rerun()
            else:
                st.error("Wrong PIN. Try again.")

    elif mode == "New player":
        name = st.text_input("Pick your name")
        pin = st.text_input("Create a 4-digit PIN", type="password", max_chars=4)
        if st.button("Create Account"):
            if not name.strip():
                st.error("Enter a name.")
            elif not (pin.isdigit() and len(pin) == 4):
                st.error("PIN must be exactly 4 digits.")
            elif name in players:
                st.error("That name is taken — pick 'Returning player' instead.")
            else:
                create_player(name.strip(), pin)
                st.session_state.player = name.strip()
                st.rerun()

    else:  # Coach
        pin = st.text_input("Coach PIN", type="password")
        if st.button("Log In as Coach"):
            if pin == COACH_PIN:
                st.session_state.is_coach = True
                st.rerun()
            else:
                st.error("Wrong coach PIN.")

# ---------- Player dashboard ----------
def player_dashboard():
    player = st.session_state.player
    st.title(f"👋 Hey, {player}")

    if st.button("Log Out"):
        st.session_state.player = None
        st.rerun()

    tab1, tab2, tab3 = st.tabs(["✅ Today", "🏆 Leaderboard", "🔥 Streak"])

    with tab1:
        st.subheader("Today's Checklist")
        tasks = get_tasks_for_date(TODAY)
        if not tasks:
            st.info("No tasks assigned yet today.")
        else:
            task_ids = [t["id"] for t in tasks]
            done_ids = set(get_completions(player, task_ids))
            for t in tasks:
                checked = st.checkbox(t["task_name"], value=t["id"] in done_ids, key=f"task_{t['id']}")
                if checked != (t["id"] in done_ids):
                    toggle_completion(player, t["id"], checked)
                    st.rerun()

    with tab2:
        st.subheader("This Week's Leaderboard")
        counts = get_week_completions()
        if not counts:
            st.info("No completions logged yet this week.")
        else:
            ranked = sorted(counts.items(), key=lambda x: x[1], reverse=True)
            for i, (name, count) in enumerate(ranked, start=1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                st.write(f"{medal} **{name}** — {count} task(s) completed")

    with tab3:
        st.subheader("Your Streak")
        st.metric("Consecutive days logged", get_player_streak(player))

# ---------- Coach dashboard ----------
def coach_dashboard():
    st.title("🧑‍🏫 Coach View")

    if st.button("Log Out"):
        st.session_state.is_coach = False
        st.rerun()

    tab1, tab2 = st.tabs(["📋 Assign Tasks", "📊 Today's Completion"])

    with tab1:
        st.subheader(f"Tasks for {TODAY.strftime('%A, %b %d')}")
        new_task = st.text_input("New task (e.g. '50 pushups')")
        if st.button("Add Task"):
            if new_task.strip():
                add_task(TODAY, new_task.strip())
                st.rerun()

        for t in get_tasks_for_date(TODAY):
            col1, col2 = st.columns([4, 1])
            col1.write(f"• {t['task_name']}")
            if col2.button("Delete", key=f"del_{t['id']}"):
                delete_task(t["id"])
                st.rerun()

    with tab2:
        st.subheader("Who's Done What Today")
        players, tasks, matrix = get_today_completion_matrix()
        if not tasks:
            st.info("No tasks assigned today yet.")
        elif not players:
            st.info("No players registered yet.")
        else:
            for p in players:
                completed = len(matrix.get(p, set()))
                total = len(tasks)
                st.write(f"**{p}**: {completed}/{total} tasks completed")
                st.progress(completed / total if total else 0)

# ---------- Router ----------
if st.session_state.is_coach:
    coach_dashboard()
elif st.session_state.player:
    player_dashboard()
else:
    login_screen()

import json
import os
from datetime import datetime, timedelta
#import ipywidgets as widgets
#from IPython.display import display, clear_output

DATA_FILE = "workout_data.json"
TIMEOUT_MINUTES = 10  # how long someone stays "active" without activity

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

data = load_data()
active_sessions = {}  # name -> datetime of last activity

def mark_active(name):
    if name:
        active_sessions[name] = datetime.now()

def mark_inactive(name):
    active_sessions.pop(name, None)

def prune_inactive():
    cutoff = datetime.now() - timedelta(minutes=TIMEOUT_MINUTES)
    stale = [name for name, last_seen in active_sessions.items() if last_seen < cutoff]
    for name in stale:
        active_sessions.pop(name, None)

# ----- Login / Logout Panel -----
login_name_input = widgets.Text(description="Name:")
login_button = widgets.Button(description="Log In", button_style="success")
logout_button = widgets.Button(description="Log Out", button_style="danger")
login_output = widgets.Output()

def do_login(b):
    with login_output:
        clear_output()
        name = login_name_input.value.strip()
        if not name:
            print("Enter a name first.")
            return
        mark_active(name)
        print(f"{name} is now logged in / active.")

def do_logout(b):
    with login_output:
        clear_output()
        name = login_name_input.value.strip()
        if not name:
            print("Enter a name first.")
            return
        mark_inactive(name)
        print(f"{name} logged out.")

login_button.on_click(do_login)
logout_button.on_click(do_logout)

login_panel = widgets.VBox([
    widgets.HTML("<h3>Login</h3>"),
    login_name_input,
    widgets.HBox([login_button, logout_button]),
    login_output
])

# ----- Log Workout Panel (unchanged) -----
name_input = widgets.Text(description="Name:")
exercise_input = widgets.Text(description="Exercise:")
sets_input = widgets.IntText(description="Sets:", value=3)
reps_input = widgets.IntText(description="Reps:", value=10)
weight_input = widgets.FloatText(description="Weight (lb):", value=0)
duration_input = widgets.FloatText(description="Duration (min):", value=0)
log_button = widgets.Button(description="Log Workout", button_style="success")
log_output = widgets.Output()

def log_workout(b):
    with log_output:
        clear_output()
        name = name_input.value.strip()
        if not name:
            print("Enter a name first.")
            return
        entry = {
            "exercise": exercise_input.value.strip() or "Unspecified",
            "sets": sets_input.value,
            "reps": reps_input.value,
            "weight": weight_input.value,
            "duration_min": duration_input.value,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        data.setdefault(name, []).append(entry)
        save_data(data)
        mark_active(name)  # logging a workout counts as activity
        print(f"Logged for {name}: {entry}")

log_button.on_click(log_workout)

log_panel = widgets.VBox([
    widgets.HTML("<h3>Log a Workout</h3>"),
    name_input, exercise_input, sets_input, reps_input,
    weight_input, duration_input, log_button, log_output
])

# ----- Dashboard Panel (everyone's full stats, regardless of active status) -----
dash_button = widgets.Button(description="Refresh Dashboard", button_style="info")
dash_output = widgets.Output()

def show_dashboard(b=None):
    with dash_output:
        clear_output()
        data_now = load_data()
        if not data_now:
            print("No workouts logged yet.")
            return
        for person, entries in data_now.items():
            total_sets = sum(e["sets"] for e in entries)
            total_reps = sum(e["sets"] * e["reps"] for e in entries)
            total_volume = sum(e["sets"] * e["reps"] * e["weight"] for e in entries)
            total_duration = sum(e["duration_min"] for e in entries)
            print(f"=== {person} ===")
            print(f"  Workouts logged: {len(entries)}")
            print(f"  Total sets: {total_sets}")
            print(f"  Total reps: {total_reps}")
            print(f"  Total volume (sets x reps x weight): {total_volume:.1f}")
            print(f"  Total duration: {total_duration:.1f} min")
            print()

dash_button.on_click(show_dashboard)

dashboard_panel = widgets.VBox([
    widgets.HTML("<h3>Dashboard — Everyone's Stats</h3>"),
    dash_button, dash_output
])

# ----- Active Users Panel (only currently online) -----
users_button = widgets.Button(description="Refresh Active Users", button_style="warning")
users_output = widgets.Output()

def show_active_users(b=None):
    prune_inactive()
    with users_output:
        clear_output()
        if not active_sessions:
            print("No one is currently active.")
            return
        print(f"=== {len(active_sessions)} user(s) currently active (last {TIMEOUT_MINUTES} min) ===\n")
        for person, last_seen in sorted(active_sessions.items()):
            mins_ago = (datetime.now() - last_seen).seconds // 60
            print(f"{person} — active {mins_ago} min ago")

users_button.on_click(show_active_users)

users_panel = widgets.VBox([
    widgets.HTML("<h3>Who's Active Right Now</h3>"),
    users_button, users_output
])

# ----- Assemble tabs -----
tabs = widgets.Tab(children=[login_panel, log_panel, dashboard_panel, users_panel])
tabs.set_title(0, "Login")
tabs.set_title(1, "Log Workout")
tabs.set_title(2, "Dashboard")
tabs.set_title(3, "Active Users")

display(tabs)
show_dashboard()
show_active_users()
