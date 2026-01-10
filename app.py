import streamlit as st
import os
from PIL import Image
from streamlit_cropper import st_cropper
from utils_vision import pdf_page_to_image, detect_clashes_with_boxes
from utils_database import init_db, save_project, get_projects, teach_ai

# --- 1. INITIALIZATION & CONFIG ---
st.set_page_config(layout="wide", page_title="TECTONICA | Future of Construction")
init_db()

# --- 2. GLOBAL STYLING (The "Rocket Lab" Theme + Video Support) ---
st.markdown("""
    <style>
    /* 1. RESET STREAMLIT DEFAULTS */
    .stApp {
        background-color: #0b0c10;
        color: white;
    }
    header {visibility: hidden;} /* Hide default Streamlit header */
    
    /* 2. NAVIGATION BAR STYLING */
    .nav-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 2rem;
        background-color: rgba(0, 0, 0, 0.8);
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        z-index: 999;
        border-bottom: 1px solid #333;
    }
    .nav-logo {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 800;
        font-size: 1.5rem;
        color: white;
        text-decoration: none;
        letter-spacing: 2px;
    }
    
    /* 3. VIDEO BACKGROUND */
    #myVideo {
        position: fixed;
        right: 0;
        bottom: 0;
        min-width: 100%; 
        min-height: 100%;
        z-index: -1;
        opacity: 0.4; /* Darkens video so text pops */
        filter: contrast(1.2) brightness(0.6);
    }
    
    /* 4. BUTTONS & UI ELEMENTS */
    .stButton>button {
        background-color: #e60012;
        color: white;
        border: none;
        border-radius: 4px;
        font-weight: bold;
        letter-spacing: 1px;
        transition: 0.3s;
        text-transform: uppercase;
    }
    .stButton>button:hover {
        background-color: #ff3344;
        box-shadow: 0 0 10px rgba(230, 0, 18, 0.5);
    }
    
    /* 5. TYPOGRAPHY */
    h1 { font-size: 3.5rem !important; font-weight: 800 !important; }
    h2 { font-size: 2rem !important; font-weight: 600 !important; color: #e60012 !important; }
    p { font-size: 1.1rem; line-height: 1.6; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SESSION STATE MANAGEMENT ---
if 'view' not in st.session_state: st.session_state.view = "LANDING" # LANDING or DASHBOARD
if 'projects' not in st.session_state: st.session_state.projects = {} 
if 'current_project' not in st.session_state: st.session_state.current_project = None
if 'step' not in st.session_state: st.session_state.step = "HOME"
if 'clash_data' not in st.session_state: st.session_state.clash_data = None

# --- 4. VIEW CONTROLLERS ---
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
    
    # A. INJECT VIDEO BACKGROUND (HTML)
    # Using a high-quality free stock video of construction/architecture
    video_url = "https://videos.pexels.com/video-files/3129957/3129957-uhd_2560_1440_25fps.mp4"
    st.markdown(f"""
    <video autoplay muted loop id="myVideo">
        <source src="{video_url}" type="video/mp4">
    </video>
    """, unsafe_allow_html=True)

    # B. CUSTOM NAVIGATION BAR (Using Columns for Buttons to mimic a Nav Bar)
    # We use empty columns to push buttons to the right
    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns([3, 1, 1, 1, 1])
    
    with nav_col1:
        st.markdown('<div class="nav-logo">TECTONICA</div>', unsafe_allow_html=True)
    with nav_col2:
        if st.button("WHY TECTONICA?", key="nav_why"):
            st.toast("AI-Driven Clash Detection at the speed of light.")
    with nav_col3:
        if st.button("SUPPORT", key="nav_help"):
            st.toast("Contact: support@tectonica.ai")
    with nav_col4:
        if st.button("MY PROJECTS", key="nav_proj"):
            go_to_dashboard()
            st.rerun()
    with nav_col5:
        if st.button("LOGIN / SIGN UP", type="primary", key="nav_login"):
            go_to_dashboard()
            st.rerun()

    # C. HERO SECTION (Centered Content)
    st.markdown("<br><br><br><br>", unsafe_allow_html=True) # Spacing
    
    hero_c1, hero_c2 = st.columns([2, 1])
    with hero_c1:
        st.markdown("# BUILD WITHOUT<br>BLIND SPOTS.", unsafe_allow_html=True)
        st.markdown("""
        The world's first **Autonomous Construction Coordinator**.
        <br>Upload drawings. Detect clashes. Break ground with confidence.
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("EXPLORE PLATFORM ➤", type="primary", use_container_width=False):
            go_to_dashboard()
            st.rerun()

    # D. FEATURE CARDS (Visuals)
    st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown("### ⚡ INSTANT ANALYSIS")
        st.caption("No more waiting for VDC meetings. Get answers in seconds.")
    with f2:
        st.markdown("### 👁️ COMPUTER VISION")
        st.caption("Our AI sees prints like a Superintendent, not just a keyword search.")
    with f3:
        st.markdown("### 🔗 PROCORE SYNC")
        st.caption("Seamlessly integrated with your existing document control.")


# =========================================================
# VIEW 2: THE DASHBOARD (The "Mission Control" App)
# =========================================================
elif st.session_state.view == "DASHBOARD":
    
    # Dashboard Header
    dash_c1, dash_c2 = st.columns([6, 1])
    with dash_c1:
        st.markdown("## MISSION CONTROL")
    with dash_c2:
        if st.button("LOGOUT"):
            go_to_landing()
            st.rerun()
            
    st.divider()

    # --- EXISTING LOGIC FROM V8.0 BELOW ---
    
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