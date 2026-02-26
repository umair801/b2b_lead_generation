# B2B Lead Generation System
### Project 2 of 50 — Agentic AI Portfolio | Muhammad Umair

**Live API:** https://leads.datawebify.com/docs

---

## Business Problem

Enterprise sales teams spend 20–40 hours per week on manual prospecting:
searching for companies, finding decision-maker contacts, verifying emails,
scoring fit, and writing personalized outreach. This process is slow,
inconsistent, and impossible to scale.

## Solution

A fully autonomous multi-agent pipeline that runs the entire process
end-to-end in minutes, not days.

**400+ qualified leads per week. Zero manual effort.**

---

## Business Impact

| Metric | Before | After | Change |
|---|---|---|---|
| Time per lead | 3–5 minutes manual | ~18 seconds automated | 93% faster |
| Leads per week | 50–80 (human limit) | 400+ (API limit) | 5x increase |
| Email enrichment rate | ~60% manual accuracy | 85%+ verified | +25% accuracy |
| Outreach drafting | 10–15 min per email | Instant (GPT-4o-mini) | 100% automated |
| Weekly hours saved | Baseline | 35+ hours/week | Eliminated |

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
     (CSV + Supabase + REST API)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent Framework | LangGraph |
| AI Model | OpenAI GPT-4o-mini |
| Lead Discovery | Hunter.io |
| Data Enrichment | Apollo.io |
| Database | Supabase (PostgreSQL) |
| API Framework | FastAPI |
| Deployment | Docker + Railway |
| Language | Python 3.12 |

---

## Live API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/docs` | GET | Interactive API documentation |
| `/pipeline/run` | POST | Trigger full pipeline for domain list |
| `/pipeline/status/{job_id}` | GET | Check job progress |
| `/leads` | GET | Retrieve leads with score filter |
| `/metrics` | GET | Pipeline performance metrics |

---

## Pipeline Stages

**Stage 1 — Discovery**
Hunter.io domain search identifies decision-makers at target companies.
Filters by seniority level: C-Suite, VP, Director, Manager.

**Stage 2 — Enrichment**
Apollo.io adds company intelligence: funding stage, revenue, headcount,
headquarters, tech stack, and industry classification.

**Stage 3 — Qualification**
GPT-powered ICP scoring (0–100) against configurable criteria.
Only leads scoring 60+ proceed to outreach.

**Stage 4 — Outreach**
GPT-4o-mini drafts personalized cold emails referencing funding stage,
company signals, and contact role. Each email is unique.

---

## Target Client Profile

- B2B SaaS companies scaling their sales teams
- Sales agencies managing multiple client pipelines
- FinTech and enterprise software companies
- Any organization spending 20+ hours/week on manual prospecting

---

## Engagement Model

| Tier | Scope | Investment |
|---|---|---|
| Starter | Single ICP, one domain vertical | $8,000 |
| Professional | 3 ICPs, full pipeline, API access | $18,000 |
| Enterprise | Custom agents, CRM integration, white-label | $35,000+ |

---

## Project Status

- [x] Multi-agent pipeline (LangGraph)
- [x] Live REST API (FastAPI)
- [x] Production deployment (Docker + Railway)
- [x] Custom domain (leads.datawebify.com)
- [x] Supabase database
- [x] CSV export
- [ ] CRM integration (Salesforce / HubSpot) — roadmap
- [ ] LinkedIn enrichment (Proxycurl) — roadmap
- [ ] Webhook support — roadmap

---

## Portfolio

**Website:** https://datawebify.com
**Project Page:** https://datawebify.com/projects/b2b-lead-generation
**GitHub:** https://github.com/umair801/b2b-lead-generation
**Live API:** https://leads.datawebify.com/docs
