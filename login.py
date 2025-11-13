import streamlit as st
import hashlib
import json
import os
from datetime import datetime
import re
import subprocess
import sys

# ---------- Configuration ----------
USER_DATA_FILE = "users.json"

# ---------- Helper Functions ----------
def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """Load users from JSON file"""
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    """Save users to JSON file"""
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    if not any(char.isdigit() for char in password):
        return False, "Password must contain at least one number"
    if not any(char.isalpha() for char in password):
        return False, "Password must contain at least one letter"
    return True, "Password is strong"

def create_user(username, email, password, full_name):
    """Create a new user"""
    users = load_users()
    
    if username in users:
        return False, "Username already exists"
    
    # Check if email already exists
    for user_data in users.values():
        if user_data.get('email') == email:
            return False, "Email already registered"
    
    users[username] = {
        'email': email,
        'password': hash_password(password),
        'full_name': full_name,
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'last_login': None
    }
    
    save_users(users)
    return True, "Account created successfully!"

def authenticate_user(username, password):
    """Authenticate user credentials"""
    users = load_users()
    
    if username not in users:
        return False, "Username not found"
    
    if users[username]['password'] != hash_password(password):
        return False, "Incorrect password"
    
    # Update last login
    users[username]['last_login'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_users(users)
    
    return True, users[username]

def launch_dashboard():
    """Launch the driver fatigue dashboard"""
    if os.path.exists("driver_fatigue_dashboard.py"):
        # Launch the dashboard in a new process
        subprocess.Popen([sys.executable, "-m", "streamlit", "run", "driver_fatigue_dashboard.py"])
        return True
    else:
        return False

# ---------- Initialize Session State ----------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_data' not in st.session_state:
    st.session_state.user_data = None

# ---------- Custom CSS ----------
st.markdown("""
    <style>
    /* Dark green theme */
    .stApp {
        background: linear-gradient(135deg, #0a4d2e 0%, #134d35 50%, #0f3d28 100%);
        min-height: 100vh;
    }
    
    /* Ensure responsive container */
    .login-container {
        background: rgba(20, 40, 30, 0.95);
        padding: clamp(1.5rem, 4vw, 3rem);
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0, 255, 100, 0.1);
        max-width: min(90vw, 500px);
        margin: 2rem auto;
        border: 1px solid rgba(0, 255, 100, 0.2);
        backdrop-filter: blur(10px);
    }
    
    /* Responsive title */
    .title {
        color: #00ff88;
        text-align: center;
        font-size: clamp(1.8rem, 5vw, 2.5rem);
        font-weight: bold;
        margin-bottom: 0.5rem;
        text-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
    }
    
    /* Responsive subtitle */
    .subtitle {
        color: #88ffaa;
        text-align: center;
        margin-bottom: 2rem;
        font-size: clamp(0.9rem, 2vw, 1.1rem);
    }
    
    /* Input fields styling */
    .stTextInput input {
        background-color: rgba(15, 61, 40, 0.6) !important;
        color: #ffffff !important;
        border: 1px solid rgba(0, 255, 100, 0.3) !important;
        border-radius: 8px !important;
        padding: 0.75rem !important;
        font-size: clamp(0.9rem, 2vw, 1rem) !important;
    }
    
    .stTextInput input:focus {
        border-color: #00ff88 !important;
        box-shadow: 0 0 0 0.2rem rgba(0, 255, 136, 0.25) !important;
    }
    
    /* Button styling */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #00ff88 0%, #00cc6a 100%) !important;
        color: #0a4d2e !important;
        border: none !important;
        padding: 0.75rem 1rem !important;
        font-size: clamp(0.9rem, 2vw, 1.1rem) !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        cursor: pointer;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(0, 255, 136, 0.3) !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0, 255, 136, 0.4) !important;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(15, 61, 40, 0.4);
        color: #88ffaa;
        border-radius: 8px 8px 0 0;
        padding: 0.75rem 1.5rem;
        font-size: clamp(0.9rem, 2vw, 1rem);
        border: 1px solid rgba(0, 255, 100, 0.2);
        border-bottom: none;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: rgba(0, 255, 136, 0.15);
        color: #00ff88;
        border-color: #00ff88;
    }
    
    /* Form styling */
    .stForm {
        background-color: transparent;
        padding: 1rem 0;
    }
    
    /* Caption styling */
    .caption {
        color: #88ffaa !important;
        font-size: clamp(0.75rem, 1.5vw, 0.85rem) !important;
    }
    
    /* Alert styling */
    .stAlert {
        background-color: rgba(15, 61, 40, 0.8) !important;
        border: 1px solid rgba(0, 255, 100, 0.3) !important;
        border-radius: 8px !important;
        font-size: clamp(0.85rem, 1.8vw, 1rem) !important;
    }
    
    /* Success message */
    .stSuccess {
        background-color: rgba(0, 255, 136, 0.1) !important;
        color: #00ff88 !important;
    }
    
    /* Error message */
    .stError {
        background-color: rgba(255, 100, 100, 0.1) !important;
        color: #ff6666 !important;
    }
    
    /* Label styling */
    label {
        color: #88ffaa !important;
        font-size: clamp(0.9rem, 2vw, 1rem) !important;
    }
    
    /* Responsive columns */
    [data-testid="column"] {
        padding: clamp(0.5rem, 2vw, 1rem);
    }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(15, 61, 40, 0.3);
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(0, 255, 136, 0.3);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(0, 255, 136, 0.5);
    }
    </style>
""", unsafe_allow_html=True)

# ---------- Page Configuration ----------
st.set_page_config(
    page_title="Driver Monitoring - Login",
    page_icon="🚗",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ---------- Main Application ----------
def login_page():
    """Display login page"""
    
    # Add some top spacing
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Center container with responsive width
    col1, col2, col3 = st.columns([0.5, 3, 0.5])
    
    with col2:
        st.markdown('<p class="title">🚗 Driver Monitoring System</p>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">Secure Access Portal</p>', unsafe_allow_html=True)
        
        # Login/Signup tabs
        tab1, tab2 = st.tabs(["🔑 Sign In", "📝 Sign Up"])
        
        # Sign In Tab
        with tab1:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username", key="login_username")
                password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                col_a, col_b, col_c = st.columns([1, 2, 1])
                with col_b:
                    submit = st.form_submit_button("🚀 Sign In", use_container_width=True)
                
                if submit:
                    if not username or not password:
                        st.error("⚠️ Please fill in all fields")
                    else:
                        success, result = authenticate_user(username, password)
                        if success:
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.session_state.user_data = result
                            st.success("✅ Login successful! Launching dashboard...")
                            
                            # Try to launch the dashboard
                            if launch_dashboard():
                                st.info("🚗 Driver Fatigue Dashboard is opening in a new window...")
                                st.balloons()
                            else:
                                st.warning("⚠️ driver_fatigue_dashboard.py not found in current directory. Please ensure the file exists.")
                            
                            # Keep the success message visible
                            st.stop()
                        else:
                            st.error(f"❌ {result}")
        
        # Sign Up Tab
        with tab2:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.form("signup_form"):
                full_name = st.text_input("Full Name", placeholder="Enter your full name", key="signup_fullname")
                email = st.text_input("Email", placeholder="Enter your email", key="signup_email")
                new_username = st.text_input("Username", placeholder="Choose a username", key="signup_username")
                new_password = st.text_input("Password", type="password", placeholder="Create a password", key="signup_password")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password", key="signup_confirm")
                
                st.caption("⚠️ Password must be at least 6 characters with letters and numbers")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                col_a, col_b, col_c = st.columns([1, 2, 1])
                with col_b:
                    signup_submit = st.form_submit_button("✨ Create Account", use_container_width=True)
                
                if signup_submit:
                    # Validation
                    if not all([full_name, email, new_username, new_password, confirm_password]):
                        st.error("⚠️ Please fill in all fields")
                    elif not validate_email(email):
                        st.error("⚠️ Invalid email format")
                    elif new_password != confirm_password:
                        st.error("⚠️ Passwords do not match")
                    else:
                        is_valid, message = validate_password(new_password)
                        if not is_valid:
                            st.error(f"⚠️ {message}")
                        else:
                            success, message = create_user(new_username, email, new_password, full_name)
                            if success:
                                st.success(f"✅ {message} Please sign in.")
                                st.balloons()
                            else:
                                st.error(f"❌ {message}")
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Footer
        st.markdown("""
            <div style='text-align: center; color: #88ffaa; font-size: clamp(0.75rem, 1.5vw, 0.9rem); margin-top: 2rem;'>
                🔒 Secure Authentication System | Driver Safety First
            </div>
        """, unsafe_allow_html=True)

# ---------- Main Logic ----------
if st.session_state.logged_in:
    # Show success page after login
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
            <div style='text-align: center; color: #00ff88;'>
                <h1 style='font-size: clamp(2rem, 6vw, 3rem);'>✅ Welcome, {st.session_state.user_data['full_name']}!</h1>
                <p style='font-size: clamp(1rem, 3vw, 1.5rem); color: #88ffaa; margin-top: 1rem;'>
                    Dashboard is launching...
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🔄 Relaunch Dashboard", use_container_width=True):
            if launch_dashboard():
                st.success("🚗 Dashboard launched successfully!")
            else:
                st.error("❌ Could not find driver_fatigue_dashboard.py")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.user_data = None
            st.rerun()
else:
    login_page()