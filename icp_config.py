# icp_config.py
from pydantic import BaseModel
from typing import Optional

class ICPConfig(BaseModel):
    # Target Industries
    industries: list[str] = [
        "B2B SaaS",
        "Sales Technology",
        "Marketing Technology",
        "FinTech",
        "Enterprise Software",
        "Revenue Operations",
    ]

    # Company Size
    min_employees: int = 20
    max_employees: int = 500

    # Revenue Signals
    min_annual_revenue: Optional[str] = "$1M"
    max_annual_revenue: Optional[str] = "$50M"

    # Funding Stages (companies with budget to spend)
    target_funding_stages: list[str] = [
        "Series A",
        "Series B",
        "Series C",
        "Bootstrapped",
    ]

    # Decision Maker Titles to Target
    target_titles: list[str] = [
        "VP of Sales", "Vice President of Sales",
        "Head of Sales",
        "Chief Revenue Officer", "CRO",
        "VP of Growth", "Vice President of Growth",
        "VP of Marketing", "Vice President of Marketing",
        "Director of Sales", "Director of Marketing",
        "Director of Product", "Director of Strategy",
        "Senior Director", "Senior Vice President",
        "CEO", "Co-Founder", "Chief of Staff",
    ]
    
    # Geography
    target_locations: list[str] = [
        "United States",
        "Canada",
        "United Kingdom",
        "Australia",
    ]

    # Technology Signals (they use tools our solution integrates with)
    technology_signals: list[str] = [
        "Salesforce",
        "HubSpot",
        "Outreach",
        "Salesloft",
        "ZoomInfo",
        "LinkedIn Sales Navigator",
    ]

    # Scoring Weights (must sum to 100)
    scoring_weights: dict[str, int] = {
        "industry_match": 25,
        "company_size_match": 20,
        "title_match": 25,
        "location_match": 15,
        "technology_match": 15,
    }

    # Qualification Threshold
    min_qualification_score: int = 60  # out of 100

    # Apollo Search Keywords
    apollo_keywords: list[str] = [
        "sales automation",
        "revenue operations",
        "B2B sales",
        "lead generation",
        "sales enablement",
    ]


# Singleton instance used across all agents
icp = ICPConfig()