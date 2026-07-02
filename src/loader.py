"""
loader.py — Efficient loading of candidate data from JSONL files.
Handles both full dataset (100K) and sample candidates.

v2: Enhanced build_candidate_text to include skills, certifications,
    and industry info for better semantic embedding quality.
"""

import json
import gzip
import os
from typing import List, Dict, Any, Optional

from tqdm import tqdm


def load_candidates_jsonl(filepath: str, max_candidates: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Load candidates from a JSONL file (plain or gzipped).

    Args:
        filepath: Path to candidates.jsonl or candidates.jsonl.gz
        max_candidates: Optional limit on number of candidates to load

    Returns:
        List of candidate dictionaries
    """
    candidates = []

    open_fn = gzip.open if filepath.endswith(".gz") else open
    mode = "rt" if filepath.endswith(".gz") else "r"

    with open_fn(filepath, mode, encoding="utf-8") as f:
        for i, line in enumerate(tqdm(f, desc="Loading candidates", unit=" profiles")):
            if max_candidates and i >= max_candidates:
                break
            line = line.strip()
            if not line:
                continue
            try:
                candidate = json.loads(line)
                candidates.append(candidate)
            except json.JSONDecodeError as e:
                print(f"Warning: Skipping malformed line {i + 1}: {e}")

    print(f"Loaded {len(candidates)} candidates from {os.path.basename(filepath)}")
    return candidates


def load_sample_candidates(filepath: str) -> List[Dict[str, Any]]:
    """Load candidates from a JSON array file (sample_candidates.json)."""
    with open(filepath, "r", encoding="utf-8") as f:
        candidates = json.load(f)
    print(f"Loaded {len(candidates)} sample candidates from {os.path.basename(filepath)}")
    return candidates


def build_candidate_text(candidate: Dict[str, Any]) -> str:
    """
    Build a rich unified text document for embedding.

    v2: Now includes skills, certifications, and industry alongside
    the original narrative (title + headline + summary + career descriptions).
    This gives the embedding model much more context for semantic matching.
    """
    parts = []
    profile = candidate.get("profile", {})

    # Current Title (weighted — appears first for emphasis)
    if profile.get("current_title"):
        parts.append(profile["current_title"])

    # Current company + industry context
    company_context = []
    if profile.get("current_company"):
        company_context.append(profile["current_company"])
    if profile.get("current_industry"):
        company_context.append(profile["current_industry"])
    if company_context:
        parts.append(" ".join(company_context))

    # Headline & summary
    if profile.get("headline"):
        parts.append(profile["headline"])
    if profile.get("summary"):
        parts.append(profile["summary"])

    # Career history descriptions (chronological context)
    for job in candidate.get("career_history", []):
        job_parts = []
        if job.get("title"):
            job_parts.append(job["title"])
        desc = job.get("description", "")
        if desc:
            job_parts.append(desc)
        if job_parts:
            parts.append(" ".join(job_parts))

    # Skills — add skill names as a skills section
    # This significantly improves semantic matching for skill-based queries
    skill_names = []
    for skill in candidate.get("skills", []):
        name = skill.get("name", "")
        if name:
            prof = skill.get("proficiency", "")
            if prof in ("expert", "advanced"):
                skill_names.append(f"{name} ({prof})")
            else:
                skill_names.append(name)
    if skill_names:
        parts.append("Skills: " + ", ".join(skill_names))

    # Certifications
    certs = candidate.get("certifications", [])
    if certs:
        cert_names = [c.get("name", "") for c in certs if c.get("name")]
        if cert_names:
            parts.append("Certifications: " + ", ".join(cert_names))

    # Education fields (for domain context)
    education = candidate.get("education", [])
    for edu in education:
        field = edu.get("field_of_study", "")
        degree = edu.get("degree", "")
        if field or degree:
            parts.append(f"{degree} in {field}".strip())

    return " ".join(parts)


def get_candidate_id(candidate: Dict[str, Any]) -> str:
    """Extract candidate_id from a candidate dict."""
    return candidate.get("candidate_id", "UNKNOWN")
