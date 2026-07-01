
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

if st.button("Log Workout", type="primary"):
if not name_input:
st.error("Enter a name first.")
else:
entry = {
"exercise": exercise_input or "Unspecified",
"sets": int(sets_input),
"reps": int(reps_input),
"weight": float(weight_input),
"duration_min": float(duration_input),
"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
}

# Update data dictionary
if name_input not in data_now:
data_now[name_input] = []
data_now[name_input].append(entry)

save_data(data_now)
st.session_state.active_users.add(name_input)

st.success(f"Logged for {name_input}: {entry['exercise']} ({entry['sets']}x{entry['reps']})")

# --- TAB 2: DASHBOARD PANEL ---
with tab2:
st.header("Dashboard — Everyone's Stats")

if st.button("Refresh Dashboard"):
st.rerun()

if not data_now:
st.info("No workouts logged yet.")
else:
for person, entries in data_now.items():
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
entries = data_now.get(person, [])
total_sets = sum(e["sets"] for e in entries)
total_reps = sum(e["sets"] * e["reps"] for e in entries)
total_volume = sum(e["sets"] * e["reps"] * e["weight"] for e in entries)
total_duration = sum(e["duration_min"] for e in entries)

st.markdown(f"### 👤 {person}")
st.text(f" Workouts logged: {len(entries)}
st.write(f"Total sets: {total_sets} | Total reps: {total_reps}")
st.write(f"Total volume: {total_volume:.1f} | Total duration: {total_duration:.1f} min")
