# orchestrator.py
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from loguru import logger
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.discovery.discovery_agent import DiscoveryAgent, DiscoveredLead
from agents.enrichment.enrichment_agent import EnrichmentAgent, EnrichedLead
from agents.qualification.qualification_agent import QualificationAgent, QualifiedLead


# --- Pipeline State ---
class PipelineState(TypedDict):
    domains: list[str]
    discovered_leads: list[DiscoveredLead]
    enriched_leads: list[EnrichedLead]
    qualified_leads: list[QualifiedLead]
    run_summary: dict


# --- Node Functions ---
def discovery_node(state: PipelineState) -> PipelineState:
    logger.info("PIPELINE | Stage 1: Discovery")
    agent = DiscoveryAgent()
    leads = agent.search_multiple_domains(state["domains"])
    logger.info(f"PIPELINE | Discovered {len(leads)} leads")
    return {**state, "discovered_leads": leads}


def enrichment_node(state: PipelineState) -> PipelineState:
    logger.info("PIPELINE | Stage 2: Enrichment")
    agent = EnrichmentAgent()
    enriched = agent.enrich_all(state["discovered_leads"])
    logger.info(f"PIPELINE | Enriched {len(enriched)} leads")
    return {**state, "enriched_leads": enriched}


def qualification_node(state: PipelineState) -> PipelineState:
    logger.info("PIPELINE | Stage 3: Qualification")
    agent = QualificationAgent()
    qualified = agent.qualify_all(state["enriched_leads"])
    passed = [q for q in qualified if q.icp_match]
    logger.info(f"PIPELINE | Qualified {len(passed)}/{len(qualified)} leads")
    return {**state, "qualified_leads": qualified}


def summary_node(state: PipelineState) -> PipelineState:
    logger.info("PIPELINE | Stage 4: Summary")
    qualified = state["qualified_leads"]
    passed = [q for q in qualified if q.icp_match]

    summary = {
        "total_discovered": len(state["discovered_leads"]),
        "total_enriched": len(state["enriched_leads"]),
        "total_qualified": len(passed),
        "qualification_rate": f"{round(len(passed) / len(qualified) * 100)}%" if qualified else "0%",
        "top_leads": [
            {
                "name": q.contact_name,
                "title": q.contact_title,
                "company": q.company_name,
                "email": q.contact_email,
                "score": q.qualification_score,
            }
            for q in passed[:5]
        ]
    }
    return {**state, "run_summary": summary}


# --- Build Graph ---
def build_pipeline() -> StateGraph:
    graph = StateGraph(PipelineState)

    graph.add_node("discovery", discovery_node)
    graph.add_node("enrichment", enrichment_node)
    graph.add_node("qualification", qualification_node)
    graph.add_node("summary", summary_node)

    graph.set_entry_point("discovery")
    graph.add_edge("discovery", "enrichment")
    graph.add_edge("enrichment", "qualification")
    graph.add_edge("qualification", "summary")
    graph.add_edge("summary", END)

    return graph.compile()


# --- API-callable wrapper ---
def run_pipeline(domain: str) -> dict:
    """Wrapper for the API to call the pipeline for a single domain."""
    pipeline = build_pipeline()

    initial_state: PipelineState = {
        "domains": [domain],
        "discovered_leads": [],
        "enriched_leads": [],
        "qualified_leads": [],
        "run_summary": {},
    }

    final_state = pipeline.invoke(initial_state)
    summary = final_state["run_summary"]

    return {
        "leads_discovered": summary.get("total_discovered", 0),
        "leads_qualified": summary.get("total_qualified", 0)
    }


# --- Run ---
if __name__ == "__main__":
    pipeline = build_pipeline()

    initial_state: PipelineState = {
        "domains": ["salesloft.com", "outreach.io", "hubspot.com"],
        "discovered_leads": [],
        "enriched_leads": [],
        "qualified_leads": [],
        "run_summary": {},
    }

    logger.info("PIPELINE | Starting B2B Lead Generation Pipeline")
    final_state = pipeline.invoke(initial_state)

    summary = final_state["run_summary"]
    print("\n" + "="*50)
    print("PIPELINE COMPLETE")
    print("="*50)
    print(f"  Discovered : {summary['total_discovered']} leads")
    print(f"  Enriched   : {summary['total_enriched']} leads")
    print(f"  Qualified  : {summary['total_qualified']} leads")
    print(f"  Pass Rate  : {summary['qualification_rate']}")
    print("\nTop Leads:")
    for lead in summary["top_leads"]:
        print(f"  {lead['name']} | {lead['title']} | {lead['company']} | Score: {lead['score']}")
    print("="*50)