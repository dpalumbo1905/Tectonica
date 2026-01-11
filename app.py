import streamlit as st
import os
import base64
from utils_database import init_db, save_project, get_projects, teach_ai
from utils_vision import pdf_page_to_image, detect_clashes_with_boxes
from streamlit_cropper import st_cropper

# --- 1. INITIALIZATION ---
st.set_page_config(layout="wide", page_title="TECTONICA | Orbital Construction")
init_db()

# --- 2. HELPER: IMAGE LOADER ---
def get_img_as_base64(file_path):
    if not os.path.exists(file_path): 
        return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    with open(file_path, "rb") as f: 
        data = f.read()
    return f"data:image/{file_path.split('.')[-1]};base64,{base64.b64encode(data).decode()}"

# --- 3. SESSION STATE ---
if 'view' not in st.session_state: st.session_state.view = "LANDING"
if 'projects' not in st.session_state: st.session_state.projects = {} 
if 'current_project' not in st.session_state: st.session_state.current_project = None
if 'step' not in st.session_state: st.session_state.step = "HOME"
if 'clash_data' not in st.session_state: st.session_state.clash_data = None

# --- 4. NAVIGATION ---
def go_to_dashboard(): 
    st.session_state.view = "DASHBOARD"

def go_to_landing(): 
    st.session_state.view = "LANDING"

def create_project(name):
    if name:
        save_project(name)
        if name not in st.session_state.projects: 
            st.session_state.projects[name] = {'files': {}}
        st.session_state.current_project = name
        st.session_state.step = "UPLOAD"

# =========================================================
# VIEW 1: LANDING PAGE (ROCKET LAB STYLE)
# =========================================================
if st.session_state.view == "LANDING":
    
    st.markdown("""
    <style>
    /* IMPORT FONTS: 'Barlow' */
    @import url('https://fonts.googleapis.com/css2?family=Barlow:wght@300;400;600;800&display=swap');

    /* 1. GLOBAL RESETS */
    .stApp { background: #000000; font-family: 'Barlow', sans-serif; }
    header {visibility: hidden;}
    .block-container { padding-top: 0rem; padding-bottom: 0rem; padding-left: 0rem; padding-right: 0rem; max-width: 100%; }
    
    /* 2. VIDEO LAYER */
    #myVideo { position: fixed; right: 0; bottom: 0; min-width: 100%; min-height: 100%; z-index: 0; opacity: 0.6; filter: grayscale(30%) contrast(1.1); }
    .overlay-grad { 
        position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
        background: linear-gradient(180deg, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.2) 40%, rgba(0,0,0,0.9) 100%);
        z-index: 1; pointer-events: none; 
    }

    /* 3. NAV BAR */
    .nav-container {
        position: absolute; top: 0; width: 100%; z-index: 10;
        display: flex; justify-content: space-between; align-items: center;
        padding: 2rem 4rem; border-bottom: 1px solid rgba(255,255,255,0.1);
    }

    /* 4. HERO SECTION */
    .hero-content {
        position: relative; z-index: 5; margin-top: 25vh; margin-left: 5vw;
        border-left: 4px solid #e60012; padding-left: 2rem;
    }
    h1 { 
        font-family: 'Barlow', sans-serif; font-weight: 800; font-size: 6rem !important; 
        color: white; line-height: 0.9; text-transform: uppercase; margin: 0;
        text-shadow: 0 4px 30px rgba(0,0,0,0.8);
    }
    .hero-sub { color: #cccccc; font-size: 1.5rem; letter-spacing: 1px; margin-top: 1rem; font-weight: 300; }

    /* 5. STATS BAR */
    .stats-bar {
        position: relative; z-index: 5; margin-top: 15vh;
        background: rgba(10,10,10,0.9); border-top: 1px solid #333; border-bottom: 1px solid #333;
        display: flex; justify-content: space-around; padding: 3rem 0;
    }
    .stat-item { text-align: center; }
    .stat-num { font-size: 4rem; font-weight: 800; color: white; line-height: 1; }
    .stat-label { font-size: 0.9rem; color: #e60012; text-transform: uppercase; letter-spacing: 2px; margin-top: 0.5rem; font-weight: 600; }

    /* 6. GRID SECTION */
    .grid-section { position: relative; z-index: 5; background: #0b0c10; padding: 4rem 5vw; }
    .grid-title { font-size: 2rem; color: white; text-transform: uppercase; border-bottom: 1px solid #333; padding-bottom: 1rem; margin-bottom: 2rem; }
    
    .tech-card {
        background: #111; border: 1px solid #333; transition: all 0.3s ease; position: relative; overflow: hidden; height: 100%;
    }
    .tech-card:hover { border-color: #e60012; transform: translateY(-5px); }
    .tech-img { width: 100%; height: 250px; object-fit: cover; filter: grayscale(100%); transition: 0.4s; }
    .tech-card:hover .tech-img { filter: grayscale(0%); }
    .tech-content { padding: 2rem; }
    .tech-head { font-size: 1.5rem; color: white; font-weight: 700; text-transform: uppercase; margin-bottom: 0.5rem; }
    .tech-desc { color: #888; font-size: 0.9rem; line-height: 1.6; }

    /* 7. BUTTONS */
    .stButton>button {
        background: transparent; color: white; border: 2px solid white;
        border-radius: 0; font-family: 'Barlow', sans-serif; font-weight: 700; 
        text-transform: uppercase; padding: 0.8rem 2.5rem; letter-spacing: 2px;
        transition: all 0.3s;
    }
    .stButton>button:hover { background: #e60012; border-color: #e60012; color: white; }
    
    /* Footer */
    .footer { background: #050505; color: #444; text-align: center; padding: 3rem; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; }
    </style>
    """, unsafe_allow_html=True)

    # LAYERS
    video_url = "https://videos.pexels.com/video-files/3129957/3129957-uhd_2560_1440_25fps.mp4"
    st.markdown(f"""<video autoplay muted loop id="myVideo"><source src="{video_url}" type="video/mp4"></video><div class="overlay-grad"></div>""", unsafe_allow_html=True)

    # 1. NAVIGATION
    c1, c2, c3 = st.columns([1, 6, 2])
    with c1:
        st.markdown('<div style="padding: 2rem 4rem;"></div>', unsafe_allow_html=True) 
    with c3:
        st.markdown('<div style="position: absolute; top: 30px; right: 50px; z-index: 99;">', unsafe_allow_html=True)
        st.button("MISSION CONTROL LOGIN", on_click=go_to_dashboard)
        st.markdown('</div>', unsafe_allow_html=True)

    # 2. HERO CONTENT
    st.markdown(f"""
    <div class="hero-content">
        <h1>We Don't Just<br>Read Plans.</h1>
        <h1>We <span style="color:#e60012">Execute.</span></h1>
        <div class="hero-sub">THE PREMIER OPERATING SYSTEM FOR CONSTRUCTION.</div>
    </div>
    """, unsafe_allow_html=True)

    # 3. STATS BAR
    st.markdown("""
    <div class="stats-bar">
        <div class="stat-item">
            <div class="stat-num">142</div>
            <div class="stat-label">PROJECTS DEPLOYED</div>
        </div>
        <div class="stat-item">
            <div class="stat-num">0</div>
            <div class="stat-label">CRITICAL FAILURES</div>
        </div>
        <div class="stat-item">
            <div class="stat-num">100%</div>
            <div class="stat-label">MISSION SUCCESS</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4. GRID SECTION (DEDENTED TO FIX CODE BLOCK ERROR)
    src_3d = get_img_as_base64("card_3d.jpg")
    src_procore = get_img_as_base64("card_procore.png")
    src_vision = "https://images.pexels.com/photos/2760241/pexels-photo-2760241.jpeg?auto=compress&cs=tinysrgb&w=800"

    st.markdown(f"""
<div class="grid-section">
<div class="grid-title">SYSTEM ARCHITECTURE</div>
<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 2rem;">

<div class="tech-card">
<img src="{src_3d}" class="tech-img">
<div class="tech-content">
<div class="tech-head">ENGINE A1: CLASH</div>
<div class="tech-desc">Autonomous spatial conflict resolution. Utilizing vector-based geometry to identify MEP collisions before fabrication.</div>
</div>
</div>

<div class="tech-card">
<img src="{src_vision}" class="tech-img">
<div class="tech-content">
<div class="tech-head">SENSOR SUITE: VISION</div>
<div class="tech-desc">Optical Character Recognition (OCR) and Semantic Segmentation tailored for architectural schematic interpretation.</div>
</div>
</div>

<div class="tech-card">
<img src="{src_procore}" class="tech-img" style="object-fit: contain; padding: 20px; background: #fff;">
<div class="tech-content">
<div class="tech-head">LINK: PROCORE</div>
<div class="tech-desc">Secure, bi-directional telemetry with your existing Construction OS. Push anomalies directly to the RFI log.</div>
</div>
</div>

</div>
</div>
<div class="footer">
TECTONICA AEROSPACE & CONSTRUCTION INDUSTRIES <br>
USA • NZ • LEO
</div>
""", unsafe_allow_html=True)


# =========================================================
# VIEW 2: DASHBOARD (MISSION CONTROL)
# =========================================================
elif st.session_state.view == "DASHBOARD":
    
    st.markdown("""
    <style>
    .stApp { background-color: #0b0c10; color: #c5c6c7; font-family: 'Barlow', sans-serif; }
    h1, h2, h3 { color: white; text-transform: uppercase; letter-spacing: 2px; }
    .stButton>button { border: 1px solid #e60012; color: #e60012; }
    .stButton>button:hover { background: #e60012; color: white; }
    </style>
    """, unsafe_allow_html=True)
    
    dash_c1, dash_c2 = st.columns([6, 1])
    with dash_c1: st.title("MISSION CONTROL")
    with dash_c2: st.button("LOGOUT", on_click=go_to_landing)
    st.divider()

    if st.session_state.step == "HOME":
        c1, c2 = st.columns([1, 2])
        with c1:
            st.write("#### ACTIVE OPERATIONS")
            existing = get_projects()
            if existing:
                sel = st.selectbox("Select Mission", existing)
                if st.button("RESUME"): 
                    create_project(sel)
            st.write("#### NEW OPERATION")
            new_p = st.text_input("Codename")
            if st.button("INITIALIZE"): 
                create_project(new_p)
        with c2: 
            st.info("Standby for input.")

    elif st.session_state.step == "UPLOAD":
        st.sidebar.title(f"OP: {st.session_state.current_project}")
        if st.sidebar.button("<< ABORT"): 
            st.session_state.step = "HOME"
            st.rerun()
        
        tab1, tab2, tab3 = st.tabs(["1. INGEST", "2. TELEMETRY", "3. LAUNCH"])
        
        with tab1:
            files = st.file_uploader("Upload Schematics", type=['pdf'], accept_multiple_files=True)
            if files:
                for f in files:
                    if f.name not in st.session_state.projects[st.session_state.current_project]['files']:
                        st.session_state.projects[st.session_state.current_project]['files'][f.name] = {
                            'image': pdf_page_to_image(f), 
                            'scale': "Unknown", 
                            'discipline': "Unassigned", 
                            'type': 'sheet', 
                            'parent': None, 
                            'needs_crop': False
                        }
                st.success("Payload Integrated.")

        with tab2:
            p_files = st.session_state.projects[st.session_state.current_project]['files']
            s_list = [f for f, d in p_files.items() if d['type'] == 'sheet']
            if s_list:
                sel_f = st.selectbox("Select Asset", s_list)
                curr = p_files[sel_f]
                c_i, c_d = st.columns([2, 1])
                with c_i: 
                    st.image(curr['image'], use_column_width=True)
                with c_d:
                    curr['discipline'] = st.selectbox("System", ["Unassigned", "Arch", "Struct", "Mech", "Elec"], key="disc")
                    if st.button("GENERATE SUB-ASSETS"): 
                        st.success("Sub-systems isolated.")

        with tab3:
            assets = st.session_state.projects[st.session_state.current_project]['files']
            a_list = list(assets.keys())
            if len(a_list) < 2: 
                st.warning("Insufficient Payload.")
            else:
                c1, c2 = st.columns(2)
                with c1: 
                    b = st.selectbox("Primary Stage", a_list, key="base")
                    st.image(assets[b]['image'], use_column_width=True)
                with c2: 
                    o = st.selectbox("Secondary Stage", [a for a in a_list if a != b], key="over") 
                
                if o: 
                    st.image(assets[o]['image'], use_column_width=True)
                
                if o and st.button("INITIATE SEQUENCE", type="primary"):
                    with st.spinner("Calculating Trajectory..."):
                        res, data = detect_clashes_with_boxes(assets[b]['image'], "1:100", assets[b]['discipline'], assets[o]['discipline'])
                        st.session_state.clash_data = data
                        st.image(res, caption="Impact Detected")
