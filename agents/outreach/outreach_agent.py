# agents/outreach/outreach_agent.py
from openai import OpenAI
from pydantic import BaseModel
from loguru import logger
from typing import Optional
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import settings
from agents.qualification.qualification_agent import QualifiedLead


class OutreachResult(BaseModel):
    contact_name: str
    contact_title: Optional[str] = None
    contact_email: Optional[str] = None
    company_name: Optional[str] = None
    qualification_score: int = 0
    email_subject: str
    email_body: str
    outreach_status: str = "drafted"


class OutreachAgent:

    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key)

    def _build_prompt(self, lead: QualifiedLead) -> str:
        return f"""You are an expert B2B sales copywriter. Write a personalized cold outreach email for the following lead.

            LEAD INFORMATION:
            - Name: {lead.contact_name}
            - Title: {lead.contact_title}
            - Company: {lead.company_name}
            - Industry: {lead.industry or 'B2B SaaS'}
            - Funding Stage: {lead.funding_stage or 'Growth stage'}
            - ICP Score: {lead.qualification_score}/100

            OUR OFFER:
            We build AI-powered lead generation systems that deliver 400+ qualified leads per week, fully automated. We replace manual prospecting that typically costs sales teams 20-40 hours per week.

            EMAIL RULES:
            - Subject line: short, curiosity-driven, no clickbait
            - Opening: reference something specific about their company or role
            - Value prop: one clear sentence on what we do and the outcome
            - Social proof: mention "sales teams at Series B-G companies"
            - CTA: ask for a 20-minute call, keep it low pressure
            - Tone: confident, peer-to-peer, not salesy
            - Length: 5-7 sentences max, no fluff
            - No em-dashes

            Respond in this exact format:
            SUBJECT: <subject line here>
            BODY: <email body here>"""

    def draft_email(self, lead: QualifiedLead) -> OutreachResult:
        """Draft a personalized cold email for a single lead."""
        logger.info(f"Drafting email for: {lead.contact_name} @ {lead.company_name}")

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert B2B sales copywriter who writes concise, personalized cold emails that get replies."
                    },
                    {
                        "role": "user",
                        "content": self._build_prompt(lead)
                    }
                ],
                temperature=0.7,
                max_tokens=400,
            )

            raw = response.choices[0].message.content.strip()

            # Parse subject and body
            subject = ""
            body = ""
            for line in raw.split("\n"):
                if line.startswith("SUBJECT:"):
                    subject = line.replace("SUBJECT:", "").strip()
                elif line.startswith("BODY:"):
                    body = line.replace("BODY:", "").strip()
                elif body:
                    body += "\n" + line

            return OutreachResult(
                contact_name=lead.contact_name,
                contact_title=lead.contact_title,
                contact_email=lead.contact_email,
                company_name=lead.company_name,
                qualification_score=lead.qualification_score,
                email_subject=subject,
                email_body=body.strip(),
            )

        except Exception as e:
            logger.error(f"Failed to draft email for {lead.contact_name}: {e}")
            return OutreachResult(
                contact_name=lead.contact_name,
                contact_title=lead.contact_title,
                contact_email=lead.contact_email,
                company_name=lead.company_name,
                qualification_score=lead.qualification_score,
                email_subject="",
                email_body="",
                outreach_status="failed",
            )

    def draft_all(self, leads: list[QualifiedLead]) -> list[OutreachResult]:
        """Draft emails for all qualified leads."""
        results = []
        qualified = [l for l in leads if l.icp_match]
        logger.info(f"Drafting emails for {len(qualified)} qualified leads")

        for lead in qualified:
            result = self.draft_email(lead)
            results.append(result)

        logger.info(f"Outreach drafting complete: {len(results)} emails written")
        return results


if __name__ == "__main__":
    from agents.discovery.discovery_agent import DiscoveryAgent
    from agents.enrichment.enrichment_agent import EnrichmentAgent
    from agents.qualification.qualification_agent import QualificationAgent

    leads = DiscoveryAgent().search_multiple_domains(["salesloft.com", "outreach.io"])
    enriched = EnrichmentAgent().enrich_all(leads)
    qualified = QualificationAgent().qualify_all(enriched)

    outreach = OutreachAgent()
    emails = outreach.draft_all(qualified)

    print(f"\nDrafted {len(emails)} emails:\n")
    for email in emails:
        print(f"TO: {email.contact_name} | {email.contact_title} | {email.contact_email}")
        print(f"SUBJECT: {email.email_subject}")
        print(f"BODY:\n{email.email_body}")
        print("-" * 60)