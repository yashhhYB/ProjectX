"""
prefilter.py — Stage 1: Rule-based pre-filtering.

v2: Softer filtering — lets more candidates through to be scored rather than
    hard-eliminating them. Adds staleness detection and wrong-domain detection
    as scoring penalties rather than hard filters.

    Philosophy: The composite scorer and honeypot detector are good enough to
    handle edge cases. Pre-filtering should only remove obvious non-fits.
"""

from datetime import datetime
from typing import Dict, Any, List, Tuple

from src.config import (
    NON_FIT_TITLES,
    CONSULTING_FIRMS,
    CORE_REQUIRED_SKILLS,
    NICE_TO_HAVE_SKILLS,
    STRONG_FIT_TITLES,
    MODERATE_FIT_TITLES,
    WRONG_DOMAIN_SKILLS,
    REFERENCE_DATETIME,
)


def _normalize(text: str) -> str:
    """Lowercase and strip text for comparison."""
    return text.strip().lower()


def _has_any_keyword(text: str, keywords: set) -> bool:
    """Check if text contains any of the keywords."""
    text_lower = _normalize(text)
    return any(kw in text_lower for kw in keywords)


def _get_all_career_companies(candidate: Dict[str, Any]) -> set:
    """Get set of all companies from career history (lowercased)."""
    companies = set()
    for job in candidate.get("career_history", []):
        company = _normalize(job.get("company", ""))
        if company:
            companies.add(company)
    # Also add current company
    profile = candidate.get("profile", {})
    current = _normalize(profile.get("current_company", ""))
    if current:
        companies.add(current)
    return companies


def _is_consulting_only(candidate: Dict[str, Any]) -> bool:
    """
    Check if candidate's entire career is at consulting firms.
    Having ANY product company experience is OK.
    """
    companies = _get_all_career_companies(candidate)
    if not companies:
        return False

    non_consulting = set()
    for company in companies:
        is_consulting = any(firm in company for firm in CONSULTING_FIRMS)
        if not is_consulting:
            non_consulting.add(company)

    return len(non_consulting) == 0


def _get_skill_names(candidate: Dict[str, Any]) -> set:
    """Get set of all skill names (lowercased)."""
    return {
        _normalize(s.get("name", ""))
        for s in candidate.get("skills", [])
        if s.get("name")
    }


def _has_ai_ml_relevance(candidate: Dict[str, Any]) -> bool:
    """
    Check if candidate has ANY AI/ML/Data Science relevance
    in their title, headline, summary, skills, or career history.
    """
    ai_ml_keywords = {
        "machine learning", "ml", "ai", "artificial intelligence",
        "deep learning", "data scientist", "data science",
        "nlp", "natural language", "neural network",
        "embedding", "retrieval", "ranking", "recommendation",
        "pytorch", "tensorflow", "transformers", "bert",
        "llm", "large language model", "gpt",
        "computer vision", "cv",  # Include CV — we filter domain later
        "model training", "model deployment",
        "feature engineering", "statistical modeling",
        "information retrieval", "search engineer",
        "vector database", "semantic search",
    }

    profile = candidate.get("profile", {})

    # Check title, headline, summary
    texts = [
        _normalize(profile.get("current_title", "")),
        _normalize(profile.get("headline", "")),
        _normalize(profile.get("summary", "")),
    ]

    for text in texts:
        if any(kw in text for kw in ai_ml_keywords):
            return True

    # Check skills
    skill_names = _get_skill_names(candidate)
    all_relevant = CORE_REQUIRED_SKILLS | NICE_TO_HAVE_SKILLS | {"machine learning", "deep learning", "ai", "data science"}
    if skill_names & all_relevant:
        return True

    # Check career descriptions
    for job in candidate.get("career_history", []):
        desc = _normalize(job.get("description", ""))
        title = _normalize(job.get("title", ""))
        combined = desc + " " + title
        if any(kw in combined for kw in ai_ml_keywords):
            return True

    # Check skill assessment scores for ML-related assessments
    signals = candidate.get("redrob_signals", {})
    assessments = signals.get("skill_assessment_scores", {})
    for skill_name in assessments:
        if any(kw in _normalize(skill_name) for kw in ai_ml_keywords):
            return True

    return False


def _is_non_technical_title(candidate: Dict[str, Any]) -> bool:
    """Check if current title is a clearly non-technical role."""
    profile = candidate.get("profile", {})
    title = _normalize(profile.get("current_title", ""))

    for non_fit in NON_FIT_TITLES:
        if non_fit in title:
            return True
    return False


def _is_stale_candidate(candidate: Dict[str, Any]) -> bool:
    """
    Check if candidate is effectively unavailable based on
    activity signals. Stale candidates are down-weighted, not eliminated.
    """
    signals = candidate.get("redrob_signals", {})

    last_active = signals.get("last_active_date")
    response_rate = signals.get("recruiter_response_rate", 0.5)

    if last_active:
        try:
            active_date = datetime.strptime(last_active, "%Y-%m-%d")
            days_since = (REFERENCE_DATETIME - active_date).days

            # Extremely stale: >365 days inactive AND very low response rate
            if days_since > 365 and response_rate < 0.05:
                return True
        except ValueError:
            pass

    return False


def prefilter_candidates(
    candidates: List[Dict[str, Any]],
    aggressive: bool = False,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Apply rule-based pre-filtering to eliminate obvious non-fits.

    v2: Softer filtering — only eliminates clearly non-technical candidates
    who have zero AI/ML relevance. The composite scorer handles edge cases.

    Args:
        candidates: Full list of candidate dicts
        aggressive: If True, also filter consulting-only careers

    Returns:
        Tuple of (passed_candidates, filtered_candidates)
    """
    passed = []
    filtered = []

    for candidate in candidates:
        cid = candidate.get("candidate_id", "?")
        profile = candidate.get("profile", {})
        title = _normalize(profile.get("current_title", ""))
        reasons = []

        # ── Check 1: Non-technical title ──
        is_non_tech = _is_non_technical_title(candidate)

        # ── Check 2: AI/ML relevance ──
        has_relevance = _has_ai_ml_relevance(candidate)

        # ── Check 3: Consulting-only career ──
        is_consulting = _is_consulting_only(candidate)

        # ── Decision logic ──
        # Only filter if BOTH non-technical title AND no AI/ML relevance
        # This is intentionally lenient — the scorer handles gray areas
        if is_non_tech and not has_relevance:
            reasons.append(f"Non-technical title ({title}) with no AI/ML relevance")

        # Consulting-only + aggressive + no relevance → filter
        if aggressive and is_consulting and not has_relevance:
            reasons.append("Consulting-only career with no AI/ML relevance")

        # Mark stale candidates but don't filter them
        if _is_stale_candidate(candidate):
            candidate["_is_stale"] = True

        if reasons:
            candidate["_filter_reasons"] = reasons
            filtered.append(candidate)
        else:
            passed.append(candidate)

    print(f"Pre-filter: {len(passed)} passed, {len(filtered)} filtered out of {len(candidates)} total")
    return passed, filtered
