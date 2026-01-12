import streamlit as st
import os
import base64
import time
from utils_database import init_db, save_project, get_projects, teach_ai
from utils_vision import pdf_page_to_image, detect_clashes_with_boxes
from streamlit_cropper import st_cropper

# --- 1. INITIALIZATION ---
st.set_page_config(layout="wide", page_title="TECTONICA | Orbital Construction")
init_db()

# --- 2. ASSET LOADER ---
def get_img_as_base64(file_path):
    if not os.path.exists(file_path): return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    with open(file_path, "rb") as f: data = f.read()
    return f"data:image/{file_path.split('.')[-1]};base64,{base64.b64encode(data).decode()}"

# --- 3. SESSION STATE ---
if 'view' not in st.session_state: st.session_state.view = "LANDING"
if 'projects' not in st.session_state: st.session_state.projects = {} 
if 'current_project' not in st.session_state: st.session_state.current_project = None
if 'step' not in st.session_state: st.session_state.step = "HOME"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []

# --- 4. NAVIGATION CONTROLLER ---
def nav_to(page): st.session_state.view = page

# --- 5. COMPONENT: THE PERSISTENT NAVBAR ---
def render_navbar():
    st.markdown("""
    <style>
    /* NAVBAR STYLING */
    .nav-container {
        display: flex; justify-content: space-between; align-items: center;
        padding: 1rem 2rem; background: rgba(0,0,0,0.8); border-bottom: 1px solid #333;
        margin-bottom: 2rem;
    }
    .nav-left { display: flex; align-items: center; gap: 20px; }
    .nav-right { display: flex; gap: 15px; }
    
    /* NAV BUTTONS */
    div.stButton > button {
        background: transparent; border: none; color: #ccc; 
        font-family: 'Barlow', sans-serif; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px;
        margin: 0; padding: 0.5rem 1rem; transition: 0.3s;
    }
    div.stButton > button:hover { color: white; text-shadow: 0 0 10px rgba(255,255,255,0.5); }
    div.stButton > button:focus { border: none; outline: none; box-shadow: none; color: #e60012; }
    
    /* SPECIAL 'LOGIN' BUTTON */
    .login-btn > button { border: 1px solid #e60012 !important; color: #e60012 !important; border-radius: 4px; }
    .login-btn > button:hover { background: #e60012 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4, c5, c6, c7 = st.columns([2, 1, 1, 1, 1, 1, 1])
    
    with c1:
        if os.path.exists("logo.png"): st.image("logo.png", width=140)
        else: st.markdown("### TECTONICA")
    
    # NAVIGATION LINKS
    with c2: st.button("STORY", on_click=lambda: nav_to("STORY"))
    with c3: st.button("EXPERIENCES", on_click=lambda: nav_to("REVIEWS"))
    with c4: st.button("CAREERS", on_click=lambda: nav_to("CAREERS"))
    with c5: st.button("SUPPORT", on_click=lambda: nav_to("SUPPORT"))
    with c6: st.button("MY PROJECTS", on_click=lambda: nav_to("DASHBOARD"))
    
    # LOGIN / SIGNUP
    with c7: 
        st.markdown('<div class="login-btn">', unsafe_allow_html=True)
        st.button("ACCESS / SIGN UP", on_click=lambda: nav_to("PRICING"))
        st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# GLOBAL STYLES (FONTS & BASICS)
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
    
    # VIDEO BACKGROUND SPECIFIC TO LANDING
    video_url = "https://videos.pexels.com/video-files/3129957/3129957-uhd_2560_1440_25fps.mp4"
    st.markdown(f"""
    <style>
    #myVideo {{ position: fixed; right: 0; bottom: 0; min-width: 100%; min-height: 100%; z-index: -1; opacity: 0.5; filter: grayscale(100%) contrast(1.2); }}
    .overlay {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(180deg, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0.4) 50%, rgba(0,0,0,1) 100%); z-index: 0; pointer-events: none; }}
    </style>
    <video autoplay muted loop id="myVideo"><source src="{video_url}" type="video/mp4"></video><div class="overlay"></div>
    """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("""
        <h1 style='font-size: 5rem; line-height: 0.9;'>BUILD WITHOUT<br><span style='color:#e60012'>BLIND SPOTS.</span></h1>
        <p style='font-size: 1.5rem; color: #ccc; margin-top: 1rem;'>The Autonomous Construction Coordinator.</p>
        """, unsafe_allow_html=True)
        st.button("INITIATE SEQUENCE ➤", type="primary", on_click=lambda: nav_to("PRICING"))

# =========================================================
# VIEW: MISSION CRITICAL (Our Story)
# =========================================================
elif st.session_state.view == "STORY":
    render_navbar()
    st.markdown("""
    <div style="max-width: 800px; margin: 0 auto; padding: 2rem;">
        <h1 style="text-align: center; border-bottom: 2px solid #e60012; padding-bottom: 1rem;">MISSION CRITICAL</h1>
        <br>
        <p style="font-size: 1.2rem; line-height: 1.8;">
        Construction is the only industry where we accept "Clashes" as a standard line item. 
        We build billion-dollar structures using 2D PDFs that haven't changed since the 1980s.
        </p>
        <p style="font-size: 1.2rem; line-height: 1.8;">
        <b>TECTONICA was forged in the field.</b> Born from the frustration of a Superintendent who saw millions of dollars wasted on rework that could have been caught by a computer in seconds.
        </p>
        <p style="font-size: 1.2rem; line-height: 1.8;">
        We are not a software company. We are a <b>Construction Efficiency Engine</b>. We utilize orbital-grade computer vision to overlay intent vs. reality, ensuring that what you draw is what you build.
        </p>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# VIEW: INTEL (User Reviews)
# =========================================================
elif st.session_state.view == "REVIEWS":
    render_navbar()
    st.title("FIELD INTELLIGENCE")
    st.markdown("### OPERATOR REPORTS")
    
    r1, r2 = st.columns(2)
    with r1:
        st.markdown("""
        <div style="background: #111; padding: 2rem; border: 1px solid #333; border-radius: 8px;">
            <h3 style="color: #e60012;">"SAVED $400K IN WEEK 1"</h3>
            <p>"We uploaded the MEP set for the Hudson Yards expansion. Tectonica caught a duct run hitting a structural beam that Navisworks missed because the beam wasn't modeled yet. It read the 2D Structural drawings and saved us a 3-week delay."</p>
            <p style="color: #888; margin-top: 1rem;">- <b>Sarah J., Senior PM, Skanska</b></p>
        </div>
        """, unsafe_allow_html=True)
    with r2:
        st.markdown("""
        <div style="background: #111; padding: 2rem; border: 1px solid #333; border-radius: 8px;">
            <h3 style="color: #e60012;">"SUPERINTENDENT'S BEST FRIEND"</h3>
            <p>"I don't have time to learn complex BIM software. Tectonica just lets me drag and drop my PDFs. It highlights the issues like a red marker. Simple, lethal, effective."</p>
            <p style="color: #888; margin-top: 1rem;">- <b>Mike R., Gen. Super, Turner</b></p>
        </div>
        """, unsafe_allow_html=True)

# =========================================================
# VIEW: CAREERS
# =========================================================
elif st.session_state.view == "CAREERS":
    render_navbar()
    st.title("JOIN THE CREW")
    st.markdown("Help us build the operating system for the built world.")
    
    jobs = [
        ("Computer Vision Engineer", "Remote / NY", "Lead our OCR and Geometry detection pipeline."),
        ("Full Stack Developer", "San Francisco", "Build the interface that Superintendents rely on."),
        ("Construction Technologist", "Austin, TX", "Bridge the gap between code and concrete.")
    ]
    
    for title, loc, desc in jobs:
        with st.expander(f"{title}  |  {loc}"):
            st.write(desc)
            st.button(f"APPLY FOR {title.split()[0].upper()}", key=title)

# =========================================================
# VIEW: SUPPORT (FAQ + Chatbot)
# =========================================================
elif st.session_state.view == "SUPPORT":
    render_navbar()
    st.title("SYSTEM SUPPORT")
    
    tab_faq, tab_chat, tab_email = st.tabs(["FAQ", "AI AGENT", "DIRECT COMMS"])
    
    with tab_faq:
        st.markdown("### COMMON QUERIES")
        with st.expander("Does Tectonica replace Navisworks?"):
            st.write("No. We augment it. We catch the clashes that happen in the 2D documentation gap before the model is even built.")
        with st.expander("Is my data secure?"):
            st.write("We use AES-256 encryption. Your drawings never leave our secure enclave.")
            
    with tab_chat:
        st.markdown("### TECTONICA SUPPORT AGENT (BETA)")
        
        # Display chat history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                
        # Chat Input
        if prompt := st.chat_input("Ask about features, pricing, or bugs..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.write(prompt)
            
            # Simple Dummy Response Logic
            time.sleep(1) # Simulate thinking
            response = "I am a demo agent. Please contact support@tectonica.ai for complex queries."
            if "price" in prompt.lower(): response = "We offer Free, Pro ($49/mo), and Enterprise tiers."
            if "upload" in prompt.lower(): response = "You can upload PDF sets in the Dashboard. We support vector and raster PDFs."
            
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"): st.write(response)

    with tab_email:
        st.text_input("Your Email")
        st.text_area("Describe your issue")
        if st.button("TRANSMIT TICKET"):
            st.success("Ticket #9942 created. Response time: < 4 hours.")

# =========================================================
# VIEW: ACCESS (Pricing/Login)
# =========================================================
elif st.session_state.view == "PRICING":
    render_navbar()
    st.title("SELECT MISSION PROFILE")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("""
        <div style="border:1px solid #333; padding:20px; border-radius:10px; text-align:center;">
            <h2>SCOUT</h2>
            <h1>FREE</h1>
            <p>1 Project</p>
            <p>Basic Clash Detection</p>
            <p>Community Support</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("LAUNCH SCOUT"): nav_to("DASHBOARD")
        
    with c2:
        st.markdown("""
        <div style="border:1px solid #e60012; padding:20px; border-radius:10px; text-align:center; background:rgba(230,0,18,0.1);">
            <h2 style="color:#e60012">COMMANDER</h2>
            <h1>$49<span style="font-size:1rem">/mo</span></h1>
            <p>Unlimited Projects</p>
            <p>Vision AI Enabled</p>
            <p>Priority Support</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("LAUNCH COMMANDER", type="primary"): nav_to("DASHBOARD")
        
    with c3:
        st.markdown("""
        <div style="border:1px solid #333; padding:20px; border-radius:10px; text-align:center;">
            <h2>ENTERPRISE</h2>
            <h1>CUSTOM</h1>
            <p>Procore Integration</p>
            <p>On-Premise Deployment</p>
            <p>Dedicated Engineer</p>
        </div>
        """, unsafe_allow_html=True)
        st.button("CONTACT SALES")

# =========================================================
# VIEW: DASHBOARD (The App)
# =========================================================
elif st.session_state.view == "DASHBOARD":
    render_navbar() # Navbar persists even in dashboard
    
    # Dashboard Header
    dash_c1, dash_c2 = st.columns([6, 1])
    with dash_c1: st.title("MISSION CONTROL")
    with dash_c2: st.button("LOGOUT", on_click=lambda: nav_to("LANDING"))
    st.divider()

    # Core App Logic 
    if st.session_state.step == "HOME":
        c1, c2 = st.columns([1, 2])
        with c1:
            st.write("#### ACTIVE OPERATIONS")
            existing = get_projects()
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
                create_project(new_p)
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
                    if st.session_state.current_project and f.name not in st.session_state.projects[st.session_state.current_project]['files']:
                        st.session_state.projects[st.session_state.current_project]['files'][f.name] = {
                            'image': pdf_page_to_image(f), 
                            'scale': "Unknown", 'discipline': "Unassigned", 'type': 'sheet', 'parent': None, 'needs_crop': False
                        }
                st.success("Payload Integrated.")

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

        with tab3:
            assets = st.session_state.projects[st.session_state.current_project]['files']
            a_list = list(assets.keys())
            if len(a_list) < 2: st.warning("Insufficient Payload.")
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

# FOOTER (On all pages)
st.markdown('<div class="footer">TECTONICA AEROSPACE & CONSTRUCTION INDUSTRIES<br>USA • NZ • LEO</div>', unsafe_allow_html=True)
