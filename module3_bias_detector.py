"""
KARM Module 3: Interview Bias Detector
========================================
Flags biased interview questions (gender, caste, age, regional, marital status),
classifies bias type, and gives a recruiter bias score with exportable PDF report.

Run: streamlit run module3_bias_detector.py
"""

import streamlit as st
import google.generativeai as genai
import json
import os
import re
from datetime import datetime

# Optional PDF libraries
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


# ─────────────────────────────────────────────────────────────
# CONFIG & THEME
# ─────────────────────────────────────────────────────────────
def setup_page():
    st.set_page_config(
        page_title="KARM - Bias Detector",
        page_icon="⚖️",
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

        /* Bias type badges */
        .bias-gender { background: linear-gradient(135deg, #fed7e2, #fff5f7); border: 1px solid #fc8181; color: #c53030; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: 600; font-size: 0.8rem; display: inline-block; }
        .bias-age { background: linear-gradient(135deg, #fefcbf, #fffff0); border: 1px solid #f6e05e; color: #b7791f; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: 600; font-size: 0.8rem; display: inline-block; }
        .bias-caste { background: linear-gradient(135deg, #fed7d7, #fff5f5); border: 1px solid #fc8181; color: #9b2c2c; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: 600; font-size: 0.8rem; display: inline-block; }
        .bias-regional { background: linear-gradient(135deg, #c6f6d5, #f0fff4); border: 1px solid #68d391; color: #276749; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: 600; font-size: 0.8rem; display: inline-block; }
        .bias-marital { background: linear-gradient(135deg, #e9d8fd, #faf5ff); border: 1px solid #b794f4; color: #553c9a; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: 600; font-size: 0.8rem; display: inline-block; }
        .bias-other { background: linear-gradient(135deg, #bee3f8, #ebf8ff); border: 1px solid #63b3ed; color: #2b6cb0; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: 600; font-size: 0.8rem; display: inline-block; }

        /* Severity badges */
        .severity-high { background: linear-gradient(135deg, #fed7d7, #fff5f5); border: 1px solid #fc8181; color: #c53030; padding: 0.25rem 0.7rem; border-radius: 20px; font-weight: 600; font-size: 0.75rem; display: inline-block; }
        .severity-medium { background: linear-gradient(135deg, #fefcbf, #fffff0); border: 1px solid #f6e05e; color: #b7791f; padding: 0.25rem 0.7rem; border-radius: 20px; font-weight: 600; font-size: 0.75rem; display: inline-block; }
        .severity-low { background: linear-gradient(135deg, #c6f6d5, #f0fff4); border: 1px solid #68d391; color: #276749; padding: 0.25rem 0.7rem; border-radius: 20px; font-weight: 600; font-size: 0.75rem; display: inline-block; }

        /* Flagged question card */
        .flag-card {
            background: linear-gradient(135deg, #ffffff 0%, #faf5ff 100%);
            border: 1px solid #e2e8f0;
            border-left: 4px solid #e53e3e;
            border-radius: 0 14px 14px 0;
            padding: 1.5rem;
            margin: 0.75rem 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            transition: transform 0.15s;
        }
        .flag-card:hover {
            transform: translateX(4px);
        }
        .flag-card-medium { border-left-color: #d69e2e; }
        .flag-card-low { border-left-color: #38a169; }

        .flag-question {
            font-size: 1rem; font-weight: 600; color: #2d3748;
            margin-bottom: 0.75rem; line-height: 1.5;
            background: linear-gradient(135deg, #fff5f5, #fed7d7);
            padding: 0.6rem 1rem; border-radius: 8px;
        }
        .flag-explanation {
            font-size: 0.9rem; color: #4a5568; line-height: 1.6;
            margin: 0.5rem 0;
        }
        .flag-alternative {
            background: linear-gradient(135deg, #f0fff4, #c6f6d5);
            padding: 0.6rem 1rem; border-radius: 8px;
            font-size: 0.88rem; color: #276749; margin-top: 0.5rem;
            border: 1px solid #9ae6b4;
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

        /* Score gauge area */
        .score-display {
            text-align: center; padding: 1.5rem;
            background: linear-gradient(135deg, #ffffff, #f8f9ff);
            border-radius: 14px; border: 1px solid #e2e8f0;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        }
        .score-big {
            font-size: 3.5rem; font-weight: 700; margin: 0.5rem 0;
        }
        .score-label { font-size: 0.9rem; color: #718096; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }

        /* Sidebar info */
        .sidebar-info {
            background: #f5f0ff; color: #553c9a;
            padding: 1rem; border-radius: 10px;
            border: 1px solid #d6bcfa; margin-bottom: 1rem; font-size: 0.85rem;
        }

        /* Clean question row */
        .question-row {
            padding: 0.6rem 1rem; border-radius: 8px; margin: 0.3rem 0;
            display: flex; align-items: center; gap: 0.75rem;
            font-size: 0.88rem;
        }
        .q-clean { background: #f0fff4; border-left: 3px solid #38a169; color: #276749; }
        .q-flagged { background: #fff5f5; border-left: 3px solid #e53e3e; color: #c53030; }
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


def load_sample_transcript():
    """Load the sample interview transcript from fake_data."""
    data_path = os.path.join(os.path.dirname(__file__), 'fake_data', 'interview_transcript.txt')
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            return f.read()
    return None


def extract_text_from_pdf(uploaded_file):
    """Extract text from an uploaded PDF file."""
    if not HAS_PDFPLUMBER:
        return None
    try:
        import io
        with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None


def extract_questions_from_transcript(transcript):
    """Extract interviewer questions from the transcript text."""
    lines = transcript.split('\n')
    questions = []
    interviewer_name = None

    # Try to detect interviewer name from header
    for line in lines[:10]:
        if 'interviewer' in line.lower():
            parts = line.split(':')
            if len(parts) >= 2:
                interviewer_name = parts[1].strip().split('(')[0].strip()
                break

    if not interviewer_name:
        interviewer_name = "Interviewer"

    # Extract lines spoken by the interviewer that contain questions
    first_name = interviewer_name.split()[0] if interviewer_name else "Interviewer"
    q_num = 0
    for line in lines:
        line = line.strip()
        if line.startswith(f"{first_name}:"):
            content = line[len(first_name) + 1:].strip()
            # Split on sentence boundaries and look for questions
            sentences = re.split(r'(?<=[.!?])\s+', content)
            for sentence in sentences:
                if '?' in sentence:
                    q_num += 1
                    questions.append({
                        'number': q_num,
                        'text': sentence.strip(),
                        'speaker': interviewer_name
                    })

    return questions, interviewer_name


# ─────────────────────────────────────────────────────────────
# GEMINI AI BIAS ANALYSIS
# ─────────────────────────────────────────────────────────────
def analyze_bias_with_ai(api_key, transcript_text):
    """Use Gemini AI to analyze the transcript for bias."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemma-3-27b-it')

    prompt = f"""You are KARM, an AI-powered interview bias detection system. Analyze the following interview transcript and identify ALL questions that contain potential bias.

INTERVIEW TRANSCRIPT:
---
{transcript_text}
---

BIAS CATEGORIES TO CHECK:
1. **Gender Bias** — Questions about marriage, children, pregnancy plans, partner's job, household responsibilities
2. **Age Bias** — Questions about candidate's age, generation, "too young/old" implications
3. **Caste/Religion Bias** — Questions about surname origin, community, religious practices, festivals
4. **Regional Bias** — Questions about native place, family origin, language abilities linked to region, accent-related comments
5. **Marital Status Bias** — Questions about being single/married, spouse's work, family planning
6. **Disability Bias** — Questions about physical/mental health conditions not relevant to job

INSTRUCTIONS:
- Analyze EVERY question the interviewer asks
- Flag questions that contain explicit or subtle bias
- For each flagged question, provide the bias type, severity, explanation, and a bias-free alternative
- Calculate an overall bias score from 0 to 100 (0 = perfectly fair, 100 = heavily biased)
- Be thorough — catch subtle biases that might seem innocent but are discriminatory

Respond ONLY with valid JSON in exactly this format (no markdown, no code fences):
{{
  "interviewer_name": "Name of the interviewer",
  "candidate_name": "Name of the candidate",
  "position": "Position being interviewed for",
  "total_questions": <number of questions the interviewer asked>,
  "flagged_questions": [
    {{
      "question_number": <sequential number>,
      "original_question": "The exact question text",
      "bias_type": "Gender|Age|Caste|Regional|Marital Status|Disability",
      "severity": "High|Medium|Low",
      "explanation": "Why this question is biased and how it could discriminate",
      "suggested_alternative": "A bias-free alternative question that gets relevant info"
    }}
  ],
  "bias_score": <0-100>,
  "summary": "A 2-3 sentence overall assessment of the interview's fairness",
  "recommendations": [
    "Specific recommendation 1 for the recruiter",
    "Specific recommendation 2",
    "Specific recommendation 3"
  ],
  "legal_notes": "Brief note about relevant anti-discrimination considerations"
}}"""

    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip()

        # Remove markdown code fences if present
        if raw_text.startswith('```'):
            raw_text = re.sub(r'^```(?:json)?\s*', '', raw_text)
            raw_text = re.sub(r'\s*```$', '', raw_text)

        result = json.loads(raw_text)
        return result
    except json.JSONDecodeError as e:
        st.error(f"⚠️ Could not parse AI response as JSON. Retrying...")
        # Retry once with a stricter prompt
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
def generate_pdf_report(analysis):
    """Generate a PDF bias analysis report."""
    if not HAS_FPDF:
        return None

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Title
    pdf.set_font('Helvetica', 'B', 20)
    pdf.cell(0, 15, 'KARM Interview Bias Analysis Report', ln=True, align='C')
    pdf.ln(5)

    # Date & metadata
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', ln=True, align='C')
    pdf.cell(0, 8, f'Interviewer: {analysis.get("interviewer_name", "N/A")} | Candidate: {analysis.get("candidate_name", "N/A")}', ln=True, align='C')
    pdf.cell(0, 8, f'Position: {analysis.get("position", "N/A")}', ln=True, align='C')
    pdf.ln(8)

    # Overall Score
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, 'Overall Bias Score', ln=True)
    pdf.set_font('Helvetica', 'B', 28)
    score = analysis.get('bias_score', 0)
    if score >= 60:
        pdf.set_text_color(197, 48, 48)
    elif score >= 30:
        pdf.set_text_color(183, 121, 31)
    else:
        pdf.set_text_color(39, 103, 73)
    pdf.cell(0, 15, f'{score}/100', ln=True, align='C')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)

    # Summary
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, 'Summary', ln=True)
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(0, 6, analysis.get('summary', 'N/A'))
    pdf.ln(5)

    # Statistics
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, 'Statistics', ln=True)
    pdf.set_font('Helvetica', '', 10)
    total_q = analysis.get('total_questions', 0)
    flagged = len(analysis.get('flagged_questions', []))
    pdf.cell(0, 7, f'Total Questions Analyzed: {total_q}', ln=True)
    pdf.cell(0, 7, f'Flagged Questions: {flagged}', ln=True)
    pdf.cell(0, 7, f'Clean Questions: {total_q - flagged}', ln=True)
    pdf.ln(5)

    # Flagged Questions
    flagged_qs = analysis.get('flagged_questions', [])
    if flagged_qs:
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(0, 10, 'Flagged Questions', ln=True)
        pdf.ln(3)

        for i, fq in enumerate(flagged_qs, 1):
            pdf.set_font('Helvetica', 'B', 11)
            pdf.set_text_color(197, 48, 48)
            pdf.multi_cell(0, 6, f'Flag #{i}: [{fq.get("bias_type", "Unknown")}] [{fq.get("severity", "Unknown")} Severity]')
            pdf.set_text_color(0, 0, 0)

            pdf.set_font('Helvetica', 'I', 10)
            pdf.multi_cell(0, 6, f'Question: "{fq.get("original_question", "")}"')

            pdf.set_font('Helvetica', '', 10)
            pdf.multi_cell(0, 6, f'Why biased: {fq.get("explanation", "")}')

            pdf.set_text_color(39, 103, 73)
            pdf.set_font('Helvetica', '', 10)
            pdf.multi_cell(0, 6, f'Better alternative: "{fq.get("suggested_alternative", "")}"')
            pdf.set_text_color(0, 0, 0)
            pdf.ln(4)

    # Recommendations
    recommendations = analysis.get('recommendations', [])
    if recommendations:
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(0, 10, 'Recommendations', ln=True)
        pdf.set_font('Helvetica', '', 10)
        for rec in recommendations:
            pdf.multi_cell(0, 6, f'  * {rec}')
            pdf.ln(2)

    # Legal Notes
    legal = analysis.get('legal_notes', '')
    if legal:
        pdf.ln(3)
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(0, 10, 'Legal Considerations', ln=True)
        pdf.set_font('Helvetica', '', 10)
        pdf.multi_cell(0, 6, legal)

    # Footer
    pdf.ln(10)
    pdf.set_font('Helvetica', 'I', 9)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 8, 'This report was generated by KARM AI-Powered HR Automation System.', ln=True, align='C')
    pdf.cell(0, 8, 'For internal use only. Not a legal assessment.', ln=True, align='C')

    return pdf.output()


# ─────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────
def get_bias_badge(bias_type):
    """Return an HTML badge for a bias type."""
    css_map = {
        'Gender': 'bias-gender',
        'Age': 'bias-age',
        'Caste': 'bias-caste',
        'Regional': 'bias-regional',
        'Marital Status': 'bias-marital',
        'Disability': 'bias-other',
    }
    css_class = css_map.get(bias_type, 'bias-other')
    return f'<span class="{css_class}">{bias_type}</span>'


def get_severity_badge(severity):
    """Return an HTML badge for severity level."""
    css_class = f'severity-{severity.lower()}'
    return f'<span class="{css_class}">{severity}</span>'


def get_score_color(score):
    """Return a color based on bias score (0–100)."""
    if score >= 60:
        return '#e53e3e'
    elif score >= 30:
        return '#d69e2e'
    else:
        return '#38a169'


def get_score_label(score):
    """Return a label based on bias score."""
    if score >= 60:
        return '🔴 High Bias Risk'
    elif score >= 30:
        return '🟡 Moderate Bias'
    else:
        return '🟢 Fair Interview'


# ─────────────────────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────────────────────
def main():
    setup_page()

    # ── Header ──
    st.markdown("""
    <div class="main-header">
        <h1>⚖️ KARM Interview Bias Detector</h1>
        <p>AI-powered analysis to flag biased interview questions and ensure fair, legally compliant hiring practices.</p>
    </div>
    """, unsafe_allow_html=True)

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
            st.info("ℹ️ Add API key to analyze transcripts")

        st.markdown("---")

        # Transcript Input
        st.markdown("### 📄 Transcript Input")
        input_mode = st.radio(
            "Choose input method:",
            ["📝 Paste Text", "📁 Upload File", "📋 Use Sample"],
            help="Paste text, upload a .txt/.pdf file, or use the built-in sample transcript"
        )

        transcript_text = None

        if input_mode == "📝 Paste Text":
            transcript_text = st.text_area(
                "Paste interview transcript",
                height=200,
                placeholder="Paste the full interview transcript here..."
            )
            if not transcript_text:
                transcript_text = None

        elif input_mode == "📁 Upload File":
            uploaded_file = st.file_uploader(
                "Upload transcript",
                type=["txt", "pdf"],
                help="Supported formats: .txt, .pdf"
            )
            if uploaded_file:
                if uploaded_file.name.endswith('.pdf'):
                    if HAS_PDFPLUMBER:
                        transcript_text = extract_text_from_pdf(uploaded_file)
                        if transcript_text:
                            st.success(f"✅ Extracted text from {uploaded_file.name}")
                    else:
                        st.error("pdfplumber is not installed. Run: pip install pdfplumber")
                else:
                    transcript_text = uploaded_file.read().decode('utf-8')
                    st.success(f"✅ Loaded {uploaded_file.name}")

        elif input_mode == "📋 Use Sample":
            sample = load_sample_transcript()
            if sample:
                transcript_text = sample
                st.success("✅ Sample transcript loaded")
            else:
                st.error("❌ Could not load sample transcript")

        st.markdown("---")

        # Analyze button
        analyze_clicked = st.button(
            "🔍 Analyze for Bias",
            use_container_width=True,
            type="primary",
            disabled=not (api_key and transcript_text)
        )

        st.markdown("---")
        st.markdown("""
        <div class="sidebar-info">
            <strong>📖 How it works:</strong><br>
            KARM scans every interviewer question and flags potential bias across 6 categories:
            gender, age, caste/religion, regional origin, marital status, and disability.
            Each flag includes an explanation and bias-free alternative.
        </div>
        """, unsafe_allow_html=True)

    # ── Main Content ──
    if not api_key:
        st.markdown("""
        <div class="ai-insight">
            ℹ️ <strong>Welcome to the Interview Bias Detector!</strong><br><br>
            To get started:<br>
            1️⃣ Enter your Gemini API key in the sidebar<br>
            2️⃣ Load a transcript (paste, upload, or use the sample)<br>
            3️⃣ Click <strong>"Analyze for Bias"</strong><br><br>
            The AI will scan every question for gender, age, caste, regional, and marital status bias.
        </div>
        """, unsafe_allow_html=True)
        return

    if not transcript_text:
        st.markdown("""
        <div class="ai-insight">
            ℹ️ <strong>No transcript loaded.</strong><br>
            Use the sidebar to paste text, upload a file, or load the sample transcript.
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Trigger Analysis ──
    if analyze_clicked:
        with st.spinner("🔍 Analyzing transcript for bias... This may take a moment."):
            result = analyze_bias_with_ai(api_key, transcript_text)
        if result:
            st.session_state['bias_analysis'] = result
        else:
            st.error("❌ Failed to analyze the transcript. Please check your API key and try again.")
            return

    # ── Display Results ──
    if 'bias_analysis' not in st.session_state:
        # Show transcript preview
        st.markdown('<div class="section-header">📄 Transcript Preview</div>', unsafe_allow_html=True)
        questions, interviewer = extract_questions_from_transcript(transcript_text)
        st.markdown(f"**Interviewer detected:** {interviewer}")
        st.markdown(f"**Questions found:** {len(questions)}")
        with st.expander("View full transcript", expanded=False):
            st.text(transcript_text[:3000] + ("..." if len(transcript_text) > 3000 else ""))
        st.info("👆 Click **'Analyze for Bias'** in the sidebar to start the AI analysis.")
        return

    analysis = st.session_state['bias_analysis']
    flagged = analysis.get('flagged_questions', [])
    total_q = analysis.get('total_questions', 0)
    bias_score = analysis.get('bias_score', 0)
    score_color = get_score_color(bias_score)
    score_label = get_score_label(bias_score)

    # Count bias types
    bias_type_counts = {}
    severity_counts = {'High': 0, 'Medium': 0, 'Low': 0}
    for fq in flagged:
        bt = fq.get('bias_type', 'Other')
        bias_type_counts[bt] = bias_type_counts.get(bt, 0) + 1
        sev = fq.get('severity', 'Medium')
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    most_common_bias = max(bias_type_counts, key=bias_type_counts.get) if bias_type_counts else "None"

    # ── KPI Summary Row ──
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Questions</div>
            <div class="kpi-value">{total_q}</div>
            <div class="kpi-sub">Analyzed by AI</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">🚩 Flagged Questions</div>
            <div class="kpi-value" style="background: linear-gradient(135deg, #e53e3e, #c53030); -webkit-background-clip: text;">{len(flagged)}</div>
            <div class="kpi-sub">Potential bias detected</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Bias Score</div>
            <div class="kpi-value" style="background: linear-gradient(135deg, {score_color}, {score_color}); -webkit-background-clip: text;">{bias_score}</div>
            <div class="kpi-sub">{score_label}</div>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Top Bias Type</div>
            <div class="kpi-value" style="font-size: 1.6rem;">{most_common_bias}</div>
            <div class="kpi-sub">{bias_type_counts.get(most_common_bias, 0)} occurrence(s)</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts Row ──
    if HAS_PLOTLY and flagged:
        chart_col1, chart_col2 = st.columns([1, 1])

        with chart_col1:
            st.markdown('<div class="section-header">📊 Bias Type Distribution</div>', unsafe_allow_html=True)
            bias_colors = {
                'Gender': '#e53e3e', 'Age': '#d69e2e', 'Caste': '#9b2c2c',
                'Regional': '#38a169', 'Marital Status': '#805ad5', 'Disability': '#3182ce', 'Other': '#718096'
            }
            fig_donut = go.Figure(data=[go.Pie(
                labels=list(bias_type_counts.keys()),
                values=list(bias_type_counts.values()),
                hole=0.55,
                marker_colors=[bias_colors.get(bt, '#718096') for bt in bias_type_counts.keys()],
                textinfo='label+value',
                textfont_size=13,
                hovertemplate='<b>%{label}</b><br>%{value} question(s)<br>%{percent}<extra></extra>'
            )])
            fig_donut.update_layout(
                showlegend=False, height=320,
                margin=dict(l=20, r=20, t=20, b=20),
                annotations=[dict(text=f'{len(flagged)}', x=0.5, y=0.5,
                                  font_size=28, font_color='#2d3748', showarrow=False)],
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_donut, use_container_width=True)

        with chart_col2:
            st.markdown('<div class="section-header">⚠️ Severity Breakdown</div>', unsafe_allow_html=True)
            sev_colors = {'High': '#e53e3e', 'Medium': '#d69e2e', 'Low': '#38a169'}
            sev_labels = [s for s in ['High', 'Medium', 'Low'] if severity_counts[s] > 0]
            sev_values = [severity_counts[s] for s in sev_labels]

            fig_bar = go.Figure(data=[go.Bar(
                x=sev_values,
                y=sev_labels,
                orientation='h',
                marker=dict(
                    color=[sev_colors[s] for s in sev_labels],
                    line=dict(width=0)
                ),
                text=sev_values,
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>%{x} question(s)<extra></extra>'
            )])
            fig_bar.update_layout(
                height=320, margin=dict(l=20, r=60, t=20, b=20),
                xaxis=dict(title='Number of Questions', gridcolor='rgba(0,0,0,0.05)'),
                yaxis=dict(title=''),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("---")

    # ── Question Timeline ──
    if HAS_PLOTLY and flagged:
        st.markdown('<div class="section-header">📋 Question-by-Question Scan</div>', unsafe_allow_html=True)
        flagged_nums = {fq.get('question_number', 0) for fq in flagged}
        timeline_colors = []
        timeline_labels = []
        for i in range(1, total_q + 1):
            if i in flagged_nums:
                timeline_colors.append('#e53e3e')
                # find the bias type
                bt = 'Bias'
                for fq in flagged:
                    if fq.get('question_number') == i:
                        bt = fq.get('bias_type', 'Bias')
                        break
                timeline_labels.append(f'Q{i}: {bt}')
            else:
                timeline_colors.append('#38a169')
                timeline_labels.append(f'Q{i}: Clean')

        fig_timeline = go.Figure(data=[go.Bar(
            x=[f'Q{i}' for i in range(1, total_q + 1)],
            y=[1] * total_q,
            marker_color=timeline_colors,
            text=timeline_labels,
            textposition='outside',
            textfont_size=10,
            hovertemplate='%{text}<extra></extra>'
        )])
        fig_timeline.update_layout(
            height=180, margin=dict(l=20, r=20, t=10, b=30),
            xaxis=dict(title='Question Number', tickangle=0),
            yaxis=dict(visible=False),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False
        )
        st.plotly_chart(fig_timeline, use_container_width=True)
        st.markdown("""
        <div style="text-align: center; font-size: 0.8rem; color: #718096; margin-top: -0.5rem;">
            <span style="color: #e53e3e;">■</span> Flagged &nbsp;&nbsp;
            <span style="color: #38a169;">■</span> Clean
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

    # ── Flagged Questions Detail ──
    if flagged:
        st.markdown('<div class="section-header">🚩 Flagged Questions — Detailed Analysis</div>', unsafe_allow_html=True)

        for i, fq in enumerate(flagged):
            severity = fq.get('severity', 'Medium')
            card_class = 'flag-card'
            if severity == 'Medium':
                card_class += ' flag-card-medium'
            elif severity == 'Low':
                card_class += ' flag-card-low'

            bias_badge = get_bias_badge(fq.get('bias_type', 'Other'))
            sev_badge = get_severity_badge(severity)

            st.markdown(f"""
            <div class="{card_class}">
                <div style="display: flex; gap: 0.5rem; margin-bottom: 0.75rem; align-items: center;">
                    <strong style="color: #718096; font-size: 0.85rem;">FLAG #{i+1}</strong>
                    {bias_badge} {sev_badge}
                </div>
                <div class="flag-question">
                    ❝ {fq.get('original_question', '')} ❞
                </div>
                <div class="flag-explanation">
                    <strong>Why this is biased:</strong> {fq.get('explanation', '')}
                </div>
                <div class="flag-alternative">
                    ✅ <strong>Better alternative:</strong> {fq.get('suggested_alternative', '')}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
    else:
        st.markdown("""
        <div class="ai-insight">
            ✅ <strong>No biased questions detected!</strong><br>
            The interview appears to be fair and focused on professional qualifications. Great job!
        </div>
        """, unsafe_allow_html=True)

    # ── AI Summary & Recommendations ──
    st.markdown('<div class="section-header">🤖 AI Assessment & Recommendations</div>', unsafe_allow_html=True)

    summary = analysis.get('summary', '')
    if summary:
        st.markdown(f'<div class="ai-insight">🧠 <strong>Overall Assessment:</strong> {summary}</div>', unsafe_allow_html=True)

    recommendations = analysis.get('recommendations', [])
    if recommendations:
        st.markdown("**📌 Recommendations for the Recruiter:**")
        for j, rec in enumerate(recommendations, 1):
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f7fafc, #edf2f7); border-left: 3px solid #6b2fa0;
                        padding: 0.75rem 1rem; border-radius: 0 8px 8px 0; margin: 0.4rem 0; font-size: 0.9rem;">
                <strong>{j}.</strong> {rec}
            </div>
            """, unsafe_allow_html=True)

    legal = analysis.get('legal_notes', '')
    if legal:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #fffff0, #fefcbf); border: 1px solid #f6e05e;
                    padding: 1rem 1.25rem; border-radius: 12px; margin: 1rem 0; font-size: 0.88rem; color: #744210;">
            ⚖️ <strong>Legal Note:</strong> {legal}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Export ──
    st.markdown('<div class="section-header">📥 Export Report</div>', unsafe_allow_html=True)

    export_col1, export_col2 = st.columns(2)

    with export_col1:
        # JSON export
        json_str = json.dumps(analysis, indent=2, ensure_ascii=False)
        st.download_button(
            "📋 Download JSON Report",
            json_str,
            f"bias_report_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            "application/json",
            use_container_width=True
        )

    with export_col2:
        # PDF export
        if HAS_FPDF:
            pdf_bytes = generate_pdf_report(analysis)
            if pdf_bytes:
                st.download_button(
                    "📄 Download PDF Report",
                    pdf_bytes,
                    f"bias_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    "application/pdf",
                    use_container_width=True
                )
        else:
            st.info("Install fpdf2 for PDF export: `pip install fpdf2`")

    # ── Transcript Reference ──
    with st.expander("📄 View Full Transcript", expanded=False):
        st.text(transcript_text)


if __name__ == "__main__":
    main()
