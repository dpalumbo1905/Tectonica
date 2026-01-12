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
st.set_page_config(layout="wide", page_title="TECTONICA | Advanced Construction Intelligence")
init_db()

# Create Local Storage Directory
STORAGE_DIR = "project_storage"
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

# --- 2. AUTHENTICATION ENGINE ---
def check_auth():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    return st.session_state.authenticated

def login(username, password):
    if username == "admin" and password == "tectonica":
        st.session_state.authenticated = True
        return True
    return False

def logout():
    st.session_state.authenticated = False
    st.session_state.view = "LANDING"

# --- 3. REPORTING ENGINE ---
class ReportPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'TECTONICA | CLASH DETECTION REPORT', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf_report(project_name, clash_data):
    pdf = ReportPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Project: {project_name}", ln=1, align='L')
    pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=1, align='L')
    pdf.cell(200, 10, txt=f"Total Clashes Detected: {len(clash_data)}", ln=1, align='L')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="CRITICAL INTERFERENCES:", ln=1, align='L')
    pdf.set_font("Arial", size=10)
    for i, clash in enumerate(clash_data):
        desc = clash.get('description', 'Unknown Issue')
        pdf.multi_cell(0, 10, txt=f"#{i+1}: {desc}")
        pdf.ln(2)
    file_name = f"clash_report_{int(time.time())}.pdf"
    pdf.output(file_name)
    return file_name

# --- 4. ASSET LOADER ---
def get_img_as_base64(file_path):
    if not os.path.exists(file_path): return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    with open(file_path, "rb") as f: data = f.read()
    return f"data:image/{file_path.split('.')[-1]};base64,{base64.b64encode(data).decode()}"

# --- 5. SESSION STATE ---
if 'view' not in st.session_state: st.session_state.view = "LANDING"
if 'projects' not in st.session_state: 
    # PRE-SEEDING DEMO PROJECTS
    st.session_state.projects = {
        "NAPLES AIRPORT AOB (COMMERCIAL)": {'files': {}},
        "SANIBEL FIRE STATION (INSTITUTIONAL)": {'files': {}},
        "TOWNE PLACE SUITES (HOSPITALITY)": {'files': {}}
    }
    for p in st.session_state.projects.keys(): save_project(p)

if 'current_project' not in st.session_state: st.session_state.current_project = None
if 'step' not in st.session_state: st.session_state.step = "HOME"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'show_vision_demo' not in st.session_state: st.session_state.show_vision_demo = False

# --- 6. NAVIGATION CONTROLLER ---
def nav_to(page): st.session_state.view = page

# --- 7. COMPONENT: NAVBAR ---
def render_navbar():
    st.markdown("""
    <style>
    .nav-container { display: flex; justify-content: space-between; align-items: center; padding: 1rem 2rem; background: #262626; border-bottom: 1px solid #444; margin-bottom: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    div.stButton > button { background: transparent; border: none; color: #ffffff !important; font-family: 'Barlow', sans-serif; font-size: 0.95rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin: 0; padding: 0.5rem 1rem; transition: 0.3s; }
    div.stButton > button:hover { color: #e60012 !important; background: rgba(255,255,255,0.05); }
    [data-testid="column"]:last-child div.stButton > button { border: 1px solid #e60012 !important; border-radius: 4px; color: #e60012 !important; }
    [data-testid="column"]:last-child div.stButton > button:hover { background: #e60012 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)
    c1, c2, c3, c4, c5, c6, c7 = st.columns([2, 1, 1, 1, 1, 1, 1])
    with c1: 
        if st.button("TECTONICA", key="home_btn"): nav_to("LANDING"); st.rerun()
    with c2: st.button("OUR STORY", on_click=lambda: nav_to("STORY"))
    with c3: st.button("CASE STUDIES", on_click=lambda: nav_to("REVIEWS"))
    with c4: st.button("CAREERS", on_click=lambda: nav_to("CAREERS"))
    with c5: st.button("SUPPORT", on_click=lambda: nav_to("SUPPORT"))
    with c6: st.button("MY PROJECTS", on_click=lambda: nav_to("DASHBOARD"))
    with c7: 
        if check_auth(): st.button("LOGOUT", on_click=logout)
        else: st.button("LOGIN", on_click=lambda: nav_to("LOGIN"))

# =========================================================
# GLOBAL STYLES
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@300;400;600;800&display=swap');
.stApp { background-color: #0b0c10; font-family: 'Barlow', sans-serif; color: #e0e0e0; }
h1, h2, h3 { font-family: 'Barlow', sans-serif; text-transform: uppercase; color: white; }
.footer { margin-top: 5rem; padding: 2rem; border-top: 1px solid #333; text-align: center; color: #555; font-size: 0.8rem; }
.css-1r6slb0 { border: 1px solid #333; border-radius: 10px; padding: 20px; background: #111; transition: 0.3s; }
.css-1r6slb0:hover { border-color: #e60012; transform: translateY(-5px); }
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
    [data-testid="stAppViewContainer"] > .main {{ background: transparent; }}
    #myVideo {{ position: fixed; right: 0; bottom: 0; min-width: 100%; min-height: 100%; z-index: -99; opacity: 0.5; filter: grayscale(100%) contrast(1.2); object-fit: cover; }}
    .overlay {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(180deg, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0.4) 50%, rgba(0,0,0,1) 100%); z-index: -98; pointer-events: none; }}
    </style>
    <video autoplay muted loop playsinline id="myVideo"><source src="{video_url}" type="video/mp4"></video><div class="overlay"></div>
    """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("""<h1 style='font-size: 5rem; line-height: 0.9;'>BUILD WITHOUT<br><span style='color:#e60012'>BLIND SPOTS.</span></h1><p style='font-size: 1.5rem; color: #ccc; margin-top: 1rem;'>The Future of Construction Technology.</p>""", unsafe_allow_html=True)
        st.button("ENTER PLATFORM ➤", type="primary", on_click=lambda: nav_to("LOGIN"))
        
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown('<div style="background: #0b0c10; padding: 3rem; border-radius: 12px; border: 1px solid #222;">', unsafe_allow_html=True)
    st.markdown("### CORE CAPABILITIES")
    st.markdown("---")
    
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        st.image("card_3d.jpg" if os.path.exists("card_3d.jpg") else "https://images.pexels.com/photos/834892/pexels-photo-834892.jpeg", use_column_width=True)
        st.markdown("#### INSTANT CLASH")
        st.caption("Identify spatial conflicts between MEP systems and Structural elements instantly.")
    
    with fc2:
        if st.session_state.show_vision_demo:
            st.video("https://videos.pexels.com/video-files/8524225/8524225-hd_1920_1080_30fps.mp4", autoplay=True, muted=True)
            if st.button("❌ Close Demo"): st.session_state.show_vision_demo = False; st.rerun()
        else:
            st.image("https://images.pexels.com/photos/2760241/pexels-photo-2760241.jpeg", use_column_width=True)
            st.markdown("#### COMPUTER VISION AI")
            st.caption("Our engine reads 2D PDF sets with the context of a Lead Superintendent.")
            if st.button("▶ WATCH DEMO"): st.session_state.show_vision_demo = True; st.rerun()

    with fc3:
        st.image("card_procore.png" if os.path.exists("card_procore.png") else "https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Procore_Logo.svg/512px-Procore_Logo.svg.png", use_column_width=True)
        st.markdown("#### PROCORE SYNC")
        st.caption("Seamlessly push RFIs and Observations directly to your existing Project Management suite.")
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# VIEW: LOGIN
# =========================================================
elif st.session_state.view == "LOGIN":
    render_navbar()
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown("### SECURE LOGIN")
        with st.form("login_form"):
            user = st.text_input("Username")
            pw = st.text_input("Password", type="password")
            submitted = st.form_submit_button("LOG IN")
            if submitted:
                if login(user, pw):
                    st.success("Access Granted.")
                    time.sleep(0.5)
                    nav_to("DASHBOARD")
                    st.rerun()
                else: st.error("Access Denied.")
        st.caption("Demo Access: admin / tectonica")

# =========================================================
# VIEW: DASHBOARD
# =========================================================
elif st.session_state.view == "DASHBOARD":
    render_navbar()
    if not check_auth():
        st.warning("⚠️ PLEASE LOG IN TO ACCESS PROJECT DATA")
        st.button("GO TO LOGIN", on_click=lambda: nav_to("LOGIN"))
    else:
        dash_c1, dash_c2 = st.columns([6, 1])
        with dash_c1: st.title("PROJECT DASHBOARD")
        st.divider()

        if st.session_state.step == "HOME":
            c1, c2 = st.columns([1, 2])
            with c1:
                st.write("#### ACTIVE PROJECTS")
                existing = list(st.session_state.projects.keys())
                if existing:
                    sel = st.selectbox("Select Project", existing, index=0)
                    if st.button("OPEN PROJECT"): 
                        if sel:
                            st.session_state.current_project = sel
                            st.session_state.step = "UPLOAD"
                            st.rerun()
                st.write("#### START NEW PROJECT")
                new_p = st.text_input("Project Name")
                if st.button("CREATE"): 
                    save_project(new_p)
                    st.session_state.projects[new_p] = {'files': {}}
                    st.session_state.current_project = new_p
                    st.session_state.step = "UPLOAD"
                    st.rerun()
            with c2: 
                st.info("Dashboard Ready.")
                st.markdown("---")
                st.markdown("#### 📥 DEMO RESOURCES")
                
                # LINK 1: NAPLES AOB
                st.markdown("**1. NAPLES AIRPORT AOB**")
                st.caption("Complex Mechanical vs. Structural")
                st.link_button("⬇ Download Naples Plans (PDF)", "https://www.flynaples.com/wp-content/uploads/2022-02-28-NAPLES-AOB-CONSTRUCTION-DRAWINGS.pdf")
                
                st.divider()
                
                # LINK 2: SANIBEL FIRE STATION
                st.markdown("**2. SANIBEL FIRE STATION**")
                st.caption("Institutional / Public Safety")
                st.link_button("⬇ Download Sanibel Plans (PDF)", "https://www.sanibelfire.com/files/d6cc0d1ed/SFRD+%23172_BID+SET+-+Architectural+Set_2024.01.05.pdf")
                
                st.divider()
                
                # LINK 3: TOWNE PLACE SUITES
                st.markdown("**3. TOWNE PLACE SUITES**")
                st.caption("Hospitality / Multi-Unit")
                st.link_button("⬇ Download Hotel Plans (PDF)", "https://chicoca.gov/documents/Departments/Community-Development/Planning-Division/Current-Projects/att_q_towne_place_suites_architectural_drawing_mwt_june_10_2021.pdf")

        elif st.session_state.step == "UPLOAD":
            st.sidebar.title(f"PROJECT: {st.session_state.current_project}")
            if st.sidebar.button("<< BACK TO DASHBOARD"): 
                st.session_state.step = "HOME"
                st.rerun()
            
            tab1, tab2, tab3 = st.tabs(["1. UPLOAD PLANS", "2. REVIEW DATA", "3. ANALYZE"])
            
            with tab1:
                st.info(f"Uploading to: {st.session_state.current_project}")
                files = st.file_uploader("Upload PDF Sets", type=['pdf'], accept_multiple_files=True)
                if files:
                    for f in files:
                        if st.session_state.current_project:
                            proj_path = os.path.join(STORAGE_DIR, st.session_state.current_project)
                            if not os.path.exists(proj_path): os.makedirs(proj_path)
                            file_path = os.path.join(proj_path, f.name)
                            with open(file_path, "wb") as buffer: buffer.write(f.getbuffer())
                            if f.name not in st.session_state.projects[st.session_state.current_project]['files']:
                                st.session_state.projects[st.session_state.current_project]['files'][f.name] = {
                                    'image': pdf_page_to_image(f), 
                                    'scale': "Unknown", 'discipline': "Unassigned", 'type': 'sheet', 'parent': None, 'needs_crop': False
                                }
                    st.success("Documents successfully uploaded.")

            with tab2:
                p_files = st.session_state.projects[st.session_state.current_project]['files']
                s_list = [f for f, d in p_files.items() if d['type'] == 'sheet']
                if s_list:
                    sel_f = st.selectbox("Select Drawing", s_list)
                    curr = p_files[sel_f]
                    c_i, c_d = st.columns([2, 1])
                    with c_i: st.image(curr['image'], use_column_width=True)
                    with c_d:
                        curr['discipline'] = st.selectbox("Discipline", ["Unassigned", "Arch", "Struct", "Mech", "Elec"], key="disc")
                        if st.button("CONFIRM METADATA"): st.success("Data Saved.")
                else: st.info("No drawings uploaded yet.")

            with tab3:
                assets = st.session_state.projects[st.session_state.current_project]['files']
                a_list = list(assets.keys())
                if len(a_list) < 2: st.warning("Please upload at least 2 drawing sheets.")
                else:
                    c1, c2 = st.columns(2)
                    with c1: 
                        b = st.selectbox("Base Layer", a_list, key="base")
                        st.image(assets[b]['image'], use_column_width=True)
                    with c2: 
                        o = st.selectbox("Overlay Layer", [a for a in a_list if a != b], key="over") 
                        if o: st.image(assets[o]['image'], use_column_width=True)
                    if o and st.button("RUN CLASH DETECTION", type="primary"):
                        with st.spinner("Analyzing geometry overlaps..."):
                            res, data = detect_clashes_with_boxes(assets[b]['image'], "1:100", assets[b]['discipline'], assets[o]['discipline'])
                            st.session_state.clash_data = data
                            st.image(res, caption="Clash Detection Results")
                    if st.session_state.clash_data:
                        st.divider()
                        if st.button("📄 DOWNLOAD PDF REPORT"):
                            pdf_file = generate_pdf_report(st.session_state.current_project, st.session_state.clash_data)
                            with open(pdf_file, "rb") as f: st.download_button("DOWNLOAD PDF", f, file_name=pdf_file)

# =========================================================
# OTHER VIEWS
# =========================================================
elif st.session_state.view == "STORY":
    render_navbar()
    st.markdown("""<div style="max-width:800px; margin:0 auto; padding: 2rem;"><h1 style="text-align:center; border-bottom: 2px solid #e60012; padding-bottom: 1rem;">OUR ORIGIN</h1><br><p style="font-size: 1.2rem; line-height: 1.8;">Construction is the only industry where "Clashes" are accepted as a standard line item. We build billion-dollar structures using static 2D PDFs that haven't evolved since the 1980s.</p><p style="font-size: 1.2rem; line-height: 1.8;"><b>TECTONICA was founded by Builders.</b> Born from the frustration of Project Managers who saw millions of dollars wasted on rework.</p></div>""", unsafe_allow_html=True)

elif st.session_state.view == "REVIEWS":
    render_navbar()
    st.title("CASE STUDIES")
    st.info("Client success stories coming soon.")

elif st.session_state.view == "CAREERS":
    render_navbar()
    st.title("CAREERS")
    st.write("We are always looking for talent at the intersection of Construction and Technology.")
    with st.expander("Senior Full Stack Engineer"): st.write("San Francisco / Remote."); st.button("Apply Now")

elif st.session_state.view == "SUPPORT":
    render_navbar()
    st.title("SUPPORT CENTER")
    st.write("Email us at: support@tectonica.ai")

# FOOTER
st.markdown('<div class="footer">TECTONICA CONSTRUCTION TECHNOLOGIES INC.<br>New York • San Francisco • Austin</div>', unsafe_allow_html=True)
