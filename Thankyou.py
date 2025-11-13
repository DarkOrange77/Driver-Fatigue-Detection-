import streamlit as st
from datetime import datetime
import subprocess
import sys
import os

# Page config
st.set_page_config(
    page_title="Thank You | Driver Fatigue Detection",
    layout="wide"
)

# Custom CSS - Lavender Farm at Dusk Theme
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600&family=Montserrat:wght@300;400;600&display=swap');
    
    .main {
        background: linear-gradient(180deg, 
            #2d1b4e 0%,
            #4a3167 25%,
            #6b4d8a 50%,
            #9d7bb5 75%,
            #d4a5c9 100%);
        padding: 2rem;
        position: relative;
        overflow: hidden;
    }
    
    .main::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: 
            radial-gradient(ellipse at 20% 80%, rgba(255, 179, 71, 0.15) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 20%, rgba(255, 140, 105, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 50% 100%, rgba(157, 123, 181, 0.3) 0%, transparent 60%);
        pointer-events: none;
        z-index: 0;
    }
    
    .stApp > div {
        position: relative;
        z-index: 1;
    }
    
    .thank-you-card {
        background: linear-gradient(135deg, 
            rgba(245, 240, 255, 0.85) 0%, 
            rgba(235, 225, 250, 0.9) 100%);
        backdrop-filter: blur(20px);
        padding: 4rem 3rem;
        border-radius: 30px;
        box-shadow: 
            0 20px 60px rgba(45, 27, 78, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.6);
        text-align: center;
        max-width: 900px;
        margin: 2rem auto;
        border: 1px solid rgba(157, 123, 181, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .thank-you-card::before {
        content: '✨';
        position: absolute;
        top: 20px;
        right: 30px;
        font-size: 2rem;
        opacity: 0.3;
        animation: twinkle 3s infinite;
    }
    
    .thank-you-card::after {
        content: '🌾';
        position: absolute;
        bottom: 20px;
        left: 30px;
        font-size: 1.5rem;
        opacity: 0.3;
        animation: sway 4s ease-in-out infinite;
    }
    
    @keyframes twinkle {
        0%, 100% { opacity: 0.3; transform: scale(1); }
        50% { opacity: 0.6; transform: scale(1.1); }
    }
    
    @keyframes sway {
        0%, 100% { transform: rotate(-5deg); }
        50% { transform: rotate(5deg); }
    }
    
    .big-emoji {
        font-size: 80px;
        margin-bottom: 1rem;
        animation: float 3s ease-in-out infinite;
        filter: drop-shadow(0 4px 8px rgba(107, 77, 138, 0.3));
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-15px); }
    }
    
    .main-heading {
        font-family: 'Cormorant Garamond', serif;
        font-size: 3.5rem;
        font-weight: 600;
        background: linear-gradient(135deg, 
            #6b4d8a 0%, 
            #9d7bb5 50%, 
            #d4a5c9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
        letter-spacing: 1px;
        text-shadow: 0 2px 10px rgba(107, 77, 138, 0.2);
    }
    
    .subtitle {
        font-family: 'Montserrat', sans-serif;
        font-size: 1.2rem;
        color: #5a4470;
        margin-bottom: 2rem;
        line-height: 1.8;
        font-weight: 300;
    }
    
    .feature-box {
        background: linear-gradient(135deg, 
            rgba(235, 225, 250, 0.7) 0%, 
            rgba(220, 210, 240, 0.8) 100%);
        backdrop-filter: blur(10px);
        padding: 2rem 1.5rem;
        border-radius: 20px;
        margin: 1rem 0;
        border: 2px solid rgba(157, 123, 181, 0.3);
        box-shadow: 0 8px 24px rgba(107, 77, 138, 0.15);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .feature-box::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255, 179, 71, 0.1) 0%, transparent 70%);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .feature-box:hover {
        transform: translateY(-5px);
        border-color: rgba(157, 123, 181, 0.6);
        box-shadow: 0 12px 32px rgba(107, 77, 138, 0.25);
    }
    
    .feature-box:hover::before {
        opacity: 1;
    }
    
    .feature-box h3 {
        font-family: 'Montserrat', sans-serif;
        color: #4a3167;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }
    
    .feature-box p {
        color: #6b5580;
        font-family: 'Montserrat', sans-serif;
        font-weight: 300;
        margin: 0;
    }
    
    .contact-section {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        padding: 3rem 2.5rem;
        border-radius: 25px;
        box-shadow: 0 15px 45px rgba(45, 27, 78, 0.2);
        max-width: 700px;
        margin: 2rem auto;
        border: 1px solid rgba(157, 123, 181, 0.2);
    }
    
    .contact-section h2 {
        font-family: 'Cormorant Garamond', serif;
        color: #6b4d8a;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, 
            #6b4d8a 0%, 
            #9d7bb5 50%, 
            #d4a5c9 100%);
        color: white;
        border: none;
        padding: 1rem 2.5rem;
        font-size: 1.1rem;
        font-weight: 500;
        font-family: 'Montserrat', sans-serif;
        border-radius: 50px;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 6px 20px rgba(107, 77, 138, 0.3);
        letter-spacing: 0.5px;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 28px rgba(107, 77, 138, 0.4);
        background: linear-gradient(135deg, 
            #5a3d75 0%, 
            #8b6ba0 50%, 
            #c094b4 100%);
    }
    
    .social-links {
        margin-top: 2rem;
        padding-top: 2rem;
        border-top: 2px solid rgba(157, 123, 181, 0.2);
    }
    
    .social-links h3 {
        font-family: 'Cormorant Garamond', serif;
        color: #6b4d8a;
    }
    
    .social-links p {
        font-family: 'Montserrat', sans-serif;
        color: #8b7a9e;
    }
    
    /* Input styling */
    .stTextInput input, .stTextArea textarea {
        border-radius: 15px;
        border: 2px solid rgba(157, 123, 181, 0.3);
        font-family: 'Montserrat', sans-serif;
        transition: all 0.3s ease;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #9d7bb5;
        box-shadow: 0 0 0 3px rgba(157, 123, 181, 0.1);
    }
    
    /* Success/Error messages */
    .stSuccess, .stError {
        border-radius: 15px;
        font-family: 'Montserrat', sans-serif;
    }
    
    /* Lavender field decoration */
    .lavender-field {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 100px;
        background: linear-gradient(0deg, 
            rgba(107, 77, 138, 0.3) 0%, 
            transparent 100%);
        pointer-events: none;
        z-index: 0;
    }
    </style>
    
    <div class="lavender-field"></div>
""", unsafe_allow_html=True)

# Main thank you section with lavender theme
st.markdown("""
    <div class="thank-you-card">
        <div class="big-emoji">💜</div>
        <h1 class="main-heading">Thank You for Visiting</h1>
        <p class="subtitle">
            <br>I'm grateful you took the time to explore my Driver Fatigue Detection System—
            <br>Because tired eyes miss warning signs—and we're here to catch them
        </p>
    </div>
""", unsafe_allow_html=True)

# Spacer
st.markdown("<br>", unsafe_allow_html=True)

# Contact Form Section
st.markdown("""
    <div class="contact-section">
        <h2 style="text-align: center; margin-bottom: 1rem;">
            💬 Let's Connect
        </h2>
        <p style="text-align: center; color: #6b5580; margin-bottom: 2rem; font-family: 'Montserrat', sans-serif; font-weight: 300;">
            Have questions, feedback, or collaboration ideas? I'd love to hear from you.
        </p>
    </div>
""", unsafe_allow_html=True)

# FormSubmit contact form
with st.form("contact_form"):
    st.markdown("### Send me a message")
    
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Your Name *", placeholder="John Doe")
    with col2:
        email = st.text_input("Your Email *", placeholder="john@example.com")
    
    subject = st.text_input("Subject *", placeholder="Project Inquiry / Collaboration / Feedback")
    
    message = st.text_area(
        "Message *", 
        placeholder="Share your thoughts about the project...",
        height=150
    )
    
    # Honeypot field (hidden from users, catches bots)
    st.markdown('<input type="text" name="_gotcha" style="display:none">', unsafe_allow_html=True)
    
    submit_button = st.form_submit_button("Send Message")
    
    if submit_button:
        if name and email and message:
            # FormSubmit HTML form
            form_html = f"""
            <form action="https://formsubmit.co/bezz39587@gmail.com" method="POST" id="contactForm">
                <input type="hidden" name="_subject" value="New Contact from Driver Fatigue Detection Project">
                <input type="hidden" name="_captcha" value="false">
                <input type="hidden" name="_template" value="table">
                <input type="hidden" name="name" value="{name}">
                <input type="hidden" name="email" value="{email}">
                <input type="hidden" name="subject" value="{subject}">
                <input type="hidden" name="message" value="{message}">
                <input type="hidden" name="timestamp" value="{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}">
            </form>
            <script>
                document.getElementById('contactForm').submit();
            </script>
            """
            
            st.success("✅ Thank you! Your message has been sent!")
            st.markdown(form_html, unsafe_allow_html=True)
        else:
            st.error("⚠️ Please fill in all required fields (Name, Email, and Message)")

# Additional info
st.markdown("<br><br>", unsafe_allow_html=True)

# Footer with social links
st.markdown("""
    <div class="contact-section">
        <p style="text-align: center; color: #9d8ab3; margin-top: 2rem; font-size: 0.9rem; font-family: 'Montserrat', sans-serif; font-weight: 300;">
            Built with ❤️ using Streamlit, MediaPipe & OpenCV
            <br>
            © 2025 Driver Fatigue Detection System
            <br><br>
            <span style="font-style: italic; font-size: 0.85rem; color: #b4a0c8;">
            "Like a lavender field at dusk, may your journeys be peaceful and safe."
            </span>
        </p>
    </div>
""", unsafe_allow_html=True)

# Optional: Add a back button (FIXED - opens in new tab like login.py)
st.markdown("<br>", unsafe_allow_html=True)
if st.button("🔙 Back to Detection System"):
    if os.path.exists("driver_fatigue_dashboard.py"):
        subprocess.Popen([sys.executable, "-m", "streamlit", "run", "driver_fatigue_dashboard.py"])
        st.success("🚗 Driver Fatigue Dashboard is opening in a new window!")
    else:
        st.error("❌ Could not find driver_fatigue_dashboard.py in the current directory")