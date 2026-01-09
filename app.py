# Add this import at the top
from utils_database import init_db, save_project, get_projects, teach_ai

# Initialize DB on app launch
init_db()

# ... (Keep existing layout code)

# IN "HOME" SECTION:
# Change the project selector to read from DB instead of session state
st.write("#### SELECT MISSION")
existing_projects = get_projects() # Reads from SQLite
if existing_projects:
    sel_proj = st.selectbox("Active Projects", existing_projects)
    if st.button("RESUME MISSION"):
        create_project(sel_proj)
        
# IN "INITIATE NEW MISSION":
if st.button("INITIALIZE PROJECT"):
    save_project(new_proj) # Saves to SQLite
    create_project(new_proj)


# IN "ANALYSIS" TAB (The Feedback Loop):
# After results are shown...
if st.session_state.get('clash_data'): # If we have results
    st.divider()
    st.markdown("### AI TRAINING FEEDBACK")
    st.info("Teach the system to improve future accuracy.")
    
    for i, clash in enumerate(st.session_state.clash_data):
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1:
            st.write(f"**Issue {i+1}:** {clash['description']}")
        with c2:
            if st.button("✅ Confirm", key=f"conf_{i}"):
                teach_ai(clash['description'], "clash")
                st.toast("Logic Confirmed.")
        with c3:
            if st.button("❌ False Alarm", key=f"false_{i}"):
                teach_ai(clash['description'], "safe")
                st.toast("AI Updated: Will ignore similar issues next time.")