import streamlit as st
import os
import base64
import time
from datetime import datetime
from fpdf import FPDF
from utils_database import init_db, save_project
from utils_vision import pdf_page_to_image, detect_clashes_with_boxes

# --- 1. CONFIGURATION ---
st.set_page_config(layout="wide", page_title="TECTONICA | Construction Intelligence")
init_db()

STORAGE_DIR = "project_storage"
if not os.path.exists(STORAGE_DIR): os.makedirs(STORAGE_DIR)

# --- 2. AUTHENTICATION & STATE MANAGEMENT ---
def check_auth():
    if 'authenticated' not in st.session_state: st.session_state.authenticated = False
    return st.session_state.authenticated

def login(username, password):
    # Simulated Credential Check
    if username.lower() == "admin" and password == "tectonica":
        st.session_state.authenticated = True
        st.session_state.user_name = "Demo User"
        st.session_state.user_role = "Senior VDC Manager"
        return True
    return False

def logout():
    st.session_state.authenticated = False
    st.session_state.view = "LANDING"
    st.session_state.current_project = None

# --- 3. PROJECT SEEDING (THE "INVITE" SYSTEM) ---
def seed_projects():
    # We simulate projects that were "sent via email invite"
    return {
        "NAPLES AIRPORT AOB": {
            "status": "INVITE PENDING", 
            "role": "Lead Reviewer",
            "inviter": "P. Manager (Turner)",
            "date": "Feb 28, 2022",
            "img": "https://images.pexels.com/photos/157811/pexels-photo-157811.jpeg",
            "files": {} 
        },
        "SANIBEL FIRE STATION": {
            "status": "ACTIVE", 
            "role": "Viewer",
            "inviter": "City of Sanibel",
            "date": "Jan 05, 2024",
            "img": "https://images.pexels.com/photos/950253/pexels-photo-950253.jpeg",
            "files": {}
        },
        "TOWNE PLACE SUITES": {
            "status": "ARCHIVED", 
            "role": "Admin",
            "inviter": "Marriott Dev",
            "date": "June 10, 2021",
            "img": "https://images.pexels.com/photos/271624/pexels-photo-271624.jpeg",
            "files": {}
        }
    }

# --- 4. REPORTING UTILS ---
class ReportPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'TECTONICA | PROJECT REPORT', 0, 1, 'C'); self.ln(5)
    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8); self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf(proj_name, data):
    pdf = ReportPDF(); pdf.add_page(); pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Project: {proj_name}", ln=1)
    pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d')}", ln=1)
    pdf.ln(10); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, "CLASH LOG:", ln=1)
    pdf.set_font("Arial", size=10)
    for i, c in enumerate(data): pdf.multi_cell(0, 10, f"#{i+1}: {c['description']}"); pdf.ln(2)
    fname = f"report_{int(time.time())}.pdf"; pdf.output(fname); return fname

# --- 5. SESSION INIT ---
if 'view' not in st.session_state: st.session_state.view = "LANDING"
if 'projects' not in st.session_state: st.session_state.projects = seed_projects()
if 'current_project' not in st.session_state: st.session_state.current_project = None
if 'step' not in st.session_state: st.session_state.step = "HOME"
if 'clash_data' not in st.session_state: st.session_state.clash_data = []

# --- 6. ASSET HELPERS ---
def get_b64_img(path):
    if os.path.exists(path):
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    return ""

# --- 7. NAVIGATION BAR ---
def nav_to(page): st.session_state.view = page

def render_navbar():
    st.markdown("""
    <style>
    .nav-bar {
        display: flex; justify-content: space-between; align-items: center;
        background: #1a1a1a; padding: 15px 30px; border-bottom: 2px solid #333;
        margin-bottom: 30px;
    }
    .nav-logo { font-family: 'Barlow', sans-serif; font-weight: 800; font-size: 1.5rem; color: white; cursor: pointer; }
    .nav-links { display: flex; gap: 20px; }
    .nav-btn {
        background: none; border: none; color: #ccc; font-family: 'Barlow', sans-serif;
        font-size: 0.9rem; font-weight: 600; cursor: pointer; text-transform: uppercase;
    }
    .nav-btn:hover { color: #e60012; }
    .nav-btn.active { color: white; border-bottom: 2px solid #e60012; }
    </style>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([2, 5, 2])
    
    with c1:
        if st.button("TECTONICA", key="nav_logo"): nav_to("LANDING"); st.rerun()
    
    with c2:
        # If logged in, show "App" links. If not, show "Marketing" links.
        if check_auth():
            col_a, col_b, col_c = st.columns(3)
            with col_a: st.button("MY PROJECTS", on_click=lambda: nav_to("DASHBOARD"))
            with col_b: st.button("COMPANY DIRECTORY", on_click=lambda: nav_to("DIRECTORY"))
            with col_c: st.button("SUPPORT", on_click=lambda: nav_to("SUPPORT"))
        else:
            col_a, col_b, col_c = st.columns(3)
            with col_a: st.button("SOLUTIONS", on_click=lambda: nav_to("REVIEWS"))
            with col_b: st.button("OUR STORY", on_click=lambda: nav_to("STORY"))
            with col_c: st.button("PRICING", on_click=lambda: nav_to("PRICING"))

    with c3:
        if check_auth():
            st.button(f"LOGOUT ({st.session_state.user_name})", on_click=logout)
        else:
            st.button("LOGIN / SIGN UP", key="nav_login", type="primary", on_click=lambda: nav_to("LOGIN"))

# =========================================================
# GLOBAL CSS
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@300;400;600;800&display=swap');
.stApp { background-color: #0b0c10; font-family: 'Barlow', sans-serif; color: #e0e0e0; }
h1, h2, h3, h4 { font-family: 'Barlow', sans-serif; text-transform: uppercase; color: white; }
.project-card {
    background: #1e1e1e; border-radius: 8px; overflow: hidden; border: 1px solid #333;
    transition: transform 0.2s; margin-bottom: 20px;
}
.project-card:hover { transform: translateY(-5px); border-color: #e60012; }
.project-img { width: 100%; height: 150px; object-fit: cover; opacity: 0.7; }
.project-body { padding: 15px; }
.status-badge {
    padding: 4px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: bold; text-transform: uppercase;
}
.status-pending { background: #e60012; color: white; }
.status-active { background: #28a745; color: white; }
.status-archived { background: #555; color: #ccc; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# VIEW 1: HOMEPAGE (Marketing)
# =========================================================
if st.session_state.view == "LANDING":
    render_navbar()
    
    # Video Background
    st.markdown("""
    <style>
    #bgVideo { position: fixed; right: 0; bottom: 0; min-width: 100%; min-height: 100%; z-index: -99; opacity: 0.4; filter: grayscale(100%); }
    .overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(180deg, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0.2) 50%, rgba(0,0,0,1) 100%); z-index: -98; }
    </style>
    <video autoplay muted loop playsinline id="bgVideo"><source src="https://videos.pexels.com/video-files/3129957/3129957-uhd_2560_1440_25fps.mp4" type="video/mp4"></video><div class="overlay"></div>
    """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("<h1 style='font-size: 5rem; line-height: 1;'>CONSTRUCTION<br>INTELLIGENCE.</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 1.5rem; color: #aaa;'>The autonomous coordination platform for modern builders.</p>", unsafe_allow_html=True)
        st.button("ACCESS PLATFORM ➤", type="primary", on_click=lambda: nav_to("LOGIN"))

    # Feature Cards
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    fc1, fc2, fc3 = st.columns(3)
    
    with fc1:
        st.image("card_3d.jpg" if os.path.exists("card_3d.jpg") else "https://images.pexels.com/photos/834892/pexels-photo-834892.jpeg", use_column_width=True)
        st.markdown("#### INSTANT CLASH")
        st.caption("Automated spatial conflict resolution.")

    with fc2:
        st.image("https://images.pexels.com/photos/2760241/pexels-photo-2760241.jpeg", use_column_width=True)
        st.markdown("#### VISION AI")
        st.caption("Blueprint optical character recognition.")

    with fc3:
        st.image("card_procore.png" if os.path.exists("card_procore.png") else "https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Procore_Logo.svg/512px-Procore_Logo.svg.png", use_column_width=True)
        st.markdown("#### PROCORE SYNC")
        st.caption("Direct RFI and Submittal integration.")

# =========================================================
# VIEW 2: LOGIN PORTAL
# =========================================================
elif st.session_state.view == "LOGIN":
    render_navbar()
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown("""
        <div style="background: #1a1a1a; padding: 30px; border-radius: 10px; border: 1px solid #333; text-align: center;">
            <h3>TECTONICA ID</h3>
            <p style="color: #666; font-size: 0.9rem;">Enter your credentials to access the secure dashboard.</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login"):
            u = st.text_input("Email / Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("SIGN IN"):
                if login(u, p):
                    st.success("Authenticating...")
                    time.sleep(1)
                    nav_to("DASHBOARD")
                    st.rerun()
                else:
                    st.error("Invalid Credentials.")
        st.caption("Demo Account: admin / tectonica")
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("New User? Contact your Project Administrator for an invite link.")

# =========================================================
# VIEW 3: "MY PROJECTS" DASHBOARD (The Procore View)
# =========================================================
elif st.session_state.view == "DASHBOARD":
    render_navbar()
    
    if not check_auth(): nav_to("LOGIN"); st.rerun()

    # -- THE PROJECT HUB LOGIC --
    if st.session_state.step == "HOME":
        st.title("MY PROJECTS")
        st.markdown("Access projects you have been invited to.")
        st.divider()
        
        # Grid Display
        cols = st.columns(3)
        projects = list(st.session_state.projects.items())
        
        for i, (p_name, p_data) in enumerate(projects):
            with cols[i % 3]:
                # Status Color Logic
                status_class = "status-active"
                if "INVITE" in p_data['status']: status_class = "status-pending"
                if "ARCHIVED" in p_data['status']: status_class = "status-archived"

                st.markdown(f"""
                <div class="project-card">
                    <img src="{p_data['img']}" class="project-img">
                    <div class="project-body">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                            <span class="status-badge {status_class}">{p_data['status']}</span>
                            <span style="color:#666; font-size:0.8rem;">{p_data['date']}</span>
                        </div>
                        <h4>{p_name}</h4>
                        <p style="color:#aaa; font-size:0.9rem;">Invited by: {p_data['inviter']}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Dynamic Action Button
                btn_label = "ENTER PROJECT"
                if "INVITE" in p_data['status']: btn_label = "ACCEPT INVITE & ENTER"
                
                if st.button(btn_label, key=f"btn_{i}", type="primary" if "INVITE" in p_data['status'] else "secondary"):
                    st.session_state.current_project = p_name
                    # If first time entering (Invite), go to Upload/Setup
                    if "INVITE" in p_data['status']:
                        st.session_state.projects[p_name]['status'] = "ACTIVE" # Auto-accept
                        st.session_state.step = "UPLOAD"
                    else:
                        st.session_state.step = "UPLOAD"
                    st.rerun()

    # -- PROJECT WORKSPACE (Inside a Project) --
    elif st.session_state.step == "UPLOAD":
        st.button("← BACK TO ALL PROJECTS", on_click=lambda: setattr(st.session_state, 'step', 'HOME'))
        st.title(f"WORKSPACE: {st.session_state.current_project}")
        
        # Project Tabs
        t1, t2, t3 = st.tabs(["DRAWINGS", "CLASH DETECTION", "RFI LOG"])
        
        with t1:
            st.info("Upload new drawing revisions here.")
            st.file_uploader("Drag & Drop PDF Sheets", accept_multiple_files=True)
            
            # Show Sample Link for Naples if active
            if "NAPLES" in st.session_state.current_project:
                st.markdown("---")
                st.write("**📥 PENDING FILES:**")
                st.markdown("The Project Admin has queued the AOB Drawing Set.")
                st.link_button("View/Download Naples PDF", "https://www.flynaples.com/wp-content/uploads/2022-02-28-NAPLES-AOB-CONSTRUCTION-DRAWINGS.pdf")

        with t2:
            st.write("### RUN ANALYSIS")
            c1, c2 = st.columns(2)
            with c1: st.selectbox("Base Layer", ["A-101 ARCH", "S-101 STRUCT"])
            with c2: st.selectbox("Compare With", ["M-101 MECH", "E-101 ELEC"])
            
            if st.button("RUN CLASH TEST", type="primary"):
                with st.spinner("Processing..."):
                    time.sleep(2)
                    st.success("Clashes Detected.")
                    # Dummy Results
                    st.error("#1: Ductwork hits Beam at Grid F-4")
                    st.error("#2: Pipe clearance issue in Corridor 102")
                    st.image("https://images.pexels.com/photos/8961059/pexels-photo-8961059.jpeg", caption="3D View", use_column_width=True)

        with t3:
            st.write("### RFI LOG")
            st.dataframe([
                {"RFI #": "001", "Subject": "Beam Penetration", "Status": "Open", "Assigned To": "Struct Eng"},
                {"RFI #": "002", "Subject": "Door Swing", "Status": "Closed", "Assigned To": "Arch"}
            ])

# =========================================================
# OTHER PAGES
# =========================================================
elif st.session_state.view in ["STORY", "REVIEWS", "CAREERS", "SUPPORT", "DIRECTORY", "PRICING"]:
    render_navbar()
    st.title(st.session_state.view)
    st.info("Content placeholder for demo.")
