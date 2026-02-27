"""
KARM Module 6: Gamified Performance Dashboard
================================================
Turns KPI data into a gamified experience with badges, points, levels,
leaderboards, trend charts, and AI-generated personalized nudges.

Run: streamlit run module6_gamified.py
"""

import streamlit as st
import google.generativeai as genai
import json
import os
import re
import io
import pandas as pd
from datetime import datetime

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
        page_title="KARM - Gamified Performance",
        page_icon="🏆",
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

        /* Leaderboard */
        .lb-row {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 0.9rem 1.2rem;
            margin: 0.4rem 0;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 1px 6px rgba(0,0,0,0.04);
            transition: transform 0.15s, box-shadow 0.15s;
        }
        .lb-row:hover {
            transform: translateX(4px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        }
        .lb-rank {
            font-size: 1.3rem; font-weight: 700; min-width: 40px; text-align: center;
        }
        .lb-rank-1 { color: #d4a017; }
        .lb-rank-2 { color: #a0aec0; }
        .lb-rank-3 { color: #c87533; }
        .lb-name {
            font-weight: 600; font-size: 0.95rem; color: #2d3748; flex: 1; margin-left: 0.75rem;
        }
        .lb-dept {
            font-size: 0.78rem; color: #718096; margin-left: 0.5rem; min-width: 90px;
        }
        .lb-pts {
            font-weight: 700; font-size: 1rem; min-width: 70px; text-align: right;
            background: linear-gradient(135deg, #6b2fa0, #3182ce);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }

        /* Level badges */
        .level-badge {
            display: inline-block; padding: 0.2rem 0.65rem; border-radius: 20px;
            font-weight: 600; font-size: 0.75rem; margin-left: 0.5rem;
        }
        .level-bronze { background: linear-gradient(135deg, #fbd38d, #f6e05e); color: #975a16; border: 1px solid #ecc94b; }
        .level-silver { background: linear-gradient(135deg, #e2e8f0, #cbd5e0); color: #4a5568; border: 1px solid #a0aec0; }
        .level-gold { background: linear-gradient(135deg, #fefcbf, #f6e05e); color: #975a16; border: 1px solid #d69e2e; }
        .level-platinum { background: linear-gradient(135deg, #e9d8fd, #d6bcfa); color: #553c9a; border: 1px solid #b794f4; }

        /* Badge pills */
        .badge-pill {
            display: inline-block; padding: 0.15rem 0.5rem; border-radius: 16px;
            font-size: 0.72rem; font-weight: 500; margin: 0.1rem;
            background: linear-gradient(135deg, #ebf4ff, #e9d8fd);
            border: 1px solid #d6bcfa; color: #553c9a;
        }

        /* Profile card */
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

        /* Points display */
        .points-big {
            font-size: 3rem; font-weight: 700; text-align: center;
            background: linear-gradient(135deg, #6b2fa0, #d69e2e);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }

        /* Badge showcase */
        .badge-showcase {
            background: linear-gradient(135deg, #fffff0, #fefcbf);
            border: 1px solid #f6e05e;
            border-radius: 12px;
            padding: 1rem 1.25rem;
            margin: 0.5rem 0;
            text-align: center;
        }
        .badge-icon { font-size: 2rem; margin: 0.25rem; }

        /* Trend indicator */
        .trend-up { color: #38a169; font-weight: 600; }
        .trend-down { color: #e53e3e; font-weight: 600; }
        .trend-flat { color: #d69e2e; font-weight: 600; }

        /* Podium */
        .podium-card {
            text-align: center; padding: 1.5rem 1rem; border-radius: 14px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
            transition: transform 0.2s;
        }
        .podium-card:hover { transform: translateY(-3px); }
        .podium-gold { background: linear-gradient(135deg, #fffff0, #fefcbf); border: 2px solid #d69e2e; }
        .podium-silver { background: linear-gradient(135deg, #f7fafc, #e2e8f0); border: 2px solid #a0aec0; }
        .podium-bronze { background: linear-gradient(135deg, #fffaf0, #feebc8); border: 2px solid #dd6b20; }
        .podium-name { font-weight: 700; font-size: 1rem; color: #2d3748; margin-top: 0.5rem; }
        .podium-pts { font-weight: 600; font-size: 0.85rem; color: #6b2fa0; }
        .podium-medal { font-size: 2.5rem; }
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


def save_employees(employees):
    """Save updated employee data back to shared data layer."""
    data_path = os.path.join(os.path.dirname(__file__), 'fake_data', 'employees.json')
    with open(data_path, 'w') as f:
        json.dump(employees, f, indent=2)


def load_kpi_data():
    """Load KPI data from CSV."""
    data_path = os.path.join(os.path.dirname(__file__), 'fake_data', 'kpi_data.csv')
    if os.path.exists(data_path):
        df = pd.read_csv(data_path)
        df.columns = df.columns.str.strip()
        return df
    return pd.DataFrame()


# ─────────────────────────────────────────────────────────────
# GAMIFICATION ENGINE
# ─────────────────────────────────────────────────────────────
def calculate_points(kpi_df, emp_id):
    """Compute total gamification points from KPI completion percentages."""
    emp_data = kpi_df[kpi_df['employee_id'] == emp_id]
    if emp_data.empty:
        return 0
    return round(emp_data['completion_percent'].sum(), 1)


def calculate_avg_completion(kpi_df, emp_id):
    """Compute average completion percentage."""
    emp_data = kpi_df[kpi_df['employee_id'] == emp_id]
    if emp_data.empty:
        return 0
    return round(emp_data['completion_percent'].mean(), 1)


def assign_level(points):
    """Assign level based on total points."""
    if points >= 500:
        return ('Platinum', '💎', 'level-platinum')
    elif points >= 400:
        return ('Gold', '🥇', 'level-gold')
    elif points >= 300:
        return ('Silver', '🥈', 'level-silver')
    else:
        return ('Bronze', '🥉', 'level-bronze')


def get_weekly_completions(kpi_df, emp_id):
    """Get weekly completion percentages for an employee."""
    emp_data = kpi_df[kpi_df['employee_id'] == emp_id].sort_values('week')
    return emp_data['completion_percent'].tolist()


def assign_badges(kpi_df, emp_id, all_points=None):
    """Assign earned badges based on KPI achievements."""
    badges = []
    emp_data = kpi_df[kpi_df['employee_id'] == emp_id].sort_values('week')

    if emp_data.empty:
        return badges

    completions = emp_data['completion_percent'].tolist()
    weeks = emp_data['week'].tolist()

    # 🔥 Streak Star — 3+ consecutive weeks above target (>=100%)
    streak = 0
    max_streak = 0
    for c in completions:
        if c >= 100:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0
    if max_streak >= 3:
        badges.append(('🔥', 'Streak Star', f'{max_streak}-week streak above target'))

    # 🎯 Overachiever — Any week >=120% completion
    over_weeks = [w for c, w in zip(completions, weeks) if c >= 120]
    if over_weeks:
        badges.append(('🎯', 'Overachiever', f'Hit 120%+ in {len(over_weeks)} week(s)'))

    # 📈 Trend Setter — Consistent improvement (last 3 weeks trending up)
    if len(completions) >= 3:
        last3 = completions[-3:]
        if last3[0] < last3[1] < last3[2]:
            badges.append(('📈', 'Trend Setter', 'Consistent upward trend'))

    # ⚡ Speed Demon — Highest total points in department
    if all_points:
        dept = emp_data['department'].iloc[0] if 'department' in emp_data.columns else None
        if dept:
            dept_employees = kpi_df[kpi_df['department'] == dept]['employee_id'].unique()
            dept_points = {eid: all_points.get(eid, 0) for eid in dept_employees}
            if dept_points and emp_id == max(dept_points, key=dept_points.get):
                badges.append(('⚡', 'Speed Demon', f'Top performer in {dept}'))

    # 🏆 Top Performer — Overall highest KPI score
    if all_points and emp_id == max(all_points, key=all_points.get):
        badges.append(('🏆', 'Top Performer', 'Highest overall points'))

    # 🌟 Consistent — All weeks at or above target
    if all(c >= 100 for c in completions) and len(completions) >= 3:
        badges.append(('🌟', 'Consistent', 'Never dropped below target'))

    return badges


def get_trend_indicator(kpi_df, emp_id):
    """Determine the trend direction for an employee."""
    completions = get_weekly_completions(kpi_df, emp_id)
    if len(completions) < 2:
        return ('→', 'trend-flat', 'Stable')

    recent = completions[-1]
    previous = completions[-2]
    diff = recent - previous

    if diff > 5:
        return ('↑', 'trend-up', f'+{diff:.0f}%')
    elif diff < -5:
        return ('↓', 'trend-down', f'{diff:.0f}%')
    else:
        return ('→', 'trend-flat', 'Stable')


def build_scoreboard(employees, kpi_df):
    """Build full scoreboard with points, levels, badges, and trends."""
    # First pass: compute all points
    all_points = {}
    for emp in employees:
        emp_id = emp['id']
        pts = calculate_points(kpi_df, emp_id)
        all_points[emp_id] = pts

    # Second pass: build scoreboard with badges (needs all_points for relative badges)
    scoreboard = []
    for emp in employees:
        emp_id = emp['id']
        pts = all_points[emp_id]
        if pts == 0:
            continue  # Skip employees with no KPI data

        avg_comp = calculate_avg_completion(kpi_df, emp_id)
        level_name, level_icon, level_class = assign_level(pts)
        badges = assign_badges(kpi_df, emp_id, all_points)
        trend_arrow, trend_class, trend_text = get_trend_indicator(kpi_df, emp_id)

        scoreboard.append({
            'id': emp_id,
            'name': emp['name'],
            'department': emp.get('department', 'N/A'),
            'role': emp.get('role', 'N/A'),
            'points': pts,
            'avg_completion': avg_comp,
            'level_name': level_name,
            'level_icon': level_icon,
            'level_class': level_class,
            'badges': badges,
            'trend_arrow': trend_arrow,
            'trend_class': trend_class,
            'trend_text': trend_text,
        })

    # Sort by points descending
    scoreboard.sort(key=lambda x: x['points'], reverse=True)
    return scoreboard


# ─────────────────────────────────────────────────────────────
# GEMINI AI NUDGES
# ─────────────────────────────────────────────────────────────
def generate_nudge(api_key, employee, kpi_summary, scoreboard_entry):
    """Use Gemini AI to generate personalized performance nudges."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemma-3-27b-it')

    badges_text = ', '.join([f"{b[0]} {b[1]}" for b in scoreboard_entry['badges']]) if scoreboard_entry['badges'] else 'None yet'

    prompt = f"""You are KARM, an AI-powered gamified performance coach. Generate a personalized, motivational nudge for this employee.

EMPLOYEE PROFILE:
- Name: {employee['name']}
- Role: {employee['role']}
- Department: {employee['department']}
- Current Level: {scoreboard_entry['level_icon']} {scoreboard_entry['level_name']}
- Total Points: {scoreboard_entry['points']}
- Average Completion: {scoreboard_entry['avg_completion']}%
- Trend: {scoreboard_entry['trend_text']}
- Badges Earned: {badges_text}

KPI DATA BY WEEK:
{kpi_summary}

NEXT LEVEL THRESHOLD:
- Bronze: <300 pts → Silver: 300 pts → Gold: 400 pts → Platinum: 500 pts

INSTRUCTIONS:
Generate an encouraging, specific, actionable message. Include:
1. Acknowledge their current achievements
2. Tell them exactly how many points they need for the next level
3. Give one specific tip to improve their KPI
4. Make it feel personal and motivating

Respond ONLY with valid JSON (no markdown, no code fences):
{{
  "nudge_message": "The personalized motivational message (2-3 sentences max)",
  "next_milestone": "What they should aim for next",
  "tip": "One actionable performance tip",
  "celebration": "A short celebratory note about their best achievement"
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
            retry_prompt = prompt + "\n\nCRITICAL: Respond with ONLY valid JSON. No markdown, no code blocks."
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
        '\u2014': '--',
        '\u2013': '-',
        '\u2018': "'",
        '\u2019': "'",
        '\u201c': '"',
        '\u201d': '"',
        '\u2022': '*',
        '\u2026': '...',
        '\u2192': '->',
        '\u00b7': '*',
        '\u2191': '^',    # ↑ up arrow
        '\u2193': 'v',    # ↓ down arrow
        '\u2190': '<-',   # ← left arrow
        '\u00d7': 'x',    # × multiplication
        '\u2713': '[Y]',  # ✓ check mark
        '\u2717': '[X]',  # ✗ cross mark
        '\u00b0': 'deg',  # ° degree
        '\u2265': '>=',   # ≥
        '\u2264': '<=',   # ≤
        '\u2248': '~=',   # ≈
        '\u00ab': '<<',   # «
        '\u00bb': '>>',   # »
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    # Remove emoji and other non-latin1 characters gracefully
    text = text.encode('latin-1', errors='replace').decode('latin-1')
    return text


def generate_pdf_report(scoreboard, selected_entry=None, ai_result=None):
    """Generate a PDF performance report."""
    if not HAS_FPDF:
        return None

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Title
    pdf.set_font('Helvetica', 'B', 20)
    pdf.cell(0, 15, 'KARM Gamified Performance Report', ln=True, align='C')
    pdf.ln(5)

    # Date
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', ln=True, align='C')
    pdf.ln(8)

    # Leaderboard
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, 'Performance Leaderboard', ln=True)
    pdf.ln(3)

    # Table header
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_fill_color(107, 47, 160)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(15, 8, 'Rank', fill=True, align='C')
    pdf.cell(50, 8, 'Name', fill=True)
    pdf.cell(35, 8, 'Department', fill=True)
    pdf.cell(25, 8, 'Points', fill=True, align='C')
    pdf.cell(25, 8, 'Avg %', fill=True, align='C')
    pdf.cell(25, 8, 'Level', fill=True, align='C')
    pdf.cell(15, 8, 'Trend', fill=True, align='C')
    pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Helvetica', '', 9)

    for i, entry in enumerate(scoreboard, 1):
        if i % 2 == 0:
            pdf.set_fill_color(248, 249, 255)
        else:
            pdf.set_fill_color(255, 255, 255)

        pdf.cell(15, 7, f'#{i}', fill=True, align='C')
        pdf.cell(50, 7, sanitize_text(entry['name']), fill=True)
        pdf.cell(35, 7, sanitize_text(entry['department']), fill=True)
        pdf.cell(25, 7, str(entry['points']), fill=True, align='C')
        pdf.cell(25, 7, f"{entry['avg_completion']}%", fill=True, align='C')
        pdf.cell(25, 7, sanitize_text(entry['level_name']), fill=True, align='C')
        pdf.cell(15, 7, sanitize_text(entry['trend_arrow']), fill=True, align='C')
        pdf.ln()

    pdf.ln(5)

    # Individual report if selected
    if selected_entry:
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(0, 10, f'Individual Report: {sanitize_text(selected_entry["name"])}', ln=True)
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 7, f'Department: {sanitize_text(selected_entry["department"])}', ln=True)
        pdf.cell(0, 7, f'Role: {sanitize_text(selected_entry["role"])}', ln=True)
        pdf.cell(0, 7, f'Level: {sanitize_text(selected_entry["level_name"])} | Points: {selected_entry["points"]}', ln=True)
        pdf.cell(0, 7, f'Average Completion: {selected_entry["avg_completion"]}%', ln=True)
        pdf.cell(0, 7, f'Trend: {sanitize_text(selected_entry["trend_text"])}', ln=True)

        if selected_entry['badges']:
            pdf.ln(3)
            pdf.set_font('Helvetica', 'B', 11)
            pdf.cell(0, 8, 'Badges Earned:', ln=True)
            pdf.set_font('Helvetica', '', 10)
            for badge in selected_entry['badges']:
                pdf.cell(0, 7, sanitize_text(f'  {badge[1]} - {badge[2]}'), ln=True)

        pdf.ln(3)

    # AI Insights
    if ai_result:
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(0, 10, 'AI Performance Coach Insights', ln=True)

        if ai_result.get('nudge_message'):
            pdf.set_font('Helvetica', 'I', 10)
            pdf.multi_cell(0, 6, sanitize_text(ai_result['nudge_message']))
            pdf.ln(2)
        if ai_result.get('next_milestone'):
            pdf.set_font('Helvetica', '', 10)
            pdf.cell(0, 7, sanitize_text(f'Next Milestone: {ai_result["next_milestone"]}'), ln=True)
        if ai_result.get('tip'):
            pdf.cell(0, 7, sanitize_text(f'Performance Tip: {ai_result["tip"]}'), ln=True)
        if ai_result.get('celebration'):
            pdf.set_font('Helvetica', 'I', 10)
            pdf.set_text_color(39, 103, 73)
            pdf.cell(0, 7, sanitize_text(ai_result['celebration']), ln=True)
            pdf.set_text_color(0, 0, 0)

    # Footer
    pdf.ln(10)
    pdf.set_font('Helvetica', 'I', 9)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 8, 'This report was generated by KARM AI-Powered HR Automation System.', ln=True, align='C')
    pdf.cell(0, 8, 'For internal use only.', ln=True, align='C')

    # Output to BytesIO buffer
    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()


# ─────────────────────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────────────────────
def main():
    setup_page()

    # ── Header ──
    st.markdown("""
    <div class="main-header">
        <h1>🏆 KARM Gamified Performance Dashboard</h1>
        <p>Turn boring KPIs into an engaging experience — earn badges, climb levels, and get AI-powered performance coaching.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Load Data ──
    employees = load_employees()
    kpi_df = load_kpi_data()

    if not employees:
        st.error("❌ Could not load employees.json from fake_data/")
        return
    if kpi_df.empty:
        st.error("❌ Could not load kpi_data.csv from fake_data/")
        return

    # ── Build Scoreboard ──
    scoreboard = build_scoreboard(employees, kpi_df)

    if not scoreboard:
        st.error("❌ No KPI data found for any employees.")
        return

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
            st.info("ℹ️ Add API key for AI nudges")

        st.markdown("---")

        # Department filter
        st.markdown("### 🏢 Filter by Department")
        departments = ['All'] + sorted(set(e['department'] for e in scoreboard))
        selected_dept = st.selectbox("Department", departments)

        st.markdown("---")

        # Employee selector
        st.markdown("### 👤 Select Employee")
        filtered_scoreboard = scoreboard if selected_dept == 'All' else [e for e in scoreboard if e['department'] == selected_dept]
        emp_names = [f"{e['name']} ({e['id']})" for e in filtered_scoreboard]
        if emp_names:
            selected_emp = st.selectbox("Choose an employee", options=emp_names)
            selected_idx = emp_names.index(selected_emp)
            selected_entry = filtered_scoreboard[selected_idx]
        else:
            st.warning("No employees in this department")
            selected_entry = None

        st.markdown("---")
        st.markdown("""
        <div class="sidebar-info">
            <strong>📖 How scoring works:</strong><br>
            Points = Sum of weekly completion percentages.<br>
            <strong>Levels:</strong> Bronze (<300) → Silver (300) → Gold (400) → Platinum (500+)<br>
            <strong>Badges:</strong> Earned for streaks, overachievement, and trends.
        </div>
        """, unsafe_allow_html=True)

    # ── KPI Summary Row ──
    total_active = len(scoreboard)
    avg_pts = sum(e['points'] for e in scoreboard) / total_active if total_active else 0
    top_performer = scoreboard[0] if scoreboard else None
    total_badges = sum(len(e['badges']) for e in scoreboard)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Active Employees</div>
            <div class="kpi-value">{total_active}</div>
            <div class="kpi-sub">With KPI data</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Avg Points</div>
            <div class="kpi-value">{avg_pts:.0f}</div>
            <div class="kpi-sub">Across all employees</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        if top_performer:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">🏆 Top Performer</div>
                <div class="kpi-value" style="font-size: 1.5rem;">{top_performer['name']}</div>
                <div class="kpi-sub">{top_performer['points']} pts — {top_performer['level_icon']} {top_performer['level_name']}</div>
            </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Badges Earned</div>
            <div class="kpi-value">{total_badges}</div>
            <div class="kpi-sub">Across all employees</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Podium (Top 3) ──
    st.markdown('<div class="section-header">🥇 Top 3 Podium</div>', unsafe_allow_html=True)
    podium_cols = st.columns([1, 1.3, 1])
    podium_styles = [
        ('podium-silver', '🥈', '2nd'),
        ('podium-gold', '🥇', '1st'),
        ('podium-bronze', '🥉', '3rd')
    ]
    podium_order = [1, 0, 2]  # Display: 2nd, 1st, 3rd

    for col_idx, display_idx in enumerate(podium_order):
        if display_idx < len(filtered_scoreboard):
            entry = filtered_scoreboard[display_idx]
            style_class, medal, label = podium_styles[display_idx]
            height = "min-height: 180px;" if display_idx == 0 else "min-height: 150px; margin-top: 30px;"
            with podium_cols[col_idx]:
                badge_html = ' '.join([f'<span class="badge-pill">{b[0]} {b[1]}</span>' for b in entry['badges'][:3]])
                st.markdown(f"""
                <div class="podium-card {style_class}" style="{height}">
                    <div class="podium-medal">{medal}</div>
                    <div class="podium-name">{entry['name']}</div>
                    <div class="podium-pts">{entry['points']} pts — {entry['level_icon']} {entry['level_name']}</div>
                    <div style="margin-top: 0.5rem; font-size: 0.78rem; color: #718096;">{entry['department']}</div>
                    <div style="margin-top: 0.4rem;">{badge_html}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Leaderboard ──
    st.markdown('<div class="section-header">📊 Full Leaderboard</div>', unsafe_allow_html=True)

    for i, entry in enumerate(filtered_scoreboard, 1):
        rank_class = f'lb-rank-{i}' if i <= 3 else ''
        rank_display = ['🥇', '🥈', '🥉'][i-1] if i <= 3 else f'#{i}'
        level_html = f'<span class="level-badge {entry["level_class"]}">{entry["level_icon"]} {entry["level_name"]}</span>'
        badges_html = ' '.join([f'<span class="badge-pill">{b[0]} {b[1]}</span>' for b in entry['badges']])
        trend_html = f'<span class="{entry["trend_class"]}">{entry["trend_arrow"]} {entry["trend_text"]}</span>'

        st.markdown(f"""
        <div class="lb-row">
            <div class="lb-rank {rank_class}">{rank_display}</div>
            <div class="lb-name">
                {entry['name']} {level_html}
                <div style="margin-top: 0.25rem;">{badges_html}</div>
            </div>
            <div class="lb-dept">{entry['department']}<br>{trend_html}</div>
            <div class="lb-pts">{entry['points']} pts</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Individual Employee Detail ──
    if selected_entry:
        st.markdown(f'<div class="section-header">👤 {selected_entry["name"]} — Detailed Performance</div>', unsafe_allow_html=True)

        detail_col1, detail_col2 = st.columns([1, 2])

        with detail_col1:
            # Profile card
            badge_icons = ' '.join([f'<span class="badge-icon">{b[0]}</span>' for b in selected_entry['badges']])
            st.markdown(f"""
            <div class="profile-card">
                <div class="profile-name">{selected_entry['name']}</div>
                <div class="profile-role">{selected_entry['role']}</div>
                <div class="profile-detail">🏢 {selected_entry['department']}</div>
                <div style="margin: 1rem 0;">
                    <div class="points-big">{selected_entry['points']}</div>
                    <div style="text-align: center; font-size: 0.85rem; color: #718096;">Total Points</div>
                </div>
                <div style="text-align: center;">
                    <span class="level-badge {selected_entry['level_class']}" style="font-size: 0.9rem; padding: 0.35rem 1rem;">
                        {selected_entry['level_icon']} {selected_entry['level_name']}
                    </span>
                </div>
                <div style="text-align: center; margin-top: 0.5rem;">
                    <span class="{selected_entry['trend_class']}" style="font-size: 0.95rem;">
                        {selected_entry['trend_arrow']} {selected_entry['trend_text']}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Badge showcase
            if selected_entry['badges']:
                st.markdown(f"""
                <div class="badge-showcase" style="margin-top: 0.75rem;">
                    <div style="font-weight: 600; font-size: 0.85rem; color: #975a16; margin-bottom: 0.5rem;">🏅 Badges Earned</div>
                    <div>{badge_icons}</div>
                </div>
                """, unsafe_allow_html=True)
                for badge in selected_entry['badges']:
                    st.markdown(f"""
                    <div style="background: #f7fafc; border-radius: 8px; padding: 0.4rem 0.75rem; margin: 0.2rem 0; font-size: 0.8rem;">
                        {badge[0]} <strong>{badge[1]}</strong> — {badge[2]}
                    </div>
                    """, unsafe_allow_html=True)

        with detail_col2:
            emp_kpi = kpi_df[kpi_df['employee_id'] == selected_entry['id']].sort_values('week')

            if HAS_PLOTLY and not emp_kpi.empty:
                # Weekly Completion Trend
                fig_trend = go.Figure()
                fig_trend.add_trace(go.Scatter(
                    x=emp_kpi['week'],
                    y=emp_kpi['completion_percent'],
                    mode='lines+markers',
                    name='Completion %',
                    line=dict(color='#6b2fa0', width=3),
                    marker=dict(size=8, color='#6b2fa0', line=dict(width=2, color='white')),
                    fill='tozeroy',
                    fillcolor='rgba(107, 47, 160, 0.1)'
                ))
                fig_trend.add_hline(
                    y=100, line_dash="dash", line_color="#38a169",
                    annotation_text="Target (100%)", annotation_position="top left"
                )
                fig_trend.update_layout(
                    title=dict(text="📈 Weekly Completion Trend", font=dict(size=14)),
                    xaxis_title="Week", yaxis_title="Completion %",
                    template="plotly_white", height=300,
                    margin=dict(l=40, r=20, t=50, b=40),
                    font=dict(family="Inter")
                )
                st.plotly_chart(fig_trend, use_container_width=True)

                # Target vs Actual bar chart
                fig_bar = go.Figure()
                fig_bar.add_trace(go.Bar(
                    x=emp_kpi['week'], y=emp_kpi['target'],
                    name='Target', marker_color='#e2e8f0',
                    text=emp_kpi['target'], textposition='auto'
                ))
                fig_bar.add_trace(go.Bar(
                    x=emp_kpi['week'], y=emp_kpi['actual'],
                    name='Actual', marker_color='#6b2fa0',
                    text=emp_kpi['actual'], textposition='auto'
                ))
                fig_bar.update_layout(
                    title=dict(text=f"🎯 Target vs Actual — {emp_kpi['metric_name'].iloc[0]}", font=dict(size=14)),
                    xaxis_title="Week", yaxis_title="Value",
                    barmode='group', template="plotly_white", height=300,
                    margin=dict(l=40, r=20, t=50, b=40),
                    font=dict(family="Inter"),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            elif not HAS_PLOTLY:
                st.info("📊 Install plotly for interactive charts: pip install plotly")

        st.markdown("---")

        # ── AI Nudge Section ──
        st.markdown('<div class="section-header">🤖 AI Performance Coach</div>', unsafe_allow_html=True)

        nudge_col1, nudge_col2 = st.columns([3, 1])
        with nudge_col2:
            nudge_clicked = st.button(
                "🚀 Get AI Nudge",
                use_container_width=True,
                type="primary",
                disabled=not api_key
            )

        if not api_key:
            with nudge_col1:
                st.info("🔑 Enter your Gemini API key in the sidebar to get personalized AI coaching.")

        if nudge_clicked and api_key:
            # Build KPI summary text
            emp_kpi_data = kpi_df[kpi_df['employee_id'] == selected_entry['id']].sort_values('week')
            kpi_lines = []
            for _, row in emp_kpi_data.iterrows():
                kpi_lines.append(f"  {row['week']}: {row['metric_name']} — Target: {row['target']}, Actual: {row['actual']}, Completion: {row['completion_percent']}%")
            kpi_summary = '\n'.join(kpi_lines)

            # Find employee record
            employee = next((e for e in employees if e['id'] == selected_entry['id']), None)
            if employee:
                with st.spinner("🤖 Generating personalized performance coaching..."):
                    ai_result = generate_nudge(api_key, employee, kpi_summary, selected_entry)

                if ai_result:
                    st.session_state['ai_nudge_result'] = ai_result
                    st.session_state['ai_nudge_emp'] = selected_entry['id']
                else:
                    st.warning("⚠️ Could not generate AI nudge. Please try again.")

        # Display stored nudge result
        if st.session_state.get('ai_nudge_emp') == selected_entry['id'] and st.session_state.get('ai_nudge_result'):
            ai_result = st.session_state['ai_nudge_result']

            st.markdown(f"""
            <div class="ai-insight">
                💬 <strong>Personalized Nudge:</strong> {ai_result.get('nudge_message', '')}<br><br>
                🎯 <strong>Next Milestone:</strong> {ai_result.get('next_milestone', '')}<br>
                💡 <strong>Performance Tip:</strong> {ai_result.get('tip', '')}<br>
                🎉 <strong>Celebration:</strong> {ai_result.get('celebration', '')}
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # ── PDF Export ──
        st.markdown('<div class="section-header">📥 Export Report</div>', unsafe_allow_html=True)

        if HAS_FPDF:
            try:
                ai_nudge = st.session_state.get('ai_nudge_result') if st.session_state.get('ai_nudge_emp') == selected_entry['id'] else None
                pdf_bytes = generate_pdf_report(scoreboard, selected_entry, ai_nudge)
                if pdf_bytes:
                    file_name = f"KARM_Performance_{selected_entry['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
                    st.download_button(
                        label="📄 Download Performance Report (PDF)",
                        data=pdf_bytes,
                        file_name=file_name,
                        mime="application/pdf",
                        use_container_width=True,
                        key=f"pdf_download_{selected_entry['id']}"
                    )
                else:
                    st.error("❌ Failed to generate PDF report.")
            except Exception as e:
                st.error(f"❌ Error generating PDF: {str(e)}")
        else:
            st.info("📦 Install fpdf2 for PDF export: pip install fpdf2")

    # ── Department Analytics ──
    if HAS_PLOTLY:
        st.markdown('<div class="section-header">🏢 Department Analytics</div>', unsafe_allow_html=True)

        dept_col1, dept_col2 = st.columns(2)

        with dept_col1:
            # Average points by department
            dept_data = {}
            for entry in scoreboard:
                dept = entry['department']
                if dept not in dept_data:
                    dept_data[dept] = []
                dept_data[dept].append(entry['points'])

            dept_names = list(dept_data.keys())
            dept_avg = [sum(v)/len(v) for v in dept_data.values()]
            dept_colors = ['#6b2fa0', '#3182ce', '#38a169', '#d69e2e', '#e53e3e']

            fig_dept = go.Figure()
            fig_dept.add_trace(go.Bar(
                x=dept_names, y=dept_avg,
                marker_color=dept_colors[:len(dept_names)],
                text=[f'{v:.0f}' for v in dept_avg],
                textposition='auto'
            ))
            fig_dept.update_layout(
                title=dict(text="Average Points by Department", font=dict(size=14)),
                xaxis_title="Department", yaxis_title="Avg Points",
                template="plotly_white", height=350,
                font=dict(family="Inter")
            )
            st.plotly_chart(fig_dept, use_container_width=True)

        with dept_col2:
            # Level distribution
            level_counts = {'Bronze': 0, 'Silver': 0, 'Gold': 0, 'Platinum': 0}
            for entry in scoreboard:
                level_counts[entry['level_name']] += 1

            level_colors = {'Bronze': '#d69e2e', 'Silver': '#a0aec0', 'Gold': '#f6e05e', 'Platinum': '#b794f4'}

            fig_levels = go.Figure()
            fig_levels.add_trace(go.Pie(
                labels=list(level_counts.keys()),
                values=list(level_counts.values()),
                marker_colors=[level_colors[l] for l in level_counts.keys()],
                hole=0.4,
                textinfo='label+value',
                textfont=dict(size=12)
            ))
            fig_levels.update_layout(
                title=dict(text="Level Distribution", font=dict(size=14)),
                template="plotly_white", height=350,
                font=dict(family="Inter"),
                showlegend=False
            )
            st.plotly_chart(fig_levels, use_container_width=True)

    # ── Save KPI Scores Back ──
    for entry in scoreboard:
        for emp in employees:
            if emp['id'] == entry['id']:
                emp['kpi_score'] = entry['avg_completion']
                break
    save_employees(employees)


if __name__ == "__main__":
    main()
