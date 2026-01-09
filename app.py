import streamlit as st
import os
from PIL import Image
from streamlit_cropper import st_cropper
from utils_vision import pdf_page_to_image, detect_clashes_with_boxes
from utils_database import init_db, save_project, get_projects, teach_ai

# --- 1. INITIALIZATION ---
# This must be the first Streamlit command
st.set_page_config(layout="wide", page_title="TECTONICA | Mission Control")

# Initialize the Database
init_db()

# --- 2. CUSTOM CSS (Rocket Lab Theme) ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0c10; color: #c5c6c7; }
    h1, h2, h3 { color: #ffffff !important; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-weight: 700; letter-spacing: 1px; }
    .stButton>button { background-color: #e60012; color: white; border: none; border-radius: 0px; font-weight: bold; letter-spacing: 1px; transition: 0.3s; }
    .stButton>button:hover { background-color: #ff3344; border: 1px solid white; }
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stTextArea>div>div>textarea { background-color: #1f2833; color: white; border-radius: 0px; }
    section[data-testid="stSidebar"] { background-color: #000000; border-right: 1px solid #333; }
    .stSuccess { background-color: #1f2833; color: #00ff00; border-left: 5px solid #00ff00; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'projects' not in st.session_state: st.session_state.projects = {} 
if 'current_project' not in st.session_state: st.session_state.current_project = None
if 'step' not in st.session_state: st.session_state.step = "HOME"
if 'clash_data' not in st.session_state: st.session_state.clash_data = None

# --- 4. NAVIGATION FUNCTIONS ---
def go_home(): 
    st.session_state.step = "HOME"
    st.session_state.current_project = None

def create_project(name):
    if name:
        # Save to SQLite DB
        save_project(name)
        # Initialize in Session State if not present
        if name not in st.session_state.projects: 
            st.session_state.projects[name] = {'files': {}}
        st.session_state.current_project = name
        st.session_state.step = "UPLOAD"

# --- 5. PAGE ROUTING ---

# === PAGE: MISSION CONTROL (HOME) ===
if st.session_state.step == "HOME":
    c1, c2 = st.columns([1, 2])
    with c1:
        # Logo Check
        if os.path.exists("logo.png"): 
            st.image("logo.png", width=250) 
        else: 
            st.title("TECTONICA")

        st.markdown("### AUTONOMOUS CLASH DETECTION SYSTEM")
        st.markdown("---")
        
        st.write("#### SELECT MISSION")
        # Load projects from Database
        existing_projects = get_projects()
        
        if existing_projects:
            sel_proj = st.selectbox("Active Projects", existing_projects)
            if st.button("RESUME MISSION"): 
                create_project(sel_proj)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.write("#### INITIATE NEW MISSION")
        new_proj = st.text_input("Project Codename", placeholder="e.g. HUDSON YARDS TOWER A")
        if st.button("INITIALIZE PROJECT"): 
            create_project(new_proj)

    with c2:
         st.markdown("""<div style="background-color: #111; height: 600px; display: flex; align-items: center; justify-content: center; border: 1px solid #333;"><h3 style="color: #333;">SYSTEM STANDBY</h3></div>""", unsafe_allow_html=True)

# === PAGE: WORKFLOW (UPLOAD -> REVIEW -> ANALYZE) ===
elif st.session_state.step == "UPLOAD":
    st.sidebar.title(f"MISSION: {st.session_state.current_project}")
    if st.sidebar.button("<< RETURN TO BASE"): go_home()
    
    tab1, tab2, tab3 = st.tabs(["1. UPLOAD DOCUMENTS", "2. DATA REVIEW & TAGGING", "3. LAUNCH ANALYSIS"])
    
    # --- TAB 1: BULK UPLOAD ---
    with tab1:
        st.header("PAYLOAD INTEGRATION")
        files = st.file_uploader("Upload Project PDF Set", type=['pdf'], accept_multiple_files=True)
        if files:
            for f in files:
                # Ensure structure exists
                if f.name not in st.session_state.projects[st.session_state.current_project]['files']:
                    img = pdf_page_to_image(f)
                    st.session_state.projects[st.session_state.current_project]['files'][f.name] = {
                        'image': img, 'scale': "Unknown", 'discipline': "Unassigned", 
                        'type': 'sheet', 'parent': None, 'needs_crop': False
                    }
            st.success(f"{len(files)} Documents Integrated.")

    # --- TAB 2: REVIEW ---
    with tab2:
        st.header("TELEMETRY CHECK")
        project_files = st.session_state.projects[st.session_state.current_project]['files']
        sheet_list = [f for f, data in project_files.items() if data['type'] == 'sheet']
        
        if not sheet_list:
            st.info("No parent sheets uploaded.")
        else:
            selected_file = st.selectbox("Select Drawing Sheet to Review", sheet_list)
            col_img, col_data = st.columns([2, 1])
            current_data = project_files[selected_file]
            
            with col_img:
                st.image(current_data['image'], use_column_width=True, caption=f"Reviewing Sheet: {selected_file}")
                
            with col_data:
                st.markdown("### SHEET DATA")
                new_disc = st.selectbox("Drawing Category", ["Unassigned", "Architectural", "Structural", "Mechanical", "Electrical", "Plumbing"], index=["Unassigned", "Architectural", "Structural", "Mechanical", "Electrical", "Plumbing"].index(current_data['discipline']))
                project_files[selected_file]['discipline'] = new_disc
                new_scale = st.text_input("Confirmed Scale", value=current_data['scale'])
                project_files[selected_file]['scale'] = new_scale
                
                st.divider()
                st.markdown("### DETAIL REFERENCES")
                detail_input = st.text_area("Enter Detail Numbers (comma separated)", placeholder="e.g. 7/A100, 4/A100")
                
                if st.button("GENERATE DETAIL ASSETS"):
                    if detail_input:
                        refs = [ref.strip() for ref in detail_input.split(',') if ref.strip()]
                        count = 0
                        for ref in refs:
                            new_asset_name = f"{selected_file} - Detail {ref}"
                            project_files[new_asset_name] = {
                                'image': current_data['image'], 
                                'scale': new_scale,
                                'discipline': new_disc,
                                'type': 'detail',
                                'parent': selected_file,
                                'needs_crop': True 
                            }
                            count += 1
                        st.success(f"Generated {count} details. Please crop them in the Analysis tab.")
                        st.rerun()

    # --- TAB 3: ANALYSIS ---
    with tab3:
        st.header("LAUNCH CLASH DETECTION")
        all_assets = st.session_state.projects[st.session_state.current_project]['files']
        asset_list = list(all_assets.keys())
        
        if len(asset_list) < 2:
             st.warning("⚠️ Insufficient Data. Please upload at least 2 distinct sheets or details.")
        else:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("BASE LAYER")
                base_name = st.selectbox("Select Base Asset", asset_list, key="base")
                # Check Crop
                if all_assets[base_name].get('needs_crop'):
                    st.warning(f"⚠️ Full Sheet. Crop to detail.")
                    cropped_img = st_cropper(all_assets[base_name]['image'], realtime_update=True, key=f"crop_{base_name}", aspect_ratio=None)
                    if st.button(f"Confirm Crop {base_name}"):
                         all_assets[base_name]['image'] = cropped_img
                         all_assets[base_name]['needs_crop'] = False
                         st.rerun()
                else:
                    st.image(all_assets[base_name]['image'], use_column_width=True)

            with c2:
                st.subheader("OVERLAY LAYER")
                overlay_options = [a for a in asset_list if a != base_name]
                if not overlay_options:
                    st.error("No other assets available.")
                else:
                    overlay_name = st.selectbox("Select Overlay Asset", overlay_options, key="overlay")
                    if overlay_name:
                        if all_assets[overlay_name].get('needs_crop'):
                            st.warning(f"⚠️ Full Sheet. Crop to detail.")
                            cropped_overlay = st_cropper(all_assets[overlay_name]['image'], realtime_update=True, key=f"crop_{overlay_name}", aspect_ratio=None)
                            if st.button(f"Confirm Crop {overlay_name}"):
                                all_assets[overlay_name]['image'] = cropped_overlay
                                all_assets[overlay_name]['needs_crop'] = False
                                st.rerun()
                        else:
                             st.image(all_assets[overlay_name]['image'], use_column_width=True)

            # --- ANALYSIS BUTTON & FEEDBACK LOOP ---
            if overlay_options and not all_assets[base_name].get('needs_crop') and not all_assets[overlay_name].get('needs_crop'):
                st.divider()
                if st.button("INITIATE SEQUENCE", type="primary"):
                    with st.spinner("Analyzing Geometry & Context..."):
                        # Get Data
                        img_crop = all_assets[base_name]['image'] # Logic simplificaton: Analyzing Base for MVP
                        scale = all_assets[base_name]['scale']
                        trade_a = all_assets[base_name]['discipline']
                        trade_b = all_assets[overlay_name]['discipline']
                        
                        # Run Vision AI (Database Aware)
                        # Note: We pass the 'base' image here, but in real logic we'd pass the overlay composite.
                        # For this MVP v8.0 fix, we keep it simple to ensure it runs.
                        res_img, data = detect_clashes_with_boxes(img_crop, scale, trade_a, trade_b)
                        st.session_state.clash_data = data
                        st.image(res_img, caption="AI Detection Result")
                
                # FEEDBACK LOOP UI
                if st.session_state.clash_data:
                    st.divider()
                    st.markdown("### AI TRAINING FEEDBACK")
                    st.info("Teach the system to improve future accuracy.")
                    
                    for i, clash in enumerate(st.session_state.clash_data):
                        fc1, fc2, fc3 = st.columns([3, 1, 1])
                        with fc1:
                            st.write(f"**Issue {i+1}:** {clash.get('description', 'Issue')}")
                        with fc2:
                            if st.button("✅ Confirm", key=f"conf_{i}"):
                                teach_ai(clash.get('description'), "clash")
                                st.toast("Logic Confirmed.")
                        with fc3:
                            if st.button("❌ False Alarm", key=f"false_{i}"):
                                teach_ai(clash.get('description'), "safe")
                                st.toast("AI Updated: Will ignore similar issues.")