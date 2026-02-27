"""
KARM Module 4: Internal Job Match Agent
==========================================
Matches employees to internal job openings using TF-IDF cosine similarity
on skills and experience, with Gemini AI-powered explanations.

Run: streamlit run module4_job_match.py
"""

import streamlit as st
import google.generativeai as genai
import json
import os
import re
from datetime import datetime

# ML libraries
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Optional libraries
try:
    import plotly.graph_objects as go
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False


# ─────────────────────────────────────────────────────────────
# CONFIG & THEME
# ─────────────────────────────────────────────────────────────
def setup_page():
    st.set_page_config(
        page_title="KARM - Job Match",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        .stApp {
            font-family: 'Inter', sans-serif;
        }

        /* Header */
        .main-header {
            background: linear-gradient(135deg, #1a0a28 0%, #3d1652 50%, #6b2fa0 100%);
            padding: 2rem 2.5rem;
            border-radius: 16px;
            margin-bottom: 1.5rem;
            color: white;
            box-shadow: 0 4px 20px rgba(107, 47, 160, 0.25);
        }
        .main-header h1 { margin: 0; font-size: 2rem; font-weight: 700; letter-spacing: -0.5px; }
        .main-header p { margin: 0.5rem 0 0 0; opacity: 0.85; font-size: 1rem; font-weight: 300; }

        /* KPI Cards */
        .kpi-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.1);
        }
        .kpi-value {
            font-size: 2.4rem; font-weight: 700; margin: 0.3rem 0;
            background: linear-gradient(135deg, #6b2fa0, #3182ce);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .kpi-label { font-size: 0.85rem; color: #718096; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
        .kpi-sub { font-size: 0.75rem; color: #a0aec0; margin-top: 0.3rem; }

        /* Match cards */
        .match-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
            border: 1px solid #e2e8f0;
            border-left: 5px solid #6b2fa0;
            border-radius: 0 14px 14px 0;
            padding: 1.5rem;
            margin: 0.75rem 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            transition: transform 0.15s, box-shadow 0.15s;
        }
        .match-card:hover {
            transform: translateX(4px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        }
        .match-card-high { border-left-color: #38a169; }
        .match-card-mid { border-left-color: #d69e2e; }
        .match-card-low { border-left-color: #e53e3e; }

        .match-title {
            font-size: 1.15rem; font-weight: 700; color: #2d3748;
            margin-bottom: 0.25rem;
        }
        .match-dept {
            font-size: 0.85rem; color: #718096; font-weight: 500;
            margin-bottom: 0.75rem;
        }

        /* Match percentage badge */
        .match-pct-high {
            background: linear-gradient(135deg, #c6f6d5, #f0fff4);
            border: 1px solid #68d391; color: #276749;
            padding: 0.35rem 0.9rem; border-radius: 20px;
            font-weight: 700; font-size: 1rem; display: inline-block;
        }
        .match-pct-mid {
            background: linear-gradient(135deg, #fefcbf, #fffff0);
            border: 1px solid #f6e05e; color: #b7791f;
            padding: 0.35rem 0.9rem; border-radius: 20px;
            font-weight: 700; font-size: 1rem; display: inline-block;
        }
        .match-pct-low {
            background: linear-gradient(135deg, #fed7d7, #fff5f5);
            border: 1px solid #fc8181; color: #c53030;
            padding: 0.35rem 0.9rem; border-radius: 20px;
            font-weight: 700; font-size: 1rem; display: inline-block;
        }

        /* Skill tags */
        .skill-tag {
            display: inline-block; padding: 0.25rem 0.6rem;
            border-radius: 12px; font-size: 0.78rem; font-weight: 500;
            margin: 0.15rem; transition: transform 0.15s;
        }
        .skill-tag:hover { transform: scale(1.05); }
        .skill-match {
            background: linear-gradient(135deg, #c6f6d5, #f0fff4);
            border: 1px solid #9ae6b4; color: #276749;
        }
        .skill-missing {
            background: linear-gradient(135deg, #fed7d7, #fff5f5);
            border: 1px solid #feb2b2; color: #c53030;
        }
        .skill-extra {
            background: linear-gradient(135deg, #bee3f8, #ebf8ff);
            border: 1px solid #90cdf4; color: #2b6cb0;
        }

        /* Employee Profile */
        .profile-card {
            background: linear-gradient(135deg, #faf5ff 0%, #ebf4ff 100%);
            border: 1px solid #d6bcfa;
            border-radius: 14px;
            padding: 1.5rem;
            box-shadow: 0 2px 12px rgba(107, 47, 160, 0.1);
        }
        .profile-name {
            font-size: 1.3rem; font-weight: 700; color: #2d3748;
            margin-bottom: 0.25rem;
        }
        .profile-role {
            font-size: 0.95rem; color: #6b2fa0; font-weight: 500;
        }
        .profile-detail {
            font-size: 0.85rem; color: #718096; margin: 0.15rem 0;
        }

        /* Section headers */
        .section-header {
            font-size: 1.2rem; font-weight: 600; color: #2d3748;
            margin: 1.5rem 0 1rem 0; padding-bottom: 0.5rem;
            border-bottom: 2px solid #e2e8f0;
        }

        /* AI insight box */
        .ai-insight {
            background: linear-gradient(135deg, #ebf4ff, #e9d8fd);
            border-left: 4px solid #6b2fa0;
            padding: 1rem 1.25rem;
            border-radius: 0 12px 12px 0;
            margin: 0.75rem 0;
            font-size: 0.92rem; line-height: 1.7;
            color: #2d3748;
        }

        /* Sidebar info */
        .sidebar-info {
            background: #f5f0ff; color: #553c9a;
            padding: 1rem; border-radius: 10px;
            border: 1px solid #d6bcfa; margin-bottom: 1rem; font-size: 0.85rem;
        }

        /* Skill gap recommendation */
        .skill-gap-card {
            background: linear-gradient(135deg, #fffff0, #fefcbf);
            border: 1px solid #f6e05e;
            border-radius: 12px;
            padding: 1rem 1.25rem;
            margin: 0.5rem 0;
            font-size: 0.9rem; color: #744210;
        }
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────
def load_employees():
    """Load employee data from shared data layer."""
    data_path = os.path.join(os.path.dirname(__file__), 'fake_data', 'employees.json')
    if os.path.exists(data_path):
        with open(data_path, 'r') as f:
            return json.load(f)
    return []


def load_open_roles():
    """Load open roles from shared data layer."""
    data_path = os.path.join(os.path.dirname(__file__), 'fake_data', 'open_roles.json')
    if os.path.exists(data_path):
        with open(data_path, 'r') as f:
            return json.load(f)
    return []


# ─────────────────────────────────────────────────────────────
# MATCHING ENGINE
# ─────────────────────────────────────────────────────────────
def build_employee_text(emp):
    """Build a text representation of an employee for TF-IDF."""
    skills = ' '.join(emp.get('skills', []))
    role = emp.get('role', '')
    dept = emp.get('department', '')
    return f"{skills} {role} {dept}".strip()


def build_role_text(role):
    """Build a text representation of a role for TF-IDF."""
    skills = ' '.join(role.get('required_skills', []))
    title = role.get('title', '')
    dept = role.get('department', '')
    desc = role.get('description', '')
    return f"{skills} {title} {dept} {desc}".strip()


def compute_matches(employees, roles):
    """Compute cosine similarity between all employees and roles using TF-IDF."""
    emp_texts = [build_employee_text(e) for e in employees]
    role_texts = [build_role_text(r) for r in roles]

    all_texts = emp_texts + role_texts
    vectorizer = TfidfVectorizer(stop_words='english', lowercase=True)
    tfidf_matrix = vectorizer.fit_transform(all_texts)

    emp_vectors = tfidf_matrix[:len(employees)]
    role_vectors = tfidf_matrix[len(employees):]

    sim_matrix = cosine_similarity(emp_vectors, role_vectors)
    return sim_matrix


def get_skill_overlap(emp_skills, role_skills):
    """Calculate matching and missing skills."""
    emp_set = {s.lower() for s in emp_skills}
    role_set = {s.lower() for s in role_skills}

    matched = emp_set & role_set
    missing = role_set - emp_set
    extra = emp_set - role_set

    # Preserve original casing
    matched_orig = [s for s in emp_skills if s.lower() in matched]
    missing_orig = [s for s in role_skills if s.lower() in missing]
    extra_orig = [s for s in emp_skills if s.lower() in extra]

    return matched_orig, missing_orig, extra_orig


def get_top_matches(employee_idx, sim_matrix, roles, top_n=3):
    """Get top N role matches for an employee."""
    scores = sim_matrix[employee_idx]
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    top = ranked[:top_n]

    results = []
    for role_idx, score in top:
        results.append({
            'role': roles[role_idx],
            'score': round(float(score) * 100, 1),
            'role_idx': role_idx
        })
    return results


# ─────────────────────────────────────────────────────────────
# GEMINI AI EXPLANATION
# ─────────────────────────────────────────────────────────────
def generate_match_explanation(api_key, employee, top_matches):
    """Use Gemini AI to generate explanations for matched roles."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemma-3-27b-it')

    matches_text = ""
    for i, m in enumerate(top_matches, 1):
        role = m['role']
        matched_skills, missing_skills, _ = get_skill_overlap(
            employee.get('skills', []),
            role.get('required_skills', [])
        )
        matches_text += f"""
Match #{i}:
- Role: {role['title']} ({role['department']})
- Match Score: {m['score']}%
- Skills Match: {', '.join(matched_skills) if matched_skills else 'None'}
- Missing Skills: {', '.join(missing_skills) if missing_skills else 'None'}
- Role Description: {role['description']}
"""

    prompt = f"""You are KARM, an AI-powered internal job matching system. Analyze why the following employee matches these internal roles.

EMPLOYEE PROFILE:
- Name: {employee['name']}
- Current Role: {employee['role']}
- Department: {employee['department']}
- Skills: {', '.join(employee.get('skills', []))}
- Seniority: Joined {employee.get('join_date', 'N/A')}
- Location: {employee.get('location', 'N/A')}

TOP MATCHED ROLES:
{matches_text}

INSTRUCTIONS:
For each match, provide:
1. A concise 2-3 sentence explanation of why this employee is a good fit
2. Specific skill gaps they'd need to fill
3. A growth recommendation

Also provide an overall career development insight for this employee.

Respond ONLY with valid JSON in exactly this format (no markdown, no code fences):
{{
  "match_explanations": [
    {{
      "role_title": "Role title",
      "explanation": "Why this employee is a good fit...",
      "skill_gaps": "What skills to develop...",
      "growth_tip": "A specific actionable recommendation..."
    }}
  ],
  "career_insight": "Overall career development insight for this employee...",
  "recommended_training": ["Specific course/training 1", "Specific course/training 2", "Specific course/training 3"]
}}"""

    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip()

        if raw_text.startswith('```'):
            raw_text = re.sub(r'^```(?:json)?\s*', '', raw_text)
            raw_text = re.sub(r'\s*```$', '', raw_text)

        result = json.loads(raw_text)
        return result
    except json.JSONDecodeError:
        try:
            retry_prompt = prompt + "\n\nCRITICAL: Respond with ONLY valid JSON. No markdown formatting, no code blocks, no extra text."
            response = model.generate_content(retry_prompt)
            raw_text = response.text.strip()
            if raw_text.startswith('```'):
                raw_text = re.sub(r'^```(?:json)?\s*', '', raw_text)
                raw_text = re.sub(r'\s*```$', '', raw_text)
            return json.loads(raw_text)
        except Exception:
            return None
    except Exception as e:
        st.error(f"⚠️ Error calling Gemini API: {str(e)}")
        return None


# ─────────────────────────────────────────────────────────────
# PDF REPORT GENERATION
# ─────────────────────────────────────────────────────────────
def sanitize_text(text):
    """Replace Unicode characters unsupported by Helvetica with ASCII equivalents."""
    if not isinstance(text, str):
        return str(text)
    replacements = {
        '\u2014': '--',  # em dash
        '\u2013': '-',   # en dash
        '\u2018': "'",   # left single quote
        '\u2019': "'",   # right single quote
        '\u201c': '"',   # left double quote
        '\u201d': '"',   # right double quote
        '\u2022': '*',   # bullet
        '\u2026': '...',  # ellipsis
        '\u2192': '->',  # right arrow
        '\u00b7': '*',   # middle dot
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    # Remove any remaining non-latin1 characters
    text = text.encode('latin-1', errors='replace').decode('latin-1')
    return text


def generate_pdf_report(employee, top_matches, ai_result):
    """Generate a PDF match report for an employee."""
    if not HAS_FPDF:
        return None

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Title
    pdf.set_font('Helvetica', 'B', 20)
    pdf.cell(0, 15, 'KARM Internal Job Match Report', ln=True, align='C')
    pdf.ln(5)

    # Date
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', ln=True, align='C')
    pdf.ln(8)

    # Employee Profile
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, 'Employee Profile', ln=True)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 7, f'Name: {employee["name"]}', ln=True)
    pdf.cell(0, 7, f'Current Role: {employee["role"]}', ln=True)
    pdf.cell(0, 7, f'Department: {employee["department"]}', ln=True)
    pdf.cell(0, 7, f'Skills: {", ".join(employee.get("skills", []))}', ln=True)
    pdf.cell(0, 7, f'Location: {employee.get("location", "N/A")}', ln=True)
    pdf.ln(5)

    # Top Matches
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, 'Top Matched Roles', ln=True)
    pdf.ln(3)

    explanations = {}
    if ai_result and 'match_explanations' in ai_result:
        for exp in ai_result['match_explanations']:
            explanations[exp.get('role_title', '')] = exp

    for i, match in enumerate(top_matches, 1):
        role = match['role']
        score = match['score']
        matched_skills, missing_skills, _ = get_skill_overlap(
            employee.get('skills', []),
            role.get('required_skills', [])
        )

        # Score color
        if score >= 75:
            pdf.set_text_color(39, 103, 73)
        elif score >= 50:
            pdf.set_text_color(183, 121, 31)
        else:
            pdf.set_text_color(197, 48, 48)

        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, sanitize_text(f'#{i}: {role["title"]} -- {score}% Match'), ln=True)
        pdf.set_text_color(0, 0, 0)

        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 7, f'Department: {role["department"]} | Seniority: {role.get("seniority", "N/A")} | Location: {role.get("location", "N/A")}', ln=True)
        pdf.cell(0, 7, f'Matching Skills: {", ".join(matched_skills) if matched_skills else "None"}', ln=True)
        pdf.cell(0, 7, f'Missing Skills: {", ".join(missing_skills) if missing_skills else "None"}', ln=True)

        exp = explanations.get(role['title'], {})
        if exp.get('explanation'):
            pdf.set_font('Helvetica', 'I', 10)
            pdf.multi_cell(0, 6, sanitize_text(f'AI Analysis: {exp["explanation"]}'))
        if exp.get('growth_tip'):
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(39, 103, 73)
            pdf.multi_cell(0, 6, sanitize_text(f'Growth Tip: {exp["growth_tip"]}'))
            pdf.set_text_color(0, 0, 0)
        pdf.ln(4)

    # Career Insight
    if ai_result and ai_result.get('career_insight'):
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(0, 10, 'Career Development Insight', ln=True)
        pdf.set_font('Helvetica', '', 10)
        pdf.multi_cell(0, 6, sanitize_text(ai_result['career_insight']))
        pdf.ln(3)

    # Recommended Training
    if ai_result and ai_result.get('recommended_training'):
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(0, 10, 'Recommended Training', ln=True)
        pdf.set_font('Helvetica', '', 10)
        for t in ai_result['recommended_training']:
            pdf.cell(0, 7, sanitize_text(f'  * {t}'), ln=True)

    # Footer
    pdf.ln(10)
    pdf.set_font('Helvetica', 'I', 9)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 8, 'This report was generated by KARM AI-Powered HR Automation System.', ln=True, align='C')
    pdf.cell(0, 8, 'For internal use only.', ln=True, align='C')

    return bytes(pdf.output())


# ─────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────
def get_match_pct_badge(score):
    """Return an HTML badge for match percentage."""
    if score >= 75:
        return f'<span class="match-pct-high">{score}%</span>'
    elif score >= 50:
        return f'<span class="match-pct-mid">{score}%</span>'
    else:
        return f'<span class="match-pct-low">{score}%</span>'


def get_match_card_class(score):
    """Return card CSS class based on score."""
    if score >= 75:
        return 'match-card match-card-high'
    elif score >= 50:
        return 'match-card match-card-mid'
    else:
        return 'match-card match-card-low'


def render_skill_tags(matched, missing, extra):
    """Render skill tags with color coding."""
    html = ''
    for s in matched:
        html += f'<span class="skill-tag skill-match">✓ {s}</span>'
    for s in missing:
        html += f'<span class="skill-tag skill-missing">✗ {s}</span>'
    for s in extra:
        html += f'<span class="skill-tag skill-extra">+ {s}</span>'
    return html


# ─────────────────────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────────────────────
def main():
    setup_page()

    # ── Header ──
    st.markdown("""
    <div class="main-header">
        <h1>🎯 KARM Internal Job Match Agent</h1>
        <p>AI-powered talent matching — find the perfect internal role for every employee using skills-based vector similarity.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Load Data ──
    employees = load_employees()
    roles = load_open_roles()

    if not employees:
        st.error("❌ Could not load employees.json from fake_data/")
        return
    if not roles:
        st.error("❌ Could not load open_roles.json from fake_data/")
        return

    # ── Compute Similarity Matrix ──
    sim_matrix = compute_matches(employees, roles)

    # ── Sidebar ──
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        api_key = st.text_input(
            "Google Gemini API Key", type="password",
            help="Get your free API key from aistudio.google.com/apikey"
        )
        if api_key:
            st.success("✅ API key set")
        else:
            st.info("ℹ️ Add API key for AI explanations")

        st.markdown("---")

        # Employee selector
        st.markdown("### 👤 Select Employee")
        emp_names = [f"{e['name']} ({e['id']})" for e in employees]
        selected_emp = st.selectbox(
            "Choose an employee",
            options=emp_names,
            help="Select an employee to find their best internal role matches"
        )
        selected_idx = emp_names.index(selected_emp)
        employee = employees[selected_idx]

        st.markdown("---")

        # Quick employee info
        st.markdown(f"""
        <div class="sidebar-info">
            <strong>📋 Quick Profile</strong><br>
            <strong>{employee['name']}</strong><br>
            🏢 {employee['department']}<br>
            💼 {employee['role']}<br>
            📍 {employee['location']}<br>
            🛠️ {', '.join(employee.get('skills', []))}
        </div>
        """, unsafe_allow_html=True)

        # Find Matches button
        find_clicked = st.button(
            "🔍 Find Best Matches",
            use_container_width=True,
            type="primary"
        )

        st.markdown("---")
        st.markdown("""
        <div class="sidebar-info">
            <strong>📖 How it works:</strong><br>
            KARM uses TF-IDF vectorization and cosine similarity to score
            employee-to-role matches based on skills, experience, and department.
            Gemini AI then explains each match with actionable growth tips.
        </div>
        """, unsafe_allow_html=True)

    # ── KPI Summary Row ──
    avg_score = float(sim_matrix.mean()) * 100
    max_score = float(sim_matrix.max()) * 100
    best_emp_idx, best_role_idx = divmod(sim_matrix.argmax(), sim_matrix.shape[1])
    best_emp = employees[best_emp_idx]
    best_role = roles[best_role_idx]
    selected_top_score = float(sim_matrix[selected_idx].max()) * 100

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Employees</div>
            <div class="kpi-value">{len(employees)}</div>
            <div class="kpi-sub">Active in system</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Open Roles</div>
            <div class="kpi-value">{len(roles)}</div>
            <div class="kpi-sub">Available positions</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Avg Match Score</div>
            <div class="kpi-value">{avg_score:.0f}%</div>
            <div class="kpi-sub">Across all pairs</div>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">🏆 Top Match</div>
            <div class="kpi-value" style="font-size: 1.5rem;">{max_score:.0f}%</div>
            <div class="kpi-sub">{best_emp['name']} → {best_role['title'][:20]}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Employee Profile ──
    st.markdown('<div class="section-header">👤 Employee Profile</div>', unsafe_allow_html=True)
    prof_col1, prof_col2 = st.columns([1, 2])

    with prof_col1:
        st.markdown(f"""
        <div class="profile-card">
            <div class="profile-name">{employee['name']}</div>
            <div class="profile-role">{employee['role']}</div>
            <div class="profile-detail">🏢 {employee['department']}</div>
            <div class="profile-detail">📍 {employee['location']}</div>
            <div class="profile-detail">📅 Joined: {employee.get('join_date', 'N/A')}</div>
            <div class="profile-detail">👤 Manager: {employee.get('manager', 'N/A')}</div>
        </div>
        """, unsafe_allow_html=True)

    with prof_col2:
        st.markdown("**🛠️ Skills Portfolio**")
        skills_html = ''
        for skill in employee.get('skills', []):
            skills_html += f'<span class="skill-tag skill-extra">{skill}</span>'
        st.markdown(skills_html, unsafe_allow_html=True)

        st.markdown(f"**📊 Best Possible Match:** {selected_top_score:.1f}%")

        # Show quick match overview for this employee
        top3 = get_top_matches(selected_idx, sim_matrix, roles, top_n=3)
        quick_html = "**🎯 Quick Match Preview:** "
        for m in top3:
            quick_html += f"`{m['role']['title']}` ({m['score']}%) · "
        st.markdown(quick_html.rstrip(' · '))

    st.markdown("---")

    # ── Trigger Detailed Match Analysis ──
    if find_clicked:
        top_matches = get_top_matches(selected_idx, sim_matrix, roles, top_n=3)
        st.session_state['job_matches'] = top_matches
        st.session_state['match_employee'] = employee
        st.session_state['match_emp_idx'] = selected_idx

        if api_key:
            with st.spinner("🤖 Generating AI-powered match explanations..."):
                ai_result = generate_match_explanation(api_key, employee, top_matches)
            if ai_result:
                st.session_state['ai_match_result'] = ai_result
            else:
                st.warning("⚠️ Could not generate AI explanations. Showing similarity scores only.")
                st.session_state['ai_match_result'] = None
        else:
            st.session_state['ai_match_result'] = None

    # ── Display Results ──
    if 'job_matches' in st.session_state and st.session_state.get('match_emp_idx') == selected_idx:
        top_matches = st.session_state['job_matches']
        ai_result = st.session_state.get('ai_match_result')

        # Build explanation lookup
        explanations = {}
        if ai_result and 'match_explanations' in ai_result:
            for exp in ai_result['match_explanations']:
                explanations[exp.get('role_title', '')] = exp

        st.markdown('<div class="section-header">🎯 Top 3 Role Matches</div>', unsafe_allow_html=True)

        for i, match in enumerate(top_matches):
            role = match['role']
            score = match['score']
            card_class = get_match_card_class(score)
            pct_badge = get_match_pct_badge(score)
            matched_skills, missing_skills, extra_skills = get_skill_overlap(
                employee.get('skills', []),
                role.get('required_skills', [])
            )
            skill_tags = render_skill_tags(matched_skills, missing_skills, extra_skills)

            st.markdown(f"""
            <div class="{card_class}">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                    <div>
                        <div class="match-title">#{i+1} — {role['title']}</div>
                        <div class="match-dept">🏢 {role['department']} &nbsp;|&nbsp; 📊 {role.get('seniority', 'N/A')} &nbsp;|&nbsp; 📍 {role.get('location', 'N/A')}</div>
                    </div>
                    <div>{pct_badge}</div>
                </div>
                <div style="margin: 0.75rem 0; font-size: 0.88rem; color: #4a5568;">{role.get('description', '')}</div>
                <div style="margin-top: 0.5rem;">
                    <strong style="font-size: 0.8rem; color: #718096;">SKILL ANALYSIS:</strong><br>
                    {skill_tags}
                </div>
                <div style="margin-top: 0.3rem; font-size: 0.75rem; color: #a0aec0;">
                    ✓ Matched: {len(matched_skills)} &nbsp;|&nbsp; ✗ Missing: {len(missing_skills)} &nbsp;|&nbsp; + Extra: {len(extra_skills)}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # AI explanation
            exp = explanations.get(role['title'], {})
            if exp:
                st.markdown(f"""
                <div class="ai-insight">
                    🤖 <strong>AI Analysis:</strong> {exp.get('explanation', '')}<br><br>
                    📈 <strong>Skill Gaps:</strong> {exp.get('skill_gaps', 'None identified')}<br>
                    💡 <strong>Growth Tip:</strong> {exp.get('growth_tip', '')}
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # ── Career Insight ──
        if ai_result and ai_result.get('career_insight'):
            st.markdown('<div class="section-header">🧭 Career Development Insight</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="ai-insight">
                🤖 {ai_result['career_insight']}
            </div>
            """, unsafe_allow_html=True)

        # ── Recommended Training ──
        if ai_result and ai_result.get('recommended_training'):
            st.markdown('<div class="section-header">📚 Recommended Training</div>', unsafe_allow_html=True)
            for training in ai_result['recommended_training']:
                st.markdown(f"""
                <div class="skill-gap-card">
                    📖 {training}
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # ── PDF Export ──
        if HAS_FPDF:
            st.markdown('<div class="section-header">📥 Export Report</div>', unsafe_allow_html=True)
            pdf_bytes = generate_pdf_report(employee, top_matches, ai_result)
            if pdf_bytes:
                st.download_button(
                    label="📄 Download Match Report (PDF)",
                    data=pdf_bytes,
                    file_name=f"KARM_Job_Match_{employee['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

    # ── Match Heatmap (always shown) ──
    if HAS_PLOTLY:
        st.markdown('<div class="section-header">🗺️ Employee–Role Match Heatmap</div>', unsafe_allow_html=True)
        st.caption("This heatmap shows match scores (%) between all employees and all open roles. Higher values (greener) indicate better fits.")

        emp_labels = [e['name'] for e in employees]
        role_labels = [r['title'] for r in roles]
        heatmap_data = (sim_matrix * 100).round(1)

        fig_heat = go.Figure(data=go.Heatmap(
            z=heatmap_data,
            x=role_labels,
            y=emp_labels,
            colorscale=[
                [0, '#fff5f5'],
                [0.25, '#fed7d7'],
                [0.5, '#fefcbf'],
                [0.75, '#c6f6d5'],
                [1.0, '#276749']
            ],
            text=heatmap_data,
            texttemplate='%{text}%',
            textfont={"size": 11},
            hovertemplate='<b>%{y}</b> → <b>%{x}</b><br>Match: %{z:.1f}%<extra></extra>',
            colorbar=dict(
                title='Match %',
                ticksuffix='%',
                thickness=15
            )
        ))
        fig_heat.update_layout(
            height=max(400, len(employees) * 45),
            margin=dict(l=20, r=20, t=20, b=80),
            xaxis=dict(title='Open Roles', tickangle=-30),
            yaxis=dict(title='Employees', autorange='reversed'),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    # ── Open Roles Overview ──
    st.markdown('<div class="section-header">📋 Open Roles Overview</div>', unsafe_allow_html=True)
    for role in roles:
        best_match_idx = sim_matrix[:, roles.index(role)].argmax()
        best_match_score = sim_matrix[best_match_idx, roles.index(role)] * 100
        best_match_emp = employees[best_match_idx]

        skills_html = ' '.join([f'<span class="skill-tag skill-extra">{s}</span>' for s in role.get('required_skills', [])])

        st.markdown(f"""
        <div class="match-card" style="border-left-color: #3182ce;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <div>
                    <div class="match-title">{role['title']}</div>
                    <div class="match-dept">🏢 {role['department']} &nbsp;|&nbsp; 📊 {role.get('seniority', 'N/A')} &nbsp;|&nbsp; 📍 {role.get('location', 'N/A')}</div>
                </div>
                <div style="text-align: right;">
                    <span style="font-size: 0.8rem; color: #718096;">Best Candidate:</span><br>
                    <strong style="color: #6b2fa0;">{best_match_emp['name']}</strong>
                    <span style="font-size: 0.85rem; color: #38a169;">({best_match_score:.0f}%)</span>
                </div>
            </div>
            <div style="margin: 0.5rem 0; font-size: 0.88rem; color: #4a5568;">{role.get('description', '')}</div>
            <div style="margin-top: 0.5rem;">{skills_html}</div>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
