# api.py
import uuid
import asyncio
import logging
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Supabase client ---
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# --- FastAPI app ---
app = FastAPI(
    title="B2B Lead Generation API",
    description="Enterprise-grade autonomous lead generation pipeline",
    version="1.0.0"
)

# --- In-memory job tracker ---
jobs: dict[str, dict] = {}


# --- Request / Response models ---
class PipelineRequest(BaseModel):
    domains: list[str]
    max_leads_per_domain: int = 5


class PipelineResponse(BaseModel):
    job_id: str
    status: str
    message: str
    started_at: str


class JobStatus(BaseModel):
    job_id: str
    status: str
    domains_processed: int
    leads_discovered: int
    leads_qualified: int
    error: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None


# --- Background pipeline runner ---
async def run_pipeline_background(job_id: str, domains: list[str]):
    """Runs the full LangGraph pipeline in the background."""
    from orchestrator import run_pipeline  # import here to avoid circular imports

    jobs[job_id]["status"] = "running"
    total_qualified = 0
    total_discovered = 0

    try:
        for domain in domains:
            logger.info(f"[Job {job_id}] Processing domain: {domain}")
            result = await asyncio.to_thread(run_pipeline, domain)

            discovered = result.get("leads_discovered", 0)
            qualified = result.get("leads_qualified", 0)
            total_discovered += discovered
            total_qualified += qualified

            jobs[job_id]["domains_processed"] += 1
            jobs[job_id]["leads_discovered"] += discovered
            jobs[job_id]["leads_qualified"] += qualified

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()
        logger.info(f"[Job {job_id}] Pipeline completed. Qualified leads: {total_qualified}")

    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()
        logger.error(f"[Job {job_id}] Pipeline failed: {e}")


# --- Endpoints ---

@app.get("/")
def root():
    return {
        "product": "B2B Lead Generation System",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.post("/pipeline/run", response_model=PipelineResponse)
async def trigger_pipeline(request: PipelineRequest, background_tasks: BackgroundTasks):
    """Trigger the full lead generation pipeline for a list of domains."""
    if not request.domains:
        raise HTTPException(status_code=400, detail="At least one domain is required.")

    job_id = str(uuid.uuid4())
    started_at = datetime.utcnow().isoformat()

    jobs[job_id] = {
        "status": "queued",
        "domains_processed": 0,
        "leads_discovered": 0,
        "leads_qualified": 0,
        "error": None,
        "started_at": started_at,
        "completed_at": None
    }

    background_tasks.add_task(run_pipeline_background, job_id, request.domains)

    return PipelineResponse(
        job_id=job_id,
        status="queued",
        message=f"Pipeline started for {len(request.domains)} domain(s).",
        started_at=started_at
    )


@app.get("/pipeline/status/{job_id}", response_model=JobStatus)
def get_job_status(job_id: str):
    """Check the status of a running or completed pipeline job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job ID not found.")

    job = jobs[job_id]
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        domains_processed=job["domains_processed"],
        leads_discovered=job["leads_discovered"],
        leads_qualified=job["leads_qualified"],
        error=job.get("error"),
        started_at=job["started_at"],
        completed_at=job.get("completed_at")
    )


@app.get("/leads")
def get_leads(
    min_score: Optional[int] = Query(None, description="Minimum qualification score"),
    limit: int = Query(50, description="Max number of leads to return")
):
    """Retrieve leads from Supabase with optional score filter."""
    try:
        query = supabase.table("leads").select("*").limit(limit)

        if min_score is not None:
            query = query.gte("qualification_score", min_score)

        response = query.execute()
        leads = response.data

        return {
            "total": len(leads),
            "leads": leads
        }

    except Exception as e:
        logger.error(f"Failed to fetch leads: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/metrics")
def get_metrics():
    """Return pipeline performance metrics."""
    try:
        all_leads = supabase.table("leads").select("qualification_score, contact_email").execute().data
        total = len(all_leads)
        qualified = sum(1 for l in all_leads if (l.get("qualification_score") or 0) >= 60)
        with_email = sum(1 for l in all_leads if l.get("contact_email"))

        return {
            "total_leads_in_db": total,
            "qualified_leads": qualified,
            "qualification_rate": f"{round(qualified / total * 100, 1)}%" if total else "0%",
            "email_enrichment_rate": f"{round(with_email / total * 100, 1)}%" if total else "0%",
            "active_jobs": len([j for j in jobs.values() if j["status"] == "running"])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))