# B2B Lead Generation System

An enterprise-grade autonomous lead generation pipeline that discovers, enriches, qualifies, and drafts personalized outreach for B2B prospects - fully automated.

**Live API:** https://leads.datawebify.com/docs

---

## Business Value

| Metric | Before | After |
|--------|--------|-------|
| Time per lead | 3–5 minutes (manual) | ~8 seconds (automated) |
| Leads per week | 20–40 (human limit) | 400+ (fully automated) |
| Outreach drafting | 30 min/email | Instant (GPT-4o-mini) |
| Team hours saved | — | 20–40 hours/week |

---

## System Architecture
```
┌─────────────────────────────────────────────┐
│              Orchestrator Agent              │
│         (LangGraph — controls flow)          │
└──────┬──────────┬──────────┬────────────────┘
       │          │          │
       ▼          ▼          ▼
 Discovery    Enrichment  Qualification
   Agent        Agent       Agent
(finds leads) (fills data) (scores fit)
       │          │          │
       └──────────┴──────────┘
                  │
                  ▼
          Outreach Agent
       (drafts personalized
           cold emails)
                  │
                  ▼
           Export Layer
     (CSV + Supabase + API)
```

---

## Pipeline Stages

**Stage 1 — Discovery**
Searches target domains via Hunter.io to find decision-makers matching the Ideal Customer Profile (VP Sales, Head of Growth, CRO, CEO at companies with 50–500 employees).

**Stage 2 — Enrichment**
Pulls company intelligence via Apollo.io — funding stage, annual revenue, headquarters, industry, technology stack. Verifies contact emails via Hunter.io.

**Stage 3 — Qualification**
Scores each lead 0–100 against ICP criteria. Leads scoring 60+ are marked as qualified. Scoring factors include industry match, company size, funding stage, location, and seniority.

**Stage 4 — Outreach**
GPT-4o-mini drafts a personalized cold email per qualified lead, referencing their funding stage, role, and company context. Emails are stored alongside lead records.

**Export Layer**
All results saved to Supabase (PostgreSQL) and exported to CSV for CRM import.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Framework | LangGraph |
| AI Model | OpenAI GPT-4o-mini |
| Lead Discovery | Hunter.io API |
| Data Enrichment | Apollo.io API |
| Database | Supabase (PostgreSQL) |
| API Layer | FastAPI |
| Deployment | Docker + Railway |
| Language | Python 3.12 |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/pipeline/run` | Trigger pipeline for a list of domains |
| GET | `/pipeline/status/{job_id}` | Check job status |
| GET | `/leads` | Retrieve leads with optional score filter |
| GET | `/metrics` | Pipeline performance metrics |

### Example: Trigger the pipeline
```bash
curl -X POST "https://leads.datawebify.com/pipeline/run" \
  -H "Content-Type: application/json" \
  -d '{"domains": ["salesloft.com", "outreach.io"], "max_leads_per_domain": 5}'
```

### Example: Get qualified leads only
```bash
curl "https://leads.datawebify.com/leads?min_score=60"
```

---

## Project Structure
```
AgAI_2_B2B_Lead_Generation/
├── agents/
│   ├── discovery/
│   │   └── discovery_agent.py      # Hunter.io domain search
│   ├── enrichment/
│   │   └── enrichment_agent.py     # Apollo.io + email verification
│   ├── qualification/
│   │   └── qualification_agent.py  # ICP scoring 0-100
│   └── outreach/
│       └── outreach_agent.py       # GPT-4o-mini email drafting
├── orchestrator.py                 # LangGraph pipeline
├── icp_config.py                   # Ideal Customer Profile definition
├── api.py                          # FastAPI wrapper
├── export.py                       # CSV + Supabase export
├── Dockerfile
├── railway.toml
├── requirements.txt
└── .env                            # API keys (never committed)
```

---

## Local Setup
```bash
# Clone the repository
git clone https://github.com/umair801/b2b_lead_generation.git
cd b2b_lead_generation

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Add your API keys to .env

# Run locally
uvicorn api:app --reload --port 8000
```

---

## Environment Variables
```env
OPENAI_API_KEY=your_openai_key
HUNTER_API_KEY=your_hunter_key
APOLLO_API_KEY=your_apollo_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

---

## Deployment

This project is containerized with Docker and deployed on Railway.
```bash
# Build Docker image
docker build -t b2b-lead-gen .

# Run container locally
docker run --env-file .env -p 8000:8000 b2b-lead-gen
```

Railway auto-deploys on every push to `main`.

---

## Target Use Cases

- B2B SaaS companies scaling outbound sales
- Sales agencies managing multiple client pipelines
- FinTech companies targeting enterprise buyers
- Any organization spending 20+ hours/week on manual prospecting

---

## Portfolio

**Muhammad Umair — Agentic AI Specialist & Enterprise Consultant**

Building enterprise-grade Agentic AI systems.

- Portfolio: [datawebify.com](https://datawebify.com)
- GitHub: [github.com/umair801](https://github.com/umair801)
