"""
ranker.py — Stage 5: Final ranking and reasoning generation.

v2: Updated to pass rank info to reasoning generator for rank-aware tone,
    integrate career depth scoring, and use enhanced honeypot detection.

Orchestrates the full pipeline: prefilter → score → honeypot check → rank → reason.
Produces the final top-100 CSV output.
"""

import csv
from typing import Dict, Any, List, Optional

from tqdm import tqdm

from src.config import TOP_K, OUTPUT_COLUMNS
from src.prefilter import prefilter_candidates
from src.embeddings import load_precomputed_embeddings, get_semantic_score_map
from src.scorer import compute_composite_score
from src.honeypot import detect_honeypot_signals


def _n(text: str) -> str:
    return text.strip().lower()


def generate_reasoning(candidate: Dict[str, Any], scores: Dict[str, float], rank: int = 0) -> str:
    """
    Generate reasoning via the rich deterministic engine.
    Passes rank for tone-appropriate reasoning.
    """
    from src.llm_reasoning import generate_reasoning as reasoning_fn
    return reasoning_fn(candidate, scores, rank=rank)


def run_ranking_pipeline(
    candidates: List[Dict[str, Any]],
    embeddings_dir: Optional[str] = None,
    use_prefilter: bool = True,
    output_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Execute the full ranking pipeline and return ranked results.

    Args:
        candidates: List of all candidate dicts
        embeddings_dir: Path to pre-computed embeddings directory
        use_prefilter: Whether to apply rule-based pre-filtering
        output_path: If provided, write CSV to this path

    Returns:
        List of ranked candidate dicts with scores and reasoning
    """
    print(f"\n{'='*60}")
    print(f"  Redrob AI Candidate Ranking Pipeline v2")
    print(f"  Candidates: {len(candidates)}")
    print(f"{'='*60}\n")

    # ── Stage 1: Pre-filter ──
    if use_prefilter:
        print("Stage 1: Rule-based pre-filtering...")
        passed, filtered = prefilter_candidates(candidates, aggressive=False)
    else:
        passed = candidates
        filtered = []

    # ── Stage 2: Load semantic scores ──
    print("\nStage 2: Loading semantic embeddings...")
    semantic_map = {}
    try:
        candidate_embs, jd_emb, emb_ids = load_precomputed_embeddings(embeddings_dir)
        semantic_map = get_semantic_score_map(candidate_embs, jd_emb, emb_ids)
        print(f"  Loaded semantic scores for {len(semantic_map)} candidates")
    except FileNotFoundError as e:
        print(f"  Warning: {e}")
        print("  Proceeding without semantic scores (using 0.0 for all)")

    # ── Stage 3: Composite scoring ──
    print("\nStage 3: Computing composite scores (with career depth + assessments)...")
    scored_candidates = []

    for candidate in tqdm(passed, desc="Scoring", unit=" candidates"):
        cid = candidate.get("candidate_id", "UNKNOWN")

        # Get semantic score for this candidate
        sem_score = semantic_map.get(cid, 0.0)

        # Compute composite (includes career depth + assessment scores)
        scores = compute_composite_score(candidate, semantic_score=sem_score)

        # Honeypot check
        is_honeypot, hp_reasons = detect_honeypot_signals(candidate)

        # Penalize honeypots heavily
        if is_honeypot:
            scores["composite"] *= 0.01  # Essentially push to bottom
            scores["honeypot"] = True
            scores["honeypot_reasons"] = hp_reasons
        else:
            scores["honeypot"] = False
            scores["honeypot_reasons"] = hp_reasons

        # Stale candidate penalty (from prefilter marking)
        if candidate.get("_is_stale", False):
            scores["composite"] *= 0.5
            scores["is_stale"] = True

        scored_candidates.append({
            "candidate": candidate,
            "scores": scores,
        })

    # Also score filtered candidates (with penalty) for completeness
    for candidate in filtered:
        cid = candidate.get("candidate_id", "UNKNOWN")
        sem_score = semantic_map.get(cid, 0.0)
        scores = compute_composite_score(candidate, semantic_score=sem_score)
        scores["composite"] *= 0.1  # Heavy penalty for filtered candidates
        scores["honeypot"] = False

        scored_candidates.append({
            "candidate": candidate,
            "scores": scores,
        })

    # ── Stage 4: Sort and select top K ──
    print(f"\nStage 4: Ranking top {TOP_K}...")
    scored_candidates.sort(
        key=lambda x: (-x["scores"]["composite"], x["candidate"].get("candidate_id", "")),
    )
    top_k = scored_candidates[:TOP_K]

    # ── Stage 5: Generate reasoning ──
    print("\nStage 5: Generating unique fact-based reasoning strings...")
    results = []
    for rank, entry in enumerate(top_k, start=1):
        candidate = entry["candidate"]
        scores = entry["scores"]
        reasoning = generate_reasoning(candidate, scores, rank=rank)

        results.append({
            "candidate_id": candidate.get("candidate_id"),
            "rank": rank,
            "score": round(scores["composite"], 6),
            "reasoning": reasoning,
            "scores_detail": scores,
            "candidate": candidate,
        })

    # ── Write CSV if output path provided ──
    if output_path:
        write_submission_csv(results, output_path)

    # ── Summary ──
    print(f"\n{'='*60}")
    print(f"  Pipeline v2 complete!")
    print(f"  Total scored: {len(scored_candidates)}")
    print(f"  Top score: {results[0]['score']:.4f}")
    print(f"  Bottom score: {results[-1]['score']:.4f}")

    # Check honeypot rate
    hp_count = sum(1 for r in results if r["scores_detail"].get("honeypot", False))
    print(f"  Honeypots in top {TOP_K}: {hp_count} ({hp_count/TOP_K*100:.1f}%)")

    if hp_count > 10:
        print(f"  [!] WARNING: Honeypot rate > 10%! Risk of disqualification!")
    else:
        print(f"  [OK] Honeypot rate OK")

    # Check reasoning uniqueness
    unique_reasons = len(set(r["reasoning"] for r in results))
    print(f"  Unique reasonings: {unique_reasons}/{TOP_K}")
    if unique_reasons < 90:
        print(f"  [!] WARNING: Too many duplicate reasonings! Improve reasoning generation.")
    else:
        print(f"  [OK] Reasoning uniqueness OK")

    print(f"{'='*60}\n")

    return results


def write_submission_csv(results: List[Dict[str, Any]], output_path: str):
    """Write the ranked results to a CSV file in the required format."""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(OUTPUT_COLUMNS)

        for entry in results:
            writer.writerow([
                entry["candidate_id"],
                entry["rank"],
                f"{entry['score']:.6f}",
                entry["reasoning"],
            ])

    print(f"  Submission CSV written to: {output_path}")
