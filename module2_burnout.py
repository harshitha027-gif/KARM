"""
KARM Module 2: Employee Burnout Risk Dashboard
================================================
Analyzes employee communication data and scores burnout risk 0–10.
Dashboard shows red/yellow/green risk levels with AI-powered insights.

Run: streamlit run module2_burnout.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
import json
import os
import numpy as np
from datetime import datetime

# ─────────────────────────────────────────────────────────────
# CONFIG & THEME
# ─────────────────────────────────────────────────────────────
def setup_page():
    st.set_page_config(
        page_title="KARM - Burnout Dashboard",
        page_icon="🔥",
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
            background: linear-gradient(135deg, #6b2fa0, #e53e3e);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .kpi-label { font-size: 0.85rem; color: #718096; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
        .kpi-sub { font-size: 0.75rem; color: #a0aec0; margin-top: 0.3rem; }
        
        /* Risk badges */
        .risk-high { background: linear-gradient(135deg, #fed7d7, #fff5f5); border: 1px solid #fc8181; color: #c53030; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: 600; font-size: 0.8rem; display: inline-block; }
        .risk-medium { background: linear-gradient(135deg, #fefcbf, #fffff0); border: 1px solid #f6e05e; color: #b7791f; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: 600; font-size: 0.8rem; display: inline-block; }
        .risk-low { background: linear-gradient(135deg, #c6f6d5, #f0fff4); border: 1px solid #68d391; color: #276749; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: 600; font-size: 0.8rem; display: inline-block; }
        
        /* Employee detail card */
        .detail-card {
            background: linear-gradient(135deg, #f7fafc, #edf2f7);
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 1.5rem;
            margin: 0.5rem 0;
        }
        .detail-card h3 { margin: 0 0 0.5rem 0; color: #2d3748; }
        
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

        /* Table styling */
        .employee-row {
            padding: 0.8rem 1rem; border-radius: 10px; margin: 0.4rem 0;
            display: flex; align-items: center; justify-content: space-between;
            transition: transform 0.15s;
        }
        .employee-row:hover { transform: translateX(4px); }
        .row-high { background: linear-gradient(135deg, #fff5f5, #fed7d7); border-left: 4px solid #e53e3e; }
        .row-medium { background: linear-gradient(135deg, #fffff0, #fefcbf); border-left: 4px solid #d69e2e; }
        .row-low { background: linear-gradient(135deg, #f0fff4, #c6f6d5); border-left: 4px solid #38a169; }
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
    """Write updated employee data back to shared data layer."""
    data_path = os.path.join(os.path.dirname(__file__), 'fake_data', 'employees.json')
    with open(data_path, 'w') as f:
        json.dump(employees, f, indent=2)


def load_communications():
    """Load communication data from CSV."""
    data_path = os.path.join(os.path.dirname(__file__), 'fake_data', 'communications_data.csv')
    if os.path.exists(data_path):
        df = pd.read_csv(data_path)
        # Clean column names (strip whitespace)
        df.columns = df.columns.str.strip()
        return df
    return pd.DataFrame()


# ─────────────────────────────────────────────────────────────
# BURNOUT SCORE COMPUTATION
# ─────────────────────────────────────────────────────────────
HIGH_SEVERITY_KEYWORDS = {'burnout', 'quitting', 'quit', 'leaving', 'hate', 'cant-cope',
                          'want-to-quit', 'miserable', 'done', 'breaking'}
MEDIUM_SEVERITY_KEYWORDS = {'stressed', 'exhausted', 'overwhelmed', 'frustrated', 'overworked',
                            'drowning', 'no-support', 'overloaded', 'insomnia'}
LOW_SEVERITY_KEYWORDS = {'tired', 'pressure', 'deadline', 'targets', 'help'}


def compute_burnout_for_employee(emp_df):
    """
    Compute a burnout risk score (0–10) for one employee from their multi-week data.
    Uses a weighted formula across 6 signals.
    """
    emp_df = emp_df.sort_values('week')
    weeks = emp_df['week'].tolist()
    sentiments = emp_df['sentiment_score'].tolist()
    msg_counts = emp_df['message_count'].tolist()
    after_hours = emp_df['after_hours_messages'].tolist()
    response_times = emp_df['avg_response_time_hours'].tolist()
    leave_reqs = emp_df['leave_requests'].tolist()
    keywords_list = emp_df['flagged_keywords'].fillna('').tolist()

    # ── Signal 1: Sentiment Decline (25%) ──
    if len(sentiments) >= 2:
        sent_decline = sentiments[0] - sentiments[-1]  # positive = declining
        sent_score = min(max(sent_decline / 0.5, 0), 1)  # 0.5 drop → max score
    else:
        sent_score = 0

    # ── Signal 2: After-Hours Ratio (20%) ──
    total_msgs = sum(msg_counts)
    total_after = sum(after_hours)
    if total_msgs > 0:
        ah_ratio = total_after / total_msgs
        ah_score = min(ah_ratio / 0.25, 1)  # 25% after-hours → max score
    else:
        ah_score = 0

    # ── Signal 3: Keyword Severity (20%) ──
    all_keywords = []
    for kw_str in keywords_list:
        if kw_str:
            all_keywords.extend([k.strip().lower() for k in kw_str.split(';') if k.strip()])

    kw_weight = 0
    for kw in all_keywords:
        if kw in HIGH_SEVERITY_KEYWORDS:
            kw_weight += 3
        elif kw in MEDIUM_SEVERITY_KEYWORDS:
            kw_weight += 2
        elif kw in LOW_SEVERITY_KEYWORDS:
            kw_weight += 1
    kw_score = min(kw_weight / 12, 1)  # 12 points → max score

    # ── Signal 4: Response Time Increase (15%) ──
    if len(response_times) >= 2:
        rt_increase = response_times[-1] - response_times[0]
        rt_score = min(max(rt_increase / 2.0, 0), 1)  # 2hr increase → max
    else:
        rt_score = 0

    # ── Signal 5: Leave Requests Spike (10%) ──
    total_leaves = sum(leave_reqs)
    leave_score = min(total_leaves / 5, 1)  # 5 requests → max score

    # ── Signal 6: Message Volume Surge (10%) ──
    if msg_counts[0] > 0:
        vol_surge = (msg_counts[-1] - msg_counts[0]) / msg_counts[0]
        vol_score = min(max(vol_surge / 0.6, 0), 1)  # 60% increase → max
    else:
        vol_score = 0

    # ── Weighted Total ──
    burnout_score = (
        sent_score * 0.25 +
        ah_score * 0.20 +
        kw_score * 0.20 +
        rt_score * 0.15 +
        leave_score * 0.10 +
        vol_score * 0.10
    ) * 10  # Scale to 0–10

    burnout_score = round(min(max(burnout_score, 0), 10), 1)

    return {
        'burnout_score': burnout_score,
        'sentiment_decline': round(sentiments[0] - sentiments[-1], 3) if len(sentiments) >= 2 else 0,
        'after_hours_ratio': round(total_after / total_msgs, 3) if total_msgs > 0 else 0,
        'keyword_count': len(all_keywords),
        'keywords': all_keywords,
        'response_time_increase': round(response_times[-1] - response_times[0], 2) if len(response_times) >= 2 else 0,
        'total_leave_requests': total_leaves,
        'volume_surge_pct': round(((msg_counts[-1] - msg_counts[0]) / msg_counts[0]) * 100, 1) if msg_counts[0] > 0 else 0,
        'sentiments': sentiments,
        'after_hours': after_hours,
        'msg_counts': msg_counts,
        'response_times': response_times,
        'weeks': weeks,
        'signal_scores': {
            'Sentiment Decline': round(sent_score * 10, 1),
            'After-Hours Work': round(ah_score * 10, 1),
            'Keyword Severity': round(kw_score * 10, 1),
            'Response Time': round(rt_score * 10, 1),
            'Leave Requests': round(leave_score * 10, 1),
            'Volume Surge': round(vol_score * 10, 1),
        }
    }


def get_risk_level(score):
    """Classify risk level from burnout score."""
    if score >= 6.1:
        return 'High'
    elif score >= 3.1:
        return 'Medium'
    else:
        return 'Low'


def get_risk_emoji(level):
    return {'High': '🔴', 'Medium': '🟡', 'Low': '🟢'}.get(level, '⚪')


def get_risk_color(level):
    return {'High': '#e53e3e', 'Medium': '#d69e2e', 'Low': '#38a169'}.get(level, '#718096')


# ─────────────────────────────────────────────────────────────
# GEMINI AI ANALYSIS
# ─────────────────────────────────────────────────────────────
def get_ai_insight(api_key, emp_name, department, role, metrics):
    """Get AI-generated burnout analysis and recommendations."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemma-3-27b-it')

    prompt = f"""You are KARM, an AI HR wellness analyst. Analyze this employee's burnout risk data and provide:
1. A concise 2-3 sentence assessment of their current state.
2. Two specific, actionable recommendations for their manager.

EMPLOYEE: {emp_name}
DEPARTMENT: {department}
ROLE: {role}
BURNOUT SCORE: {metrics['burnout_score']}/10 ({get_risk_level(metrics['burnout_score'])} Risk)
SENTIMENT TREND: Started at {metrics['sentiments'][0]}, now {metrics['sentiments'][-1]} (decline of {metrics['sentiment_decline']})
AFTER-HOURS MESSAGES: {sum(metrics['after_hours'])} total ({metrics['after_hours_ratio']*100:.1f}% of all messages)
FLAGGED KEYWORDS: {', '.join(metrics['keywords']) if metrics['keywords'] else 'None'}
RESPONSE TIME CHANGE: +{metrics['response_time_increase']} hours
LEAVE REQUESTS: {metrics['total_leave_requests']} in 4 weeks
MESSAGE VOLUME SURGE: {metrics['volume_surge_pct']}%

Be direct, professional, and empathetic. No fluff. No "As an AI" phrasing. Use the employee's first name."""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Could not generate AI insight: {str(e)}"


# ─────────────────────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────────────────────
def main():
    setup_page()

    # ── Header ──
    st.markdown("""
    <div class="main-header">
        <h1>🔥 KARM Burnout Risk Dashboard</h1>
        <p>AI-powered analysis of employee communication patterns to detect burnout risk before it's too late.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Load Data ──
    employees = load_employees()
    comm_df = load_communications()

    if comm_df.empty:
        st.error("❌ Could not load communications_data.csv. Make sure fake_data/ folder exists.")
        return
    if not employees:
        st.error("❌ Could not load employees.json. Make sure fake_data/ folder exists.")
        return

    # ── Compute Burnout Scores ──
    emp_metrics = {}
    for emp_id in comm_df['employee_id'].unique():
        emp_data = comm_df[comm_df['employee_id'] == emp_id]
        emp_name = emp_data['employee_name'].iloc[0].strip()
        metrics = compute_burnout_for_employee(emp_data)
        emp_metrics[emp_id] = {**metrics, 'name': emp_name, 'id': emp_id}

    # Enrich with employee info
    emp_lookup = {e['id']: e for e in employees}
    for emp_id, m in emp_metrics.items():
        info = emp_lookup.get(emp_id, {})
        m['department'] = info.get('department', 'Unknown')
        m['role'] = info.get('role', 'Unknown')
        m['risk_level'] = get_risk_level(m['burnout_score'])
        m['manager'] = info.get('manager', 'N/A')

    # Write burnout scores back to employees.json
    updated = False
    for emp in employees:
        if emp['id'] in emp_metrics:
            emp['burnout_score'] = emp_metrics[emp['id']]['burnout_score']
            updated = True
    if updated:
        save_employees(employees)

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
            st.info("ℹ️ Add API key for AI insights")

        st.markdown("---")

        # Department filter
        st.markdown("### 🏢 Filters")
        departments = sorted(set(m['department'] for m in emp_metrics.values()))
        selected_dept = st.multiselect("Department", departments, default=departments)

        # Risk filter
        risk_levels = ['High', 'Medium', 'Low']
        selected_risk = st.multiselect("Risk Level", risk_levels, default=risk_levels)

        st.markdown("---")

        # Export
        st.markdown("### 📥 Export")
        if st.button("📊 Download CSV Report", use_container_width=True):
            export_data = []
            for m in emp_metrics.values():
                export_data.append({
                    'Employee ID': m['id'],
                    'Name': m['name'],
                    'Department': m['department'],
                    'Role': m['role'],
                    'Burnout Score': m['burnout_score'],
                    'Risk Level': m['risk_level'],
                    'Sentiment Decline': m['sentiment_decline'],
                    'After-Hours Ratio': f"{m['after_hours_ratio']*100:.1f}%",
                    'Flagged Keywords': '; '.join(m['keywords']),
                    'Leave Requests': m['total_leave_requests'],
                    'Manager': m['manager'],
                })
            export_df = pd.DataFrame(export_data)
            csv = export_df.to_csv(index=False)
            st.download_button(
                "⬇️ Download", csv, "burnout_report.csv", "text/csv",
                use_container_width=True
            )

        st.markdown("---")
        st.markdown("""
        <div class="sidebar-info">
            <strong>📖 How it works:</strong><br>
            Burnout risk is scored 0–10 using 6 weighted signals from communication data:
            sentiment decline, after-hours work, keyword severity, response times,
            leave requests, and message volume surge.
        </div>
        """, unsafe_allow_html=True)

    # ── Apply Filters ──
    filtered = {k: v for k, v in emp_metrics.items()
                if v['department'] in selected_dept and v['risk_level'] in selected_risk}

    if not filtered:
        st.warning("No employees match the selected filters.")
        return

    # ── KPI Summary Row ──
    all_scores = [m['burnout_score'] for m in filtered.values()]
    high_count = sum(1 for m in filtered.values() if m['risk_level'] == 'High')
    med_count = sum(1 for m in filtered.values() if m['risk_level'] == 'Medium')
    avg_score = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Employees</div>
            <div class="kpi-value">{len(filtered)}</div>
            <div class="kpi-sub">Currently monitored</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">🔴 High Risk</div>
            <div class="kpi-value" style="background: linear-gradient(135deg, #e53e3e, #c53030); -webkit-background-clip: text;">{high_count}</div>
            <div class="kpi-sub">Need immediate attention</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">🟡 Medium Risk</div>
            <div class="kpi-value" style="background: linear-gradient(135deg, #d69e2e, #b7791f); -webkit-background-clip: text;">{med_count}</div>
            <div class="kpi-sub">Watch closely</div>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Avg Burnout Score</div>
            <div class="kpi-value">{avg_score}</div>
            <div class="kpi-sub">Organization-wide</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts Row ──
    chart_col1, chart_col2 = st.columns([1, 1])

    with chart_col1:
        st.markdown('<div class="section-header">📊 Risk Distribution</div>', unsafe_allow_html=True)
        risk_counts = {'High': 0, 'Medium': 0, 'Low': 0}
        for m in filtered.values():
            risk_counts[m['risk_level']] += 1

        fig_donut = go.Figure(data=[go.Pie(
            labels=list(risk_counts.keys()),
            values=list(risk_counts.values()),
            hole=0.55,
            marker_colors=['#e53e3e', '#d69e2e', '#38a169'],
            textinfo='label+value',
            textfont_size=14,
            hovertemplate='<b>%{label}</b><br>%{value} employees<br>%{percent}<extra></extra>'
        )])
        fig_donut.update_layout(
            showlegend=False, height=320,
            margin=dict(l=20, r=20, t=20, b=20),
            annotations=[dict(text=f'{len(filtered)}', x=0.5, y=0.5,
                              font_size=28, font_color='#2d3748', showarrow=False)],
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with chart_col2:
        st.markdown('<div class="section-header">🏢 Department Burnout Heatmap</div>', unsafe_allow_html=True)
        dept_scores = {}
        for m in filtered.values():
            dept_scores.setdefault(m['department'], []).append(m['burnout_score'])
        dept_avg = {d: round(sum(s)/len(s), 1) for d, s in dept_scores.items()}

        fig_bar = go.Figure(data=[go.Bar(
            x=list(dept_avg.values()),
            y=list(dept_avg.keys()),
            orientation='h',
            marker=dict(
                color=list(dept_avg.values()),
                colorscale=[[0, '#38a169'], [0.5, '#d69e2e'], [1, '#e53e3e']],
                cmin=0, cmax=10,
                line=dict(width=0)
            ),
            text=[f'{v}/10' for v in dept_avg.values()],
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Avg Score: %{x}/10<extra></extra>'
        )])
        fig_bar.update_layout(
            height=320, margin=dict(l=20, r=60, t=20, b=20),
            xaxis=dict(range=[0, 11], title='Average Burnout Score', gridcolor='rgba(0,0,0,0.05)'),
            yaxis=dict(title=''),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # ── Sentiment Trends All Employees ──
    st.markdown('<div class="section-header">📈 Weekly Sentiment Trends (All Employees)</div>', unsafe_allow_html=True)
    fig_trends = go.Figure()
    for emp_id, m in filtered.items():
        color = get_risk_color(m['risk_level'])
        fig_trends.add_trace(go.Scatter(
            x=m['weeks'], y=m['sentiments'],
            mode='lines+markers', name=m['name'],
            line=dict(color=color, width=2.5),
            marker=dict(size=7),
            hovertemplate=f'<b>{m["name"]}</b><br>Week: %{{x}}<br>Sentiment: %{{y}}<extra></extra>'
        ))
    fig_trends.update_layout(
        height=350, margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title='Week', yaxis_title='Sentiment Score (0–1)',
        yaxis=dict(range=[0, 1]),
        legend=dict(orientation='h', yanchor='bottom', y=-0.35, xanchor='center', x=0.5),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(gridcolor='rgba(0,0,0,0.05)'),
        yaxis_gridcolor='rgba(0,0,0,0.05)'
    )
    st.plotly_chart(fig_trends, use_container_width=True)

    st.markdown("---")

    # ── Employee Risk Table ──
    st.markdown('<div class="section-header">👥 Employee Risk Overview</div>', unsafe_allow_html=True)

    # Sort by burnout score descending
    sorted_employees = sorted(filtered.values(), key=lambda x: x['burnout_score'], reverse=True)

    for m in sorted_employees:
        risk = m['risk_level']
        emoji = get_risk_emoji(risk)
        css_class = f'row-{risk.lower()}'
        kw_display = ', '.join(m['keywords'][-3:]) if m['keywords'] else '—'

        st.markdown(f"""
        <div class="employee-row {css_class}">
            <div style="flex: 2;">
                <strong>{emoji} {m['name']}</strong>
                <span style="color: #718096; font-size: 0.8rem; margin-left: 0.5rem;">{m['role']}</span>
            </div>
            <div style="flex: 1; text-align: center; color: #718096; font-size: 0.85rem;">{m['department']}</div>
            <div style="flex: 1; text-align: center;">
                <strong style="font-size: 1.2rem; color: {get_risk_color(risk)};">{m['burnout_score']}</strong>
                <span style="color: #a0aec0; font-size: 0.75rem;">/10</span>
            </div>
            <div style="flex: 1; text-align: center;">
                <span class="risk-{risk.lower()}">{risk} Risk</span>
            </div>
            <div style="flex: 1.5; text-align: right; color: #718096; font-size: 0.8rem;">{kw_display}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Employee Detail Panel ──
    st.markdown('<div class="section-header">🔍 Employee Deep Dive</div>', unsafe_allow_html=True)

    emp_names = [f"{get_risk_emoji(m['risk_level'])} {m['name']} — Score: {m['burnout_score']}/10"
                 for m in sorted_employees]
    selected_idx = st.selectbox("Select an employee for detailed analysis", range(len(emp_names)),
                                format_func=lambda i: emp_names[i])

    selected = sorted_employees[selected_idx]

    # Info row
    info_col1, info_col2, info_col3 = st.columns(3)
    with info_col1:
        st.markdown(f"""
        <div class="detail-card">
            <h3>👤 {selected['name']}</h3>
            <p style="color:#718096; margin:0;">{selected['role']} • {selected['department']}</p>
            <p style="color:#718096; margin:0.3rem 0 0 0;">Manager: {selected['manager']}</p>
        </div>""", unsafe_allow_html=True)
    with info_col2:
        st.markdown(f"""
        <div class="detail-card">
            <h3>🎯 Burnout Score</h3>
            <p style="font-size: 2rem; font-weight: 700; color: {get_risk_color(selected['risk_level'])}; margin: 0;">
                {selected['burnout_score']}<span style="font-size: 1rem; color: #a0aec0;">/10</span>
            </p>
            <span class="risk-{selected['risk_level'].lower()}">{selected['risk_level']} Risk</span>
        </div>""", unsafe_allow_html=True)
    with info_col3:
        st.markdown(f"""
        <div class="detail-card">
            <h3>📊 Key Signals</h3>
            <p style="color:#718096; margin:0; font-size: 0.85rem;">
                Sentiment Drop: <strong>{selected['sentiment_decline']}</strong><br>
                After-Hours: <strong>{selected['after_hours_ratio']*100:.1f}%</strong><br>
                Leave Requests: <strong>{selected['total_leave_requests']}</strong>
            </p>
        </div>""", unsafe_allow_html=True)

    # Signal Breakdown Radar
    detail_chart1, detail_chart2 = st.columns(2)

    with detail_chart1:
        st.markdown("**📡 Signal Breakdown**")
        signals = selected['signal_scores']
        radar_fills = {'High': 'rgba(229,62,62,0.15)', 'Medium': 'rgba(214,158,46,0.15)', 'Low': 'rgba(56,161,105,0.15)'}
        fig_radar = go.Figure(data=go.Scatterpolar(
            r=list(signals.values()),
            theta=list(signals.keys()),
            fill='toself',
            fillcolor=radar_fills.get(selected['risk_level'], 'rgba(113,128,150,0.15)'),
            line_color=get_risk_color(selected['risk_level']),
            marker=dict(size=6)
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10], gridcolor='rgba(0,0,0,0.1)'),
                       angularaxis=dict(gridcolor='rgba(0,0,0,0.1)')),
            showlegend=False, height=300,
            margin=dict(l=60, r=60, t=30, b=30),
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with detail_chart2:
        st.markdown("**📉 4-Week Sentiment Trend**")
        fig_sent = go.Figure()
        fig_sent.add_trace(go.Scatter(
            x=selected['weeks'], y=selected['sentiments'],
            mode='lines+markers+text',
            text=[f'{s:.2f}' for s in selected['sentiments']],
            textposition='top center',
            line=dict(color=get_risk_color(selected['risk_level']), width=3),
            marker=dict(size=10, line=dict(width=2, color='white')),
            fill='tozeroy',
            fillcolor=f'rgba(107, 47, 160, 0.08)'
        ))
        fig_sent.update_layout(
            height=300, margin=dict(l=20, r=20, t=30, b=30),
            xaxis_title='Week', yaxis_title='Sentiment',
            yaxis=dict(range=[0, 1], gridcolor='rgba(0,0,0,0.05)'),
            xaxis=dict(gridcolor='rgba(0,0,0,0.05)'),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False
        )
        st.plotly_chart(fig_sent, use_container_width=True)

    # After-hours + message volume
    vol_col1, vol_col2 = st.columns(2)
    with vol_col1:
        st.markdown("**🌙 After-Hours Messages**")
        fig_ah = go.Figure(data=[go.Bar(
            x=selected['weeks'], y=selected['after_hours'],
            marker_color=['#805ad5' if v < 8 else '#e53e3e' for v in selected['after_hours']],
            text=selected['after_hours'], textposition='outside',
            hovertemplate='%{x}<br>After-hours: %{y}<extra></extra>'
        )])
        fig_ah.update_layout(
            height=250, margin=dict(l=20, r=20, t=10, b=30),
            xaxis_title='Week', yaxis_title='Messages',
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(gridcolor='rgba(0,0,0,0.05)')
        )
        st.plotly_chart(fig_ah, use_container_width=True)

    with vol_col2:
        st.markdown("**📨 Total Message Volume**")
        fig_vol = go.Figure(data=[go.Bar(
            x=selected['weeks'], y=selected['msg_counts'],
            marker_color=['#3182ce' if v < 55 else '#e53e3e' for v in selected['msg_counts']],
            text=selected['msg_counts'], textposition='outside',
            hovertemplate='%{x}<br>Messages: %{y}<extra></extra>'
        )])
        fig_vol.update_layout(
            height=250, margin=dict(l=20, r=20, t=10, b=30),
            xaxis_title='Week', yaxis_title='Messages',
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(gridcolor='rgba(0,0,0,0.05)')
        )
        st.plotly_chart(fig_vol, use_container_width=True)

    # Flagged keywords
    if selected['keywords']:
        st.markdown("**🚩 Flagged Keywords Over 4 Weeks**")
        kw_html = ""
        for kw in selected['keywords']:
            if kw in HIGH_SEVERITY_KEYWORDS:
                kw_html += f'<span class="risk-high" style="margin: 0.2rem;">{kw}</span> '
            elif kw in MEDIUM_SEVERITY_KEYWORDS:
                kw_html += f'<span class="risk-medium" style="margin: 0.2rem;">{kw}</span> '
            else:
                kw_html += f'<span class="risk-low" style="margin: 0.2rem;">{kw}</span> '
        st.markdown(kw_html, unsafe_allow_html=True)
    else:
        st.markdown("**🚩 Flagged Keywords:** None — communication appears healthy ✅")

    st.markdown("<br>", unsafe_allow_html=True)

    # AI Insight
    st.markdown("**🤖 AI-Powered Burnout Analysis**")
    if api_key:
        cache_key = f"ai_insight_{selected['id']}"
        if cache_key not in st.session_state:
            with st.spinner(f"Generating AI analysis for {selected['name']}..."):
                insight = get_ai_insight(
                    api_key, selected['name'], selected['department'],
                    selected['role'], selected
                )
                st.session_state[cache_key] = insight
        st.markdown(f'<div class="ai-insight">🧠 {st.session_state[cache_key]}</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="ai-insight">
            ℹ️ Enter your Gemini API key in the sidebar to get AI-powered burnout analysis 
            and personalized recommendations for this employee.
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
