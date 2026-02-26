# agents/enrichment/enrichment_agent.py
"""
Step 4 (Discovery) [agents/discovery/discovery_agent.py]
Hunter Domain Search → company domain IN → contacts + emails OUT

Step 5 (Enrichment)
Apollo Org Enrichment → domain IN → industry, funding, tech stack OUT
Hunter Email Verifier → email IN → verified: True/False OUT
"""
import httpx
from pydantic import BaseModel
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Optional
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import settings
from agents.discovery.discovery_agent import DiscoveredLead


class EnrichedLead(BaseModel):
    # Carry over from discovery
    contact_name: str
    contact_title: Optional[str] = None
    contact_email: Optional[str] = None
    contact_linkedin: Optional[str] = None
    company_name: Optional[str] = None
    company_domain: Optional[str] = None

    # Enriched fields
    industry: Optional[str] = None
    employee_count: Optional[int] = None
    headquarters: Optional[str] = None
    funding_stage: Optional[str] = None
    annual_revenue: Optional[str] = None
    technology_stack: Optional[list[str]] = None
    email_verified: bool = False
    enrichment_status: str = "enriched"
    data_source: str = "hunter+apollo"


class EnrichmentAgent:
    APOLLO_URL = "https://api.apollo.io/api/v1"
    HUNTER_URL = "https://api.hunter.io/v2"

    def __init__(self) -> None:
        self.apollo_headers = {
            "Content-Type": "application/json",
            "X-Api-Key": settings.apollo_api_key,
        }
        self.hunter_key = settings.hunter_api_key

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    def enrich_company(self, domain: str) -> dict:
        """Get company signals from Apollo Organization Enrichment."""
        url = f"{self.APOLLO_URL}/organizations/enrich"
        params = {"domain": domain}

        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=self.apollo_headers, params=params)
            if response.status_code == 200:
                return response.json().get("organization", {})
            else:
                logger.warning(f"Apollo enrichment failed for {domain}: {response.status_code}")
                return {}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    def verify_email(self, email: str) -> bool:
        """Verify email deliverability via Hunter."""
        url = f"{self.HUNTER_URL}/email-verifier"
        params = {"email": email, "api_key": self.hunter_key}

        with httpx.Client(timeout=30) as client:
            response = client.get(url, params=params)
            if response.status_code == 200:
                result = response.json().get("data", {}).get("result")
                return result in ("deliverable", "accept_all")
            return False

    def enrich_lead(self, lead: DiscoveredLead) -> EnrichedLead:
        """Enrich a single lead with company signals and email verification."""
        logger.info(f"Enriching: {lead.contact_name} @ {lead.company_domain}")

        # Get company data
        org = self.enrich_company(lead.company_domain) if lead.company_domain else {}

        # Verify email
        email_verified = self.verify_email(lead.contact_email) if lead.contact_email else False

        return EnrichedLead(
            contact_name=lead.contact_name,
            contact_title=lead.contact_title,
            contact_email=lead.contact_email,
            contact_linkedin=lead.contact_linkedin,
            company_name=lead.company_name or org.get("name"),
            company_domain=lead.company_domain,
            industry=org.get("industry"),
            employee_count=org.get("num_employees"),
            headquarters=org.get("city") or org.get("country"),
            funding_stage=org.get("latest_funding_stage"),
            annual_revenue=org.get("annual_revenue_printed"),
            technology_stack=org.get("technology_names", [])[:10],
            email_verified=email_verified,
        )

    def enrich_all(self, leads: list[DiscoveredLead]) -> list[EnrichedLead]:
        """Enrich a list of leads."""
        enriched = []
        for lead in leads:
            try:
                enriched_lead = self.enrich_lead(lead)
                enriched.append(enriched_lead)
            except Exception as e:
                logger.error(f"Failed to enrich {lead.contact_name}: {e}")
                continue
        logger.info(f"Enrichment complete: {len(enriched)}/{len(leads)} leads enriched")
        return enriched


if __name__ == "__main__":
    from agents.discovery.discovery_agent import DiscoveryAgent

    # Discover leads first
    discovery = DiscoveryAgent()
    leads = discovery.search_multiple_domains(["salesloft.com", "outreach.io"])

    # Enrich them
    enricher = EnrichmentAgent()
    enriched = enricher.enrich_all(leads)

    print(f"\nEnriched {len(enriched)} leads:\n")
    for lead in enriched:
        print(f"  {lead.contact_name} | {lead.contact_title}")
        print(f"    Company: {lead.company_name} | Industry: {lead.industry}")
        print(f"    Employees: {lead.employee_count} | Funding: {lead.funding_stage}")
        print(f"    Email: {lead.contact_email} | Verified: {lead.email_verified}")
        print()