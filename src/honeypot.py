"""
honeypot.py — Stage 4: Enhanced Honeypot detection.
Deterministic Trap Doors & Consistency Checks.

v2: Added 3 new checks:
    - Impossible YOE vs education timeline
    - Excessive expert skills for experience level
    - Assessment vs profile domain mismatch (extended)
"""

from datetime import datetime
from typing import Dict, Any, List, Tuple
from src.config import REFERENCE_DATETIME, NON_FIT_TITLES


def detect_honeypot_signals(candidate: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Evaluates nine core dimensions of structural, biographical, and chronological consistency.
    If the returned list of failed checks is non-empty, the candidate is a honeypot.
    """
    reasons = []

    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    skills = candidate.get("skills", [])
    signals = candidate.get("redrob_signals", {})
    education = candidate.get("education", [])

    # ── 1. GitHub Link Integrity Anomaly ──
    gh_score = signals.get("github_activity_score", 0)
    if gh_score > 0:
        gh_url = profile.get("github_url") or candidate.get("github_url") or ""
        if "github.com" not in gh_url.lower():
            reasons.append("GITHUB_LINK_MISMATCH")

    # ── 2. Chronological Experience Feasibility & 3. Reversed Timelines ──
    earliest_date = None
    reversed_timeline = False

    for job in career:
        start_str = job.get("start_date")
        end_str = job.get("end_date")

        if start_str:
            try:
                start_dt = datetime.strptime(start_str, "%Y-%m-%d")
                if earliest_date is None or start_dt < earliest_date:
                    earliest_date = start_dt

                if end_str:
                    end_dt = datetime.strptime(end_str, "%Y-%m-%d")
                    if start_dt > end_dt:
                        reversed_timeline = True
            except ValueError:
                pass

    if reversed_timeline:
        reasons.append("REVERSED_TIMELINE")

    if earliest_date:
        max_days = (REFERENCE_DATETIME - earliest_date).days
        max_years = max_days / 365.25
        claimed_yoe = profile.get("years_of_experience", 0.0)
        if claimed_yoe > max_years + 0.5:
            reasons.append("CHRONOLOGICAL_IMPOSSIBILITY")

    # ── 4. Stuffed Skills Validity Check ──
    fraudulent_skills = 0
    for skill in skills:
        if skill.get("proficiency", "").lower() == "expert":
            if skill.get("duration_months", 0) == 0 and skill.get("endorsements", 0) == 0:
                fraudulent_skills += 1

    if fraudulent_skills >= 3:
        reasons.append("STUFFED_SKILLS_FRAUD")

    # ── 5. Domain Alignment Protection (Keyword Stuffer Sieve) ──
    current_title = profile.get("current_title", "").lower()
    admin_keywords = [
        "marketing", "hr", "sales", "human resources", "graphic designer",
        "administrative", "representative", "specialist", "coordinator",
        "accountant", "recruiter", "content writer",
    ]

    is_admin = any(kw in current_title for kw in admin_keywords)
    if is_admin:
        assessment_scores = signals.get("skill_assessment_scores", {})
        ml_skills = [
            "llm architecture", "deep learning", "neural networks",
            "pytorch", "transformers", "vector databases",
            "machine learning", "nlp", "ranking systems",
        ]
        high_ml_assessments = 0
        for key, score in assessment_scores.items():
            key_lower = key.lower()
            if any(ml in key_lower for ml in ml_skills) and score >= 70:
                high_ml_assessments += 1

        if high_ml_assessments >= 2:
            reasons.append("ADMIN_DOMAIN_MISMATCH")

    # ── 6. Impossible Behavioral Bot Patterns ──
    apps = signals.get("applications_submitted_30d", 0)
    response_rate = signals.get("recruiter_response_rate", 1.0)
    completion = signals.get("interview_completion_rate", 1.0)

    if apps > 15 and response_rate < 0.05 and completion == 0.0:
        reasons.append("IMPOSSIBLE_BEHAVIORAL_BOT")

    # ── 7. [NEW] Impossible YOE vs Education Timeline ──
    if education:
        latest_edu_end = None
        for edu in education:
            end_year = edu.get("end_year", 0)
            if end_year and end_year > 0:
                if latest_edu_end is None or end_year > latest_edu_end:
                    latest_edu_end = end_year

        if latest_edu_end:
            claimed_yoe = profile.get("years_of_experience", 0.0)
            # Max possible years since graduation
            max_work_years = REFERENCE_DATETIME.year - latest_edu_end
            if max_work_years > 0 and claimed_yoe > max_work_years + 1.5:
                reasons.append("YOE_VS_EDUCATION_IMPOSSIBLE")

    # ── 8. [NEW] Excessive Expert Skills for Experience Level ──
    claimed_yoe = profile.get("years_of_experience", 0.0)
    expert_count = sum(1 for s in skills if s.get("proficiency", "").lower() == "expert")

    # Someone with 3 years experience claiming 10+ expert skills is suspicious
    if claimed_yoe < 5 and expert_count >= 10:
        reasons.append("EXCESSIVE_EXPERT_CLAIMS")
    elif claimed_yoe < 3 and expert_count >= 5:
        reasons.append("EXCESSIVE_EXPERT_CLAIMS")

    # ── 9. [NEW] Zero-duration Expert Skills with High Count ──
    # Variant of stuffed skills — checks for many expert skills with 0 duration
    # even if they have some endorsements (which can be faked)
    zero_dur_experts = sum(
        1 for s in skills
        if s.get("proficiency", "").lower() == "expert"
        and s.get("duration_months", 0) == 0
    )
    if zero_dur_experts >= 5:
        reasons.append("MASS_ZERO_DURATION_EXPERTS")

    is_honeypot = len(reasons) > 0
    return is_honeypot, reasons


def filter_honeypots(
    candidates: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Scan all candidates for honeypot indicators."""
    clean = []
    honeypots = []

    for candidate in candidates:
        is_hp, reasons = detect_honeypot_signals(candidate)
        candidate["_honeypot_reasons"] = reasons
        if is_hp:
            honeypots.append(candidate)
        else:
            clean.append(candidate)

    print(f"Honeypot detection: {len(honeypots)} flagged, {len(clean)} clean")
    return clean, honeypots
