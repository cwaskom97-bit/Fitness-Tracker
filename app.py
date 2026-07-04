import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta
import base64

# 1. Page Configuration (Browser Tab Title and Icon)
st.set_page_config(page_title="RunItBack", page_icon="🏃‍♂️", layout="centered")

# Initialize Theme States Early - Defaulting directly to Dark Mode
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Dark"

# Inject Runtime Theme configuration values
if st.session_state.theme_mode == "Dark":
    st._config.set_option("theme.base", "dark")
    st._config.set_option("theme.backgroundColor", "#0E1117")
    st._config.set_option("theme.secondaryBackgroundColor", "#262730")
    st._config.set_option("theme.textColor", "#FAFAFA")
else:
    st._config.set_option("theme.base", "light")
    st._config.set_option("theme.backgroundColor", "#FFFFFF")
    st._config.set_option("theme.secondaryBackgroundColor", "#F0F2F6")
    st._config.set_option("theme.textColor", "#31333F")

# Custom CSS Styling
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    overflow-y: auto !important;
    scroll-behavior: smooth;
}

/* Default standard button styling */
div.stButton > button {
    width: 100%;
    height: 3em;
    font-size: 1.05em;
    border-radius: 10px;
}

/* Distinct styling targeting ONLY the Finish Workout button to make it green */
div.stButton > button[key*="finish_workout_action_btn"] {
    background-color: #28a745 !important;
    color: white !important;
    border: none !important;
    font-weight: bold !important;
}
div.stButton > button[key*="finish_workout_action_btn"]:hover {
    background-color: #218838 !important;
    color: white !important;
}

/* Unified circular crop layout structure */
.profile-pic-round {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    object-fit: cover;
    border: 2px solid #ff4b4b;
    display: inline-block;
    vertical-align: middle;
}
.header-container {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 20px;
}
.header-name {
    font-size: 1.3em;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# Helper function to convert uploaded file to base64
def file_to_base64(uploaded_file):
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        return base64.b64encode(file_bytes).decode()
    return None

# Default generic placeholder avatar icon
DEFAULT_AVATAR = "https://www.w3schools.com/howto/img_avatar.png"

# 2. Database Initialization
@st.cache_resource
def get_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_client()

# 3. Session State Tracker
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "profile_pic" not in st.session_state:
    st.session_state.profile_pic = None

TIMEOUT_MINUTES = 10

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

# Render User identity elements globally in the upper workspace when logged in
if st.session_state.current_user:
    with st.container():
        img_src = f"data:image/png;base64,{st.session_state.profile_pic}" if st.session_state.profile_pic else DEFAULT_AVATAR
        
        st.markdown(f"""
        <div class="header-container">
            <img class="profile-pic-round" src="{img_src}">
            <div class="header-name">{st.session_state.current_user}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Profile Configuration Expander (Edit Pic & Toggle Mode)
        with st.expander("⚙️ Edit Profile / Settings"):
            new_pic = st.file_uploader("Update Profile Picture", type=["png", "jpg", "jpeg"], key="update_avatar_input")
            if new_pic:
                st.session_state.profile_pic = file_to_base64(new_pic)
                st.success("Profile photo updated!")
                st.rerun()
                
            # Theme switcher
            current_mode = st.session_state.theme_mode
            theme_toggle = st.toggle("Dark Mode Active", value=(current_mode == "Dark"), key="theme_toggle_widget")
            expected_mode = "Dark" if theme_toggle else "Light"
            if expected_mode != current_mode:
                st.session_state.theme_mode = expected_mode
                st.rerun()
        st.write("---")

# 5. Interface Tabs
def login_tab():
    st.subheader("Login / Registration")
    
    if not st.session_state.current_user:
        col_first, col_last = st.columns(2)
        with col_first:
            first_name = st.text_input("First Name", key="user_first_name")
        with col_last:
            last_name = st.text_input("Last Name", key="user_last_name")
            
        uploaded_file = st.file_uploader("Upload Profile Picture", type=["png", "jpg", "jpeg"], key="user_profile_pic")
        st.caption("(Optional)")
            
        if st.button("Log In", key="login_btn"):
            if not first_name.strip() or not last_name.strip():
                st.error("Please enter both your first and last name.")
            else:
                full_name = f"{first_name.strip()} {last_name.strip()}"
                st.session_state.current_user = full_name
                
                if uploaded_file is not None:
                    st.session_state.profile_pic = file_to_base64(uploaded_file)
                
                mark_active(full_name)
                st.success(f"Successfully logged in as {full_name}")
                st.rerun()
    else:
        st.info(f"Logged in as: **{st.session_state.current_user}**")
        if st.button("Log Out", key="action_logout_btn"):
            mark_inactive(st.session_state.current_user)
            st.session_state.current_user = None
            st.session_state.profile_pic = None
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

    # The green button style maps directly onto this key name
    if st.button("Finish Workout", key="finish_workout_action_btn"):
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
                log_text = f" {entry.get('exercise')}: {entry.get('sets')} sets x {entry.get('reps')} reps @ {entry.get('weight')} lbs (Rest: {entry.get('rest_time', 'N/A')}s)"
                
                # Strict Ownership Check: Only show delete button if workout 'name' matches 'current_user'
                if entry.get("name") == st.session_state.current_user:
                    col_text, col_del = st.columns([0.9, 0.1])
                    col_text.write(log_text)
                    if col_del.button("❌", key=f"del_{entry.get('id')}"):
                        delete_workout(entry.get('id'))
                else:
                    # Renders as standard text with no button for other users' entries
                    st.write(log_text)

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
st.title("RunItBack 🏃‍♂️")

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
