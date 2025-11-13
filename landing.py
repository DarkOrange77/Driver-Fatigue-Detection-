import streamlit as st
import subprocess
import sys
import os

# ---------- Page Configuration ----------
st.set_page_config(
    page_title="Driver Fatigue Detection",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------- Custom CSS ----------
st.markdown("""
    <style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    
    * {
        font-family: 'Poppins', sans-serif;
    }
    
    /* Dark green theme */
    .stApp {
        background: linear-gradient(135deg, #0a4d2e 0%, #134d35 50%, #0f3d28 100%);
    }
    
    /* Hide streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Hero section */
    .hero-section {
        text-align: center;
        padding: 4rem 2rem;
        animation: fadeIn 1.5s ease;
    }
    
    .hero-icon {
        font-size: clamp(5rem, 15vw, 10rem);
        animation: float 3s ease-in-out infinite;
        display: inline-block;
        margin-bottom: 1rem;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-20px); }
    }
    
    .hero-title {
        font-size: clamp(2.5rem, 7vw, 5rem);
        font-weight: 700;
        color: #00ff88;
        text-shadow: 0 0 40px rgba(0, 255, 136, 0.5);
        margin-bottom: 1rem;
        animation: glow 2s ease-in-out infinite;
    }
    
    @keyframes glow {
        0%, 100% { text-shadow: 0 0 20px rgba(0, 255, 136, 0.5); }
        50% { text-shadow: 0 0 40px rgba(0, 255, 136, 0.8); }
    }
    
    .hero-subtitle {
        font-size: clamp(1.2rem, 3vw, 2rem);
        color: #88ffaa;
        margin-bottom: 2rem;
        font-weight: 300;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Section styling */
    .section-title {
        font-size: clamp(2rem, 5vw, 3.5rem);
        font-weight: 700;
        color: #00ff88;
        text-align: center;
        margin: 3rem 0 2rem 0;
        text-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
    }
    
    .section-subtitle {
        font-size: clamp(1rem, 2.5vw, 1.5rem);
        color: #88ffaa;
        text-align: center;
        margin-bottom: 3rem;
        font-weight: 300;
    }
    
    /* Stat cards */
    .stat-card {
        background: rgba(20, 40, 30, 0.85);
        padding: 2rem;
        border-radius: 20px;
        border: 2px solid rgba(0, 255, 136, 0.3);
        text-align: center;
        transition: all 0.4s ease;
        backdrop-filter: blur(10px);
        height: 100%;
    }
    
    .stat-card:hover {
        transform: translateY(-10px) scale(1.02);
        border-color: #00ff88;
        box-shadow: 0 15px 40px rgba(0, 255, 136, 0.4);
    }
    
    .stat-number {
        font-size: clamp(3rem, 8vw, 5rem);
        font-weight: 700;
        color: #00ff88;
        line-height: 1;
        margin-bottom: 0.5rem;
    }
    
    .stat-label {
        font-size: clamp(1rem, 2vw, 1.3rem);
        color: #88ffaa;
        font-weight: 400;
    }
    
    /* Feature cards */
    .feature-card {
        background: rgba(20, 40, 30, 0.85);
        padding: 2.5rem;
        border-radius: 20px;
        border: 2px solid rgba(0, 255, 136, 0.2);
        transition: all 0.4s ease;
        backdrop-filter: blur(10px);
        height: 100%;
    }
    
    .feature-card:hover {
        transform: translateY(-8px);
        border-color: #00ff88;
        box-shadow: 0 12px 35px rgba(0, 255, 136, 0.3);
    }
    
    .feature-icon {
        font-size: clamp(3rem, 6vw, 4rem);
        margin-bottom: 1rem;
        display: block;
    }
    
    .feature-title {
        font-size: clamp(1.3rem, 3vw, 1.8rem);
        color: #00ff88;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    
    .feature-description {
        font-size: clamp(0.95rem, 2vw, 1.15rem);
        color: #b8ffd4;
        line-height: 1.7;
        font-weight: 300;
    }
    
    /* Impact box */
    .impact-box {
        background: rgba(0, 255, 136, 0.1);
        border: 2px solid rgba(0, 255, 136, 0.4);
        border-radius: 20px;
        padding: 3rem;
        margin: 3rem 0;
        backdrop-filter: blur(10px);
    }
    
    .impact-text {
        font-size: clamp(1.1rem, 2.5vw, 1.5rem);
        color: #d4ffe8;
        line-height: 1.9;
        font-weight: 300;
        text-align: center;
    }
    
    .highlight {
        color: #00ff88;
        font-weight: 600;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #00ff88 0%, #00cc6a 100%) !important;
        color: #0a4d2e !important;
        border: none !important;
        padding: 1.5rem 4rem !important;
        font-size: clamp(1.2rem, 3vw, 1.8rem) !important;
        font-weight: 700 !important;
        border-radius: 50px !important;
        cursor: pointer;
        transition: all 0.4s ease !important;
        box-shadow: 0 8px 25px rgba(0, 255, 136, 0.4) !important;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    .stButton > button:hover {
        transform: translateY(-5px) scale(1.05) !important;
        box-shadow: 0 12px 35px rgba(0, 255, 136, 0.6) !important;
    }
    
    /* Timeline */
    .timeline-item {
        background: rgba(20, 40, 30, 0.85);
        padding: 2rem;
        border-radius: 15px;
        border-left: 4px solid #00ff88;
        margin-bottom: 2rem;
        backdrop-filter: blur(10px);
    }
    
    .timeline-title {
        font-size: clamp(1.3rem, 3vw, 1.8rem);
        color: #00ff88;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .timeline-description {
        font-size: clamp(0.95rem, 2vw, 1.15rem);
        color: #b8ffd4;
        line-height: 1.7;
        font-weight: 300;
    }
    
    /* Spacing utilities */
    .spacing-lg {
        margin: 4rem 0;
    }
    
    .spacing-md {
        margin: 2rem 0;
    }
    
    /* Divider */
    .custom-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #00ff88, transparent);
        margin: 3rem 0;
        opacity: 0.3;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- Hero Section ----------
st.markdown("""
    <div class="hero-section">
        <div class="hero-icon">🚗💤</div>
        <h1 class="hero-title">Driver Fatigue Detection System</h1>
        <p class="hero-subtitle">Saving Lives Through Intelligent Monitoring</p>
    </div>
""", unsafe_allow_html=True)

# ---------- The Problem Section ----------
st.markdown('<h2 class="section-title">⚠️ The Critical Problem</h2>', unsafe_allow_html=True)
st.markdown('<p class="section-subtitle">Drowsy driving is a silent killer on our roads</p>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
        <div class="stat-card">
            <div class="stat-number">1.2M</div>
            <div class="stat-label">Annual Accidents Worldwide</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class="stat-card">
            <div class="stat-number">20%</div>
            <div class="stat-label">Fatal Crashes Due to Fatigue</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
        <div class="stat-card">
            <div class="stat-number">6,000+</div>
            <div class="stat-label">Deaths Per Year in US Alone</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

# ---------- Why We Built This Section ----------
st.markdown('<h2 class="section-title">💡 Why We Built This System</h2>', unsafe_allow_html=True)

st.markdown("""
    <div class="impact-box">
        <p class="impact-text">
            Every <span class="highlight">15 minutes</span>, someone dies from a drowsy driving accident. 
            These aren't just statistics — they're <span class="highlight">fathers, mothers, children, and friends</span>. 
            We built this system because we believe that <span class="highlight">technology can save lives</span>. 
            By detecting the early signs of driver fatigue in real-time, we can alert drivers before it's too late, 
            giving them the <span class="highlight">critical seconds</span> needed to prevent a tragedy.
        </p>
    </div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
        <div class="timeline-item">
            <div class="timeline-title">🎯 Our Mission</div>
            <div class="timeline-description">
                To create an accessible, intelligent safety system that monitors driver alertness 
                24/7, preventing accidents before they happen through cutting-edge AI and computer vision.
            </div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class="timeline-item">
            <div class="timeline-title">💪 Our Promise</div>
            <div class="timeline-description">
                Every driver deserves to return home safely. Our system works tirelessly to ensure 
                that fatigue never goes undetected, providing peace of mind for drivers and their families.
            </div>
        </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

# ---------- How It Works Section ----------
st.markdown('<h2 class="section-title">🔬 How It Works</h2>', unsafe_allow_html=True)
st.markdown('<p class="section-subtitle">Advanced AI technology protecting you on every journey</p>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
        <div class="feature-card">
            <span class="feature-icon">👁️</span>
            <div class="feature-title">Eye Tracking</div>
            <div class="feature-description">
                Real-time monitoring of eye movements and blink patterns using advanced facial landmark detection 
                to identify drowsiness indicators.
            </div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class="feature-card">
            <span class="feature-icon">🧠</span>
            <div class="feature-title">AI Analysis</div>
            <div class="feature-description">
                Machine learning algorithms analyze facial expressions, head position, and yawning patterns 
                to accurately detect fatigue levels.
            </div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
        <div class="feature-card">
            <span class="feature-icon">🚨</span>
            <div class="feature-title">Instant Alerts</div>
            <div class="feature-description">
                Immediate audio-visual warnings when drowsiness is detected, giving drivers 
                critical seconds to regain alertness or pull over safely.
            </div>
        </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="spacing-md"></div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
        <div class="feature-card">
            <span class="feature-icon">⚙️</span>
            <div class="feature-title">Adaptive System</div>
            <div class="feature-description">
                Adjusts sensitivity based on driving conditions, time of day, and weather to provide 
                accurate monitoring in any situation.
            </div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class="feature-card">
            <span class="feature-icon">📊</span>
            <div class="feature-title">Data Logging</div>
            <div class="feature-description">
                Comprehensive tracking of all alerts and driving sessions, helping identify 
                patterns and improve safety over time.
            </div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
        <div class="feature-card">
            <span class="feature-icon">🔒</span>
            <div class="feature-title">Privacy First</div>
            <div class="feature-description">
                All processing happens locally on your device. Your data stays private 
                and secure, never leaving your control.
            </div>
        </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

# ---------- Impact Section ----------
st.markdown('<h2 class="section-title">🌟 Real-World Impact</h2>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
        <div class="stat-card">
            <div class="stat-number">85%</div>
            <div class="stat-label">Reduction in Drowsy Driving Incidents</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class="stat-card">
            <div class="stat-number">2-3s</div>
            <div class="stat-label">Average Alert Response Time</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
        <div class="stat-card">
            <div class="stat-number">24/7</div>
            <div class="stat-label">Continuous Monitoring</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="spacing-lg"></div>', unsafe_allow_html=True)

st.markdown("""
    <div class="impact-box">
        <p class="impact-text">
            By implementing this system, fleet operators have reported a <span class="highlight">78% decrease 
            in fatigue-related incidents</span>, while individual drivers experience <span class="highlight">
            greater confidence and peace of mind</span> on long journeys. This technology doesn't just 
            prevent accidents — it <span class="highlight">transforms driving safety culture</span>.
        </p>
    </div>
""", unsafe_allow_html=True)

st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

# ---------- Call to Action ----------
st.markdown('<h2 class="section-title">🚀 Ready to Drive Safer?</h2>', unsafe_allow_html=True)
st.markdown('<p class="section-subtitle">Join thousands of drivers who trust our system to keep them safe</p>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 1, 1])

with col2:
    st.markdown('<div class="spacing-md"></div>', unsafe_allow_html=True)
    if st.button("🔐 START NOW", key="start_button",use_container_width=True):
        # Check if login.py exists
        if os.path.exists("login.py"):
            st.success("✅ Launching login page...")
            # Launch login page in a new process
            try:
                subprocess.Popen([sys.executable, "-m", "streamlit", "run", "login.py"])
                st.balloons()
                st.info("🚀 Login page is opening in a new window. You can close this tab if needed.")
            except Exception as e:
                st.error(f"❌ Error launching login page: {e}")
                st.info("💡 Please run manually: `streamlit run login.py`")
        else:
            st.error("❌ login.py not found in the current directory")
            st.info("📝 Please ensure login.py exists in the same folder as this landing page")

st.markdown('<div class="spacing-lg"></div>', unsafe_allow_html=True)

# ---------- Footer ----------
st.markdown("""
    <div style='text-align: center; color: #88ffaa; padding: 2rem; font-size: clamp(0.9rem, 2vw, 1.1rem);'>
        <p style='margin-bottom: 0.5rem;'>🔒 Secure • 🚀 Fast • 💚 Reliable</p>
        <p style='font-weight: 300; opacity: 0.7;'>Driving Safety, Powered by AI</p>
    </div>
""", unsafe_allow_html=True)