"""
embeddings.py — Stage 2: Semantic embedding and similarity scoring.

Handles pre-computation and loading of sentence-transformer embeddings.
At rank time, this module only loads pre-computed numpy arrays — no model needed.
"""

import os
import numpy as np
from typing import List, Dict, Any, Optional

from src.config import EMBEDDINGS_DIR, EMBEDDING_DIM


def load_precomputed_embeddings(
    embeddings_dir: Optional[str] = None,
) -> tuple:
    """
    Load pre-computed candidate and JD embeddings from disk.

    Returns:
        Tuple of (candidate_embeddings: np.ndarray, jd_embedding: np.ndarray, candidate_ids: List[str])
    """
    edir = embeddings_dir or EMBEDDINGS_DIR

    candidate_emb_path = os.path.join(edir, "candidate_embeddings.npy")
    jd_emb_path = os.path.join(edir, "jd_embedding.npy")
    ids_path = os.path.join(edir, "candidate_ids.npy")

    if not all(os.path.exists(p) for p in [candidate_emb_path, jd_emb_path, ids_path]):
        raise FileNotFoundError(
            f"Pre-computed embeddings not found in {edir}. "
            f"Run precompute/precompute_embeddings.py first."
        )

    candidate_embeddings = np.load(candidate_emb_path)
    jd_embedding = np.load(jd_emb_path)
    candidate_ids = np.load(ids_path, allow_pickle=True).tolist()

    print(f"Loaded embeddings: {candidate_embeddings.shape[0]} candidates, dim={candidate_embeddings.shape[1]}")
    return candidate_embeddings, jd_embedding, candidate_ids


def compute_semantic_scores(
    candidate_embeddings: np.ndarray,
    jd_embedding: np.ndarray,
) -> np.ndarray:
    """
    Compute cosine similarity between each candidate embedding and the JD embedding.

    Args:
        candidate_embeddings: (N, D) array of candidate embeddings
        jd_embedding: (1, D) or (D,) array of JD embedding

    Returns:
        (N,) array of cosine similarity scores in [0, 1]
    """
    # Ensure JD embedding is 2D
    if jd_embedding.ndim == 1:
        jd_embedding = jd_embedding.reshape(1, -1)

    jd_norm = np.linalg.norm(jd_embedding, axis=1, keepdims=True)
    candidate_norms = np.linalg.norm(candidate_embeddings, axis=1, keepdims=True)

    zero_mask = (candidate_norms.flatten() == 0.0) | (jd_norm.flatten()[0] == 0.0)

    safe_jd = np.maximum(jd_norm, 1e-10)
    safe_cand = np.maximum(candidate_norms, 1e-10)

    cosine_sim = np.dot((candidate_embeddings / safe_cand), (jd_embedding / safe_jd).T).flatten()

    # Scale safely from [-1, 1] to [0, 1] range to avoid negative similarity scores
    similarities = (cosine_sim + 1.0) / 2.0

    # Fall back to a neutral score to maintain pipeline consistency
    similarities[zero_mask] = 0.5

    return similarities


def get_semantic_score_map(
    candidate_embeddings: np.ndarray,
    jd_embedding: np.ndarray,
    candidate_ids: List[str],
) -> Dict[str, float]:
    """
    Compute semantic scores and return as a dict mapping candidate_id -> score.
    """
    scores = compute_semantic_scores(candidate_embeddings, jd_embedding)
    return dict(zip(candidate_ids, scores.tolist()))
