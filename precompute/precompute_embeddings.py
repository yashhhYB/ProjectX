"""
precompute_embeddings.py — One-time embedding pre-computation.

v2: Upgraded to all-mpnet-base-v2 (768-dim) for better semantic matching.
    Uses enriched candidate text (skills, certs, industry included).
    Creates more focused JD embeddings with enriched query text.

Run this ONCE before rank.py. It downloads the sentence-transformer model,
embeds all candidates + the JD, and saves the results as numpy arrays.

This step can take 10-30 minutes depending on hardware, but only needs to
run once. The rank.py step then just loads the saved arrays.

Usage:
    python precompute/precompute_embeddings.py [--candidates path] [--max-candidates N]
"""

import argparse
import os
import sys
import time
import json
import numpy as np

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.config import (
    CANDIDATES_FILE,
    EMBEDDINGS_DIR,
    MODEL_CACHE_DIR,
    EMBEDDING_MODEL_NAME,
)
from src.loader import load_candidates_jsonl, build_candidate_text, get_candidate_id
from src.jd_parser import JD_FULL_TEXT


def precompute(candidates_path: str, max_candidates: int = None):
    """Pre-compute and save embeddings for all candidates and the JD."""

    # ── Lazy import: only needed during pre-computation ──
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("Error: sentence-transformers not installed.")
        print("Run: pip install sentence-transformers")
        sys.exit(1)

    # ── Create output directory ──
    os.makedirs(EMBEDDINGS_DIR, exist_ok=True)
    os.makedirs(MODEL_CACHE_DIR, exist_ok=True)

    # ── Load model ──
    print(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
    print(f"  Model cache: {MODEL_CACHE_DIR}")
    start = time.time()
    model = SentenceTransformer(EMBEDDING_MODEL_NAME, cache_folder=MODEL_CACHE_DIR)
    print(f"  Model loaded in {time.time() - start:.1f}s")

    # ── Load candidates ──
    print(f"\nLoading candidates from: {candidates_path}")
    candidates = load_candidates_jsonl(candidates_path, max_candidates=max_candidates)

    # ── Build candidate texts ──
    print("\nBuilding enriched candidate text representations...")
    candidate_ids = []
    candidate_texts = []

    for candidate in candidates:
        cid = get_candidate_id(candidate)
        text = build_candidate_text(candidate)
        candidate_ids.append(cid)
        candidate_texts.append(text)

    print(f"  Built {len(candidate_texts)} text representations")
    print(f"  Average text length: {sum(len(t) for t in candidate_texts) / len(candidate_texts):.0f} chars")

    # ── Embed candidates ──
    print(f"\nEmbedding {len(candidate_texts)} candidates with {EMBEDDING_MODEL_NAME}...")
    print("  This may take 10-30 minutes for 100K candidates...")
    start = time.time()

    candidate_embeddings = model.encode(
        candidate_texts,
        batch_size=256,
        show_progress_bar=True,
        normalize_embeddings=True,  # Pre-normalize for cosine similarity
    )

    elapsed = time.time() - start
    print(f"  Candidate embeddings complete in {elapsed:.1f}s ({elapsed/60:.1f}min)")
    print(f"  Shape: {candidate_embeddings.shape}")

    # ── Embed JD ──
    # Enriched JD embedding with expanded keywords for better matching
    print("\nEmbedding enriched job description...")
    enriched_jd = (
        f"{JD_FULL_TEXT} "
        "RAG embeddings retrieval ranking LLM fine-tuning vector database "
        "indexing search systems PyTorch pipeline semantic search "
        "sentence-transformers FAISS Pinecone Weaviate Qdrant "
        "NLP information retrieval text understanding "
        "NDCG MRR MAP evaluation A/B testing "
        "production deployment scale real users "
        "ranking systems recommendation matching "
        "hybrid retrieval dense retrieval BM25 "
        "product company startup Series A "
        "mentor engineering team India Pune Noida "
    )
    jd_embedding = model.encode(
        [enriched_jd],
        normalize_embeddings=True,
    )
    print(f"  JD embedding shape: {jd_embedding.shape}")

    # ── Save embeddings ──
    print(f"\nSaving embeddings to: {EMBEDDINGS_DIR}")

    np.save(os.path.join(EMBEDDINGS_DIR, "candidate_embeddings.npy"), candidate_embeddings)
    np.save(os.path.join(EMBEDDINGS_DIR, "jd_embedding.npy"), jd_embedding)
    np.save(os.path.join(EMBEDDINGS_DIR, "candidate_ids.npy"), np.array(candidate_ids))

    # Save metadata
    meta = {
        "model": EMBEDDING_MODEL_NAME,
        "num_candidates": len(candidate_ids),
        "embedding_dim": candidate_embeddings.shape[1],
        "pre_normalized": True,
        "compute_time_seconds": elapsed,
        "enriched_text": True,
        "enriched_jd": True,
    }
    with open(os.path.join(EMBEDDINGS_DIR, "metadata.json"), "w") as f:
        json.dump(meta, f, indent=2)

    sizes = {
        "candidate_embeddings": os.path.getsize(os.path.join(EMBEDDINGS_DIR, "candidate_embeddings.npy")),
        "jd_embedding": os.path.getsize(os.path.join(EMBEDDINGS_DIR, "jd_embedding.npy")),
        "candidate_ids": os.path.getsize(os.path.join(EMBEDDINGS_DIR, "candidate_ids.npy")),
    }
    total_mb = sum(sizes.values()) / (1024 * 1024)
    print(f"\n  Total embeddings size: {total_mb:.1f} MB")
    print(f"  Files saved:")
    for name, size in sizes.items():
        print(f"    {name}: {size / (1024*1024):.1f} MB")

    print(f"\n[DONE] Pre-computation complete!")
    print(f"   Now run: python rank.py --candidates {candidates_path} --out submission.csv")


def main():
    parser = argparse.ArgumentParser(
        description="Pre-compute sentence-transformer embeddings for candidates and JD"
    )
    parser.add_argument(
        "--candidates",
        type=str,
        default=CANDIDATES_FILE,
        help=f"Path to candidates.jsonl (default: {CANDIDATES_FILE})",
    )
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=None,
        help="Limit number of candidates (for testing)",
    )

    args = parser.parse_args()

    if not os.path.exists(args.candidates):
        print(f"Error: Candidates file not found: {args.candidates}")
        print(f"Expected at: {args.candidates}")
        sys.exit(1)

    precompute(args.candidates, args.max_candidates)


if __name__ == "__main__":
    main()
