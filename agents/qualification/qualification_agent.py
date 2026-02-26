# agents/qualification/qualification_agent.py
from pydantic import BaseModel
from loguru import logger
from typing import Optional
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from icp_config import icp
from agents.enrichment.enrichment_agent import EnrichedLead


class QualifiedLead(BaseModel):
    # Carry over all enriched fields
    contact_name: str
    contact_title: Optional[str] = None
    contact_email: Optional[str] = None
    contact_linkedin: Optional[str] = None
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    industry: Optional[str] = None
    employee_count: Optional[int] = None
    headquarters: Optional[str] = None
    funding_stage: Optional[str] = None
    annual_revenue: Optional[str] = None
    technology_stack: Optional[list[str]] = None
    email_verified: bool = False

    # Qualification results
    qualification_score: int = 0
    qualification_notes: list[str] = []
    icp_match: bool = False


class QualificationAgent:

    def _score_industry(self, industry: Optional[str]) -> tuple[int, str]:
        """Score 0-25 based on industry match."""
        if not industry:
            return 0, "Industry unknown"
        for target in icp.industries:
            if target.lower() in industry.lower():
                return icp.scoring_weights["industry_match"], f"Industry match: {industry}"
        # Partial credit for tech-adjacent industries
        if any(k in industry.lower() for k in ["tech", "software", "internet", "information", "services"]):
            return icp.scoring_weights["industry_match"], f"Industry match: {industry}"
        return 0, f"Industry mismatch: {industry}"

    def _score_company_size(self, employee_count: Optional[int]) -> tuple[int, str]:
        """Score 0-20 based on employee count."""
        if not employee_count:
            # Give partial credit — free Apollo tier withholds headcount
            partial = icp.scoring_weights["company_size_match"] // 2
            return partial, "Employee count unavailable (partial credit)"
        if icp.min_employees <= employee_count <= icp.max_employees:
            return icp.scoring_weights["company_size_match"], f"Size match: {employee_count} employees"
        if employee_count < icp.min_employees:
            return 0, f"Too small: {employee_count} employees"
        # Large companies: partial credit (budget but slower sales cycle)
        partial = icp.scoring_weights["company_size_match"] // 2
        return partial, f"Larger than ideal: {employee_count} employees"

    def _score_title(self, title: Optional[str]) -> tuple[int, str]:
        """Score 0-25 based on decision-maker title."""
        if not title:
            return 0, "Title unknown"
        for target in icp.target_titles:
            if target.lower() in title.lower():
                return icp.scoring_weights["title_match"], f"Title match: {title}"
        return 0, f"Title not in ICP: {title}"

    def _score_location(self, headquarters: Optional[str]) -> tuple[int, str]:
        """Score 0-15 based on location."""
        if not headquarters:
            return icp.scoring_weights["location_match"] // 2, "Location unknown (partial credit)"
        for loc in icp.target_locations:
            if loc.lower() in headquarters.lower():
                return icp.scoring_weights["location_match"], f"Location match: {headquarters}"
        # US cities won't contain "United States" — give partial credit
        return icp.scoring_weights["location_match"] // 2, f"Location partial credit: {headquarters}"

    def _score_technology(self, tech_stack: Optional[list[str]]) -> tuple[int, str]:
        """Score 0-15 based on technology signals."""
        if not tech_stack:
            return icp.scoring_weights["technology_match"] // 2, "Tech stack unavailable (partial credit)"
        matches = [t for t in icp.technology_signals if any(
            t.lower() in tech.lower() for tech in tech_stack
        )]
        if matches:
            return icp.scoring_weights["technology_match"], f"Tech signals: {', '.join(matches)}"
        return 0, "No matching technology signals"

    def qualify_lead(self, lead: EnrichedLead) -> QualifiedLead:
        """Score a single lead against ICP criteria."""
        logger.info(f"Qualifying: {lead.contact_name} @ {lead.company_name}")

        notes = []
        total_score = 0

        industry_score, industry_note = self._score_industry(lead.industry)
        total_score += industry_score
        notes.append(industry_note)

        size_score, size_note = self._score_company_size(lead.employee_count)
        total_score += size_score
        notes.append(size_note)

        title_score, title_note = self._score_title(lead.contact_title)
        total_score += title_score
        notes.append(title_note)

        location_score, location_note = self._score_location(lead.headquarters)
        total_score += location_score
        notes.append(location_note)

        tech_score, tech_note = self._score_technology(lead.technology_stack)
        total_score += tech_score
        notes.append(tech_note)

        icp_match = total_score >= icp.min_qualification_score

        return QualifiedLead(
            contact_name=lead.contact_name,
            contact_title=lead.contact_title,
            contact_email=lead.contact_email,
            contact_linkedin=lead.contact_linkedin,
            company_name=lead.company_name,
            company_domain=lead.company_domain,
            industry=lead.industry,
            employee_count=lead.employee_count,
            headquarters=lead.headquarters,
            funding_stage=lead.funding_stage,
            annual_revenue=lead.annual_revenue,
            technology_stack=lead.technology_stack,
            email_verified=lead.email_verified,
            qualification_score=total_score,
            qualification_notes=notes,
            icp_match=icp_match,
        )

    def qualify_all(self, leads: list[EnrichedLead]) -> list[QualifiedLead]:
        """Qualify a list of enriched leads."""
        qualified = []
        for lead in leads:
            try:
                result = self.qualify_lead(lead)
                qualified.append(result)
            except Exception as e:
                logger.error(f"Failed to qualify {lead.contact_name}: {e}")
                continue

        qualified.sort(key=lambda x: x.qualification_score, reverse=True)
        passed = sum(1 for q in qualified if q.icp_match)
        logger.info(f"Qualification complete: {passed}/{len(qualified)} leads passed ICP threshold")
        return qualified


if __name__ == "__main__":
    from agents.discovery.discovery_agent import DiscoveryAgent
    from agents.enrichment.enrichment_agent import EnrichmentAgent

    leads = DiscoveryAgent().search_multiple_domains(["salesloft.com", "outreach.io"])
    enriched = EnrichmentAgent().enrich_all(leads)
    qualified = QualificationAgent().qualify_all(enriched)

    print(f"\nQualification Results ({len(qualified)} leads):\n")
    for lead in qualified:
        status = "QUALIFIED" if lead.icp_match else "REJECTED"
        print(f"  [{status}] {lead.contact_name} | {lead.contact_title} | Score: {lead.qualification_score}/100")
        for note in lead.qualification_notes:
            print(f"    - {note}")
        print()