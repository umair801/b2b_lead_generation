# tests/test_icp.py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from icp_config import icp

def test_icp() -> None:
    assert sum(icp.scoring_weights.values()) == 100, "Scoring weights must sum to 100"
    assert icp.min_qualification_score > 0
    print("ICP Config loaded successfully:")
    print(f"  Industries: {icp.industries}")
    print(f"  Company size: {icp.min_employees} - {icp.max_employees} employees")
    print(f"  Target titles: {icp.target_titles}")
    print(f"  Min score to qualify: {icp.min_qualification_score}/100")
    print(f"  Scoring weights sum: {sum(icp.scoring_weights.values())}")

if __name__ == "__main__":
    test_icp()