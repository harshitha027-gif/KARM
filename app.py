import streamlit as st
import json
import os

st.set_page_config(
    page_title="KARM - Core Application",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_employees():
    file_path = os.path.join("fake_data", "employees.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

employees = load_employees()
employee_dict = {emp["name"]: emp for emp in employees}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None

def login():
    st.title("Welcome to KARM 🤖")
    st.markdown("Please log in to access your modules.")
    
    st.markdown("### User Login")
    email_input = st.text_input("Email")
    password_input = st.text_input("Password", type="password")
    
    if st.button("Login", type="primary"):
        if email_input and password_input:
            # Find user by email
            user_found = next((emp for emp in employees if emp["email"] == email_input), None)
            
            if user_found and user_found.get("password") == password_input:
                st.session_state.logged_in = True
                st.session_state.current_user = user_found
                st.session_state.employee_id = user_found["id"]
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid email or password.")
        else:
            st.warning("Please enter both email and password.")

def logout():
    st.session_state.logged_in = False
    st.session_state.current_user = None
    if "employee_id" in st.session_state:
        del st.session_state.employee_id
    st.rerun()

login_page = st.Page(login, title="Login", icon="🔐")

if not st.session_state.logged_in:
    pg = st.navigation([login_page])
    pg.run()
else:
    user = st.session_state.current_user
    
    def home_page():
        st.title("KARM - AI-Powered HR Automation System")
        st.markdown(f"### Welcome, {user['name']}! 👋")
        st.markdown("This platform transforms how Human Resource departments operate. Use the sidebar to navigate to your available modules.")
        
        st.markdown("---")
        st.markdown("### 📋 Available Modules Quick Summary")
        st.markdown("- **🔥 Burnout Dashboard** *(HR Only)*: Analyze employee communication data to detect burnout risk.")
        st.markdown("- **⚖️ Bias Detector** *(HR Only)*: Flag biased interview questions and ensure fair hiring.")
        st.markdown("- **📅 Interview Scheduler** *(HR Only)*: Autonomously schedule and negotiate interviews.")
        st.markdown("- **📋 Policy AMA**: Ask questions about company policies and get instant answers.")
        st.markdown("- **🎯 Internal Job Match**: Find the best internal roles based on your skills.")
        st.markdown("- **🌐 Vernacular Training**: Generate native-language training from English PDFs.")
        st.markdown("- **🏆 Gamified Performance**: Track KPIs with badges, levels, and AI nudges.")
        
    home = st.Page(home_page, title="Home / Overview", icon="🏠")
    
    # Render user profile in sidebar
    st.sidebar.markdown(f"### 👤 {user['name']}")
    st.sidebar.markdown(f"**Role:** {user['role']}  \n**Dept:** {user['department']}")
    st.sidebar.markdown("---")
    
    is_hr = user.get("department") == "HR"
    
    # Define pages corresponding to modules
    module1 = st.Page("module1_policy_ama.py", title="Policy AMA", icon="📋")
    module2 = st.Page("module2_burnout.py", title="Burnout Dashboard", icon="🔥")
    module3 = st.Page("module3_bias_detector.py", title="Bias Detector", icon="⚖️")
    module4 = st.Page("module4_job_match.py", title="Internal Job Match", icon="🎯")
    module5 = st.Page("module5_training_bot.py", title="Vernacular Training", icon="🌐")
    module6 = st.Page("module6_gamified.py", title="Gamified Performance", icon="🏆")
    module7 = st.Page("module7_scheduler.py", title="Interview Scheduler", icon="📅")
    
    # Assign pages based on role
    pages = {"Overview": [home]}
    if is_hr:
        pages["HR Modules"] = [module2, module3, module7]
        # HR can also see regular employee modules if needed, or we can just categorize them below
        pages["Employee Modules"] = [module1, module4, module5, module6]
    else:
        # Regular employee views
        pages["Employee Modules"] = [module1, module4, module5, module6]
        
    pg = st.navigation(pages)
    
    # Put logout button at the bottom of the sidebar
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout", type="primary"):
        logout()
        
    pg.run()
