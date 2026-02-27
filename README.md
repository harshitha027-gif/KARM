# KARM — AI-Powered HR Automation System

**KARM** (Knowledge, Analytics, Recruiter, Manager) is a modular, AI-powered HR automation platform built using Python, Streamlit, and Google's Gemini AI (`gemma-3-27b`). It transforms traditional Human Resource departments by replacing manual, error-prone workflows with intelligent, interconnected AI-driven tools.

## 🚀 The Problem

HR departments spend over 60% of their time on repetitive tasks:
- Answering the same routine policy questions.
- Trying to spot employee burnout before it leads to churn.
- Manually reviewing interview transcripts for fairness and avoiding unconscious bias.
- Guessing which internal employees are best suited for open roles.
- Handling the back-and-forth email chains to schedule panel interviews.

**The result:** A reactive, inefficient HR function that relies on gut feeling rather than data.

## 💡 The Solution (USP)

KARM is a unified, intelligent platform that centralizes and automates these disparate HR workflows. It moves beyond gimmicky chatbots by delivering truly *usable AI* that shares deep, continuous context across all its modules. When the Burnout Detector flags an employee, that context immediately informs the Job Match Agent and the Interview Scheduler, creating a smart, interconnected HR ecosystem.

## 🏗️ Architecture Overview

The system architecture is a multi-module, hub-and-spoke design where 7 standalone Streamlit modules connect to a central **Shared Data Layer**.

*   **The Hub (Shared Data Layer):** JSON and CSV files (e.g., `employees.json`, `open_roles.json`, `communications_data.csv`) act as a local, lightweight database ensuring context is preserved across the platform.
*   **The Spokes (The Modules):**
    1.  **Policy AMA Bot:** Uses RAG to answer specific policy questions from uploaded PDFs, citing the exact page and section.
    2.  **Burnout Risk Dashboard:** Analyzes communication patterns (after-hours messages, sentiment) to score and flag burnout risks.
    3.  **Interview Bias Detector:** Generative AI analyzes interview transcripts to flag questions containing unconscious bias (gender, age, regional).
    4.  **Internal Job Match Agent:** Uses vector similarity to proactively match existing employee skillsets to open internal roles.
    5.  **Vernacular Training Bot:** Translates the company policy into interactive, multilingual Q&A modules to ensure compliance across diverse teams.
    6.  **Gamified Performance Dashboard:** Turns KPIs into a gamified experience with leaderboards and badges.
    7.  **Autonomous Interview Scheduler:** AI agent that simulates schedule negotiation to find optimal overlap between recruiters and candidates.
*   **The Backbone (AI Engine):** Google's Gemini AI (`gemma-3-27b`) provides the underlying reasoning, NLP, and generative capabilities for all modules.

## 🛠️ Tech Stack
*   **Frontend & UI:** Streamlit (Python)
*   **AI Engine:** Google Gemini API (`gemma-3-27b`)
*   **Data Processing:** Pandas, scikit-learn (TF-IDF Cosine Similarity)
*   **Data Visualization:** Plotly
*   **Document Parsing:** pdfplumber
*   **Text-to-Speech:** gTTS
*   **Data Storage:** Local JSON & CSV files

## 📦 Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/username/Karm.git
   cd Karm
   ```

2. **Install the dependencies:**
   Make sure you have Python installed, then run:
   ```bash
   pip install -r requirements.txt
   ```
   *(Or manually install: `pip install streamlit google-generativeai pdfplumber pandas plotly scikit-learn gTTS fpdf2`)*

3. **Get your Gemini API Key:**
   - Go to [Google AI Studio](https://aistudio.google.com/apikey)
   - Create a new API key (Free Tier provides 15 requests/minute).

4. **Run any module standalone:**
   Every module can run on its own. For example, to launch the Policy AMA bot:
   ```bash
   streamlit run module1_policy_ama.py
   ```
   *Note: Provide your Gemini API key in the Streamlit sidebar when the app launches.*

## 📂 Project Structure
```text
KARM/
├── fake_data/                  # The Hub: Shared Data Layer
│   ├── employees.json          # Master employee records
│   ├── communications_data.csv # Burnout analysis data
│   ├── company_policy.pdf      # Example HR policy document
│   ├── open_roles.json         # Internal job openings
│   └── ...
├── module1_policy_ama.py       # Spoke 1
├── module2_burnout.py          # Spoke 2
├── module3_bias_detector.py    # Spoke 3
├── module4_job_match.py        # Spoke 4
├── module5_training_bot.py     # Spoke 5
├── module6_gamified.py         # Spoke 6
├── module7_scheduler.py        # Spoke 7
├── KARM_PLAN.md                # Detailed initial project plan
└── README.md                   # This file
```

## 🔐 Security & Compliance Considerations
If adapting this project for a production enterprise environment, the following architectural upgrades are crucial:
1.  **Data Sanitization Layer:** Implement strict PII scrubbing before sending text/transcripts to external LLMs to comply with GDPR/CCPA.
2.  **Role-Based Access Control (RBAC):** Restrict access so employees only see their data, while HR managers see aggregated dashboards.
3.  **Audit Logging:** Ensure every AI-driven HR decision (like bias scoring or job matching) stores its "chain of reasoning" in an immutable log for explainability and legal defensibility.
4.  **Private AI Deployments:** Shift from public APIs to private cloud deployments (e.g., Google Cloud Vertex AI) to maintain strict data residency.
