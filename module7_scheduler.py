import streamlit as st
import pandas as pd
import json
import os
import google.generativeai as genai

# --- Configuration ---
def setup_page():
    try:
        st.set_page_config(
            page_title="KARM - Autonomous Interview Scheduler",
            page_icon="📅",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    except Exception:
        pass
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        .stApp {
            font-family: 'Inter', sans-serif;
        }
        
        /* Header styling */
        .main-header {
            background: linear-gradient(135deg, #0a1628 0%, #1a365d 50%, #2b4c7e 100%);
            padding: 2rem 2.5rem;
            border-radius: 16px;
            margin-bottom: 1.5rem;
            color: white;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        }
        .main-header h1 {
            margin: 0;
            font-size: 2rem;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        .main-header p {
            margin: 0.5rem 0 0 0;
            opacity: 0.85;
            font-size: 1rem;
            font-weight: 300;
        }
        
        /* Card Styling for Calendar Invite */
        .invite-card {
            background-color: #FFFFFF;
            border: 1px solid #CBD5E1;
            border-left: 5px solid #3B82F6;
            border-radius: 8px;
            padding: 25px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            margin-top: 15px;
        }
        .invite-header {
            font-size: 1.25rem;
            font-weight: 700;
            color: #1E293B;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .invite-detail {
            color: #334155;
            margin-bottom: 8px;
            font-size: 0.95rem;
        }
        .invite-label {
            font-weight: 600;
            color: #64748B;
            display: inline-block;
            width: 100px;
        }
        
        /* Analysis styling */
        .reasoning-box {
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 15px;
            font-size: 0.9rem;
            color: #475569;
            margin-bottom: 20px;
        }
    </style>
    """, unsafe_allow_html=True)


# --- Data Loading ---
def load_employees():
    file_path = os.path.join(os.path.dirname(__file__), 'fake_data', 'employees.json')
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return []

def load_roles():
    file_path = os.path.join(os.path.dirname(__file__), 'fake_data', 'open_roles.json')
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return []


# --- Gemini Scheduler Agent ---
def generate_interview_schedule(api_key, role, candidate, recruiter_avail, candidate_avail, duration):
    genai.configure(api_key=api_key)
    # Using gemma-3-27b as per project standard
    model = genai.GenerativeModel('gemma-3-27b-it')
    
    prompt = f"""You are KARM, an Autonomous Interview Scheduler. Your job is to analyze the availability of the Recruiter and the Candidate, and find the best overlapping time slot for an interview. 

Role details:
- Title: {role['title']}
- Department: {role['department']}

Candidate details:
- Name: {candidate['name']}
- Current Role: {candidate['role']}

Recruiter Availability:
{recruiter_avail}

Candidate Availability:
{candidate_avail}

Interview Duration Required: {duration} minutes

TASK:
1. Identify all possible overlapping slots that are at least {duration} minutes long.
2. Select the earliest optimal slot.
3. If no clear overlap exists, propose the closest possible slot and explain why an exception is needed.
4. Output your answer in exactly two parts separated by '===INVITE===' on a new line.

Part 1: Your reasoning (a short paragraph explaining how you found the slot).
Part 2: The exact JSON for the calendar invite. The JSON must have these exact keys: "subject", "date", "time", "attendees", "link".

Example output format:
Comparing the schedules, the recruiter is free Monday morning and the candidate is free all day Monday. The best overlap for a {duration}-minute interview is Monday at 10:00 AM.
===INVITE===
{{
  "subject": "Interview: Role Title - Candidate Name",
  "date": "Monday (Next Available)",
  "time": "10:00 AM - 10:30 AM",
  "attendees": "Recruiter, Candidate Name",
  "link": "https://meet.google.com/mock-link-123"
}}
"""

    try:
        response = model.generate_content(prompt)
        text = response.text
        return parse_gemini_response(text)
    except Exception as e:
        return None, f"Error calling Gemini: {str(e)}"

def parse_gemini_response(text):
    if "===INVITE===" in text:
        parts = text.split("===INVITE===")
        reasoning = parts[0].strip()
        json_str = parts[1].strip()
        try:
            # handle markdown block if present
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            invite_data = json.loads(json_str.strip())
            return invite_data, reasoning
        except json.JSONDecodeError:
            return None, "Error parsing the invite JSON from AI. Raw JSON provided: " + json_str
    else:
        return None, "AI response did not follow the expected format. Raw response: " + text


# --- Main Application ---
def main():
    setup_page()
    
    # ── Header ──
    st.markdown("""
    <div class="main-header">
        <h1>📅 KARM Autonomous Scheduler</h1>
        <p>Simulate intelligent schedule negotiation between recruiters and candidates. Eliminate back-and-forth emails to find the perfect interview slot.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load Data
    employees = load_employees()
    roles = load_roles()
    
    if not employees or not roles:
        st.error("Error: Could not load data from fake_data/. Please verify 'employees.json' and 'open_roles.json' exist.")
        st.stop()
        
    # ── Sidebar ──
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        api_key = st.text_input(
            "Google Gemini API Key",
            type="password",
            help="Get your free API key from aistudio.google.com/apikey"
        )
        if api_key:
            st.success("✅ API key set")
        else:
            st.warning("⚠️ Enter your Gemini API key to start")
            
        st.markdown("---")
        
        st.markdown("### 👤 Selection")
        role_titles = [r['title'] for r in roles]
        selected_role_title = st.selectbox("Select Role", role_titles)
        role = next(r for r in roles if r['title'] == selected_role_title)
        
        emp_names = [e['name'] for e in employees]
        selected_emp_name = st.selectbox("Select Candidate", emp_names)
        candidate = next(e for e in employees if e['name'] == selected_emp_name)
        
        duration = st.selectbox("Interview Duration", ["30", "45", "60"])
    
    # ── Main Area ──
    st.markdown("### 🔄 Enter Availability to Negotiate")
    st.write("Input the availability constraints for both parties. The AI will find the optimal overlap and generate an invite.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🧑‍💼 Recruiter (You)")
        recruiter_avail = st.text_area(
            "Recruiter Availability",
            value="Monday and Tuesday from 10:00 AM to 2:00 PM. Thursday afternoon 3:00 PM to 5:00 PM.",
            height=100
        )
        
    with col2:
        st.markdown(f"#### 👤 Candidate ({candidate['name']})")
        candidate_avail = st.text_area(
            "Candidate Availability",
            value="I am completely booked on Monday. I am free Tuesday from 1:00 PM onwards, and anytime Wednesday.",
            height=100
        )
        
    if st.button("✨ Generate Optimal Interview Schedule", type="primary", use_container_width=True):
        if not api_key:
            st.error("Please enter your Gemini API Key in the sidebar.")
        elif not recruiter_avail or not candidate_avail:
            st.error("Please provide availability for both parties.")
        else:
            with st.spinner("🧠 KARM AI is negotiating the schedule..."):
                invite_data, reasoning_or_error = generate_interview_schedule(
                    api_key, role, candidate, recruiter_avail, candidate_avail, duration
                )
                
                if invite_data:
                    st.success("✅ Schedule finalized successfully!")
                    
                    st.markdown("### 🤖 Scheduler AI Reasoning")
                    st.markdown(f'<div class="reasoning-box">{reasoning_or_error}</div>', unsafe_allow_html=True)
                    
                    st.markdown("### 📅 Generated Calendar Invite")
                    st.markdown(f"""
                    <div class="invite-card">
                        <div class="invite-header">🗓️ {invite_data.get('subject', 'Interview Invite')}</div>
                        <div class="invite-detail"><span class="invite-label">Date:</span> {invite_data.get('date', 'TBD')}</div>
                        <div class="invite-detail"><span class="invite-label">Time:</span> {invite_data.get('time', 'TBD')}</div>
                        <div class="invite-detail"><span class="invite-label">Attendees:</span> {invite_data.get('attendees', 'TBD')}</div>
                        <div class="invite-detail" style="margin-top: 15px;">
                            <span class="invite-label">Meeting Link:</span> 
                            <a href="{invite_data.get('link', '#')}" target="_blank" style="color: #3B82F6; text-decoration: none; font-weight: 500;">
                                📹 Join Video Call
                            </a>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                else:
                    st.error(f"Failed to generate schedule.\\nDetails: {reasoning_or_error}")

if __name__ == "__main__":
    main()
