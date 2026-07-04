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

/* Make inline delete buttons look like clean clickable text links */
div.stButton > button[key*="inline_del_"] {
    background-color: transparent !important;
    border: none !important;
    color: #ff4b4b !important;
    text-align: right !important;
    height: auto !important;
    padding: 0 !important;
    width: auto !important;
    font-size: 1.1em !important;
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
