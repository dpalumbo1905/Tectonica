import streamlit as st
import os
import base64
from PIL import Image
from streamlit_cropper import st_cropper
from utils_vision import pdf_page_to_image, detect_clashes_with_boxes
from utils_database import init_db, save_project, get_projects, teach_ai

# --- 1. INITIALIZATION ---
st.set_page_config(layout="wide", page_title="TECTONICA | Construction Intelligence")
init_db()

# --- 2. HELPER: IMAGE LOADER ---
def get_img_as_base64(file_path):
    if not os.path.exists(file_path):
        return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    with open(file_path, "rb") as f: data = f.read()
    encoded = base64.b64encode(data).decode()
    ext = file_path.split('.')[-1]
    return f"data:image/{ext};base64,{encoded}"

# --- 3. SESSION STATE ---
if 'view' not in st.session_state: st.session_state.view = "LANDING"
if 'projects' not in st.session_state: st.session_state.projects = {} 
if 'current_project' not in st.session_state: st.session_state.current_project = None
if 'step' not in st.session_state: st.session_state.step = "HOME"
if 'clash_data' not in st.session_state: st.session_state.clash_data = None

# --- 4. NAVIGATION ---
def go_to_dashboard(): st.session_state.view = "DASHBOARD"
def go_to_landing(): st.session_state.view = "LANDING"
def create_project(name):
    if name:
        save_project(name)
        if name not in st.session_state.projects: st.session_state.projects[name] = {'files': {}}
        st.session_state.current_project = name
        st.session_state.step = "UPLOAD"

# =========================================================
# VIEW 1: LANDING PAGE (PROFESSIONAL V10.0)
# =========================================================
if st.session_state.view == "LANDING":
    
    st.markdown("""
    <style>
    /* IMPORT FONTS: 'Orbitron' for headers, 'Inter' for text */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Orbitron:wght@500;700;900&display=swap');

    /* 1. GLOBAL RESETS */
    .stApp { background: transparent; font-family: 'Inter', sans-serif; }
    header {visibility: hidden;}
    
    /* 2. VIDEO LAYER */
    #myVideo { position: fixed; right: 0; bottom: 0; min-width: 100%; min-height: 100%; z-index: -1; }
    .video-overlay { 
        position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
        background: radial-gradient(circle, rgba(0,0,0,0.4) 0%, rgba(0,0,0,0.9) 100%); /* Vignette effect */
        z-index: 0; pointer-events: none; 
    }
    .block-container { z-index: 1; padding-top: 2rem; max-width: 1200px; }

    /* 3. TYPOGRAPHY */
    h1 { 
        font-family: 'Orbitron', sans-serif !important; 
        font-weight: 900 !important; 
        letter-spacing: 2px !important;
        text-transform: uppercase;
        background: linear-gradient(90deg, #FFFFFF 0%, #B0B0B0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0px 4px 10px rgba(0,0,0,0.5);
    }
    p { color: #cccccc; font-size: 1.1rem; line-height: 1.6; }

    /* 4. GLASSMORPHISM CARDS */
    .feature-card {
        background: rgba(25, 25, 25, 0.4); /* Low opacity */
        backdrop-filter: blur(12px); /* The "Frosted Glass" effect */
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1); /* Subtle white border */
        border-radius: 16px;
        overflow: hidden;
        margin-bottom: 20px;
        display: flex; flex-direction: column;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); /* Bouncy transition */
    }
    
    .feature-card:hover { 
        transform: translateY(-8px); 
        background: rgba(40, 40, 40, 0.6);
        border: 1px solid rgba(230, 0, 18, 0.5); /* Red Glow Border */
        box-shadow: 0 20px 40px rgba(0,0,0,0.6), 0 0 20px rgba(230, 0, 18, 0.2); /* Red Glow Shadow */
    }
    
    .card-header-img { width: 100%; height: 220px; position: relative; overflow: hidden; border-bottom: 1px solid rgba(255,255,255,0.05); }
    .card-img { width: 100%; height: 100%; object-fit: cover; opacity: 0.8; transition: opacity 0.3s, transform 0.5s; }
    .feature-card:hover .card-img { opacity: 1; transform: scale(1.05); }

    .procore-header { background-color: rgba(255,255,255,0.95); display: flex; align-items: center; justify-content: center; }
    .procore-img { width: 50% !important; height: auto !important; object-fit: contain !important; opacity: 1 !important; }

    .card-content { padding: 24px; }
    .card-title { 
        font-family: 'Orbitron', sans-serif; 
        color: white; font-size: 1.1rem; margin-bottom: 8px; letter-spacing: 1px; 
    }
    .card-desc { color: #aaa; font-size: 0.95rem; }

    /* 5. BUTTONS (NEON STYLE) */
    .stButton>button { 
        background-color: #e60012; color: white; border: none; 
        border-radius: 6px; font-family: 'Orbitron', sans-serif; font-weight: 700; 
        letter-spacing: 1px; padding: 0.5rem 1.5rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover { 
        background-color: #ff1f32; 
        box-shadow: 0 0 15px rgba(230, 0, 18, 0.6); /* Neon Glow */
        transform: scale(1.02);
    }
    
    /* 6. LOGO & NAV */
    [data-testid="stImage"] img { filter: drop-shadow(0 0 8px rgba(255,255,255,0.3)); }

    /* 7. FOOTER */
    .footer {
        margin-top: 100px;
        padding: 40px 0;
        border-top: 1px solid rgba(255,255,255,0.1);
        text-align: center;
        color: #666;
        font-size: 0.8rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # VIDEO BG
    video_url = "https://videos.pexels.com/video-files/3129957/3129957-uhd_2560_1440_25fps.mp4"
    st.markdown(f"""<video autoplay muted loop id="myVideo"><source src="{video_url}" type="video/mp4"></video><div class="video-overlay"></div>""", unsafe_allow_html=True)

    # NAV
    nav_c1, nav_c2, nav_c3, nav_c4 = st.columns([4, 1, 1, 1])
    with nav_c1: 
        if os.path.exists("logo.png"): st.image("logo.png", width=160)
        else: st.markdown('### TECTONICA')
    with nav_c2: st.button("PROJECTS", key="nav_proj", on_click=go_to_dashboard)
    with nav_c3: st.button("SUPPORT", key="nav_sup")
    with nav_c4: st.button("LOGIN", key="nav_log", type="primary", on_click=go_to_dashboard)

    # HERO
    st.markdown("<br><br>", unsafe_allow_html=True)
    hero_col, _ = st.columns([2, 1])
    with hero_col:
        st.markdown("# BUILD WITHOUT<br>BLIND SPOTS.", unsafe_allow_html=True)
        st.markdown("""
        <p>
        The world's first <b>Autonomous Construction Coordinator</b>.<br>
        Stop clashes before they reach the field.
        </p>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("EXPLORE PLATFORM ➤", key="hero_cta", type="primary", on_click=go_to_dashboard)

    # FEATURES
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    src_3d = get_img_as_base64("card_3d.jpg")
    src_procore = get_img_as_base64("card_procore.png")
    src_blueprints = "https://images.pexels.com/photos/2760241/pexels-photo-2760241.jpeg?auto=compress&cs=tinysrgb&w=800"

    st.markdown(f"""
    <div style="display: flex; gap: 24px; justify-content: center; flex-wrap: wrap;">

    <div class="feature-card" style="flex: 1; min-width: 320px; max-width: 400px;">
        <div class="card-header-img">
            <img src="{src_3d}" class="card-img">
        </div>
        <div class="card-content">
            <div class="card-title">INSTANT 3D ANALYSIS</div>
            <div class="card-desc">Ingest BIM models and 2D sets simultaneously. Detect MEP clashes with 99.8% accuracy in seconds.</div>
        </div>
    </div>

    <div class="feature-card" style="flex: 1; min-width: 320px; max-width: 400px;">
        <div class="card-header-img">
            <img src="{src_blueprints}" class="card-img">
        </div>
        <div class="card-content">
            <div class="card-title">CONTEXTUAL VISION AI</div>
            <div class="card-desc">Our engine understands architectural intent, distinguishing between actual clashes and necessary penetrations.</div>
        </div>
    </div>

    <div class="feature-card" style="flex: 1; min-width: 320px; max-width: 400px;">
        <div class="card-header-img procore-header">
            <img src="{src_procore}" class="card-img procore-img">
        </div>
        <div class="card-content">
            <div class="card-title">NATIVE PROCORE SYNC</div>
            <div class="card-desc">Two-way integration. Push RFIs and Observations directly to your existing Project Management OS.</div>
        </div>
    </div>

    </div>
    
    <div class="footer">
        TECTONICA © 2026. All Systems Operational.<br>
        New York • London • Tokyo
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# VIEW 2: DASHBOARD (UNCHANGED CORE)
# =========================================================
elif st.session_state.view == "DASHBOARD":
    
    st.markdown("""<style>.stApp { background-color: #0b0c10; color: #c5c6c7; font-family: 'Inter', sans-serif;} header {visibility: hidden;} .stButton>button { background-color: #e60012; color: white; border-radius: 0px; margin-top: 0px; font-family: 'Orbitron', sans-serif; } [data-testid="stImage"] img { mix-blend-mode: normal; filter: none; } h1, h2, h3 { color: #ffffff !important; font-family: 'Orbitron', sans-serif; }</style>""", unsafe_allow_html=True)
    
    dash_c1, dash_c2 = st.columns([6, 1])
    with dash_c1: st.markdown("## MISSION CONTROL")
    with dash_c2: st.button("LOGOUT", on_click=go_to_landing)
    st.divider()

    if st.session_state.step == "HOME":
        c1, c2 = st.columns([1, 2])
        with c1:
            st.write("#### SELECT MISSION")
            existing = get_projects()
            if existing:
                sel = st.selectbox("Active Projects", existing)
                if st.button("RESUME MISSION"): create_project(sel)
            st.write("#### INITIATE NEW MISSION")
            new_p = st.text_input("Project Codename")
            if st.button("INITIALIZE PROJECT"): create_project(new_p)
        with c2: st.info("System Ready.")

    elif st.session_state.step == "UPLOAD":
        st.sidebar.title(f"PROJECT: {st.session_state.current_project}")
        if st.sidebar.button("<< DASHBOARD"): st.session_state.step = "HOME"; st.rerun()
        
        tab1, tab2, tab3 = st.tabs(["1. UPLOAD", "2. REVIEW", "3. ANALYZE"])
        
        with tab1:
            st.header("PAYLOAD INTEGRATION")
            files = st.file_uploader("Upload PDF Set", type=['pdf'], accept_multiple_files=True)
            if files:
                for f in files:
                    if f.name not in st.session_state.projects[st.session_state.current_project]['files']:
                        img = pdf_page_to_image(f)
                        st.session_state.projects[st.session_state.current_project]['files'][f.name] = {'image': img, 'scale': "Unknown", 'discipline': "Unassigned", 'type': 'sheet', 'parent': None, 'needs_crop': False}
                st.success(f"{len(files)} Documents Integrated.")

        with tab2:
            st.header("TELEMETRY CHECK")
            p_files = st.session_state.projects[st.session_state.current_project]['files']
            s_list = [f for f, d in p_files.items() if d['type'] == 'sheet']
            if s_list:
                sel_f = st.selectbox("Select Drawing", s_list)
                curr = p_files[sel_f]
                c_i, c_d = st.columns([2, 1])
                with c_i: st.image(curr['image'], use_column_width=True)
                with c_d:
                    curr['discipline'] = st.selectbox("Category", ["Unassigned", "Arch", "Struct", "Mech", "Elec"], key="disc")
                    curr['scale'] = st.text_input("Scale", value=curr['scale'])
                    st.divider()
                    dets = st.text_area("Generate Details (e.g. 7/A100)")
                    if st.button("GENERATE"):
                        if dets:
                            for r in dets.split(','):
                                nm = f"{sel_f} - {r.strip()}"
                                p_files[nm] = curr.copy(); p_files[nm]['type'] = 'detail'; p_files[nm]['needs_crop'] = True
                            st.success("Generated.")
                            st.rerun()

        with tab3:
            st.header("LAUNCH ANALYSIS")
            assets = st.session_state.projects[st.session_state.current_project]['files']
            a_list = list(assets.keys())
            if len(a_list) < 2: st.warning("Upload more files.")
            else:
                c1, c2 = st.columns(2)
                with c1:
                    b = st.selectbox("Base Layer", a_list, key="base")
                    if assets[b].get('needs_crop'):
                        st.warning("Crop Required")
                        cr = st_cropper(assets[b]['image'], realtime_update=True, key="c1", aspect_ratio=None)
                        if st.button("Confirm Base"): assets[b]['image'] = cr; assets[b]['needs_crop'] = False; st.rerun()
                    else: st.image(assets[b]['image'], use_column_width=True)
                with c2:
                    o = st.selectbox("Overlay Layer", [a for a in a_list if a != b], key="over")
                    if o:
                        if assets[o].get('needs_crop'):
                            st.warning("Crop Required")
                            cr2 = st_cropper(assets[o]['image'], realtime_update=True, key="c2", aspect_ratio=None)
                            if st.button("Confirm Overlay"): assets[o]['image'] = cr2; assets[o]['needs_crop'] = False; st.rerun()
                        else: st.image(assets[o]['image'], use_column_width=True)
                
                if o and not assets[b].get('needs_crop') and not assets[o].get('needs_crop'):
                    if st.button("INITIATE SEQUENCE", type="primary"):
                        with st.spinner("Processing..."):
                            res, data = detect_clashes_with_boxes(assets[b]['image'], assets[b]['scale'], assets[b]['discipline'], assets[o]['discipline'])
                            st.session_state.clash_data = data
                            st.image(res, caption="Results")
                    if st.session_state.clash_data:
                        for i, cl in enumerate(st.session_state.clash_data):
                            ca, cb = st.columns([4,1])
                            ca.write(f"**{i+1}:** {cl.get('description')}")
                            if cb.button("False Alarm", key=f"f{i}"): teach_ai(cl.get('description'), "safe"); st.toast("Memory Updated")
