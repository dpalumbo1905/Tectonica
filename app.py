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
    
    /* 2. VIDEO LAYER */
    #myVideo {
        position: fixed;
        right: 0;
        bottom: 0;
        min-width: 100%; 
        min-height: 100%;
        z-index: -1; 
    }
    .video-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7); /* Darker tint for better contrast */
        z-index: 0;
        pointer-events: none; 
    }

    /* 3. CONTENT LAYER */
    .block-container {
        z-index: 1;
        padding-top: 2rem;
    }

    /* 4. LOGO CHECKERBOARD FIX */
    /* This blends the image with the background, hiding dark pixels */
    [data-testid="stImage"] img {
        mix-blend-mode: screen; 
        filter: contrast(1.2);
    }

    /* 5. INTERACTIVE FEATURE CARDS */
    .feature-card {
        background-color: rgba(20, 20, 20, 0.8);
        border: 1px solid #333;
        border-radius: 10px;
        padding: 0px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        overflow: hidden;
        height: 100%;
    }
    .feature-card:hover {
        transform: scale(1.05); /* The "Pop Up" Effect */
        box-shadow: 0 10px 20px rgba(230, 0, 18, 0.3);
        border: 1px solid #e60012;
    }
    .card-img {
        width: 100%;
        height: 150px;
        object-fit: cover;
        opacity: 0.8;
        transition: opacity 0.3s;
    }
    .feature-card:hover .card-img {
        opacity: 1;
    }
    .card-content {
        padding: 20px;
    }
    .card-title {
        color: white;
        font-weight: bold;
        font-size: 1.2rem;
        margin-bottom: 5px;
    }
    .card-desc {
        color: #bbb;
        font-size: 0.9rem;
    }

    /* 6. BUTTONS */
    .stButton>button {
        background-color: #e60012;
        color: white;
        border: none;
        border-radius: 4px;
        font-weight: bold;
        text-transform: uppercase;
        margin-top: 10px;
    }
    .stButton>button:hover {
        background-color: transparent;
        border: 1px solid white;
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

    # B. NAV BAR
    nav_c1, nav_c2, nav_c3, nav_c4 = st.columns([4, 1, 1, 1])
    with nav_c1: 
        if os.path.exists("logo.png"):
            st.image("logo.png", width=180)
        else:
            st.markdown('### TECTONICA')
    with nav_c2: st.button("PROJECTS", key="nav_proj", on_click=go_to_dashboard)
    with nav_c3: st.button("SUPPORT", key="nav_sup")
    with nav_c4: st.button("LOGIN", key="nav_log", type="primary", on_click=go_to_dashboard)

    # C. HERO CONTENT
    st.markdown("<br><br>", unsafe_allow_html=True)
    hero_col, _ = st.columns([2, 1])
    with hero_col:
        st.markdown("# BUILD WITHOUT<br>BLIND SPOTS.", unsafe_allow_html=True)
        st.markdown("""
        <p style="font-size: 1.2rem; color: #ddd;">
        The Autonomous Construction Coordinator. <br>
        Upload drawings. Detect clashes. Break ground with confidence.
        </p>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("EXPLORE PLATFORM ➤", key="hero_cta", type="primary", on_click=go_to_dashboard)

    # D. POP-UP FEATURE CARDS (HTML Implementation)
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    # Image URLs for the cards
    img_navis = "https://images.pexels.com/photos/834892/pexels-photo-834892.jpeg?auto=compress&cs=tinysrgb&w=600" # 3D Model vibe
    img_super = "https://images.pexels.com/photos/544966/pexels-photo-544966.jpeg?auto=compress&cs=tinysrgb&w=600" # Workers with plans
    img_procore = "https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Procore_Logo.svg/512px-Procore_Logo.svg.png" # Procore Logo
    
    # Injecting HTML Cards
    st.markdown(f"""
    <div style="display: flex; gap: 20px; justify-content: space-between;">
        
        <div class="feature-card">
            <img src="{img_navis}" class="card-img">
            <div class="card-content">
                <div class="card-title">⚡ INSTANT ANALYSIS</div>
                <div class="card-desc">Navisworks-grade clash detection in seconds, not weeks.</div>
            </div>
        </div>

        <div class="feature-card">
            <img src="{img_super}" class="card-img">
            <div class="card-content">
                <div class="card-title">👁️ VISION AI</div>
                <div class="card-desc">Our AI reads blueprints like a Superintendent.</div>
            </div>
        </div>

        <div class="feature-card">
            <div style="height:150px; background:white; display:flex; align-items:center; justify-content:center;">
                <img src="{img_procore}" style="width:150px; height:auto; opacity:1;">
            </div>
            <div class="card-content">
                <div class="card-title">🔗 PROCORE SYNC</div>
                <div class="card-desc">Seamless integration with your existing Construction OS.</div>
            </div>
        </div>

    </div>
    """, unsafe_allow_html=True)


# =========================================================
# VIEW 2: THE DASHBOARD (Mission Control)
# =========================================================
elif st.session_state.view == "DASHBOARD":
    
    # [FIX] DYNAMIC CSS: Re-apply SOLID background for the dashboard
    st.markdown("""
    <style>
    .stApp {
        background-color: #0b0c10;
        color: #c5c6c7;
    }
    header {visibility: hidden;}
    .stButton>button {
        background-color: #e60012;
        color: white;
        border: none;
        border-radius: 0px;
        margin-top: 0px;
    }
    /* Reset the mix-blend-mode for dashboard images so plans look normal */
    [data-testid="stImage"] img {
        mix-blend-mode: normal; 
        filter: none;
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
        
        tab1, tab2, tab3 = st.tabs(["1. UPLOAD", "2. REVIEW", "3. ANALYZE"])
        
        with tab1:
            st.header("PAYLOAD INTEGRATION")
            files = st.file_uploader("Upload Project PDF Set", type=['pdf'], accept_multiple_files=True)
            if files:
                for f in files:
                    if f.name not in st.session_state.projects[st.session_state.current_project]['files']:
                        img = pdf_page_to_image(f)
                        st.session_state.projects[st.session_state.current_project]['files'][f.name] = {
                            'image': img, 'scale': "Unknown", 'discipline': "Unassigned", 
                            'type': 'sheet', 'parent': None, 'needs_crop': False
                        }
                st.success(f"{len(files)} Documents Integrated.")

        with tab2:
            st.header("TELEMETRY CHECK")
            project_files = st.session_state.projects[st.session_state.current_project]['files']
            sheet_list = [f for f, data in project_files.items() if data['type'] == 'sheet']
            if sheet_list:
                selected_file = st.selectbox("Select Drawing", sheet_list)
                current_data = project_files[selected_file]
                c_img, c_data = st.columns([2, 1])
                with c_img: st.image(current_data['image'], use_column_width=True)
                with c_data:
                    current_data['discipline'] = st.selectbox("Category", ["Unassigned", "Arch", "Struct", "Mech", "Elec"], key="disc")
                    current_data['scale'] = st.text_input("Scale", value=current_data['scale'])
                    st.divider()
                    detail_input = st.text_area("Generate Details (e.g. 7/A100)")
                    if st.button("GENERATE"):
                        if detail_input:
                            for ref in detail_input.split(','):
                                name = f"{selected_file} - {ref.strip()}"
                                project_files[name] = current_data.copy()
                                project_files[name]['type'] = 'detail'
                                project_files[name]['needs_crop'] = True
                            st.success("Details Generated.")
                            st.rerun()

        with tab3:
            st.header("LAUNCH ANALYSIS")
            all_assets = st.session_state.projects[st.session_state.current_project]['files']
            asset_list = list(all_assets.keys())
            if len(asset_list) < 2:
                st.warning("Upload more files to compare.")
            else:
                c1, c2 = st.columns(2)
                with c1:
                    base = st.selectbox("Base Layer", asset_list, key="base")
                    if all_assets[base].get('needs_crop'):
                        st.warning("Crop Required")
                        cropped = st_cropper(all_assets[base]['image'], realtime_update=True, key="c1", aspect_ratio=None)
                        if st.button("Confirm Base Crop"):
                            all_assets[base]['image'] = cropped
                            all_assets[base]['needs_crop'] = False
                            st.rerun()
                    else: st.image(all_assets[base]['image'], use_column_width=True)
                with c2:
                    over = st.selectbox("Overlay Layer", [a for a in asset_list if a != base], key="over")
                    if over:
                        if all_assets[over].get('needs_crop'):
                            st.warning("Crop Required")
                            cropped2 = st_cropper(all_assets[over]['image'], realtime_update=True, key="c2", aspect_ratio=None)
                            if st.button("Confirm Overlay Crop"):
                                all_assets[over]['image'] = cropped2
                                all_assets[over]['needs_crop'] = False
                                st.rerun()
                        else: st.image(all_assets[over]['image'], use_column_width=True)
                
                if over and not all_assets[base].get('needs_crop') and not all_assets[over].get('needs_crop'):
                    if st.button("INITIATE SEQUENCE", type="primary"):
                        with st.spinner("Processing..."):
                            res, data = detect_clashes_with_boxes(
                                all_assets[base]['image'], all_assets[base]['scale'], 
                                all_assets[base]['discipline'], all_assets[over]['discipline']
                            )
                            st.session_state.clash_data = data
                            st.image(res, caption="Results")
                    
                    if st.session_state.clash_data:
                        for i, clash in enumerate(st.session_state.clash_data):
                            col_a, col_b = st.columns([4,1])
                            col_a.write(f"**{i+1}:** {clash.get('description')}")
                            if col_b.button("False Alarm", key=f"f{i}"):
                                teach_ai(clash.get('description'), "safe")
                                st.toast("Memory Updated")