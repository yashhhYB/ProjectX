"""Quick test script for the full pipeline v2."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.loader import load_sample_candidates
from src.ranker import run_ranking_pipeline
from src.config import SAMPLE_CANDIDATES_FILE

# Load sample
candidates = load_sample_candidates(SAMPLE_CANDIDATES_FILE)

# Run full pipeline (no embeddings — will use 0.0 for semantic score)
results = run_ranking_pipeline(
    candidates=candidates,
    use_prefilter=True,
    output_path="test_submission.csv",
)

# Show top 10 with full detail
print("\n=== TOP 10 CANDIDATES ===")
for r in results[:10]:
    c = r["candidate"]
    p = c.get("profile", {})
    title = p.get("current_title", "?")
    company = p.get("current_company", "?")
    yoe = p.get("years_of_experience", 0)
    score = r["score"]
    rank = r["rank"]

    detail = r["scores_detail"]
    print(f"  #{rank:>2} | Score: {score:.4f} | {title} at {company} ({yoe:.1f}yr)")
    print(f"       Title={detail['title_career']:.2f} Skill={detail['skill_match']:.2f} "
          f"Sem={detail.get('semantic', 0):.2f} Exp={detail['experience_fit']:.2f} "
          f"Loc={detail['location']:.2f} Edu={detail['education']:.2f} "
          f"Beh={detail['behavioral']:.2f} Career={detail['career_depth']:.2f} "
          f"Assess={detail['assessment']:.2f}")

    hp = detail.get("honeypot", False)
    if hp:
        print(f"       [!!] HONEYPOT DETECTED: {detail.get('honeypot_reasons', [])}")

    # Show reasoning preview
    reasoning = r.get("reasoning", "")
    if reasoning:
        preview = reasoning[:120] + "..." if len(reasoning) > 120 else reasoning
        print(f"       Reasoning: {preview}")
    print()

# Verify reasoning uniqueness
all_reasonings = [r["reasoning"] for r in results]
unique_count = len(set(all_reasonings))
print(f"\n=== REASONING UNIQUENESS: {unique_count}/{len(results)} ===")
if unique_count >= len(results) * 0.95:
    print("[OK] Reasoning uniqueness is excellent!")
else:
    print("[!] Some duplicate reasonings detected")
