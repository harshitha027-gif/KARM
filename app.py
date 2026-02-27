import streamlit as st

st.set_page_config(
    page_title="KARM - Core Application",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def home_page():
    st.title("KARM - AI-Powered HR Automation System")
    st.markdown("### Welcome to KARM 👋")
    st.markdown("This platform transforms how Human Resource departments operate. Use the sidebar to navigate to any module.")
    
    st.markdown("---")
    st.markdown("### 📋 Available Modules Quick Summary")
    st.markdown("- **📋 Policy AMA**: Ask questions about company policies and get instant answers.")
    st.markdown("- **🔥 Burnout Dashboard**: Analyze employee communication data to detect burnout risk.")
    st.markdown("- **⚖️ Bias Detector**: Flag biased interview questions and ensure fair hiring.")
    st.markdown("- **🎯 Internal Job Match**: Find the best internal roles based on employee skills.")
    st.markdown("- **🌐 Vernacular Training**: Generate native-language training from English PDFs.")
    st.markdown("- **🏆 Gamified Performance**: Track KPIs with badges, levels, and AI nudges.")
    st.markdown("- **📅 Interview Scheduler**: Autonomously schedule and negotiate interviews.")
    
home = st.Page(home_page, title="Home / Overview", icon="🏠")

module1 = st.Page("module1_policy_ama.py", title="Policy AMA", icon="📋")
module2 = st.Page("module2_burnout.py", title="Burnout Dashboard", icon="🔥")
module3 = st.Page("module3_bias_detector.py", title="Bias Detector", icon="⚖️")
module4 = st.Page("module4_job_match.py", title="Internal Job Match", icon="🎯")
module5 = st.Page("module5_training_bot.py", title="Vernacular Training", icon="🌐")
module6 = st.Page("module6_gamified.py", title="Gamified Performance", icon="🏆")
module7 = st.Page("module7_scheduler.py", title="Interview Scheduler", icon="📅")

pg = st.navigation({
    "Overview": [home],
    "All Modules": [module1, module2, module3, module4, module5, module6, module7]
})

pg.run()
