import cv2
import mediapipe as mp
import numpy as np
from scipy.spatial import distance as dist
import streamlit as st
from PIL import Image
import time
import datetime
from collections import deque
import os
from io import BytesIO
import base64
import subprocess
import sys

# Try to import audio libraries
try:
    from pygame import mixer
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("pygame not available, will use browser-based audio")

# ---------- Landmarks ----------
L_EYE = [33, 160, 158, 133, 153, 144]
R_EYE = [263, 387, 385, 362, 380, 373]
UPPER_LIP = [13, 14]
LOWER_LIP = [17, 18]
LEFT_MOUTH = 78
RIGHT_MOUTH = 308

# ---------- Helper Functions ----------
def eye_aspect_ratio(eye):
    if len(eye) < 6:
        return 0.0
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    if C == 0:
        return 0.0
    return (A + B) / (2.0 * C)

def mouth_aspect_ratio(upper_pts, lower_pts, left_pt, right_pt):
    vertical = np.mean([dist.euclidean(u, l) for u, l in zip(upper_pts, lower_pts)])
    horizontal = dist.euclidean(left_pt, right_pt)
    if horizontal == 0:
        return 0.0
    return vertical / horizontal

def get_fatigue_threshold(speed, weather, time_period):
    base_thresh = 2.0
    if speed < 15:
        return float('inf')
    elif speed < 40:
        base_thresh = 3.0
    elif speed >= 80:
        base_thresh = 1.5
    if time_period.lower() == "night":
        base_thresh *= 0.7
    if weather.lower() in ["fog", "rain", "storm"]:
        base_thresh *= 0.8
    return base_thresh

def generate_beep_sound(frequency=1000, duration=0.5, sample_rate=44100):
    """Generate a beep sound as numpy array"""
    t = np.linspace(0, duration, int(sample_rate * duration))
    wave = np.sin(2 * np.pi * frequency * t)
    # Add envelope to avoid clicks
    envelope = np.exp(-3 * t)
    wave = wave * envelope
    # Normalize to 16-bit range
    wave = np.int16(wave * 32767)
    return wave

def play_alert_sound():
    """Play alert sound using available method"""
    if PYGAME_AVAILABLE:
        try:
            if not mixer.get_init():
                mixer.init()
            # Generate beep sound
            sound_array = generate_beep_sound(1200, 0.3)
            # Convert to stereo
            sound_stereo = np.column_stack((sound_array, sound_array))
            sound = mixer.Sound(sound_stereo)
            sound.play()
        except Exception as e:
            print(f"Audio playback error: {e}")
    else:
        # Fallback: use streamlit's audio with autoplay
        try:
            sound_array = generate_beep_sound(1200, 0.3)
            # This will be handled in the UI section
            return sound_array
        except Exception as e:
            print(f"Audio generation error: {e}")

def autoplay_audio(sound_array, sample_rate=44100):
    """Create HTML audio element with autoplay"""
    # Convert numpy array to bytes
    byte_io = BytesIO()
    # Simple WAV header
    import struct
    import wave
    
    # Create WAV in memory
    wav_io = BytesIO()
    with wave.open(wav_io, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(sound_array.tobytes())
    
    wav_io.seek(0)
    b64 = base64.b64encode(wav_io.read()).decode()
    
    audio_html = f"""
    <audio autoplay>
        <source src="data:audio/wav;base64,{b64}" type="audio/wav">
    </audio>
    """
    return audio_html

# ---------- Streamlit UI ----------
st.set_page_config(layout="wide", page_title="🚗 Driver Fatigue Detection")
st.title("🚗 Advanced Driver Fatigue Detection Dashboard")

# Add custom CSS for better UI
st.markdown("""
    <style>
    .stAlert {
        padding: 1rem;
        margin: 1rem 0;
    }
    .big-font {
        font-size: 24px !important;
        font-weight: bold;
    }
    .metric-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for audio
if 'play_sound' not in st.session_state:
    st.session_state.play_sound = False

# Layout columns
left_col, right_col = st.columns([3, 1])

# Controls in right column
with right_col:
    st.subheader("🎛️ Control Panel")
    
    # Settings in an expander for cleaner UI
    with st.expander("⚙️ Detection Settings", expanded=True):
        speed = st.slider("🚗 Vehicle Speed (km/h)", 0, 120, 60)
        time_period = st.selectbox("🕐 Time of Day", ["Day", "Night"])
        weather = st.selectbox("🌤️ Weather Condition", ["Clear", "Fog", "Rain", "Storm"])
        demo_mode = st.checkbox("🎬 Demo Mode (driver_demo.mp4)")
    
    with st.expander("🎚️ Threshold Settings", expanded=False):
        EAR_THRESH = st.slider("EAR Threshold", 0.15, 0.35, 0.25, 0.01)
        MAR_THRESH = st.slider("MAR Threshold", 0.5, 0.8, 0.65, 0.05)
        sound_enabled = st.checkbox("🔊 Enable Audio Alerts", value=True)
    
    st.markdown("---")
    
    # Action buttons with better spacing
    col1, col2 = st.columns(2)
    with col1:
        calibrate_btn = st.button("📸 Calibrate", use_container_width=True)
    with col2:
        start_btn = st.button("▶ START", use_container_width=True, type="primary")
    
    stop_btn = st.button("⏸ STOP", use_container_width=True)
    
    st.markdown("---")
    
    # Session Info with better formatting
    st.markdown("### 📊 Session Statistics")
    session_text = st.empty()
    alerts_text = st.empty()
    status_display = st.empty()

# Video display in left column
with left_col:
    video_placeholder = st.empty()
    calibration_progress = st.empty()
    alert_placeholder = st.empty()

# ---------- MediaPipe setup ----------
mp_face = mp.solutions.face_mesh
face_mesh = mp_face.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# ---------- Detection variables ----------
cap = None
running = False
base_open_ear = None
eyes_closed_start = None
yawn_start = None
ear_history = deque(maxlen=3)
consecutive_drowsy = 0
total_alerts = 0
session_start = None
ear_values = deque(maxlen=100)
mar_values = deque(maxlen=100)
timestamps = deque(maxlen=100)
last_alert_time = 0

# ---------- Helper functions ----------
def compute_frame_ear(frame):
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(frame_rgb)
    if not results.multi_face_landmarks:
        return None
    lm = results.multi_face_landmarks[0]
    h, w = frame.shape[:2]
    left_pts = [(int(lm.landmark[i].x * w), int(lm.landmark[i].y * h)) for i in L_EYE]
    right_pts = [(int(lm.landmark[i].x * w), int(lm.landmark[i].y * h)) for i in R_EYE]
    l_ear = eye_aspect_ratio(left_pts)
    r_ear = eye_aspect_ratio(right_pts)
    if l_ear > 0 and r_ear > 0:
        return (l_ear + r_ear) / 2
    elif l_ear > 0:
        return l_ear
    elif r_ear > 0:
        return r_ear
    else:
        return None

def log_event(ear, mar):
    global total_alerts
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("fatigue_log.txt", "a") as f:
        f.write(f"{timestamp} | ALERT #{total_alerts} | EAR={ear:.3f} | MAR={mar:.3f} | "
                f"Speed={speed} km/h | Weather={weather} | Time={time_period}\n")

# ---------- Calibration with Live Feed ----------
if calibrate_btn:
    cap_calib = cv2.VideoCapture(0)
    if demo_mode:
        if os.path.exists("driver_demo.mp4"):
            cap_calib = cv2.VideoCapture("driver_demo.mp4")
        else:
            st.error("Demo video not found")
            cap_calib = None
    
    if cap_calib:
        calibration_progress.info("👁️ **Calibrating...** Keep your eyes wide open!")
        progress_bar = calibration_progress.progress(0)
        
        ear_vals = []
        start_time = time.time()
        frame_count = 0
        
        while time.time() - start_time < 3:
            ret, frame = cap_calib.read()
            if not ret:
                if demo_mode:
                    cap_calib.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break
            
            frame = cv2.resize(frame, (640, 480))
            
            # Show calibration on frame
            elapsed = time.time() - start_time
            remaining = 3 - elapsed
            cv2.putText(frame, f"Calibrating: {remaining:.1f}s", 
                       (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 3)
            cv2.putText(frame, "Keep eyes WIDE OPEN!", 
                       (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            # Show live feed during calibration
            video_placeholder.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), 
                                   channels="RGB", use_container_width=True)
            
            ear = compute_frame_ear(frame)
            if ear is not None and ear > 0.1:
                ear_vals.append(ear)
            
            # Update progress bar
            progress = int((elapsed / 3.0) * 100)
            progress_bar.progress(min(progress, 100))
            
            frame_count += 1
            time.sleep(0.033)  # ~30 FPS
        
        cap_calib.release()
        progress_bar.empty()
        
        if ear_vals:
            ear_vals = sorted(ear_vals)
            # Remove outliers
            ear_vals = ear_vals[len(ear_vals)//4:-len(ear_vals)//4] if len(ear_vals) > 4 else ear_vals
            base_open_ear = np.mean(ear_vals)
            EAR_THRESH = max(0.18, base_open_ear * 0.65)
            calibration_progress.success(
                f"✅ **Calibration Complete!**\n\n"
                f"Open-eye EAR: **{base_open_ear:.3f}**\n\n"
                f"New Threshold: **{EAR_THRESH:.3f}**"
            )
        else:
            calibration_progress.error("❌ Calibration failed. Face not detected clearly.")

# ---------- Start Detection ----------
if start_btn:
    running = True
    session_start = time.time()
    total_alerts = 0
    consecutive_drowsy = 0
    eyes_closed_start = None
    yawn_start = None
    last_alert_time = 0
    ear_history.clear()
    alert_placeholder.empty()
    
    cap = cv2.VideoCapture(0)
    if demo_mode:
        if not os.path.exists("driver_demo.mp4"):
            st.error("❌ Demo video 'driver_demo.mp4' not found!")
            running = False
        else:
            cap = cv2.VideoCapture("driver_demo.mp4")
    
    if not cap.isOpened():
        st.error("❌ Cannot open camera/video!")
        running = False

# ---------- Stop Detection ----------
if stop_btn:
    running = False
    eyes_closed_start = None
    yawn_start = None
    ear_history.clear()
    consecutive_drowsy = 0
    alert_placeholder.empty()
    if cap:
        cap.release()

# ---------- Detection Loop ----------
while running and cap and cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        if demo_mode:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        break

    frame = cv2.resize(frame, (640, 480))
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(frame_rgb)

    avg_ear = None
    mar = None

    if results.multi_face_landmarks:
        lm = results.multi_face_landmarks[0]
        h, w = frame.shape[:2]

        # Eyes
        left_pts = [(int(lm.landmark[i].x * w), int(lm.landmark[i].y * h)) for i in L_EYE]
        right_pts = [(int(lm.landmark[i].x * w), int(lm.landmark[i].y * h)) for i in R_EYE]
        left_ear = eye_aspect_ratio(left_pts)
        right_ear = eye_aspect_ratio(right_pts)
        avg_ear = (left_ear + right_ear) / 2.0

        # Mouth
        up = [(int(lm.landmark[i].x * w), int(lm.landmark[i].y * h)) for i in UPPER_LIP]
        low = [(int(lm.landmark[i].x * w), int(lm.landmark[i].y * h)) for i in LOWER_LIP]
        left_mouth = (int(lm.landmark[LEFT_MOUTH].x * w), int(lm.landmark[LEFT_MOUTH].y * h))
        right_mouth = (int(lm.landmark[RIGHT_MOUTH].x * w), int(lm.landmark[RIGHT_MOUTH].y * h))
        mar = mouth_aspect_ratio(up, low, left_mouth, right_mouth)

    # Smoothing
    if avg_ear:
        ear_history.append(avg_ear)
        smooth_ear = np.mean(ear_history)
    else:
        smooth_ear = None
        ear_history.clear()

    # Store metrics
    if smooth_ear:
        ear_values.append(smooth_ear)
        timestamps.append(time.time())
    if mar:
        mar_values.append(mar)

    # Detection logic
    threshold_time = get_fatigue_threshold(speed, weather, time_period)
    alert = False
    status_text = "✅ ATTENTIVE"
    alert_type = ""

    if smooth_ear is None:
        status_text = "⚠️ NO FACE DETECTED"
        eyes_closed_start = None
        consecutive_drowsy = 0
    else:
        # Eyes closed
        if smooth_ear < EAR_THRESH:
            if eyes_closed_start is None:
                eyes_closed_start = time.time()
            elapsed = time.time() - eyes_closed_start
            if elapsed > threshold_time:
                alert = True
                alert_type = "DROWSINESS"
                status_text = f"🚨 DROWSINESS ALERT ({elapsed:.1f}s)"
                consecutive_drowsy += 1
            else:
                status_text = f"⚠️ Eyes Closing... ({elapsed:.1f}s)"
        else:
            eyes_closed_start = None
            consecutive_drowsy = max(0, consecutive_drowsy - 1)
        
        # Yawn
        if mar and mar > MAR_THRESH:
            if yawn_start is None:
                yawn_start = time.time()
            yawn_duration = time.time() - yawn_start
            if yawn_duration > 1.0:
                alert = True
                alert_type = "YAWNING"
                status_text = "🚨 YAWNING DETECTED"
        else:
            yawn_start = None
        
        # Trigger alert
        if alert:
            current_time = time.time()
            # Prevent alert spam (at least 2 seconds between alerts)
            if current_time - last_alert_time > 2.0:
                total_alerts += 1
                last_alert_time = current_time
                log_event(smooth_ear if smooth_ear else 0, mar if mar else 0)
                
                # Play sound
                if sound_enabled:
                    if PYGAME_AVAILABLE:
                        play_alert_sound()
                    else:
                        # Use HTML audio for web
                        sound_array = generate_beep_sound(1200, 0.3)
                        audio_html = autoplay_audio(sound_array)
                        alert_placeholder.markdown(audio_html, unsafe_allow_html=True)
                
                # Show visual alert
                alert_placeholder.error(f"🚨 **{alert_type} ALERT!** Wake up!")

    # Draw metrics on frame
    color = (0, 255, 0) if "ATTENTIVE" in status_text else (0, 0, 255)
    
    # Background rectangles for better visibility
    cv2.rectangle(frame, (10, 10), (350, 150), (0, 0, 0), -1)
    cv2.rectangle(frame, (10, 10), (350, 150), color, 2)
    
    cv2.putText(frame, f"EAR: {smooth_ear:.3f}" if smooth_ear else "EAR: --",
                (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    cv2.putText(frame, f"MAR: {mar:.3f}" if mar else "MAR: --",
                (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    cv2.putText(frame, f"Threshold: {EAR_THRESH:.3f}", (20, 115),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    
    # Status at bottom
    status_bg_color = (0, 100, 0) if "ATTENTIVE" in status_text else (0, 0, 150)
    cv2.rectangle(frame, (0, 440), (640, 480), status_bg_color, -1)
    cv2.putText(frame, status_text, (20, 470), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    # Display frame
    video_placeholder.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), 
                           channels="RGB", use_container_width=True)

    # Update session info
    if session_start:
        elapsed = int(time.time() - session_start)
        mins = elapsed // 60
        secs = elapsed % 60
        session_text.markdown(f"**⏱️ Duration:** {mins:02d}:{secs:02d}")
        alerts_text.markdown(f"**🚨 Total Alerts:** {total_alerts}")
        
        # Status indicator
        if "ATTENTIVE" in status_text:
            status_display.success("🟢 **Status:** Attentive")
        elif "NO FACE" in status_text:
            status_display.warning("🟡 **Status:** No Face Detected")
        else:
            status_display.error("🔴 **Status:** Alert!")

    time.sleep(0.033)  # ~30 FPS  

# Optional: Add a back button (FIXED - opens in new tab like login.py)
st.markdown("<br>", unsafe_allow_html=True)
if st.button("Thank you page"):
    if os.path.exists("Thankyou.py"):
        subprocess.Popen([sys.executable, "-m", "streamlit", "run", "Thankyou.py"])
        st.success("🚗 Thank You page is opening in a new window!")
    else:
        st.error("❌ Could not find Thankyou.py in the current directory")

# Cleanup
if cap:
    cap.release()