import streamlit as st
import os
import base64
import time
import shutil
from datetime import datetime
from fpdf import FPDF
from utils_database import init_db, save_project, get_projects, teach_ai
from utils_vision import pdf_page_to_image, detect_clashes_with_boxes
from streamlit_cropper import st_cropper

# --- 1. CONFIGURATION & SETUP ---
st.set_page_config(layout="wide", page_title="TECTONICA | Orbital Construction")
init_db()

# Create Local Storage Directory (Step 4: Persistence)
STORAGE_DIR = "project_storage"
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

# --- 2. AUTHENTICATION ENGINE (Step 1: Security) ---
def check_auth():
    """Simple Gatekeeper System"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    return st.session_state.authenticated

def login(username, password):
    # In a real app, this would check a secure database hash
    if username == "admin" and password == "tectonica":
        st.session_state.authenticated = True
        return True
    return False

def logout():
    st.session_state.authenticated = False
    st.session_state.view = "LANDING"

# --- 3. REPORTING ENGINE (Step 2: PDF Export) ---
class ReportPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'TECTONICA | MISSION CLASH REPORT', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf_report(project_name, clash_data):
    pdf = ReportPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Meta Data
    pdf.cell(200, 10, txt=f"Project: {project_name}", ln=1, align='L')
    pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=1, align='L')
    pdf.cell(200, 10, txt=f"Total Anomalies Detected: {len(clash_data)}", ln=1, align='L')
    pdf.ln(10)
    
    # Clash Details
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="CRITICAL INTERFERENCES:", ln=1, align='L')
    pdf.set_font("Arial", size=10)
    
    for i, clash in enumerate(clash_data):
        desc = clash.get('description', 'Unknown Issue')
        pdf.multi_cell(0, 10, txt=f"#{i+1}: {desc}")
        pdf.ln(2)
        
    # Save to temp path
    file_name = f"report_{int(time.time())}.pdf"
    pdf.output(file_name)
    return file_name

# --- 4. ASSET LOADER ---
def get_img_as_base64(file_path):
    if not os.path.exists(file_path): return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    with open(file_path, "rb") as f: data = f.read()
    return f"data:image/{file_path.split('.')[-1]};base64,{base64.b64encode(data).decode()}"

# --- 5. SESSION STATE ---
if 'view' not in st.session_state: st.session_state.view = "LANDING"
if 'projects' not in st.session_state: st.session_state.projects = {} 
if 'current_project' not in st.session_state: st.session_state.current_project = None
if 'step' not in st.session_state: st.session_state.step = "HOME"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []

# --- 6. NAVIGATION CONTROLLER ---
def nav_to(page): st.session_state.view = page

# --- 7. COMPONENT: NAVBAR ---
def render_navbar():
    st.markdown("""
    <style>
    .nav-container { display: flex; justify-content: space-between; align-items: center; padding: 1rem 2rem; background: rgba(0,0,0,0.8); border-bottom: 1px solid #333; margin-bottom: 2rem; }
    .logo-btn button { background: transparent !important; border: none !important; padding: 0 !important; }
    div.stButton > button { background: transparent; border: none; color: #ccc; font-family: 'Barlow', sans-serif; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; margin: 0; padding: 0.5rem 1rem; transition: 0.3s; }
    div.stButton > button:hover { color: white; text-shadow: 0 0 10px rgba(255,255,255,0.5); }
    .login-btn > button { border: 1px solid #e60012 !important; color: #e60012 !important; border-radius: 4px; }
    .login-btn > button:hover { background: #e60012 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4, c5, c6, c7 = st.columns([2, 1, 1, 1, 1, 1, 1])
    with c1: 
        if st.button("TECTONICA", key="home_btn"): nav_to("LANDING"); st.rerun()
    with c2: st.button("STORY", on_click=lambda: nav_to("STORY"))
    with c3: st.button("EXPERIENCES", on_click=lambda: nav_to("REVIEWS"))
    with c4: st.button("CAREERS", on_click=lambda: nav_to("CAREERS"))
    with c5: st.button("SUPPORT", on_click=lambda: nav_to("SUPPORT"))
    with c6: st.button("MY PROJECTS", on_click=lambda: nav_to("DASHBOARD"))
    with c7: 
        st.markdown('<div class="login-btn">', unsafe_allow_html=True)
        # Dynamic Button: Show "LOGOUT" if logged in, else "ACCESS"
        if check_auth():
            st.button("LOGOUT", on_click=logout)
        else:
            st.button("ACCESS / LOGIN", on_click=lambda: nav_to("LOGIN"))
        st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# GLOBAL STYLES
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@300;400;600;800&display=swap');
.stApp { background-color: #0b0c10; font-family: 'Barlow', sans-serif; color: #e0e0e0; }
h1, h2, h3 { font-family: 'Barlow', sans-serif; text-transform: uppercase; color: white; }
.footer { margin-top: 5rem; padding: 2rem; border-top: 1px solid #333; text-align: center; color: #555; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)


# =========================================================
# VIEW: LANDING PAGE
# =========================================================
if st.session_state.view == "LANDING":
    render_navbar()
    video_url = "https://videos.pexels.com/video-files/3129957/3129957-uhd_2560_1440_25fps.mp4"
    st.markdown(f"""
    <style>
    #myVideo {{ position: fixed; right: 0; bottom: 0; min-width: 100%; min-height: 100%; z-index: -1; opacity: 0.5; filter: grayscale(100%) contrast(1.2); }}
    .overlay {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(180deg, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0.4) 50%, rgba(0,0,0,1) 100%); z-index: 0; pointer-events: none; }}
    </style>
    <video autoplay muted loop playsinline id="myVideo"><source src="{video_url}" type="video/mp4"></video><div class="overlay"></div>
    """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("""<h1 style='font-size: 5rem; line-height: 0.9;'>BUILD WITHOUT<br><span style='color:#e60012'>BLIND SPOTS.</span></h1><p style='font-size: 1.5rem; color: #ccc; margin-top: 1rem;'>The Autonomous Construction Coordinator.</p>""", unsafe_allow_html=True)
        st.button("INITIATE SEQUENCE ➤", type="primary", on_click=lambda: nav_to("LOGIN"))


# =========================================================
# VIEW: AUTHENTICATION (LOGIN)
# =========================================================
elif st.session_state.view == "LOGIN":
    render_navbar()
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown("### SYSTEM ACCESS")
        with st.form("login_form"):
            user = st.text_input("Operator ID")
            pw = st.text_input("Access Key", type="password")
            submitted = st.form_submit_button("AUTHENTICATE")
            
            if submitted:
                if login(user, pw):
                    st.success("Identity Verified.")
                    time.sleep(0.5)
                    nav_to("DASHBOARD")
                    st.rerun()
                else:
                    st.error("Access Denied. Invalid Credentials.")
        st.caption("Hint: admin / tectonica")

# =========================================================
# VIEW: DASHBOARD (SECURE AREA)
# =========================================================
elif st.session_state.view == "DASHBOARD":
    render_navbar()
    
    # SECURITY CHECK
    if not check_auth():
        st.warning("⚠️ UNAUTHORIZED ACCESS DETECTED")
        st.info("Redirecting to Login...")
        time.sleep(2)
        nav_to("LOGIN")
        st.rerun()
    else:
        # Dashboard Header
        dash_c1, dash_c2 = st.columns([6, 1])
        with dash_c1: st.title("MISSION CONTROL")
        st.divider()

        # Core App Logic 
        if st.session_state.step == "HOME":
            c1, c2 = st.columns([1, 2])
            with c1:
                st.write("#### ACTIVE OPERATIONS")
                existing = list(st.session_state.projects.keys())
                if existing:
                    sel = st.selectbox("Select Mission", existing)
                    if st.button("RESUME"): 
                        if sel:
                            st.session_state.current_project = sel
                            st.session_state.step = "UPLOAD"
                            st.rerun()
                st.write("#### NEW OPERATION")
                new_p = st.text_input("Codename")
                if st.button("INITIALIZE"): 
                    save_project(new_p)
                    # Create Project Folder (Persistence)
                    proj_path = os.path.join(STORAGE_DIR, new_p)
                    if not os.path.exists(proj_path): os.makedirs(proj_path)
                    
                    st.session_state.projects[new_p] = {'files': {}}
                    st.session_state.current_project = new_p
                    st.session_state.step = "UPLOAD"
                    st.rerun()
            with c2: 
                st.info("System Ready. Select a mission.")

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
                        if st.session_state.current_project:
                            # SAVE FILE LOCALLY (PERSISTENCE)
                            proj_path = os.path.join(STORAGE_DIR, st.session_state.current_project)
                            file_path = os.path.join(proj_path, f.name)
                            
                            with open(file_path, "wb") as buffer:
                                buffer.write(f.getbuffer())
                            
                            # Load into session
                            if f.name not in st.session_state.projects[st.session_state.current_project]['files']:
                                st.session_state.projects[st.session_state.current_project]['files'][f.name] = {
                                    'image': pdf_page_to_image(f), 
                                    'scale': "Unknown", 'discipline': "Unassigned", 'type': 'sheet', 'parent': None, 'needs_crop': False
                                }
                    st.success("Payload Integrated & Persisted to Secure Storage.")

            with tab2:
                p_files = st.session_state.projects[st.session_state.current_project]['files']
                s_list = [f for f, d in p_files.items() if d['type'] == 'sheet']
                if s_list:
                    sel_f = st.selectbox("Select Asset", s_list)
                    curr = p_files[sel_f]
                    c_i, c_d = st.columns([2, 1])
                    with c_i: st.image(curr['image'], use_column_width=True)
                    with c_d:
                        curr['discipline'] = st.selectbox("System", ["Unassigned", "Arch", "Struct", "Mech", "Elec"], key="disc")
                        if st.button("GENERATE SUB-ASSETS"): st.success("Sub-systems isolated.")
                else:
                    st.info("Awaiting schematic upload for telemetry analysis.")

            with tab3:
                assets = st.session_state.projects[st.session_state.current_project]['files']
                a_list = list(assets.keys())
                if len(a_list) < 2: st.warning("Insufficient Payload. Upload at least 2 schematics.")
                else:
                    c1, c2 = st.columns(2)
                    with c1: 
                        b = st.selectbox("Primary Stage", a_list, key="base")
                        st.image(assets[b]['image'], use_column_width=True)
                    with c2: 
                        o = st.selectbox("Secondary Stage", [a for a in a_list if a != b], key="over") 
                        if o: st.image(assets[o]['image'], use_column_width=True)
                    
                    if o and st.button("INITIATE SEQUENCE", type="primary"):
                        with st.spinner("Calculating Trajectory..."):
                            res, data = detect_clashes_with_boxes(assets[b]['image'], "1:100", assets[b]['discipline'], assets[o]['discipline'])
                            st.session_state.clash_data = data
                            st.image(res, caption="Impact Detected")
                    
                    # PDF EXPORT (Step 2)
                    if st.session_state.clash_data:
                        st.divider()
                        st.markdown("### MISSION REPORT")
                        if st.button("📄 GENERATE PDF DOSSIER"):
                            pdf_file = generate_pdf_report(st.session_state.current_project, st.session_state.clash_data)
                            with open(pdf_file, "rb") as f:
                                st.download_button("DOWNLOAD ENCRYPTED REPORT", f, file_name=pdf_file)

# =========================================================
# OTHER VIEWS (Content Pages)
# =========================================================
elif st.session_state.view == "STORY":
    render_navbar()
    st.markdown("""<div style="max-width:800px; margin:0 auto;"><h1 style="text-align:center;">MISSION CRITICAL</h1><p>We are the operating system for the built world.</p></div>""", unsafe_allow_html=True)

elif st.session_state.view == "REVIEWS":
    render_navbar()
    st.title("FIELD INTELLIGENCE")
    st.markdown("### OPERATOR REPORTS")
    st.info("No public reports declassified at this time.")

elif st.session_state.view == "CAREERS":
    render_navbar()
    st.title("JOIN THE CREW")
    st.write("No active sorties.")

elif st.session_state.view == "SUPPORT":
    render_navbar()
    st.title("SYSTEM SUPPORT")
    st.write("Contact Command: support@tectonica.ai")

# FOOTER
st.markdown('<div class="footer">TECTONICA AEROSPACE & CONSTRUCTION INDUSTRIES<br>USA • NZ • LEO</div>', unsafe_allow_html=True)
