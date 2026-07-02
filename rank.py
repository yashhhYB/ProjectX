"""
rank.py — Main entry point for the Redrob Candidate Ranking System.

Usage:
    python rank.py --candidates ./candidates.jsonl --out ./submission.csv

This is the ranking step that must complete within 5 minutes on CPU with 16GB RAM.
It loads pre-computed embeddings (run precompute/precompute_embeddings.py first).
"""

import argparse
import os
import sys
import time

# Ensure offline execution for sentence-transformers
os.environ["SENTENCE_TRANSFORMERS_HOME"] = "./.cache"

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.loader import load_candidates_jsonl
from src.ranker import run_ranking_pipeline
from src.config import EMBEDDINGS_DIR


def main():
    parser = argparse.ArgumentParser(
        description="Redrob AI Candidate Ranking System — produce top-100 ranking CSV"
    )
    parser.add_argument(
        "--candidates",
        type=str,
        required=True,
        help="Path to candidates.jsonl or candidates.jsonl.gz",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="./submission.csv",
        help="Output CSV path (default: ./submission.csv)",
    )
    parser.add_argument(
        "--embeddings-dir",
        type=str,
        default=None,
        help=f"Path to pre-computed embeddings directory (default: {EMBEDDINGS_DIR})",
    )
    parser.add_argument(
        "--no-prefilter",
        action="store_true",
        help="Skip rule-based pre-filtering (score all candidates)",
    )
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=None,
        help="Limit number of candidates to load (for testing)",
    )

    args = parser.parse_args()

    # ── Validate inputs ──
    if not os.path.exists(args.candidates):
        print(f"Error: Candidates file not found: {args.candidates}")
        sys.exit(1)

    # ── Time the ranking ──
    start_time = time.time()

    # ── Load candidates ──
    candidates = load_candidates_jsonl(args.candidates, max_candidates=args.max_candidates)

    # ── Run ranking pipeline ──
    results = run_ranking_pipeline(
        candidates=candidates,
        embeddings_dir=args.embeddings_dir,
        use_prefilter=not args.no_prefilter,
        output_path=args.out,
    )

    # ── Report timing ──
    elapsed = time.time() - start_time
    print(f"\n[TIME] Total ranking time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")

    if elapsed > 300:
        print("[!] WARNING: Exceeded 5-minute compute budget!")
    else:
        print(f"[OK] Within 5-minute budget ({300 - elapsed:.0f}s remaining)")

    return results


if __name__ == "__main__":
    main()
