"""
KARM Module 5: Vernacular Training Bot
=========================================
Converts company policy PDFs into interactive multilingual Q&A training
modules with audio playback and training progress tracking.

Run: streamlit run module5_training_bot.py
"""

import streamlit as st
import pdfplumber
import google.generativeai as genai
import json
import os
import re
import io
import base64
from datetime import datetime

# Optional libraries
try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False

try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False


# ─────────────────────────────────────────────────────────────
# LANGUAGE CONFIG
# ─────────────────────────────────────────────────────────────
SUPPORTED_LANGUAGES = {
    "Hindi": "hi",
    "Tamil": "ta",
    "Telugu": "te",
    "Malayalam": "ml",
    "Marathi": "mr",
    "Urdu": "ur",
    "Gujarati": "gu",
    "Kannada": "kn",
    "Bengali": "bn",
    "English": "en",
}

LANGUAGE_SCRIPTS = {
    "Hindi": "हिन्दी",
    "Tamil": "தமிழ்",
    "Telugu": "తెలుగు",
    "Malayalam": "മലയാളം",
    "Marathi": "मराठी",
    "Urdu": "اردو",
    "Gujarati": "ગુજરાતી",
    "Kannada": "ಕನ್ನಡ",
    "Bengali": "বাংলা",
    "English": "English",
}


# ─────────────────────────────────────────────────────────────
# CONFIG & THEME
# ─────────────────────────────────────────────────────────────
def setup_page():
    try:
        st.set_page_config(
            page_title="KARM - Vernacular Training Bot",
            page_icon="🌐",
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

        /* Header */
        .main-header {
            background: linear-gradient(135deg, #0a2818 0%, #1a5c38 50%, #2d8659 100%);
            padding: 2rem 2.5rem;
            border-radius: 16px;
            margin-bottom: 1.5rem;
            color: white;
            box-shadow: 0 4px 20px rgba(45, 134, 89, 0.25);
        }
        .main-header h1 { margin: 0; font-size: 2rem; font-weight: 700; letter-spacing: -0.5px; }
        .main-header p { margin: 0.5rem 0 0 0; opacity: 0.85; font-size: 1rem; font-weight: 300; }

        /* Language badge */
        .lang-badge {
            display: inline-block; padding: 0.3rem 0.8rem; border-radius: 20px;
            font-weight: 600; font-size: 0.85rem;
            background: linear-gradient(135deg, #d4edda, #c3e6cb);
            color: #155724; border: 1px solid #a3d9a5;
        }

        /* QA Card */
        .qa-card {
            background: linear-gradient(135deg, #ffffff 0%, #f0faf4 100%);
            border: 1px solid #c6f6d5;
            border-radius: 14px;
            padding: 1.5rem;
            margin: 0.75rem 0;
            box-shadow: 0 2px 12px rgba(0,0,0,0.05);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .qa-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.08);
        }
        .qa-number {
            display: inline-block; background: linear-gradient(135deg, #2d8659, #1a5c38);
            color: white; width: 32px; height: 32px; border-radius: 50%;
            text-align: center; line-height: 32px; font-weight: 700; font-size: 0.9rem;
            margin-right: 0.75rem;
        }
        .qa-question {
            font-size: 1.05rem; font-weight: 600; color: #1a202c;
            margin-bottom: 0.75rem; line-height: 1.5;
        }
        .qa-answer {
            font-size: 0.95rem; color: #2d3748; line-height: 1.7;
            padding: 0.75rem 1rem;
            background: linear-gradient(135deg, #f7fafc, #edf2f7);
            border-left: 4px solid #38a169;
            border-radius: 0 10px 10px 0;
        }
        .qa-original {
            font-size: 0.82rem; color: #718096; margin-top: 0.5rem;
            padding: 0.5rem 0.75rem;
            background: #f7fafc; border-radius: 8px;
            border: 1px dashed #cbd5e0;
        }

        /* Progress bar */
        .progress-container {
            background: #e2e8f0; border-radius: 10px; height: 24px;
            overflow: hidden; margin: 0.5rem 0;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
        }
        .progress-fill {
            height: 100%; border-radius: 10px;
            background: linear-gradient(90deg, #38a169, #2d8659, #1a5c38);
            transition: width 0.5s ease;
            display: flex; align-items: center; justify-content: center;
            color: white; font-weight: 700; font-size: 0.75rem;
        }

        /* KPI cards */
        .kpi-card {
            background: linear-gradient(135deg, #ffffff 0%, #f0faf4 100%);
            border: 1px solid #c6f6d5;
            border-radius: 14px;
            padding: 1.25rem;
            text-align: center;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        }
        .kpi-value {
            font-size: 2.2rem; font-weight: 700; margin: 0.2rem 0;
            background: linear-gradient(135deg, #2d8659, #1a5c38);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .kpi-label { font-size: 0.82rem; color: #718096; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
        .kpi-sub { font-size: 0.72rem; color: #a0aec0; margin-top: 0.2rem; }

        /* AI insight */
        .ai-insight {
            background: linear-gradient(135deg, #ebf8ff, #e6fffa);
            border-left: 4px solid #2d8659;
            padding: 1rem 1.25rem;
            border-radius: 0 12px 12px 0;
            margin: 0.75rem 0;
            font-size: 0.92rem; line-height: 1.7;
            color: #2d3748;
        }

        /* Sidebar */
        .sidebar-info {
            background: #e6ffed; color: #22543d;
            padding: 1rem; border-radius: 10px;
            border: 1px solid #9ae6b4; margin-bottom: 1rem; font-size: 0.85rem;
        }

        /* Status */
        .status-ready {
            background: #f0fff4; border: 1px solid #c6f6d5;
            padding: 0.75rem 1rem; border-radius: 8px;
            color: #276749; font-weight: 500;
        }
        .status-waiting {
            background: #fffaf0; border: 1px solid #feebc8;
            padding: 0.75rem 1rem; border-radius: 8px;
            color: #975a16; font-weight: 500;
        }

        /* Section headers */
        .section-header {
            font-size: 1.2rem; font-weight: 600; color: #2d3748;
            margin: 1.5rem 0 1rem 0; padding-bottom: 0.5rem;
            border-bottom: 2px solid #c6f6d5;
        }

        /* Completed badge */
        .completed-badge {
            display: inline-block; padding: 0.15rem 0.5rem; border-radius: 16px;
            font-size: 0.72rem; font-weight: 600;
            background: linear-gradient(135deg, #c6f6d5, #9ae6b4);
            border: 1px solid #68d391; color: #22543d;
        }
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# PDF PROCESSING
# ─────────────────────────────────────────────────────────────
def extract_pdf_text(pdf_file):
    """Extract full text from a PDF file."""
    full_text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n\n"
    return full_text.strip()


# ─────────────────────────────────────────────────────────────
# GEMINI AI — Q&A GENERATION
# ─────────────────────────────────────────────────────────────
def generate_training_qa(api_key, pdf_text, language, num_questions=8):
    """Use Gemini to generate translated Q&A training pairs from policy text."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemma-3-27b-it')

    # Truncate PDF text if too long (keep most relevant parts)
    max_chars = 12000
    if len(pdf_text) > max_chars:
        pdf_text = pdf_text[:max_chars] + "\n\n[...truncated for length...]"

    prompt = f"""You are KARM, an AI Training Module Generator for HR.

TASK: Generate exactly {num_questions} training Q&A pairs from the company policy document below.

POLICY DOCUMENT:
{pdf_text}

CRITICAL INSTRUCTIONS:
1. Generate {num_questions} questions covering the most important policy topics
2. The questions AND answers must be translated to {language}
3. Also provide the English version of each question for reference
4. Questions should cover diverse topics: leave, benefits, conduct, WFH, etc.
5. Answers should be concise but complete (2-3 sentences each)
6. Make questions practical — things an employee would actually ask

Respond ONLY with valid JSON (no markdown, no code fences):
{{
  "training_module": {{
    "language": "{language}",
    "qa_pairs": [
      {{
        "id": 1,
        "question_translated": "Question in {language}",
        "answer_translated": "Answer in {language}",
        "question_english": "Question in English",
        "answer_english": "Answer in English",
        "topic": "Topic category (e.g., Leave Policy, Benefits, Conduct)"
      }}
    ]
  }}
}}"""

    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        # Clean markdown code fences if present
        if raw_text.startswith('```'):
            raw_text = re.sub(r'^```(?:json)?\s*', '', raw_text)
            raw_text = re.sub(r'\s*```$', '', raw_text)
        result = json.loads(raw_text)
        return result
    except json.JSONDecodeError:
        try:
            retry_prompt = prompt + "\n\nCRITICAL: Respond with ONLY valid JSON. No markdown, no code blocks, no extra text."
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


def generate_training_summary(api_key, employee, language, completed, total):
    """Use Gemini to generate a summary of training progress."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemma-3-27b-it')

    pct = round((completed / total) * 100) if total > 0 else 0

    prompt = f"""You are KARM, an AI Training Coach.

An employee just completed part of their vernacular policy training. Generate a brief, encouraging progress report.

EMPLOYEE: {employee['name']}
ROLE: {employee['role']}
DEPARTMENT: {employee['department']}
LANGUAGE: {language}
COMPLETED: {completed} out of {total} questions ({pct}%)

Generate a 2-3 sentence personalized motivational message about their training progress. If they completed all questions, congratulate them. If not, encourage them to finish.

Respond with plain text only, no JSON."""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return f"{'🎉 Great job completing all training!' if pct == 100 else f'You have completed {pct}% of your training. Keep going!'}"


# ─────────────────────────────────────────────────────────────
# AUDIO GENERATION (gTTS)
# ─────────────────────────────────────────────────────────────
def generate_audio(text, lang_code):
    """Generate audio bytes from text using gTTS."""
    if not HAS_GTTS:
        return None
    try:
        tts = gTTS(text=text, lang=lang_code, slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return audio_buffer.getvalue()
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────
# SHARED DATA LAYER
# ─────────────────────────────────────────────────────────────
def load_employees():
    """Load employee data from shared data layer."""
    data_path = os.path.join(os.path.dirname(__file__), 'fake_data', 'employees.json')
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_training_progress(emp_id, percent):
    """Update training_completion_percent in employees.json."""
    data_path = os.path.join(os.path.dirname(__file__), 'fake_data', 'employees.json')
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            employees = json.load(f)
        for emp in employees:
            if emp['id'] == emp_id:
                emp['training_completion_percent'] = percent
                break
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(employees, f, indent=2, ensure_ascii=False)
        return True
    return False


# ─────────────────────────────────────────────────────────────
# PDF REPORT GENERATION
# ─────────────────────────────────────────────────────────────
def sanitize_text(text):
    """Replace Unicode characters unsupported by Helvetica with ASCII equivalents."""
    if not isinstance(text, str):
        return str(text)
    replacements = {
        '\u2014': '--', '\u2013': '-', '\u2018': "'", '\u2019': "'",
        '\u201c': '"', '\u201d': '"', '\u2022': '*', '\u2026': '...',
        '\u2192': '->', '\u00b7': '*', '\u2191': '^', '\u2193': 'v',
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    text = text.encode('latin-1', errors='replace').decode('latin-1')
    return text


def generate_pdf_report(employee, language, qa_pairs, completed_ids):
    """Generate a PDF training completion report."""
    if not HAS_FPDF:
        return None

    total = len(qa_pairs)
    completed = len(completed_ids)
    pct = round((completed / total) * 100) if total > 0 else 0

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Title
    pdf.set_font('Helvetica', 'B', 20)
    pdf.cell(0, 15, 'KARM Training Completion Report', ln=True, align='C')
    pdf.ln(5)

    # Date
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', ln=True, align='C')
    pdf.ln(8)

    # Employee info
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, 'Employee Details', ln=True)
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 7, f'Name: {sanitize_text(employee["name"])}', ln=True)
    pdf.cell(0, 7, f'Department: {sanitize_text(employee["department"])}', ln=True)
    pdf.cell(0, 7, f'Role: {sanitize_text(employee["role"])}', ln=True)
    pdf.cell(0, 7, f'Training Language: {sanitize_text(language)}', ln=True)
    pdf.ln(5)

    # Progress
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, 'Training Progress', ln=True)
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 7, f'Completed: {completed} / {total} questions ({pct}%)', ln=True)
    status = 'COMPLETED' if pct == 100 else 'IN PROGRESS'
    pdf.cell(0, 7, f'Status: {status}', ln=True)
    pdf.ln(5)

    # Q&A details
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, 'Training Questions (English Reference)', ln=True)
    pdf.ln(3)

    for qa in qa_pairs:
        is_done = qa['id'] in completed_ids
        marker = '[DONE]' if is_done else '[PENDING]'

        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 7, sanitize_text(f'{marker} Q{qa["id"]}: {qa.get("question_english", qa.get("question_translated", ""))}'), ln=True)
        pdf.set_font('Helvetica', '', 10)
        answer = qa.get("answer_english", qa.get("answer_translated", ""))
        pdf.multi_cell(0, 6, sanitize_text(f'A: {answer}'))
        pdf.ln(2)

    # Footer
    pdf.ln(10)
    pdf.set_font('Helvetica', 'I', 9)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 8, 'This report was generated by KARM AI-Powered HR Automation System.', ln=True, align='C')
    pdf.cell(0, 8, 'For internal use only.', ln=True, align='C')

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
        <h1>🌐 KARM Vernacular Training Bot</h1>
        <p>Convert company policies into interactive multilingual training modules with audio support — inclusion in action.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Sidebar ──
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")

        # API Key
        api_key = st.text_input(
            "Google Gemini API Key", type="password",
            help="Get your free API key from aistudio.google.com/apikey"
        )
        if api_key:
            st.success("✅ API key set")
        else:
            st.warning("⚠️ Enter your Gemini API key to start")

        st.markdown("---")

        # PDF Upload
        st.markdown("### 📄 Policy Document")
        uploaded_file = st.file_uploader(
            "Upload a PDF file", type=['pdf'],
            help="Upload your company HR policy document"
        )

        use_sample = st.checkbox(
            "📂 Use sample company policy (for demo)",
            help="Load the pre-generated KARM Corp policy PDF"
        )

        st.markdown("---")

        # Employee selection
        employees = load_employees()
        st.markdown("### 👤 Select Employee")
        if employees:
            emp_names = [f"{e['name']} ({e['id']})" for e in employees]
            selected_emp_name = st.selectbox("Choose an employee", emp_names)
            selected_idx = emp_names.index(selected_emp_name)
            selected_employee = employees[selected_idx]

            # Auto-detect language
            auto_lang = selected_employee.get('language_preference', 'English')
            st.markdown(f'Auto-detected: <span class="lang-badge">{auto_lang}</span>', unsafe_allow_html=True)
        else:
            selected_employee = None
            auto_lang = 'English'

        st.markdown("---")

        # Language override
        st.markdown("### 🗣️ Training Language")
        lang_list = list(SUPPORTED_LANGUAGES.keys())
        default_idx = lang_list.index(auto_lang) if auto_lang in lang_list else lang_list.index('English')
        selected_language = st.selectbox(
            "Override language", lang_list, index=default_idx,
            help="Auto-populated from employee profile. Override if needed."
        )
        lang_code = SUPPORTED_LANGUAGES[selected_language]
        native_name = LANGUAGE_SCRIPTS.get(selected_language, selected_language)
        st.markdown(f"**Native script:** {native_name}")

        st.markdown("---")

        # Number of questions
        num_questions = st.slider("Number of Q&A pairs", min_value=3, max_value=12, value=8)

        st.markdown("---")
        st.markdown("""
        <div class="sidebar-info">
            <strong>🌐 How it works:</strong><br>
            1. Upload a policy PDF<br>
            2. Select an employee<br>
            3. Click "Generate Training"<br>
            4. Q&A appears in their language<br>
            5. Listen to audio with 🔊<br>
            6. Mark questions as completed ✅
        </div>
        """, unsafe_allow_html=True)

    # ── Load PDF ──
    pdf_file = None
    if uploaded_file:
        pdf_file = uploaded_file
    elif use_sample:
        sample_path = os.path.join(os.path.dirname(__file__), 'fake_data', 'company_policy.pdf')
        if os.path.exists(sample_path):
            pdf_file = sample_path
        else:
            st.error("❌ Sample policy PDF not found. Please generate it first with `python generate_policy_pdf.py`.")

    # Extract text
    if pdf_file and 'pdf_text_m5' not in st.session_state:
        with st.spinner("📖 Reading policy document..."):
            st.session_state['pdf_text_m5'] = extract_pdf_text(pdf_file)
            st.session_state['pdf_loaded_m5'] = True

    # ── Status bar ──
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.session_state.get('pdf_loaded_m5'):
            text_len = len(st.session_state.get('pdf_text_m5', ''))
            st.markdown(
                f'<div class="status-ready">📗 Policy document loaded — {text_len:,} characters extracted and ready for training</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="status-waiting">📙 Upload a policy PDF or check "Use sample company policy" in the sidebar</div>',
                unsafe_allow_html=True
            )
    with col2:
        if st.button("🗑️ Reset Training", use_container_width=True):
            for key in ['training_qa_m5', 'completed_m5', 'pdf_text_m5', 'pdf_loaded_m5', 'ai_summary_m5']:
                st.session_state.pop(key, None)
            st.rerun()

    st.markdown("---")

    # ── Generate Training Button ──
    if st.session_state.get('pdf_loaded_m5') and selected_employee:
        if 'training_qa_m5' not in st.session_state:
            st.markdown(f"""
            <div style="text-align: center; padding: 2rem;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🌐</div>
                <div style="font-size: 1.1rem; color: #2d3748; font-weight: 500;">
                    Ready to generate training for <strong>{selected_employee['name']}</strong> in <strong>{selected_language}</strong> ({native_name})
                </div>
                <div style="font-size: 0.85rem; color: #718096; margin-top: 0.5rem;">
                    {num_questions} Q&A pairs will be generated from the policy document
                </div>
            </div>
            """, unsafe_allow_html=True)

            gen_col1, gen_col2, gen_col3 = st.columns([1, 2, 1])
            with gen_col2:
                if st.button("🚀 Generate Training Module", use_container_width=True, type="primary"):
                    if not api_key:
                        st.error("⚠️ Please enter your Gemini API key in the sidebar first.")
                    else:
                        with st.spinner(f"🤖 Generating {num_questions} Q&A pairs in {selected_language}... This may take a moment."):
                            result = generate_training_qa(
                                api_key,
                                st.session_state['pdf_text_m5'],
                                selected_language,
                                num_questions
                            )
                            if result and 'training_module' in result:
                                st.session_state['training_qa_m5'] = result['training_module']['qa_pairs']
                                st.session_state['training_lang_m5'] = selected_language
                                st.session_state['training_emp_m5'] = selected_employee
                                st.session_state['completed_m5'] = set()
                                st.rerun()
                            else:
                                st.error("❌ Failed to generate training module. Please try again.")

    elif not st.session_state.get('pdf_loaded_m5'):
        st.info("📄 Upload a policy document in the sidebar to get started.")
    elif not selected_employee:
        st.info("👤 Select an employee from the sidebar.")

    # ── Display Training Module ──
    if 'training_qa_m5' in st.session_state:
        qa_pairs = st.session_state['training_qa_m5']
        completed = st.session_state.get('completed_m5', set())
        training_lang = st.session_state.get('training_lang_m5', 'English')
        training_emp = st.session_state.get('training_emp_m5', selected_employee)
        total = len(qa_pairs)
        done_count = len(completed)
        pct = round((done_count / total) * 100) if total > 0 else 0

        # ── KPI Summary ──
        kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)
        with kpi_c1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Employee</div>
                <div class="kpi-value" style="font-size: 1.4rem;">{training_emp['name']}</div>
                <div class="kpi-sub">{training_emp['department']}</div>
            </div>""", unsafe_allow_html=True)
        with kpi_c2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Language</div>
                <div class="kpi-value" style="font-size: 1.4rem;">{LANGUAGE_SCRIPTS.get(training_lang, training_lang)}</div>
                <div class="kpi-sub">{training_lang}</div>
            </div>""", unsafe_allow_html=True)
        with kpi_c3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Progress</div>
                <div class="kpi-value">{done_count}/{total}</div>
                <div class="kpi-sub">Questions completed</div>
            </div>""", unsafe_allow_html=True)
        with kpi_c4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Completion</div>
                <div class="kpi-value">{pct}%</div>
                <div class="kpi-sub">{'🎉 Complete!' if pct == 100 else '📚 In progress'}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Progress Bar ──
        st.markdown(f"""
        <div class="progress-container">
            <div class="progress-fill" style="width: {max(pct, 2)}%;">
                {pct}%
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Q&A Cards ──
        st.markdown(f'<div class="section-header">📝 Training Questions — {training_lang}</div>', unsafe_allow_html=True)

        for qa in qa_pairs:
            qa_id = qa['id']
            is_completed = qa_id in completed

            # Card
            question_text = qa.get('question_translated', qa.get('question_english', ''))
            answer_text = qa.get('answer_translated', qa.get('answer_english', ''))
            english_q = qa.get('question_english', '')
            english_a = qa.get('answer_english', '')
            topic = qa.get('topic', 'General')

            completed_html = ' <span class="completed-badge">✅ Completed</span>' if is_completed else ''

            st.markdown(f"""
            <div class="qa-card">
                <div class="qa-question">
                    <span class="qa-number">{qa_id}</span>
                    {question_text}{completed_html}
                    <span style="float: right; font-size: 0.72rem; color: #a0aec0; padding-top: 0.4rem;">{topic}</span>
                </div>
                <div class="qa-answer">
                    💬 {answer_text}
                </div>
                <div class="qa-original">
                    🇬🇧 <strong>English:</strong> {english_q}<br>
                    <em>{english_a}</em>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Audio + Completion in columns
            btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 2])

            with btn_col1:
                if st.button(f"🔊 Listen (Question)", key=f"audio_q_{qa_id}", use_container_width=True):
                    if HAS_GTTS:
                        with st.spinner("Generating audio..."):
                            audio_data = generate_audio(question_text, lang_code)
                            if audio_data:
                                st.audio(audio_data, format='audio/mp3')
                            else:
                                st.warning("⚠️ Could not generate audio for this text.")
                    else:
                        st.warning("⚠️ gTTS not installed. Run: pip install gTTS")

            with btn_col2:
                if st.button(f"🔊 Listen (Answer)", key=f"audio_a_{qa_id}", use_container_width=True):
                    if HAS_GTTS:
                        with st.spinner("Generating audio..."):
                            audio_data = generate_audio(answer_text, lang_code)
                            if audio_data:
                                st.audio(audio_data, format='audio/mp3')
                            else:
                                st.warning("⚠️ Could not generate audio for this text.")
                    else:
                        st.warning("⚠️ gTTS not installed. Run: pip install gTTS")

            with btn_col3:
                if is_completed:
                    if st.button(f"↩️ Mark as Incomplete", key=f"undo_{qa_id}", use_container_width=True):
                        completed.discard(qa_id)
                        st.session_state['completed_m5'] = completed
                        st.rerun()
                else:
                    if st.button(f"✅ Mark as Completed", key=f"done_{qa_id}", use_container_width=True):
                        completed.add(qa_id)
                        st.session_state['completed_m5'] = completed
                        st.rerun()

            st.markdown("")  # spacer

        st.markdown("---")

        # ── Save Progress & Actions ──
        st.markdown('<div class="section-header">💾 Save & Export</div>', unsafe_allow_html=True)

        action_c1, action_c2, action_c3 = st.columns(3)

        with action_c1:
            if st.button("💾 Save Progress to Employee Record", use_container_width=True, type="primary"):
                if training_emp:
                    success = save_training_progress(training_emp['id'], pct)
                    if success:
                        st.success(f"✅ Saved! {training_emp['name']}'s training completion updated to {pct}% in employees.json")
                    else:
                        st.error("❌ Failed to save progress.")

        with action_c2:
            if st.button("🤖 Get AI Summary", use_container_width=True):
                if api_key and training_emp:
                    with st.spinner("Generating AI summary..."):
                        summary = generate_training_summary(
                            api_key, training_emp, training_lang, done_count, total
                        )
                        st.session_state['ai_summary_m5'] = summary
                        st.rerun()
                else:
                    st.warning("⚠️ Enter API key in sidebar first.")

        with action_c3:
            if HAS_FPDF:
                pdf_data = generate_pdf_report(
                    training_emp, training_lang, qa_pairs, completed
                )
                if pdf_data:
                    st.download_button(
                        "📥 Download Report (PDF)",
                        data=pdf_data,
                        file_name=f"training_report_{training_emp['id']}_{training_lang.lower()}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
            else:
                st.warning("⚠️ fpdf2 not installed for PDF export")

        # Show AI summary if generated
        if st.session_state.get('ai_summary_m5'):
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class="ai-insight">
                🤖 <strong>KARM AI Training Coach:</strong><br><br>
                {st.session_state['ai_summary_m5']}
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
