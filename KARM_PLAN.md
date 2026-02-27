# KARM — AI-Powered HR Automation System
## Master Planning Document

---

## 1. Project Overview

**KARM** (Knowledge, Analytics, Recruiter, Manager) is an AI-powered HR automation platform that transforms how Human Resource departments operate. It replaces manual, error-prone HR workflows with intelligent, AI-driven tools — from policy Q&A to burnout detection to bias-free hiring.

### Problem It Solves
HR departments spend 60%+ of their time on repetitive tasks: answering the same policy questions, manually reviewing interview fairness, guessing which employees are burning out, and trying to match people to internal roles by gut feeling. KARM automates all of this using Google's Gemini AI, turning HR from reactive to proactive.

### Who It Is For
- **HR Managers** — get dashboards, risk alerts, and bias reports
- **Employees** — ask policy questions in their own language, see gamified performance
- **Recruiters** — detect interview bias, auto-schedule interviews, find internal talent
- **Organizations** — reduce HR overhead, improve fairness, boost retention

### Tech Stack
| Layer | Technology |
|-------|------------|
| Frontend / UI | Streamlit (Python) |
| AI / LLM | Google Gemini API (gemini-3-flash-preview) |
| PDF Parsing | pdfplumber |
| Data Processing | Pandas |
| Charts | Plotly |
| Text-to-Speech | gTTS |
| Vector Similarity | scikit-learn (cosine_similarity) |
| Data Storage | JSON + CSV files (shared data layer) |

---

## 2. Full Module List

### Module 1 — Internal Policy Ask-Me-Anything Chatbot
| Attribute | Detail |
|-----------|--------|
| **What it does** | HR uploads a company policy PDF. Any employee asks questions in plain English and gets instant answers with page/section citations. |
| **Tech** | Python, Streamlit, Gemini API, pdfplumber, scikit-learn (cosine similarity) |
| **Inputs** | Company policy PDF (uploaded via sidebar) |
| **Outputs** | AI-generated answers with source citations (page number + section) |
| **Shared Data** | Reads `employees.json` for employee context; uses uploaded PDF |
| **File** | `module1_policy_ama.py` |

### Module 2 — Employee Burnout Risk Dashboard
| Attribute | Detail |
|-----------|--------|
| **What it does** | Analyzes employee communication data and scores burnout risk 0–10. Dashboard shows red/yellow/green risk levels. |
| **Tech** | Python, Streamlit, Gemini API, Pandas, Plotly |
| **Inputs** | `communications_data.csv` (mock employee communication data) |
| **Outputs** | Burnout risk scores, visual dashboard, exportable report |
| **Shared Data** | Reads `employees.json`, reads `communications_data.csv`, writes burnout scores back to shared data |
| **File** | `module2_burnout.py` |

### Module 3 — Interview Bias Detector
| Attribute | Detail |
|-----------|--------|
| **What it does** | Flags biased interview questions (gender, caste, age, regional), classifies bias type, and gives a recruiter bias score. |
| **Tech** | Python, Streamlit, Gemini API |
| **Inputs** | Interview transcript (text or PDF file) |
| **Outputs** | Flagged questions with explanations, overall bias score, exportable PDF report |
| **Shared Data** | Reads `employees.json` for context; uses uploaded transcript |
| **File** | `module3_bias_detector.py` |

### Module 4 — Internal Job Match Agent
| Attribute | Detail |
|-----------|--------|
| **What it does** | Matches employees to internal job openings using vector similarity on skills and experience. |
| **Tech** | Python, Streamlit, Gemini API (embeddings), scikit-learn |
| **Inputs** | `employees.json`, `open_roles.json` |
| **Outputs** | Top 3 matched roles per employee with match percentage and explanation |
| **Shared Data** | Reads `employees.json` and `open_roles.json` |
| **File** | `module4_job_match.py` |

### Module 5 — Vernacular Training Bot
| Attribute | Detail |
|-----------|--------|
| **What it does** | Converts policy PDFs into interactive multilingual Q&A training modules with audio support. |
| **Tech** | Python, Streamlit, Gemini API, gTTS |
| **Inputs** | Company policy PDF, employee language preference |
| **Outputs** | Translated Q&A, audio playback, training progress tracking |
| **Shared Data** | Reads `employees.json` for language preferences; uses policy PDF |
| **File** | `module5_training_bot.py` |

### Module 6 — Gamified Performance Dashboard
| Attribute | Detail |
|-----------|--------|
| **What it does** | Turns KPI data into a gamified experience with badges, points, levels, and AI-generated personalized nudges. |
| **Tech** | Python, Streamlit, Pandas, Plotly, Gemini API |
| **Inputs** | `kpi_data.csv`, `employees.json` |
| **Outputs** | Leaderboard, badges, trend charts, personalized messages |
| **Shared Data** | Reads `employees.json` and `kpi_data.csv` |
| **File** | `module6_gamified.py` |

### Module 7 — Autonomous Interview Scheduler
| Attribute | Detail |
|-----------|--------|
| **What it does** | Simulates schedule negotiation between recruiter and candidate, proposes optimal slots, generates calendar summary. |
| **Tech** | Python, Streamlit, Gemini API, simulated calendar logic |
| **Inputs** | Recruiter availability, candidate availability |
| **Outputs** | Proposed interview slots, confirmed event summary |
| **Shared Data** | Reads `employees.json` for candidate info; reads `open_roles.json` for role context |
| **File** | `module7_scheduler.py` |

---

## 3. Shared Data Layer

All modules read from and write to a common set of data files stored in the `fake_data/` folder. This is the backbone of integration — consistent data across all modules.

### Folder Structure
```
KARM/
├── KARM_PLAN.md              # This planning document
├── fake_data/
│   ├── employees.json         # Master employee records
│   ├── communications_data.csv # Burnout analysis data
│   ├── company_policy.pdf     # HR policy document
│   ├── interview_transcript.txt # Sample interview
│   ├── open_roles.json        # Internal job openings
│   └── kpi_data.csv           # Performance KPI data
├── module1_policy_ama.py
├── module2_burnout.py
├── module3_bias_detector.py
├── module4_job_match.py
├── module5_training_bot.py
├── module6_gamified.py
├── module7_scheduler.py
├── app.py                     # Integration: unified multi-page app
└── requirements.txt           # All dependencies
```

### employees.json Schema
This is the **master record** that every module references.

```json
[
  {
    "id": "EMP001",
    "name": "Priya Sharma",
    "email": "priya.sharma@karmcorp.com",
    "department": "Engineering",
    "role": "Senior Software Engineer",
    "skills": ["Python", "Machine Learning", "Data Analysis", "SQL"],
    "join_date": "2020-03-15",
    "language_preference": "Hindi",
    "burnout_score": null,
    "kpi_score": null,
    "training_completion_percent": 0,
    "manager": "Rajesh Kumar",
    "location": "Bangalore"
  }
]
```

**Field definitions:**
| Field | Type | Used By Modules | Description |
|-------|------|-----------------|-------------|
| `id` | string | All | Unique employee ID (EMP001–EMP012) |
| `name` | string | All | Full name |
| `email` | string | 7 | Email address |
| `department` | string | 2, 4, 6 | Department name |
| `role` | string | 4, 6 | Current job title |
| `skills` | list[string] | 4 | List of skills for job matching |
| `join_date` | string | 2, 6 | ISO date of joining |
| `language_preference` | string | 5 | Preferred language for training |
| `burnout_score` | float/null | 2 | Updated by Module 2 (0–10) |
| `kpi_score` | float/null | 6 | Updated by Module 6 |
| `training_completion_percent` | int | 5 | Updated by Module 5 (0–100) |
| `manager` | string | 2 | Reporting manager name |
| `location` | string | 7 | Office location |

### communications_data.csv Schema
```
employee_id, employee_name, week, sentiment_score, message_count, after_hours_messages, flagged_keywords, avg_response_time_hours, leave_requests
EMP001, Priya Sharma, Week 1, 0.7, 45, 3, "", 1.2, 0
```

### open_roles.json Schema
```json
[
  {
    "role_id": "ROLE001",
    "title": "Machine Learning Lead",
    "department": "Engineering",
    "required_skills": ["Python", "Machine Learning", "Team Leadership"],
    "seniority": "Senior",
    "location": "Bangalore",
    "description": "Lead the ML team in building recommendation systems"
  }
]
```

### kpi_data.csv Schema
```
employee_id, employee_name, department, week, metric_name, target, actual, completion_percent
EMP001, Priya Sharma, Engineering, Week 1, Code Reviews, 10, 12, 120
```

---

## 4. Integration Map

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SHARED DATA LAYER                            │
│                                                                     │
│  employees.json ─────────── THE BACKBONE ─────────── open_roles.json│
│  communications_data.csv         │                   kpi_data.csv   │
│  company_policy.pdf              │            interview_transcript  │
│                                  │                                  │
└──────────────────────────────────┼──────────────────────────────────┘
                                   │
       ┌───────────────────────────┼────────────────────────────┐
       │                           │                            │
       ▼                           ▼                            ▼
┌─────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│  MODULE 1   │  │      MODULE 2        │  │      MODULE 3        │
│  Policy AMA │  │  Burnout Dashboard   │  │   Bias Detector      │
│             │  │                      │  │                      │
│ Reads:      │  │ Reads:               │  │ Reads:               │
│ • policy.pdf│  │ • employees.json     │  │ • transcript.txt     │
│ • employees │  │ • communications.csv │  │ • employees.json     │
│             │  │                      │  │                      │
│ Writes:     │  │ Writes:              │  │ Writes:              │
│ • (none)    │  │ • burnout_score in   │  │ • (bias report)      │
│             │  │   employees.json     │  │                      │
└─────────────┘  └──────────────────────┘  └──────────────────────┘
       │                    │                         │
       │                    ▼                         │
       │         ┌──────────────────┐                 │
       │         │    MODULE 6      │                 │
       │         │  Gamified Perf   │                 │
       │         │                  │                 │
       │         │ Reads:           │                 │
       │         │ • employees.json │                 │
       │         │ • kpi_data.csv   │                 │
       │         │                  │                 │
       │         │ Writes:          │                 │
       │         │ • kpi_score in   │                 │
       │         │   employees.json │                 │
       │         └──────────────────┘                 │
       │                                              │
       ▼                                              ▼
┌─────────────┐  ┌──────────────────┐  ┌──────────────────────┐
│  MODULE 5   │  │    MODULE 4      │  │      MODULE 7        │
│  Training   │  │  Job Match       │  │  Interview Scheduler │
│  Bot        │  │                  │  │                      │
│             │  │ Reads:           │  │ Reads:               │
│ Reads:      │  │ • employees.json │  │ • employees.json     │
│ • policy.pdf│  │ • open_roles.json│  │ • open_roles.json    │
│ • employees │  │                  │  │                      │
│             │  │ Writes:          │  │ Writes:              │
│ Writes:     │  │ • (match results)│  │ • (schedule summary) │
│ • training% │  │                  │  │                      │
│   in empls  │  │                  │  │                      │
└─────────────┘  └──────────────────┘  └──────────────────────┘

DATA FLOW:
  Module 2 writes burnout_score → Module 6 can reference it
  Module 5 writes training_completion_percent → Module 6 can reference it
  Module 4 reads skills → matches to open_roles.json
  Module 7 reads employees + open_roles → schedules interviews for matched candidates
```

---

## 5. Build Order

Ranked by simplicity and dependency. Build one at a time, test fully, then move on.

| Priority | Module | Why This Order | Est. Time |
|----------|--------|---------------|-----------|
| 1 | Module 1 — Policy AMA | Simplest. PDF upload + chat. Core AI pattern. | 1.5 hrs |
| 2 | Module 2 — Burnout Dashboard | CSV + charts + AI scoring. Visual impact for judges. | 1.5 hrs |
| 3 | Module 3 — Bias Detector | Text analysis + flagging. Strong social impact story. | 1.5 hrs |
| 4 | Module 4 — Job Match | Vector similarity on existing data. Clean logic. | 1.5 hrs |
| 5 | Module 6 — Gamified Dashboard | Fun UI, badges, charts. Crowd pleaser. | 1.5 hrs |
| 6 | Module 5 — Training Bot | Builds on Module 1's PDF logic + multilingual + TTS. | 2 hrs |
| 7 | Module 7 — Scheduler | Needs simulated calendar. Most complex interaction loop. | 2 hrs |

**Total estimated build time: ~12 hours**
**Integration: ~1–2 hours**
**Testing + polish: ~2 hours**
**Buffer: ~7–8 hours**

---

## 6. Integration Strategy

### How It Works
Every module is a self-contained Streamlit script. Integration is just wrapping them in a Streamlit multi-page app.

### Step-by-Step Integration Process

**Step 1:** Create a `pages/` folder inside `KARM/`

**Step 2:** Copy each completed module file into `pages/` with numbered prefixes:
```
pages/
├── 1_📋_Policy_AMA.py
├── 2_🔥_Burnout_Dashboard.py
├── 3_⚖️_Bias_Detector.py
├── 4_🎯_Job_Match.py
├── 5_🌐_Training_Bot.py
├── 6_🏆_Performance.py
└── 7_📅_Scheduler.py
```

**Step 3:** Create `app.py` as the home page with:
- KARM branding and logo
- Welcome message
- Quick summary of all available modules
- Sidebar navigation (handled automatically by Streamlit)

**Step 4:** Run with `streamlit run app.py`

### Why This Works for Any Number of Modules
- Streamlit's multi-page app feature auto-discovers files in `pages/`
- If we only finished 3 modules, we only put 3 files in `pages/`
- No code rewriting needed — each module already works standalone
- The `app.py` home page dynamically lists available modules

### Integration Rules
1. Every module must use `st.set_page_config()` only when run standalone
2. All modules use a shared `load_employees()` utility (defined in each file, reading from `fake_data/employees.json`)
3. The integration wrapper handles page config centrally
4. All data paths use relative paths from the project root: `fake_data/filename`

---

## 7. Demo Script

*This is a 3–4 minute walkthrough script. Read it naturally to the judges.*

---

> "Good [morning/afternoon], we're Team [YOUR TEAM NAME], and we built **KARM** — an AI-powered HR automation platform.
>
> Here's the problem: HR teams today are drowning. They answer the same policy questions hundreds of times. They can't tell which employees are burning out until they quit. They have no idea if their interviewers are asking biased questions. And matching people to internal opportunities? That's done by gut feeling.
>
> KARM fixes all of this with one unified platform powered by Google's Gemini AI.
>
> Let me show you how it works.
>
> **[Switch to Module 1 — Policy AMA]**
> Imagine you're a new employee at a company. You want to know about the work-from-home policy, but you don't want to read a 50-page handbook. With KARM, you just ask. Watch — I'll upload our company's HR policy document right here. Now I type: *'How many days can I work from home?'* And instantly, KARM gives me the exact answer, and it even tells me which page and section it found it on. No more waiting for HR to respond to emails.
>
> **[Switch to Module 2 — Burnout Dashboard]**
> Now let's look at something HR managers care deeply about — employee wellbeing. KARM analyzes communication patterns and flags employees at risk of burnout. See this dashboard? Red means high risk. I can click on any employee and see *why* they were flagged — maybe they've been sending late-night messages, or their sentiment has dropped over the past few weeks. HR can now intervene *before* someone quits.
>
> **[Switch to Module 3 — Bias Detector]**
> Here's something that sets KARM apart — fairness in hiring. When we upload an interview transcript, KARM scans every question and flags anything that might contain bias — gender, age, caste, region. Look at this one: *'Where is your family originally from?'* — that's flagged as regional bias. The recruiter gets a bias score and a full report. This makes hiring more fair and legally compliant.
>
> **[Switch to Module 4 — Job Match]**
> Instead of posting jobs and hoping the right person applies, KARM proactively matches employees to internal openings using AI. I select an employee, and instantly see their top 3 matched roles with match percentages and explanations. This reduces attrition because people find growth within the company.
>
> **[Switch to Module 5 — Training Bot]** *(if completed)*
> India is a diverse country. Not everyone reads English policy documents comfortably. KARM's training bot takes the same policy PDF and creates interactive Q&A modules in Hindi, Tamil, Telugu, and more — with audio playback. This is inclusion in action.
>
> **[Switch to Module 6 — Gamified Dashboard]** *(if completed)*
> Nobody likes boring performance reviews. KARM gamifies KPIs — employees earn badges, climb leaderboards, and get personalized AI nudges like *'You're 2 tasks away from Gold badge!'* It makes performance tracking *fun*.
>
> **[Switch to Module 7 — Scheduler]** *(if completed)*
> And finally, scheduling interviews. KARM simulates the entire negotiation — it takes recruiter and candidate availability, proposes optimal slots, handles conflicts, and generates a calendar invite. No more 10-email chains to schedule one interview.
>
> **[Back to home page]**
> That's KARM. Every module works independently, reads from a shared employee database, and can be deployed together or separately. We built this in under 24 hours using Python, Streamlit, and Google Gemini.
>
> Thank you."

---

## 8. Pitch

> **KARM is an AI-powered HR automation platform that turns your HR department from reactive to proactive.** It lets employees get instant policy answers in their own language, alerts managers to burnout risks before people quit, catches interview bias in real-time, and intelligently matches people to internal opportunities. Built on Google Gemini AI, the entire platform runs as one unified web app that HR teams can use starting today — no complex setup, no expensive enterprise licenses, just smarter HR.

---

## 9. API Keys Needed

### Google Gemini API Key (FREE) — Required for ALL modules

**Step-by-step instructions:**

1. **Open your browser** and go to: [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)

2. **Sign in** with your Google account (any Gmail account works)

3. **Click "Create API Key"** — it's a blue button on the page

4. **Select a Google Cloud project**:
   - If you don't have one, click "Create API key in new project"
   - If you have existing projects, select any one and click "Create API key in existing project"

5. **Copy the API key** — it will look something like: `AIzaSyA1B2C3D4E5F6G7H8I9J0...`

6. **Save it securely** — you'll paste this into each module when you run it. We'll store it using Streamlit's sidebar input so you never hardcode it.

> ⚠️ **IMPORTANT:** The free tier gives you 15 requests per minute and 1 million tokens per day. This is MORE than enough for a hackathon demo. Never share your API key publicly.

### No Other API Keys Needed!
All other features (PDF parsing, charts, text-to-speech) use free, offline Python libraries with no API keys required.

---

## 10. Requirements (All Modules)

```
streamlit>=1.30.0
google-generativeai>=0.8.0
pdfplumber>=0.10.0
pandas>=2.0.0
plotly>=5.18.0
scikit-learn>=1.3.0
gTTS>=2.5.0
fpdf2>=2.7.0
```

### Install Command (run once)
```bash
pip install streamlit google-generativeai pdfplumber pandas plotly scikit-learn gTTS fpdf2
```

---

## 11. Common Errors & Solutions (All Modules)

| # | Error | Cause | Fix |
|---|-------|-------|-----|
| 1 | `ModuleNotFoundError: No module named 'streamlit'` | Libraries not installed | Run `pip install streamlit google-generativeai pdfplumber pandas plotly scikit-learn gTTS fpdf2` |
| 2 | `google.api_core.exceptions.InvalidArgument: API key not valid` | Wrong or missing Gemini API key | Go to https://aistudio.google.com/apikey and create a new key |
| 3 | `FileNotFoundError: fake_data/employees.json` | Running from wrong directory | Make sure you `cd` into the `KARM` folder before running `streamlit run` |
| 4 | `ResourceExhausted: 429 Quota exceeded` | Too many Gemini API calls too fast | Wait 60 seconds and try again. Free tier = 15 requests/minute |
| 5 | `st.set_page_config() can only be called once` | Module has page config that conflicts with integration | Each module wraps `set_page_config` in `if __name__ == "__main__":` |
