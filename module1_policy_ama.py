"""
KARM Module 1: Internal Policy Ask-Me-Anything Chatbot
=======================================================
Upload a company policy PDF and ask any question in plain English.
Get instant answers with page and section citations.

Run: streamlit run module1_policy_ama.py
"""

import streamlit as st
import pdfplumber
import google.generativeai as genai
import json
import os
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ─────────────────────────────────────────────────────────────
# CONFIG & THEME
# ─────────────────────────────────────────────────────────────
def setup_page():
    try:
        st.set_page_config(
            page_title="KARM - Policy AMA",
            page_icon="📋",
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
        
        /* Chat message styling */
        .user-msg {
            background: linear-gradient(135deg, #e8f4fd, #d1ecf9);
            border-left: 4px solid #2b6cb0;
            padding: 1rem 1.25rem;
            border-radius: 0 12px 12px 0;
            margin: 0.75rem 0;
            font-size: 0.95rem;
            color: #1a202c; /* Ensure dark text */
        }
        .bot-msg {
            background: linear-gradient(135deg, #f7fafc, #edf2f7);
            border-left: 4px solid #38a169;
            padding: 1rem 1.25rem;
            border-radius: 0 12px 12px 0;
            margin: 0.75rem 0;
            font-size: 0.95rem;
            line-height: 1.7;
            color: #1a202c; /* Ensure dark text */
        }
        
        /* Citation badge */
        .citation {
            display: inline-block;
            background: #ebf4ff;
            color: #2b6cb0;
            padding: 0.2rem 0.6rem;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-top: 0.5rem;
            border: 1px solid #bee3f8;
        }
        
        /* Sidebar styling */
        .sidebar-info {
            background: #f0f7ff;
            color: #2b4c7e; /* Ensure text is visible on light background */
            padding: 1rem;
            border-radius: 10px;
            border: 1px solid #d1e3f6;
            margin-bottom: 1rem;
            font-size: 0.85rem;
        }
        
        /* Status indicators */
        .status-ready {
            background: #f0fff4;
            border: 1px solid #c6f6d5;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            color: #276749;
            font-weight: 500;
        }
        .status-waiting {
            background: #fffaf0;
            border: 1px solid #feebc8;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            color: #975a16;
            font-weight: 500;
        }
    </style>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# PDF PROCESSING
# ─────────────────────────────────────────────────────────────
def extract_pdf_chunks(pdf_file, chunk_size=500):
    """Extract text from PDF and split into chunks with page tracking."""
    chunks = []
    full_text_by_page = {}
    
    with pdfplumber.open(pdf_file) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if text:
                full_text_by_page[page_num] = text
                # Split page text into overlapping chunks
                words = text.split()
                for i in range(0, len(words), chunk_size // 2):
                    chunk_words = words[i:i + chunk_size]
                    if len(chunk_words) > 20:  # Skip very small chunks
                        chunk_text = ' '.join(chunk_words)
                        # Try to detect section headers
                        section = detect_section(chunk_text)
                        chunks.append({
                            'text': chunk_text,
                            'page': page_num,
                            'section': section
                        })
    
    return chunks, full_text_by_page


def detect_section(text):
    """Try to detect which policy section a chunk belongs to."""
    text_lower = text.lower()
    sections = {
        'Leave Policy': ['leave policy', 'earned leave', 'sick leave', 'casual leave', 'bereavement'],
        'Maternity & Paternity Leave': ['maternity', 'paternity', 'parental', 'adoption leave'],
        'Work From Home Policy': ['work from home', 'wfh', 'remote work', 'hybrid'],
        'Maternity & Parental Benefits': ['maternity benefit', 'childcare', 'parental benefit'],
        'Employee Perks & Benefits': ['health insurance', 'wellness', 'referral', 'learning', 'perks'],
        'Code of Conduct': ['code of conduct', 'harassment', 'dress code', 'conflict of interest', 'anti-discrimination'],
    }
    for section_name, keywords in sections.items():
        if any(kw in text_lower for kw in keywords):
            return section_name
    return 'General'


def find_relevant_chunks(query, chunks, top_k=4):
    """Find the most relevant chunks using TF-IDF cosine similarity."""
    if not chunks:
        return []
    
    texts = [c['text'] for c in chunks]
    texts.append(query)
    
    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(texts)
    
    query_vector = tfidf_matrix[-1]
    chunk_vectors = tfidf_matrix[:-1]
    
    similarities = cosine_similarity(query_vector, chunk_vectors).flatten()
    top_indices = similarities.argsort()[-top_k:][::-1]
    
    relevant = []
    for idx in top_indices:
        if similarities[idx] > 0.05:  # Minimum relevance threshold
            relevant.append({
                **chunks[idx],
                'score': float(similarities[idx])
            })
    
    return relevant


# ─────────────────────────────────────────────────────────────
# GEMINI AI
# ─────────────────────────────────────────────────────────────
def get_gemini_answer(api_key, question, relevant_chunks, chat_history):
    """Get an answer from Gemini with citations and hybrid (Doc + General) intelligence."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemma-3-27b-it')
    
    # Build context from relevant chunks
    context_parts = []
    for i, chunk in enumerate(relevant_chunks, 1):
        context_parts.append(
            f"[Doc Chunk {i} - Page {chunk['page']}, Section: {chunk['section']}]\n"
            f"{chunk['text']}\n"
        )
    context = "\n".join(context_parts)
    
    # Conversation history for true memory
    history_ctx = ""
    if chat_history:
        recent_history = chat_history[-5:]
        history_ctx = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in recent_history])

    prompt = f"""You are KARM, an intelligent AI HR Assistant.

PRIORITY WORKFLOW:
1. First, search the "DOCUMENT CONTEXT" below for an exact answer.
2. If the answer is in the document, provide it and cite (Page X, Section: Y).
3. If the answer is NOT in the document OR refers to behavior not covered by policy (like ethical questions, general advice, or conversational filler), use your General AI knowledge to respond professionally.
4. If you use general knowledge, do not invent citations. Just provide a helpful, professional HR response.

DOCUMENT CONTEXT:
{context}

CONVERSATION HISTORY (MEMORY):
{history_ctx}

USER QUESTION: {question}

STRICT STYLE RULES:
- NO repetitive introductions like "Hi I'm KARM".
- NO "As an AI model".
- Be professional, intelligent, and human-like.
- If answering based on general HR best practices rather than the manual, be clear but firm.

ANSWER:"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error getting response: {str(e)}"


# ─────────────────────────────────────────────────────────────
# SHARED DATA LAYER
# ─────────────────────────────────────────────────────────────
def load_employees():
    """Load employee data from shared data layer."""
    data_path = os.path.join(os.path.dirname(__file__), 'fake_data', 'employees.json')
    if os.path.exists(data_path):
        with open(data_path, 'r') as f:
            return json.load(f)
    return []


# ─────────────────────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────────────────────
def main():
    setup_page()
    
    # ── Header ──
    st.markdown("""
    <div class="main-header">
        <h1>📋 KARM Policy Ask-Me-Anything</h1>
        <p>Upload your company policy PDF and ask any question in plain English. Get instant answers with citations.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ── Sidebar ──
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        
        # API Key
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
        
        # PDF Upload
        st.markdown("### 📄 Upload Policy Document")
        uploaded_file = st.file_uploader(
            "Upload a PDF file",
            type=['pdf'],
            help="Upload your company HR policy document"
        )
        
        # Quick load option for demo
        use_sample = st.checkbox(
            "📂 Use sample company policy (for demo)",
            help="Load the pre-generated KARM Corp policy PDF"
        )
        
        st.markdown("---")
        
        # Employee context (optional)
        employees = load_employees()
        if employees:
            st.markdown("### 👤 Ask as Employee (Optional)")
            emp_names = ["-- None --"] + [e['name'] for e in employees]
            selected_emp = st.selectbox("Select employee context", emp_names)
        else:
            selected_emp = "-- None --"
        
        st.markdown("---")
        st.markdown("""
        <div class="sidebar-info">
            <strong>💡 Tips:</strong><br>
            • Ask specific questions for better answers<br>
            • Try: "How many days of WFH per week?"<br>
            • Try: "What is the maternity leave policy?"<br>
            • Try: "What gifts can I accept from vendors?"
        </div>
        """, unsafe_allow_html=True)
    
    # ── Process PDF ──
    pdf_file = None
    if uploaded_file:
        pdf_file = uploaded_file
    elif use_sample:
        sample_path = os.path.join(os.path.dirname(__file__), 'fake_data', 'company_policy.pdf')
        if os.path.exists(sample_path):
            pdf_file = sample_path
        else:
            st.error("Sample policy PDF not found. Please generate it first.")
    
    # Extract chunks if PDF is loaded
    if pdf_file and 'pdf_chunks' not in st.session_state:
        with st.spinner("📖 Reading and indexing your policy document..."):
            chunks, pages = extract_pdf_chunks(pdf_file)
            st.session_state['pdf_chunks'] = chunks
            st.session_state['pdf_pages'] = pages
            st.session_state['pdf_loaded'] = True
    
    # ── Chat Interface ──
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []
    
    # Show status
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.session_state.get('pdf_loaded'):
            chunks = st.session_state['pdf_chunks']
            st.markdown(
                f'<div class="status-ready">📗 Policy document loaded — '
                f'{len(chunks)} sections indexed and ready for questions</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="status-waiting">📙 Upload a policy PDF or check '
                '"Use sample company policy" in the sidebar to get started</div>',
                unsafe_allow_html=True
            )
    with col2:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state['chat_history'] = []
            st.rerun()
    
    st.markdown("---")
    
    # Display chat history
    for msg in st.session_state['chat_history']:
        if msg['role'] == 'user':
            st.markdown(f'<div class="user-msg">🧑‍💼 <strong>You:</strong> {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bot-msg">🤖 <strong>KARM:</strong><br>{msg["content"]}</div>', unsafe_allow_html=True)
            # Only show citations if they exist AND are not already mentioned in text
            if msg.get('citations'):
                # Unique citations to avoid duplicates
                unique_cites = {f"{c['page']}-{c['section']}": c for c in msg['citations']}.values()
                cite_html = ""
                for cite in unique_cites:
                    cite_html += f'<span class="citation">📄 Page {cite["page"]} — {cite["section"]}</span> '
                st.markdown(cite_html, unsafe_allow_html=True)
    
    # Question input
    question = st.chat_input("Ask a question about your company policy...")
    
    if question:
        # Add user message
        st.session_state['chat_history'].append({
            'role': 'user',
            'content': question
        })
        
        if not api_key:
            st.session_state['chat_history'].append({
                'role': 'assistant',
                'content': '⚠️ Please enter your Gemini API key in the sidebar first.',
                'citations': []
            })
            st.rerun()
        
        if not st.session_state.get('pdf_loaded'):
            st.session_state['chat_history'].append({
                'role': 'assistant',
                'content': '⚠️ Please upload a policy PDF first using the sidebar.',
                'citations': []
            })
            st.rerun()
        
        # Find relevant chunks
        chunks = st.session_state['pdf_chunks']
        
        # Add employee context if selected
        full_question = question
        if selected_emp != "-- None --":
            emp = next((e for e in employees if e['name'] == selected_emp), None)
            if emp:
                full_question = (
                    f"[Employee context: {emp['name']}, {emp['role']} in "
                    f"{emp['department']}, joined {emp['join_date']}] {question}"
                )
        
        with st.spinner("🔍 Searching policy document and generating answer..."):
            relevant = find_relevant_chunks(full_question, chunks, top_k=4)
            
            if relevant:
                # Pass chat history for memory
                answer = get_gemini_answer(api_key, full_question, relevant, st.session_state['chat_history'][:-1])
                citations = [{'page': c['page'], 'section': c['section']} for c in relevant]
            else:
                answer = ("I'm sorry, that specific information is not covered in the current policy document.")
                citations = []
        
        st.session_state['chat_history'].append({
            'role': 'assistant',
            'content': answer,
            'citations': citations
        })
        st.rerun()
    
    # ── Sample Questions ──
    if not st.session_state['chat_history'] and st.session_state.get('pdf_loaded'):
        st.markdown("### 💬 Try asking:")
        sample_cols = st.columns(2)
        samples = [
            "How many days can I work from home per week?",
            "What is the maternity leave policy?",
            "How much is the employee referral bonus?",
            "What is the anti-harassment policy?"
        ]
        for i, sample in enumerate(samples):
            with sample_cols[i % 2]:
                if st.button(f"➡️ {sample}", key=f"sample_{i}", use_container_width=True):
                    st.session_state['chat_history'].append({'role': 'user', 'content': sample})
                    if api_key and st.session_state.get('pdf_loaded'):
                        chunks = st.session_state['pdf_chunks']
                        relevant = find_relevant_chunks(sample, chunks, top_k=4)
                        if relevant:
                            # Pass chat history for memory
                            answer = get_gemini_answer(api_key, sample, relevant, st.session_state['chat_history'][:-1])
                            citations = [{'page': c['page'], 'section': c['section']} for c in relevant]
                        else:
                            answer = "I'm sorry, that specific information is not covered in the current policy document."
                            citations = []
                        st.session_state['chat_history'].append({
                            'role': 'assistant', 'content': answer, 'citations': citations
                        })
                    st.rerun()


if __name__ == "__main__":
    main()
