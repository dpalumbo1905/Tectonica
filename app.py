import streamlit as st
import os
import base64
from PIL import Image
from streamlit_cropper import st_cropper
from utils_vision import pdf_page_to_image, detect_clashes_with_boxes
from utils_database import init_db, save_project, get_projects, teach_ai

# --- 1. INITIALIZATION ---
st.set_page_config(layout="wide", page_title="TECTONICA | Future of Construction")
init_db()

# --- 2. HELPER: IMAGE LOADER ---
def get_img_as_base64(file_path):
    """
    Reads a local image file and converts it to base64 so it can be shown in HTML.
    If file is missing, returns a transparent placeholder.
    """
    if not os.path.exists(file_path):
        return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=" # Empty pixel
    
    with open(file_path, "rb") as f:
        data = f.read()
    
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
# VIEW 1: LANDING PAGE
# =========================================================
if st.session_state.view == "LANDING":
    
    st.markdown("""
    <style>
    .stApp { background: transparent; }
    header {visibility: hidden;}
    #myVideo { position: fixed; right: 0; bottom: 0; min-width: 100%; min-height: 100%; z-index: -1; }
    .video-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.7); z-index: 0; pointer-events: none; }
    .block-container { z-index: 1; padding-top: 2rem; }
    [data-testid="stImage"] img { mix-blend-mode: screen; filter: contrast(1.2); }

    /* CARD STYLES */
    .feature-card {
        background-color: rgba(20, 20, 20, 0.85);
        border: 1px solid #333; border-radius: 12px;
        transition: transform 0.3s ease, box-shadow 0.3s ease, border 0.3s ease;
        overflow: hidden; margin-bottom: 20px;
        display: flex; flex-direction: column;
    }
    .feature-card:hover { transform: translateY(-10px) scale(1.02); box-shadow: 0 15px 30px rgba(230, 0, 18, 0.4); border: 1px solid #e60012; }
    
    .card-header-img { width: 100%; height: 250px; position: relative; overflow: hidden; }
    .card-img { width: 100%; height: 100%; object-fit: cover; opacity: 0.85; transition: opacity 0.3s, transform 0.3s; }
    
    .procore-header { background-color: white; display: flex; align-items: center; justify-content: center; }
    .procore-img { width: 60% !important; height: auto !important; object-fit: contain !important; opacity: 1 !important; }

    .feature-card:hover .card-img { opacity: 1; transform: scale(1.1); }
    .card-content { padding: 25px; flex-grow: 1; display: flex; flex-direction: column; justify-content: flex-start; }
    .card-title { color: white; font-weight: 800; font-size: 1.3rem; margin-bottom: 10px; letter-spacing: 1px; }
    .card-desc { color: #ccc; font-size: 1rem; line-height: 1.5; }

    .stButton>button { background-color: #e60012; color: white; border: none; border-radius: 4px; font-weight: bold; text-transform: uppercase; margin-top: 10px; }
    .stButton>button:hover { background-color: transparent; border: 1px solid white; }
    </style>
    """, unsafe_allow_html=True)

    # BACKGROUND
    video_url = "https://videos.pexels.com/video-files/3129957/3129957-uhd_2560_1440_25fps.mp4"
    st.markdown(f"""<video autoplay muted loop id="myVideo"><source src="{video_url}" type="video/mp4"></video><div class="video-overlay"></div>""", unsafe_allow_html=True)

    # NAV BAR
    nav_c1, nav_c2, nav_c3, nav_c4 = st.columns([4, 1, 1, 1])
    with nav_c1: 
        if os.path.exists("logo.png"): st.image("logo.png", width=180)
        else: st.markdown('### TECTONICA')
    with nav_c2: st.button("PROJECTS", key="nav_proj", on_click=go_to_dashboard)
    with nav_c3: st.button("SUPPORT", key="nav_sup")
    with nav_c4: st.button("LOGIN", key="nav_log", type="primary", on_click=go_to_dashboard)

    # HERO
    st.markdown("<br><br>", unsafe_allow_html=True)
    hero_col, _ = st.columns([2, 1])
    with hero_col:
        st.markdown("# BUILD WITHOUT<br>BLIND SPOTS.", unsafe_allow_html=True)
        st.markdown('<p style="font-size: 1.2rem; color: #ddd;">The Autonomous Construction Coordinator.</p>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("EXPLORE PLATFORM ➤", key="hero_cta", type="primary", on_click=go_to_dashboard)

    # FEATURE CARDS (Dynamic Loading)
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    # 1. LOAD LOCAL IMAGES SAFELY
    # NOTE: You must upload 'card_3d.jpg' and 'card_procore.png' to GitHub for this to work!
    src_3d = get_img_as_base64("card_3d.jpg")
    src_procore = get_img_as_base64("card_procore.png")
    src_blueprints = "https://images.pexels.com/photos/2760241/pexels-photo-2760241.jpeg?auto=compress&cs=tinysrgb&w=800"

    st.markdown(f"""
<div style="display: flex; gap: 30px; justify-content: center; flex-wrap: wrap;">

<div class="feature-card" style="flex: 1; min-width: 300px; max-width: 400px;">
<div class="card-header-img">
<img src="{src_3d}" class="card-img">
</div>
<div class="card-content">
<div class="card-title">⚡ INSTANT 3D ANALYSIS</div>
<div class="card-desc">AI-driven clash detection on complex BIM and MEP systems in seconds.</div>
</div>
</div>

<div class="feature-card" style="flex: 1; min-width: 300px; max-width: 400px;">
<div class="card-header-img">
<img src="{src_blueprints}" class="card-img">
</div>
<div class="card-content">
<div class="card-title">👁️ COMPUTER VISION</div>
<div class="card-desc">Our engine reads 2D blueprints with the context of a Lead Superintendent.</div>
</div>
</div>

<div class="feature-card" style="flex: 1; min-width: 300px; max-width: 400px;">
<div class="card-header-img procore-header">
<img src="{src_procore}" class="card-img procore-img">
</div>
<div class="card-content">
<div class="card-title">🔗 PROCORE SYNC</div>
<div class="card-desc">Seamless, two-way integration with your existing Construction OS.</div>
</div>
</div>

</div>
""", unsafe_allow_html=True)

# =========================================================
# VIEW 2: DASHBOARD
# =========================================================
elif st.session_state.view == "DASHBOARD":
    
    st.markdown("""<style>.stApp { background-color: #0b0c10; color: #c5c6c7; } header {visibility: hidden;} .stButton>button { background-color: #e60012; color: white; border-radius: 0px; margin-top: 0px; } [data-testid="stImage"] img { mix-blend-mode: normal; filter: none; } h1, h2, h3 { color: #ffffff !important; font-family: 'Helvetica Neue', sans-serif; }</style>""", unsafe_allow_html=True)
    
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
