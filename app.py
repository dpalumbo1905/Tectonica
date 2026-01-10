import streamlit as st
import os
from PIL import Image
from streamlit_cropper import st_cropper
from utils_vision import pdf_page_to_image, detect_clashes_with_boxes
from utils_database import init_db, save_project, get_projects, teach_ai

# --- 1. INITIALIZATION ---
st.set_page_config(layout="wide", page_title="TECTONICA | Future of Construction")
init_db()

# --- 2. SESSION STATE MANAGEMENT ---
if 'view' not in st.session_state: st.session_state.view = "LANDING"
if 'projects' not in st.session_state: st.session_state.projects = {} 
if 'current_project' not in st.session_state: st.session_state.current_project = None
if 'step' not in st.session_state: st.session_state.step = "HOME"
if 'clash_data' not in st.session_state: st.session_state.clash_data = None

# --- 3. VIEW CONTROLLERS ---
def go_to_dashboard():
    st.session_state.view = "DASHBOARD"

def go_to_landing():
    st.session_state.view = "LANDING"

def create_project(name):
    if name:
        save_project(name)
        if name not in st.session_state.projects: st.session_state.projects[name] = {'files': {}}
        st.session_state.current_project = name
        st.session_state.step = "UPLOAD"

# =========================================================
# VIEW 1: THE LANDING PAGE (Cinematic Experience)
# =========================================================
if st.session_state.view == "LANDING":
    
    # [FIX] DYNAMIC CSS: Make background TRANSPARENT only for this page
    st.markdown("""
    <style>
    /* 1. MAKE MAIN CONTAINER TRANSPARENT TO REVEAL VIDEO */
    .stApp {
        background: transparent;
    }
    header {visibility: hidden;}
    
    /* 2. VIDEO LAYER (Behind everything) */
    #myVideo {
        position: fixed;
        right: 0;
        bottom: 0;
        min-width: 100%; 
        min-height: 100%;
        z-index: -1; /* Behind content */
    }
    
    /* 3. DARK OVERLAY (To make text readable over video) */
    .video-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.6); /* 60% Dark Tint */
        z-index: 0;
        pointer-events: none; /* Let clicks pass through */
    }

    /* 4. CONTENT LAYER (Above video) */
    .block-container {
        z-index: 1;
    }

    /* 5. NAVIGATION BAR */
    .nav-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 2rem;
        background-color: rgba(0, 0, 0, 0.8);
        border-bottom: 1px solid #333;
        margin-bottom: 2rem;
    }
    
    /* UI ELEMENTS */
    .nav-logo { font-size: 1.5rem; font-weight: 800; color: white; letter-spacing: 2px; }
    h1 { font-size: 4rem !important; font-weight: 800 !important; color: white !important; text-shadow: 2px 2px 4px #000000; }
    p { font-size: 1.2rem; color: #ddd; text-shadow: 1px 1px 2px #000000; }
    
    .stButton>button {
        background-color: #e60012;
        color: white;
        border: none;
        border-radius: 4px;
        font-weight: bold;
        letter-spacing: 1px;
        transition: 0.3s;
        text-transform: uppercase;
        border: 1px solid #e60012;
    }
    .stButton>button:hover {
        background-color: transparent;
        border: 1px solid white;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

    # A. INJECT VIDEO
    video_url = "https://videos.pexels.com/video-files/3129957/3129957-uhd_2560_1440_25fps.mp4"
    st.markdown(f"""
    <video autoplay muted loop id="myVideo">
        <source src="{video_url}" type="video/mp4">
    </video>
    <div class="video-overlay"></div>
    """, unsafe_allow_html=True)

    # B. NAV BAR (Simulated with Columns)
    nav_c1, nav_c2, nav_c3, nav_c4 = st.columns([4, 1, 1, 1])
    with nav_c1: st.markdown('<div class="nav-logo">TECTONICA</div>', unsafe_allow_html=True)
    with nav_c2: st.button("PROJECTS", key="nav_proj", on_click=go_to_dashboard)
    with nav_c3: st.button("SUPPORT", key="nav_sup")
    with nav_c4: st.button("LOGIN", key="nav_log", type="primary", on_click=go_to_dashboard)

    # C. HERO CONTENT
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    hero_col, _ = st.columns([2, 1])
    with hero_col:
        st.markdown("# BUILD WITHOUT<br>BLIND SPOTS.", unsafe_allow_html=True)
        st.markdown("""
        The Autonomous Construction Coordinator.  
        Upload drawings. Detect clashes. Break ground with confidence.
        """)
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("EXPLORE PLATFORM ➤", key="hero_cta", type="primary", on_click=go_to_dashboard)

    # D. FEATURE CARDS
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    f1, f2, f3 = st.columns(3)
    with f1: st.markdown("### ⚡ INSTANT ANALYSIS"); st.caption("Answers in seconds, not weeks.")
    with f2: st.markdown("### 👁️ VISION AI"); st.caption("Sees prints like a Superintendent.")
    with f3: st.markdown("### 🔗 PROCORE SYNC"); st.caption("Integrated document control.")


# =========================================================
# VIEW 2: THE DASHBOARD (Mission Control)
# =========================================================
elif st.session_state.view == "DASHBOARD":
    
    # [FIX] DYNAMIC CSS: Re-apply SOLID background for the dashboard
    st.markdown("""
    <style>
    .stApp {
        background-color: #0b0c10; /* Solid Dark Grey */
        color: #c5c6c7;
    }
    header {visibility: hidden;}
    .stButton>button {
        background-color: #e60012;
        color: white;
        border: none;
        border-radius: 0px; /* Sharp corners for Dashboard */
    }
    h1, h2, h3 { color: #ffffff !important; font-family: 'Helvetica Neue', sans-serif; }
    </style>
    """, unsafe_allow_html=True)
    
    # Dashboard Header
    dash_c1, dash_c2 = st.columns([6, 1])
    with dash_c1:
        st.markdown("## MISSION CONTROL")
    with dash_c2:
        st.button("LOGOUT", on_click=go_to_landing)
            
    st.divider()

    # --- CORE LOGIC (V8.0) ---
    if st.session_state.step == "HOME":
        c1, c2 = st.columns([1, 2])
        with c1:
            st.write("#### SELECT MISSION")
            existing_projects = get_projects()
            if existing_projects:
                sel_proj = st.selectbox("Active Projects", existing_projects)
                if st.button("RESUME MISSION"): 
                    create_project(sel_proj)
            
            st.write("#### INITIATE NEW MISSION")
            new_proj = st.text_input("Project Codename")
            if st.button("INITIALIZE PROJECT"): 
                create_project(new_proj)
        with c2:
             st.info("System Ready. Select a mission to begin telemetry.")

    elif st.session_state.step == "UPLOAD":
        st.sidebar.title(f"PROJECT: {st.session_state.current_project}")
        if st.sidebar.button("<< DASHBOARD"): 
            st.session_state.step = "HOME"
            st.rerun()
        
        tab1, tab2, tab3 = st.tabs(["1. UPLOAD", "2. REVIEW