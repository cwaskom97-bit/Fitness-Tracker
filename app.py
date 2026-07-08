import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta
import base64
import random
import string
import os

# ==========================================
# 1. Page Configuration
# ==========================================
st.set_page_config(page_title="RunItBack", page_icon="🏃‍♂️", layout="centered")

st.title("RunItBack 🏃‍♂️")

# ==========================================
# 2. APP THEME & INITIALIZATION
# ==========================================

if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Dark"
if "hub_code" not in st.session_state:
    st.session_state.hub_code = None

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

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    overflow-y: auto !important;
    scroll-behavior: smooth;
}
div.stButton > button {
    width: 100%;
    height: 3em;
    font-size: 1.05em;
    border-radius: 10px;
}
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

def file_to_base64(uploaded_file):
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        return base64.b64encode(file_bytes).decode()
    return None

def generate_hub_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

DEFAULT_AVATAR = "https://www.w3schools.com/howto/img_avatar.png"

@st.cache_resource
def get_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_client()

if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "profile_pic" not in st.session_state:
    st.session_state.profile_pic = None

TIMEOUT_MINUTES = 10

# ==========================================
# 3. DATABASE & STORAGE INTERACTIONS
# ==========================================
def upload_video_to_supabase(file_payload, unique_name):
    """Uploads video file binary to Supabase storage bucket and returns public link"""
    try:
        bucket_name = "workout-videos"
        # Rewind file buffer position to read clean data safely
        file_payload.seek(0)
        file_bytes = file_payload.read()
        
        # Determine clean content type based on extension
        file_ext = os.path.splitext(unique_name)[1].lower()
        mime_type = "video/mp4"
        if "mov" in file_ext: mime_type = "video/quicktime"
        elif "avi" in file_ext: mime_type = "video/x-msvideo"

        # Execute bucket upload binary tracking payload
        res = supabase.storage.from_(bucket_name).upload(
            path=unique_name,
            file=file_bytes,
            file_options={"content-type": mime_type, "x-upsert": "true"}
        )
        
        # Retrieve final public accessibility asset routing URL 
        public_url_res = supabase.storage.from_(bucket_name).get_public_url(unique_name)
        return public_url_res
    except Exception as e:
        st.error(f"Cloud Storage Error: {e}")
        return None

def verify_hub_exists(hub_code):
    try:
        res_comp = supabase.table("Completions").select("hub_code").eq("hub_code", hub_code).limit(1).execute()
        if hasattr(res_comp, 'data') and len(res_comp.data) > 0:
            return True
        res_tasks = supabase.table("tasks").select("hub_code").eq("hub_code", hub_code).limit(1).execute()
        if hasattr(res_tasks, 'data') and len(res_tasks.data) > 0:
            return True
        return False
    except Exception as e:
        return False

def mark_active(name, hub_code):
    try:
        supabase.table("tasks").upsert({
            "task_name": name, 
            "task_date": datetime.utcnow().date().isoformat(),
            "hub_code": hub_code
        }).execute()
    except Exception as e:
        pass

def mark_inactive(name, hub_code):
    try:
        supabase.table("tasks").delete().eq("task_name", name).eq("hub_code", hub_code).execute()
    except Exception as e:
        pass

def get_active_users(hub_code):
    try:
        cutoff = (datetime.utcnow() - timedelta(minutes=TIMEOUT_MINUTES)).date().isoformat()
        res = supabase.table("tasks").select("*").gte("task_date", cutoff).eq("hub_code", hub_code).execute()
        return res.data if hasattr(res, 'data') else []
    except Exception as e:
        return []

def get_all_workouts(hub_code):
    try:
        res = supabase.table("Completions").select("*").eq("hub_code", hub_code).order("created_at", descending=True).execute()
        return res.data if hasattr(res, 'data') else []
    except Exception as e:
        return []

def log_workout(name, exercise, sets, reps, weight, duration, rest_time, hub_code, completed=False, video_url=None):
    try:
        supabase.table("Completions").insert({
            "name": name, 
            "exercise": exercise or "Unspecified", 
            "sets": sets, 
            "reps": reps, 
            "weight": weight, 
            "duration": duration,
            "rest_time": rest_time,
            "completed": completed,
            "hub_code": hub_code,
            "video_url": video_url
        }).execute()
        st.success("Workout recorded permanently to cloud database!")
    except Exception as e:
        st.error(f"Database Error: {e}")

def delete_workout(workout_id):
    try:
        supabase.table("Completions").delete().eq("id", workout_id).execute()
        st.success("Workout deleted successfully!")
        st.rerun()
    except Exception as e:
        st.error(f"Failed to delete workout: {e}")

# Render identity elements
if st.session_state.current_user:
    with st.container():
        img_src = f"data:image/png;base64,{st.session_state.profile_pic}" if st.session_state.profile_pic else DEFAULT_AVATAR
        st.markdown(f"""
        <div class="header-container">
            <img class="profile-pic-round" src="{img_src}">
            <div class="header-name">{st.session_state.current_user}</div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("⚙️ Edit Profile / Settings"):
            st.info(f"🔑 **Your Shared Hub Code:** `{st.session_state.hub_code}`")
            st.caption("This matches the Hub Code entered at the login window.")
            st.write("---")
            
            new_pic = st.file_uploader("Update Profile Picture", type=["png", "jpg", "jpeg"], key="update_avatar_input")
            if new_pic:
                st.session_state.profile_pic = file_to_base64(new_pic)
                st.success("Profile photo updated!")
                st.rerun()
                
            current_mode = st.session_state.theme_mode
            theme_toggle = st.toggle("Dark Mode Active", value=(current_mode == "Dark"), key="theme_toggle_widget")
            expected_mode = "Dark" if theme_toggle else "Light"
            if expected_mode != current_mode:
                st.session_state.theme_mode = expected_mode
                st.rerun()
        st.write("---")

# ==========================================
# 4. INTERFACE TABS DEFINITIONS
# ==========================================
def login_tab():
    st.subheader("Hub Selection / Profile Creation")
    if not st.session_state.current_user:
        col_first, col_last = st.columns(2)
        with col_first:
            first_name = st.text_input("First Name", key="user_first_name")
        with col_last:
            last_name = st.text_input("Last Name", key="user_last_name")
            
        uploaded_file = st.file_uploader("Upload Profile Picture", type=["png", "jpg", "jpeg"], key="user_profile_pic")
        st.caption("(Optional)")
        st.write("---")
        st.markdown("#### Enter Hub Code or Create Hub")
        join_hub_code = st.text_input("Enter Hub Code", key="join_hub_input").strip().upper()
        st.info("💡 Create hub then enter code above")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Log In to Hub", key="login_btn"):
                if not first_name.strip() or not last_name.strip():
                    st.error("Please enter both your first and last name.")
                elif not join_hub_code:
                    st.error("Please type a Hub Code to log into.")
                else:
                    if not verify_hub_exists(join_hub_code):
                        st.error("Hub code entered does not exist")
                    else:
                        st.session_state.hub_code = join_hub_code
                        full_name = f"{first_name.strip().title()} {last_name.strip().title()}"
                        st.session_state.current_user = full_name
                        if uploaded_file is not None:
                            st.session_state.profile_pic = file_to_base64(uploaded_file)
                        mark_active(full_name, join_hub_code)
                        st.success(f"Logged into Hub {join_hub_code} successfully!")
                        st.rerun()
                        
        with col_btn2:
            if st.button("✨ Create New Hub", key="create_hub_btn"):
                new_code = generate_hub_code()
                try:
                    supabase.table("tasks").insert({
                        "task_name": "Hub Initialized",
                        "task_date": datetime.utcnow().date().isoformat(),
                        "hub_code": new_code
                    }).execute()
                    st.success(f"🎉 Hub created: **{new_code}**")
                except Exception as e:
                    st.error(f"Error saving new Hub to database: {e}")
    else:
        st.info(f"Logged in as: **{st.session_state.current_user}** (Hub: `{st.session_state.hub_code}`)")
        if st.button("Log Out", key="action_logout_btn"):
            mark_inactive(st.session_state.current_user, st.session_state.hub_code)
            st.session_state.current_user = None
            st.session_state.profile_pic = None
            st.session_state.hub_code = None
            st.success("Logged out successfully.")
            st.rerun()

def log_workout_tab():
    st.subheader("Log a Workout")
    name = st.text_input("Account:", value=st.session_state.current_user or "", key="workout_entry_name", disabled=True)
    
    st.write("---")
    st.markdown("### 🎥 Live Workout Camera & Video Tracker")
    
    workout_video_frame = st.camera_input("Take Live Form Snapshot", key="workout_tracker_camera")
    if workout_video_frame:
        st.caption("✅ Snapshot captured successfully.")
        
    workout_video_file = st.file_uploader("Record / Upload Workout Video", type=["mp4", "mov", "avi", "m4v"], key="workout_tracker_video")
    uploaded_video_url = None
    
    if workout_video_file:
        st.caption("✅ Video recording recognized.")
        # Process immediate file payload upload to Cloud Bucket Storage
        with st.spinner("Uploading video to cloud tracking file..."):
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_filename = f"{st.session_state.hub_code}_{timestamp_str}_{workout_video_file.name.replace(' ', '_')}"
            uploaded_video_url = upload_video_to_supabase(workout_video_file, clean_filename)
            if uploaded_video_url:
                st.success("Video linked successfully and ready for database entry!")
                
    st.write("---")
    exercise = st.text_input("Exercise:", key="workout_entry_exercise")
    
    col1, col2 = st.columns(2)
    with col1:
        sets = st.number_input("Sets:", min_value=0, value=3, step=1, key="workout_entry_sets")
        weight = st.number_input("Weight (lb):", min_value=0.0, value=0.0, step=5.0, key="workout_entry_weight")
    with col2:
        reps = st.number_input("Reps:", min_value=0, value=10, step=1, key="workout_entry_reps")
        duration = st.number_input("Duration (min):", min_value=0.0, value=0.0, step=1.0, key="workout_entry_duration")
        
    rest_time = st.number_input("Rest Time (seconds):", min_value=0, value=60, step=5, key="workout_entry_rest")

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("Log Workout", key="normal_log_workout_btn"):
            if not name.strip():
                st.error("Please setup your profile layout first.")
            else:
                log_workout(name.strip(), exercise.strip(), sets, reps, weight, duration, rest_time, st.session_state.hub_code, completed=False, video_url=uploaded_video_url)
                mark_active(name.strip(), st.session_state.hub_code)
                
    with btn_col2:
        if st.button("Finish Workout", key="finish_workout_action_btn"):
            if not name.strip():
                st.error("Please setup your profile layout first.")
            else:
                log_workout(name.strip(), exercise.strip(), sets, reps, weight, duration, rest_time, st.session_state.hub_code, completed=True, video_url=uploaded_video_url)
                mark_active(name.strip(), st.session_state.hub_code)

def dashboard_tab():
    st.subheader(f"Hub Dashboard — Hub: {st.session_state.hub_code}")
    if st.button("Refresh Dashboard", key="dashboard_manual_refresh_btn"):
        st.rerun()

    workouts = get_all_workouts(st.session_state.hub_code)
    if not workouts:
        st.info("No logged workouts found in this Hub.")
        return

    by_person = {}
    for w in workouts:
        by_person.setdefault(w.get("name", "Unknown"), []).append(w)

    for person, entries in by_person.items():
        total_sets = sum(int(e.get("sets", 0) or 0) for e in entries)
        with st.expander(f"{person} — {len(entries)} workouts logged"):
            st.write(f"**Total Sets Tracked:** {total_sets}")
            for entry in entries:
                log_text = f"{entry.get('exercise')}: {entry.get('sets')} sets x {entry.get('reps')} reps @ {entry.get('weight')} lbs (Rest: {entry.get('rest_time', 'N/A')}s)"
                db_name = str(entry.get("name", "")).strip().lower()
                session_name = str(st.session_state.current_user or "").strip().lower()
                
                if session_name and (session_name in db_name or db_name in session_name):
                    col_text, col_del = st.columns([0.88, 0.12])
                    col_text.write(log_text)
                    if col_del.button("❌", key=f"inline_del_{entry.get('id')}"):
                        delete_workout(entry.get('id'))
                else:
                    st.write(log_text)

def active_users_tab():
    st.subheader("Who's Active in this Hub")
    if st.button("Refresh Active List", key="active_users_manual_refresh_btn"):
        st.rerun()

    active = get_active_users(st.session_state.hub_code)
    if not active:
        st.info("No active users online in this Hub.")
        return

    for user in active:
        user_name = user.get("task_name", "Anonymous User")
        st.write(f" 🔥 **{user_name}** is actively crushing it")

def finished_workouts_tab():
    st.subheader("Finished Workouts")
    if st.button("Refresh Workouts", key="finished_workouts_refresh_btn"):
        st.rerun()

    workouts = get_all_workouts(st.session_state.hub_code)
    if not workouts:
        st.info("No finished workouts recorded yet.")
        return

    finished_entries = [w for w in workouts if w.get("completed") is True]
    if not finished_entries:
        st.info("No workouts finalized using 'Finish Workout' yet.")
        return

    for entry in finished_entries:
        person = entry.get("name", "Unknown")
        exercise = entry.get("exercise", "Unspecified")
        sets = entry.get("sets", 0)
        reps = entry.get("reps", 0)
        weight = entry.get("weight", 0.0)
        duration = entry.get("duration", 0.0)
        st.write(f"🏆 **{person}** finalized workout: **{exercise}** — {sets} sets x {reps} reps @ {weight} lbs ({duration} mins)")

def recorded_workouts_tab():
    st.subheader("📼 Recorded Workouts Hub Feed")
    st.caption("Review cloud video clips and workout performance records uploaded by hub members.")
    
    if st.button("Refresh Videos Feed", key="videos_feed_refresh_btn"):
        st.rerun()

    workouts = get_all_workouts(st.session_state.hub_code)
    if not workouts:
        st.info("No recordings logged in this hub yet.")
        return
        
    # Filter entries that contain valid uploaded cloud URLs
    video_entries = [w for w in workouts if w.get("video_url")]
    
    if not video_entries:
        st.info("No logged entries have an attached video recording file yet.")
        return

    for entry in video_entries:
        with st.container():
            st.markdown(f"#### 🎥 {entry.get('name')} — {entry.get('exercise')}")
            st.write(f"**Stats:** {entry.get('sets')} sets x {entry.get('reps')} reps @ {entry.get('weight')} lbs")
            st.video(entry.get("video_url"))
            st.write("---")

# ==========================================
# 5. APP ROUTER NAVIGATION LOGIC
# ==========================================
if st.session_state.current_user is None:
    tab1, = st.tabs(["Hub Registration"])
    with tab1:
        login_tab()
        st.warning("Please join or create a workout Hub to unlock tracking options.")
else:
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Hub Options", "Log Workout", "Dashboard", "Active Users", "Finished Workouts", "Recorded Workouts"])
    with tab1:
        login_tab()
    with tab2:
        log_workout_tab()
    with tab3:
        dashboard_tab()
    with tab4:
        active_users_tab()
    with tab5:
        finished_workouts_tab()
    with tab6:
        recorded_workouts_tab()
