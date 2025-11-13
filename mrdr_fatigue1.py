import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from scipy.spatial import distance as dist
import threading
import time
import datetime
import winsound
import os
from collections import deque

try:
    import mediapipe as mp
except ImportError:
    mp = None

# ---------- Landmarks ----------
L_EYE = [33, 160, 158, 133, 153, 144]
R_EYE = [263, 387, 385, 362, 380, 373]
UPPER_LIP = [13, 14]
LOWER_LIP = [17, 18]
LEFT_MOUTH = 78
RIGHT_MOUTH = 308

# ============ Helper Functions ============
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
    """Returns threshold in seconds for eye closure"""
    base_thresh = 2.0  # Reduced from 10 for faster detection
    
    if speed < 15:
        return float('inf')
    elif speed < 40:
        base_thresh = 3.0
    elif speed >= 80:
        base_thresh = 1.5  # Very strict at high speeds
    
    if time_period.lower() == "night":
        base_thresh *= 0.7
    
    if weather.lower() in ["fog", "rain", "storm"]:
        base_thresh *= 0.8
    
    return base_thresh

# ============ Main Class ============
class DriverFatigueDashboard:
    def __init__(self, root):
        if mp is None:
            messagebox.showerror("Missing dependency", "mediapipe required")
            root.destroy()
            return

        self.root = root
        self.root.title("🚗 Advanced Driver Fatigue Detection System")
        self.root.geometry("1400x800")
        self.root.configure(bg="#1a1a2e")

        self.demo_mode = tk.BooleanVar(value=False)
        self.cap = None
        self.running = False
        self.mp_face = mp.solutions.face_mesh
        self.face_mesh = self.mp_face.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # Detection variables - IMPROVED
        self.eyes_closed_start = None
        self.yawn_start = None
        self.base_open_ear = None
        self.EAR_THRESH = 0.25  # Increased default threshold
        self.MAR_THRESH = 0.65
        self.current_status = "Ready"
        self.ear_history = deque(maxlen=3)  # Reduced smoothing for faster response
        self.consecutive_drowsy = 0
        self.total_alerts = 0
        self.session_start = None
        
        # Real-time metrics
        self.ear_values = deque(maxlen=100)
        self.mar_values = deque(maxlen=100)
        self.timestamps = deque(maxlen=100)

        self.speed_var = tk.DoubleVar(value=60)
        self.weather_var = tk.StringVar(value="Clear")
        self.time_var = tk.StringVar(value="Day")

        self.setup_ui()

    # ---------- UI Setup ----------
    def setup_ui(self):
        # Main container
        main_container = tk.Frame(self.root, bg="#1a1a2e")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # LEFT PANEL - Video Feed
        left_panel = tk.Frame(main_container, bg="#16213e", relief="ridge", bd=3)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Video label with border
        video_frame = tk.Frame(left_panel, bg="#0f3460", bd=2, relief="sunken")
        video_frame.pack(padx=15, pady=15, fill="both", expand=True)
        
        self.video_label = tk.Label(video_frame, bg="#000000", text="Camera Feed", 
                                     fg="white", font=("Helvetica", 16))
        self.video_label.pack(fill="both", expand=True)

        # Metrics display below video
        metrics_frame = tk.Frame(left_panel, bg="#16213e")
        metrics_frame.pack(fill="x", padx=15, pady=(0, 15))

        self.ear_display = tk.Label(metrics_frame, text="EAR: --", bg="#16213e", 
                                     fg="#00ff88", font=("Courier", 14, "bold"))
        self.ear_display.pack(side="left", padx=20)

        self.mar_display = tk.Label(metrics_frame, text="MAR: --", bg="#16213e", 
                                     fg="#00ff88", font=("Courier", 14, "bold"))
        self.mar_display.pack(side="left", padx=20)

        self.blink_display = tk.Label(metrics_frame, text="Alerts: 0", bg="#16213e", 
                                       fg="#ff6b6b", font=("Courier", 14, "bold"))
        self.blink_display.pack(side="left", padx=20)

        # RIGHT PANEL - Controls
        right_panel = tk.Frame(main_container, bg="#16213e", relief="ridge", bd=3)
        right_panel.pack(side="right", fill="both", padx=(0, 0))
        right_panel.config(width=450)

        # Header
        header = tk.Label(right_panel, text="🚗 CONTROL CENTER", bg="#0f3460", 
                         fg="white", font=("Helvetica", 18, "bold"), pady=15)
        header.pack(fill="x", padx=10, pady=(10, 20))

        # Status Display - PROMINENT
        self.status_frame = tk.Frame(right_panel, bg="#16213e", relief="solid", bd=2)
        self.status_frame.pack(fill="x", padx=20, pady=(0, 20))

        tk.Label(self.status_frame, text="SYSTEM STATUS", bg="#16213e", 
                fg="#aaaaaa", font=("Helvetica", 10)).pack(pady=(8, 2))

        self.status_label = tk.Label(self.status_frame, text="● Ready", 
                                     bg="#16213e", fg="#00ff88", 
                                     font=("Helvetica", 16, "bold"))
        self.status_label.pack(pady=(0, 12))

        # Scrollable controls frame
        canvas = tk.Canvas(right_panel, bg="#16213e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(right_panel, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#16213e")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=(10, 0))
        scrollbar.pack(side="right", fill="y")

        # Controls inside scrollable frame
        controls = scrollable_frame

        # Speed Control
        self._create_control_section(controls, "🚗 Vehicle Speed", 
                                     self.speed_var, 0, 120, "km/h")

        # Time Control
        time_frame = self._create_section(controls, "🕐 Time of Day")
        time_combo = ttk.Combobox(time_frame, values=["Day", "Night"], 
                                  textvariable=self.time_var, state="readonly", 
                                  font=("Helvetica", 11))
        time_combo.pack(fill="x", padx=20, pady=8)

        # Weather Control
        weather_frame = self._create_section(controls, "🌤️ Weather Condition")
        weather_combo = ttk.Combobox(weather_frame, 
                                     values=["Clear", "Fog", "Rain", "Storm"], 
                                     textvariable=self.weather_var, 
                                     state="readonly", font=("Helvetica", 11))
        weather_combo.pack(fill="x", padx=20, pady=8)

        # Detection Settings
        settings_frame = self._create_section(controls, "⚙️ Detection Settings")
        
        tk.Label(settings_frame, text=f"EAR Threshold: {self.EAR_THRESH:.2f}", 
                bg="#16213e", fg="#aaaaaa", font=("Helvetica", 10)).pack(pady=(5, 2))
        
        self.ear_thresh_scale = ttk.Scale(settings_frame, from_=0.15, to=0.35, 
                                          orient="horizontal", 
                                          command=self._update_ear_threshold)
        self.ear_thresh_scale.set(self.EAR_THRESH)
        self.ear_thresh_scale.pack(fill="x", padx=20, pady=(0, 8))

        tk.Label(settings_frame, text=f"MAR Threshold: {self.MAR_THRESH:.2f}", 
                bg="#16213e", fg="#aaaaaa", font=("Helvetica", 10)).pack(pady=(5, 2))
        
        self.mar_thresh_scale = ttk.Scale(settings_frame, from_=0.5, to=0.8, 
                                          orient="horizontal",
                                          command=self._update_mar_threshold)
        self.mar_thresh_scale.set(self.MAR_THRESH)
        self.mar_thresh_scale.pack(fill="x", padx=20, pady=(0, 15))

        # Demo mode and calibration
        options_frame = self._create_section(controls, "🎬 Options")
        
        demo_check = ttk.Checkbutton(options_frame, 
                                     text="Demo Mode (driver_demo.mp4)", 
                                     variable=self.demo_mode)
        demo_check.pack(pady=8)

        tk.Button(options_frame, text="📸 CALIBRATE EYES (3s)", 
                 bg="#3498db", fg="white", font=("Helvetica", 11, "bold"),
                 command=self.calibrate_open_eye, relief="flat",
                 cursor="hand2").pack(fill="x", padx=20, pady=(8, 15))

        # Main Control Buttons
        btn_frame = self._create_section(controls, "🎮 System Control")
        
        tk.Button(btn_frame, text="▶ START MONITORING", bg="#27ae60", 
                 fg="white", font=("Helvetica", 12, "bold"),
                 command=self.start_detection, relief="flat", 
                 cursor="hand2", pady=12).pack(fill="x", padx=20, pady=8)
        
        tk.Button(btn_frame, text="⏸ STOP MONITORING", bg="#e67e22", 
                 fg="white", font=("Helvetica", 12, "bold"),
                 command=self.stop_detection, relief="flat", 
                 cursor="hand2", pady=12).pack(fill="x", padx=20, pady=8)
        
        tk.Button(btn_frame, text="❌ EXIT SYSTEM", bg="#e74c3c", 
                 fg="white", font=("Helvetica", 12, "bold"),
                 command=self.close_system, relief="flat", 
                 cursor="hand2", pady=12).pack(fill="x", padx=20, pady=(8, 15))

        # Session info
        info_frame = self._create_section(controls, "📊 Session Info")
        self.session_label = tk.Label(info_frame, text="Duration: 00:00", 
                                      bg="#16213e", fg="#aaaaaa", 
                                      font=("Courier", 10))
        self.session_label.pack(pady=8)

    def _create_section(self, parent, title):
        frame = tk.Frame(parent, bg="#0f3460", relief="solid", bd=1)
        frame.pack(fill="x", padx=15, pady=10)
        
        tk.Label(frame, text=title, bg="#0f3460", fg="white", 
                font=("Helvetica", 12, "bold")).pack(anchor="w", padx=15, pady=8)
        
        return frame

    def _create_control_section(self, parent, title, var, from_, to, unit):
        frame = self._create_section(parent, title)
        
        value_label = tk.Label(frame, textvariable=var, bg="#0f3460", 
                              fg="#00ff88", font=("Courier", 14, "bold"))
        value_label.pack()
        
        tk.Label(frame, text=unit, bg="#0f3460", fg="#aaaaaa", 
                font=("Helvetica", 9)).pack()
        
        scale = ttk.Scale(frame, from_=from_, to=to, orient="horizontal", 
                         variable=var)
        scale.pack(fill="x", padx=20, pady=(8, 15))

    def _update_ear_threshold(self, val):
        self.EAR_THRESH = float(val)

    def _update_mar_threshold(self, val):
        self.MAR_THRESH = float(val)

    # ---------- Calibration ----------
    def calibrate_open_eye(self):
        if self.running:
            messagebox.showinfo("Calibration", "Please stop detection first.")
            return
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Error", "Camera not available")
            return
        
        messagebox.showinfo("Calibration", 
                           "Keep your eyes WIDE OPEN and look straight ahead.\n"
                           "Calibration will run for 3 seconds.")
        
        ear_vals = []
        start = time.time()
        
        while time.time() - start < 3:
            ret, frame = cap.read()
            if not ret:
                continue
            ear = self._compute_frame_ear(frame)
            if ear is not None and ear > 0.1:  # Filter out bad readings
                ear_vals.append(ear)
            time.sleep(0.03)
        
        cap.release()
        
        if len(ear_vals) < 10:
            messagebox.showerror("Calibration", 
                               "Not enough data. Face not detected properly.")
            return
        
        # Remove outliers
        ear_vals = sorted(ear_vals)
        ear_vals = ear_vals[len(ear_vals)//4:-len(ear_vals)//4]  # Remove top/bottom 25%
        
        self.base_open_ear = np.mean(ear_vals)
        self.EAR_THRESH = max(0.18, self.base_open_ear * 0.65)  # More sensitive
        
        self.ear_thresh_scale.set(self.EAR_THRESH)
        
        messagebox.showinfo("Calibration", 
                           f"✓ Calibration Complete!\n\n"
                           f"Your open-eye EAR: {self.base_open_ear:.3f}\n"
                           f"Alert threshold: {self.EAR_THRESH:.3f}\n\n"
                           f"The system will alert if EAR drops below this threshold.")

    # ---------- Start/Stop Detection ----------
    def start_detection(self):
        if self.running:
            return
        
        if self.demo_mode.get():
            video_path = "driver_demo.mp4"
            if not os.path.exists(video_path):
                messagebox.showerror("Error", "Demo video 'driver_demo.mp4' not found")
                return
            self.cap = cv2.VideoCapture(video_path)
        else:
            self.cap = cv2.VideoCapture(0)
        
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Cannot access camera/video")
            return
        
        self.running = True
        self.session_start = time.time()
        self.total_alerts = 0
        self.consecutive_drowsy = 0
        self.status_label.config(text="● Monitoring...", fg="#00ff88")
        
        threading.Thread(target=self.update_video_feed, daemon=True).start()
        threading.Thread(target=self.update_session_info, daemon=True).start()

    def stop_detection(self):
        self.running = False
        self.eyes_closed_start = None
        self.yawn_start = None
        self.ear_history.clear()
        self.consecutive_drowsy = 0
        self.status_label.config(text="● Stopped", fg="#ff6b6b")

    # ---------- Video Feed & Detection ----------
    def update_video_feed(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                if self.demo_mode.get():
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Loop demo video
                    continue
                break

            frame = cv2.resize(frame, (800, 600))
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(frame_rgb)
            
            avg_ear = None
            mar = None

            if results.multi_face_landmarks:
                lm = results.multi_face_landmarks[0]
                h, w = frame.shape[:2]

                # Eyes
                left_pts = [(int(lm.landmark[i].x * w), int(lm.landmark[i].y * h)) 
                           for i in L_EYE]
                right_pts = [(int(lm.landmark[i].x * w), int(lm.landmark[i].y * h)) 
                            for i in R_EYE]
                
                left_ear = eye_aspect_ratio(left_pts)
                right_ear = eye_aspect_ratio(right_pts)
                avg_ear = (left_ear + right_ear) / 2.0

                # Mouth
                up = [(int(lm.landmark[i].x * w), int(lm.landmark[i].y * h)) 
                     for i in UPPER_LIP]
                low = [(int(lm.landmark[i].x * w), int(lm.landmark[i].y * h)) 
                      for i in LOWER_LIP]
                left_mouth = (int(lm.landmark[LEFT_MOUTH].x * w), 
                             int(lm.landmark[LEFT_MOUTH].y * h))
                right_mouth = (int(lm.landmark[RIGHT_MOUTH].x * w), 
                              int(lm.landmark[RIGHT_MOUTH].y * h))
                mar = mouth_aspect_ratio(up, low, left_mouth, right_mouth)

                # Draw eye contours
                cv2.polylines(frame, [np.array(left_pts)], True, (0, 255, 0), 1)
                cv2.polylines(frame, [np.array(right_pts)], True, (0, 255, 0), 1)
                
                # Draw mouth
                cv2.line(frame, left_mouth, right_mouth, (255, 0, 0), 2)
                for pt in up + low:
                    cv2.circle(frame, pt, 2, (255, 0, 0), -1)

            # Minimal smoothing for faster response
            if avg_ear is not None:
                self.ear_history.append(avg_ear)
                smooth_ear = np.mean(self.ear_history)
            else:
                smooth_ear = None
                self.ear_history.clear()

            # Store for display
            current_time = time.time()
            if smooth_ear is not None:
                self.ear_values.append(smooth_ear)
                self.timestamps.append(current_time)
            if mar is not None:
                self.mar_values.append(mar)

            # Detection logic
            threshold_time = get_fatigue_threshold(
                self.speed_var.get(), 
                self.weather_var.get(), 
                self.time_var.get()
            )

            alert = False
            color = (0, 255, 0)
            status_text = "ATTENTIVE"
            status_color = "#00ff88"

            if smooth_ear is None:
                status_text = "NO FACE"
                status_color = "#ff6b6b"
                color = (0, 165, 255)
                self.eyes_closed_start = None
                self.consecutive_drowsy = 0
            else:
                # Eyes closed detection - IMPROVED
                if smooth_ear < self.EAR_THRESH:
                    if self.eyes_closed_start is None:
                        self.eyes_closed_start = time.time()
                    
                    elapsed = time.time() - self.eyes_closed_start
                    
                    if elapsed > threshold_time:
                        alert = True
                        status_text = f"⚠️ EYES CLOSED ({elapsed:.1f}s)"
                        self.consecutive_drowsy += 1
                    else:
                        status_text = f"Drowsy... ({elapsed:.1f}s)"
                        status_color = "#ffa500"
                        color = (0, 165, 255)
                else:
                    self.eyes_closed_start = None
                    self.consecutive_drowsy = max(0, self.consecutive_drowsy - 1)

                # Yawn detection
                if mar is not None and mar > self.MAR_THRESH:
                    if self.yawn_start is None:
                        self.yawn_start = time.time()
                    
                    yawn_duration = time.time() - self.yawn_start
                    if yawn_duration > 1.0:  # Yawn for more than 1 second
                        alert = True
                        status_text = "⚠️ YAWNING DETECTED"
                else:
                    self.yawn_start = None

                # Trigger alert
                if alert:
                    status_color = "#ff0000"
                    color = (0, 0, 255)
                    self.total_alerts += 1
                    
                    # Sound alert
                    try:
                        winsound.Beep(1000, 500)
                    except:
                        pass
                    
                    self.log_event(smooth_ear, mar)
                    
                    # Flash effect
                    cv2.rectangle(frame, (0, 0), (w, h), (0, 0, 255), 20)

            # Update UI labels
            self.status_label.config(text=f"● {status_text}", fg=status_color)
            self.ear_display.config(text=f"EAR: {smooth_ear:.3f}" if smooth_ear else "EAR: --")
            self.mar_display.config(text=f"MAR: {mar:.3f}" if mar else "MAR: --")
            self.blink_display.config(text=f"Alerts: {self.total_alerts}")

            # Draw on frame
            cv2.putText(frame, f"EAR: {smooth_ear:.3f}" if smooth_ear else "EAR: --", 
                       (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
            cv2.putText(frame, f"MAR: {mar:.3f}" if mar else "MAR: --", 
                       (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
            cv2.putText(frame, f"Threshold: {self.EAR_THRESH:.3f}", 
                       (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

            # Convert for Tkinter
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

            time.sleep(0.03)

        if self.cap:
            self.cap.release()

    # ---------- Session Info Update ----------
    def update_session_info(self):
        while self.running and self.session_start:
            elapsed = int(time.time() - self.session_start)
            mins = elapsed // 60
            secs = elapsed % 60
            self.session_label.config(text=f"Duration: {mins:02d}:{secs:02d}")
            time.sleep(1)

    # ---------- Compute EAR ----------
    def _compute_frame_ear(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(frame_rgb)
        if not results.multi_face_landmarks:
            return None
        
        lm = results.multi_face_landmarks[0]
        h, w = frame.shape[:2]
        
        left_pts = [(int(lm.landmark[i].x * w), int(lm.landmark[i].y * h)) 
                   for i in L_EYE]
        right_pts = [(int(lm.landmark[i].x * w), int(lm.landmark[i].y * h)) 
                    for i in R_EYE]
        
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

    # ---------- Log Event ----------
    def log_event(self, ear, mar):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("fatigue_log.txt", "a") as f:
            f.write(f"{timestamp} | ALERT #{self.total_alerts} | "
                   f"EAR={ear:.3f} | MAR={mar:.3f} | "
                   f"Speed={int(self.speed_var.get())} km/h | "
                   f"Weather={self.weather_var.get()} | "
                   f"Time={self.time_var.get()}\n")

    # ---------- Close System ----------
    def close_system(self):
        self.running = False
        if self.cap:
            self.cap.release()
        try:
            self.face_mesh.close()
        except:
            pass
        self.root.destroy()

# ============ MAIN ============
if __name__ == "__main__":
    root = tk.Tk()
    app = DriverFatigueDashboard(root)
    root.mainloop()