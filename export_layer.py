# export_layer.py
import csv
import os
from datetime import datetime
from loguru import logger
from supabase import create_client
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import settings
from agents.outreach.outreach_agent import OutreachResult
from agents.qualification.qualification_agent import QualifiedLead


class ExportLayer:

    def __init__(self) -> None:
        self.supabase = create_client(settings.supabase_url, settings.supabase_key)
        self.output_dir = "data"
        os.makedirs(self.output_dir, exist_ok=True)

    def to_csv(self, leads: list[QualifiedLead], emails: list[OutreachResult]) -> str:
        """Export qualified leads + email drafts to CSV."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/leads_{timestamp}.csv"

        # Build email lookup by contact name
        email_map = {e.contact_name: e for e in emails}

        fieldnames = [
            "contact_name", "contact_title", "contact_email",
            "contact_linkedin", "company_name", "company_domain",
            "industry", "employee_count", "headquarters",
            "funding_stage", "annual_revenue", "qualification_score",
            "icp_match", "email_verified", "email_subject", "email_body",
        ]

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for lead in leads:
                outreach = email_map.get(lead.contact_name)
                writer.writerow({
                    "contact_name": lead.contact_name,
                    "contact_title": lead.contact_title,
                    "contact_email": lead.contact_email,
                    "contact_linkedin": lead.contact_linkedin,
                    "company_name": lead.company_name,
                    "company_domain": lead.company_domain,
                    "industry": lead.industry,
                    "employee_count": lead.employee_count,
                    "headquarters": lead.headquarters,
                    "funding_stage": lead.funding_stage,
                    "annual_revenue": lead.annual_revenue,
                    "qualification_score": lead.qualification_score,
                    "icp_match": lead.icp_match,
                    "email_verified": lead.email_verified,
                    "email_subject": outreach.email_subject if outreach else "",
                    "email_body": outreach.email_body if outreach else "",
                })

        logger.info(f"CSV exported: {filename}")
        return filename

    def to_supabase(self, leads: list[QualifiedLead], emails: list[OutreachResult]) -> int:
        """Save qualified leads to Supabase. Returns count of saved leads."""
        email_map = {e.contact_name: e for e in emails}
        saved = 0

        for lead in leads:
            outreach = email_map.get(lead.contact_name)
            try:
                record = {
                    "contact_name": lead.contact_name,
                    "contact_title": lead.contact_title,
                    "contact_email": lead.contact_email,
                    "contact_linkedin": lead.contact_linkedin,
                    "company_name": lead.company_name,
                    "company_domain": lead.company_domain,
                    "industry": lead.industry,
                    "employee_count": lead.employee_count,
                    "headquarters": lead.headquarters,
                    "funding_stage": lead.funding_stage,
                    "annual_revenue": lead.annual_revenue,
                    "qualification_score": lead.qualification_score,
                    "icp_match": lead.icp_match,
                    "email_verified": lead.email_verified,
                    "outreach_email_draft": outreach.email_body if outreach else None,
                    "outreach_status": "drafted" if outreach else "pending",
                    "data_source": "hunter+apollo",
                    "enrichment_status": "enriched",
                }
                self.supabase.table("leads").upsert(
                    record,
                    on_conflict="contact_email"
                ).execute()
                saved += 1
            except Exception as e:
                logger.error(f"Failed to save {lead.contact_name} to Supabase: {e}")
                continue

        logger.info(f"Supabase export complete: {saved}/{len(leads)} leads saved")
        return saved

    def export_all(self, leads: list[QualifiedLead], emails: list[OutreachResult]) -> dict:
        """Run both CSV and Supabase exports."""
        logger.info("Starting export...")
        csv_file = self.to_csv(leads, emails)
        supabase_count = self.to_supabase(leads, emails)
        return {
            "csv_file": csv_file,
            "supabase_saved": supabase_count,
            "total_leads": len(leads),
        }


if __name__ == "__main__":
    from agents.discovery.discovery_agent import DiscoveryAgent
    from agents.enrichment.enrichment_agent import EnrichmentAgent
    from agents.qualification.qualification_agent import QualificationAgent
    from agents.outreach.outreach_agent import OutreachAgent

    # Run full pipeline
    leads = DiscoveryAgent().search_multiple_domains(["salesloft.com", "outreach.io"])
    enriched = EnrichmentAgent().enrich_all(leads)
    qualified = QualificationAgent().qualify_all(enriched)
    emails = OutreachAgent().draft_all(qualified)

    # Export
    exporter = ExportLayer()
    result = exporter.export_all(qualified, emails)

    print("\n" + "="*50)
    print("EXPORT COMPLETE")
    print("="*50)
    print(f"  CSV file    : {result['csv_file']}")
    print(f"  Supabase    : {result['supabase_saved']} leads saved")
    print(f"  Total leads : {result['total_leads']}")
    print("="*50)