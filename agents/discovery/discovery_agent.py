# agents/discovery/discovery_agent.py
import httpx
from pydantic import BaseModel
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Optional
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import settings
from icp_config import icp


class DiscoveredLead(BaseModel):
    contact_name: str
    contact_title: Optional[str] = None
    contact_email: Optional[str] = None
    contact_linkedin: Optional[str] = None
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    data_source: str = "hunter"


class DiscoveryAgent:
    BASE_URL = "https://api.hunter.io/v2"

    def __init__(self) -> None:
        self.api_key = settings.hunter_api_key

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    def search_domain(self, domain: str) -> list[DiscoveredLead]:
        """Search Hunter.io for decision-makers at a given company domain."""
        url = f"{self.BASE_URL}/domain-search"
        params = {
            "domain": domain,
            "api_key": self.api_key,
            "limit": 10,
            "type": "personal",
        }

        logger.info(f"Searching Hunter.io | domain={domain}")

        with httpx.Client(timeout=30) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        emails = data.get("data", {}).get("emails", [])
        company_name = data.get("data", {}).get("organization")
        logger.info(f"Hunter returned {len(emails)} contacts for {domain}")

        for e in emails:
            print(f"  RAW TITLE: '{e.get('position')}'")

        results = []
        for e in emails:
            # Filter for decision-maker titles only
            title = e.get("position") or ""
            is_decision_maker = any(
                t.lower() in title.lower() for t in icp.target_titles
            ) if title else False
            if not is_decision_maker:
                continue

            try:
                lead = DiscoveredLead(
                    contact_name=f"{e.get('first_name', '')} {e.get('last_name', '')}".strip(),
                    contact_title=title,
                    contact_email=e.get("value"),
                    contact_linkedin=e.get("linkedin"),
                    company_name=company_name,
                    company_domain=domain,
                )
                results.append(lead)
            except Exception as ex:
                logger.warning(f"Skipping malformed record: {ex}")
                continue

        return results

    def search_multiple_domains(self, domains: list[str]) -> list[DiscoveredLead]:
        """Search multiple domains and aggregate results."""
        all_leads = []
        for domain in domains:
            leads = self.search_domain(domain)
            all_leads.extend(leads)
            logger.info(f"Running total: {len(all_leads)} leads")
        return all_leads


if __name__ == "__main__":
    # Target domains matching our ICP
    test_domains = [
        "hubspot.com",
        "salesloft.com",
        "outreach.io",
    ]

    agent = DiscoveryAgent()
    leads = agent.search_multiple_domains(test_domains)

    print(f"\nDiscovered {len(leads)} decision-maker leads:\n")
    for lead in leads:
        print(f"  {lead.contact_name} | {lead.contact_title} | {lead.company_domain} | {lead.contact_email}")