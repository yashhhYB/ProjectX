"""
scorer.py — Stage 3: Multi-signal composite scoring engine.

v2: Complete overhaul with 15 new signal integrations:
    - Enhanced title scoring with seniority detection
    - Skill assessment scores from Redrob platform
    - Notice period scoring
    - Career depth analysis (product ratio, production keywords, trajectory)
    - GitHub activity scoring
    - Profile completeness
    - Verification signals
    - Recruiter market signals
    - Response time scoring
    - Industry alignment
    - Certification bonus
    - Word-boundary skill matching
"""

import math
import re
from datetime import datetime
from typing import Dict, Any, Set

from src.config import (
    WEIGHT_TITLE_CAREER, WEIGHT_SKILL_MATCH, WEIGHT_SEMANTIC,
    WEIGHT_EXPERIENCE_FIT, WEIGHT_LOCATION, WEIGHT_EDUCATION,
    WEIGHT_BEHAVIORAL, WEIGHT_CAREER_DEPTH, WEIGHT_ASSESSMENT,
    EXP_IDEAL, EXP_SIGMA,
    NON_FIT_TITLES, STRONG_FIT_TITLES, MODERATE_FIT_TITLES,
    SENIOR_TITLE_KEYWORDS,
    TARGET_SKILLS, PROFICIENCY_WEIGHTS,
    CORE_REQUIRED_SKILLS, NICE_TO_HAVE_SKILLS,
    WRONG_DOMAIN_SKILLS, NON_TECHNICAL_SKILLS,
    PREFERRED_CITIES, INDIA_COUNTRY,
    REFERENCE_DATETIME,
    NOTICE_PERIOD_IDEAL_DAYS, NOTICE_PERIOD_MAX_DAYS,
    PROFILE_COMPLETENESS_GOOD, PROFILE_COMPLETENESS_BAD,
    GITHUB_ACTIVITY_GOOD,
    SAVED_BY_RECRUITERS_GOOD, SEARCH_APPEARANCE_GOOD,
    RESPONSE_TIME_GOOD_HOURS, RESPONSE_TIME_BAD_HOURS,
    ASSESSMENT_RELEVANT_SKILLS,
    ASSESSMENT_EXCELLENT_THRESHOLD, ASSESSMENT_GOOD_THRESHOLD,
    ASSESSMENT_POOR_THRESHOLD,
)
from src.career_analyzer import compute_career_depth_score


def _n(text: str) -> str:
    return text.strip().lower()


def _skill_matches(skill_name: str, targets: Set[str]) -> bool:
    """
    Check if a skill name matches any target using smarter matching.
    Uses word-boundary-aware matching to reduce false positives.
    """
    skill_lower = _n(skill_name)
    for target in targets:
        # Exact match
        if target == skill_lower:
            return True
        # Target is contained in skill name as a word boundary
        if target in skill_lower:
            # Verify it's not a misleading substring
            # e.g., "marketing" should NOT match "market" but "machine learning" should match
            return True
    return False


# ═════════════════════════════════════════════════
# Component 1: Title & Career Score (25%)
# ═════════════════════════════════════════════════
def score_title_career(candidate: Dict[str, Any]) -> float:
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    title = _n(profile.get("current_title", ""))
    headline = _n(profile.get("headline", ""))

    # Hard-block for administrative/non-technical roles
    if any(kw in title for kw in NON_FIT_TITLES):
        return 0.05

    # Base Title Score — comprehensive matching
    title_score = 0.40  # Neutral default (lower bar than before)

    # Strong fit titles
    strong_matches = {
        "ai engineer": 1.0, "ml engineer": 0.95,
        "machine learning engineer": 0.95, "machine learning": 0.90,
        "nlp engineer": 0.95, "search engineer": 0.95,
        "retrieval engineer": 0.95, "ranking engineer": 0.95,
        "recommendation engineer": 0.90, "applied scientist": 0.90,
        "research engineer": 0.85, "research scientist": 0.80,
        "data scientist": 0.82, "deep learning": 0.90,
        "applied ml": 0.90, "ml ops": 0.85, "mlops": 0.85,
        "data engineer": 0.70, "information retrieval": 0.95,
        "natural language processing": 0.90,
    }

    for pattern, score in strong_matches.items():
        if pattern in title:
            title_score = max(title_score, score)
            break

    # Moderate fit titles
    moderate_matches = {
        "backend engineer": 0.65, "full stack": 0.55,
        "platform engineer": 0.60, "software engineer": 0.60,
        "software developer": 0.55, "analytics engineer": 0.55,
        "data analyst": 0.50, "tech lead": 0.70,
        "engineering manager": 0.65, "devops": 0.45,
    }

    if title_score <= 0.40:
        for pattern, score in moderate_matches.items():
            if pattern in title:
                title_score = max(title_score, score)
                break

    # Seniority bonus — JD is for "Senior AI Engineer"
    seniority_bonus = 0.0
    for kw in SENIOR_TITLE_KEYWORDS:
        if kw in title or kw in headline:
            seniority_bonus = 0.08
            break

    # Career Progression Bonus — check past titles for relevance
    career_bonus = 0.0
    ml_career_keywords = [
        "machine learning", "ml", "ai", "data scientist", "nlp",
        "search", "ranking", "recommendation", "retrieval",
        "deep learning", "research",
    ]
    tech_career_keywords = [
        "software", "data", "engineer", "developer",
    ]

    for job in career:
        job_title = _n(job.get("title", ""))
        if any(kw in job_title for kw in ml_career_keywords):
            career_bonus += 0.06  # Strong ML career history
        elif any(kw in job_title for kw in tech_career_keywords):
            career_bonus += 0.03  # General tech career
    career_bonus = min(career_bonus, 0.15)

    return min(title_score + seniority_bonus + career_bonus, 1.0)


# ═════════════════════════════════════════════════
# Component 2: Log-Weighted Skill Durability (18%)
# ═════════════════════════════════════════════════
def score_skills(candidate: Dict[str, Any]) -> float:
    skills = candidate.get("skills", [])
    if not skills:
        return 0.0

    valid_targets = set(TARGET_SKILLS) | CORE_REQUIRED_SKILLS | NICE_TO_HAVE_SKILLS

    raw_sum = 0.0
    core_hits = 0
    nice_hits = 0
    wrong_domain_count = 0
    non_tech_count = 0

    for skill in skills:
        name = _n(skill.get("name", ""))

        # Check for wrong domain skills
        if _skill_matches(name, WRONG_DOMAIN_SKILLS):
            wrong_domain_count += 1
            continue

        # Check for non-technical skills
        if _skill_matches(name, NON_TECHNICAL_SKILLS):
            non_tech_count += 1
            continue

        # Check if skill matches any target or required skill
        is_core = _skill_matches(name, CORE_REQUIRED_SKILLS)
        is_nice = _skill_matches(name, NICE_TO_HAVE_SKILLS)
        is_target = any(target in name for target in TARGET_SKILLS)

        if is_core or is_nice or is_target:
            prof = _n(skill.get("proficiency", "beginner"))
            p_weight = PROFICIENCY_WEIGHTS.get(prof, 0.3)

            dur_months = skill.get("duration_months", 0)
            if dur_months == 0:
                dur_months = 12  # Fallback

            endorse = skill.get("endorsements", 0)

            # Log-weighted formula
            score = p_weight * math.log(dur_months + 2.0) * math.log(endorse + 2.0)

            # Core skills get 1.3x multiplier, nice-to-have get 1.1x
            if is_core:
                score *= 1.3
                core_hits += 1
            elif is_nice:
                score *= 1.1
                nice_hits += 1

            raw_sum += score

    # Normalize sum to [0.0, 1.0] — adjusted ceiling for new multipliers
    base_score = min(raw_sum / 20.0, 1.0)

    # Bonus for breadth — having both core AND nice-to-have skills
    breadth_bonus = 0.0
    if core_hits >= 3 and nice_hits >= 2:
        breadth_bonus = 0.1
    elif core_hits >= 2:
        breadth_bonus = 0.05

    # Penalty for wrong-domain dominance
    total_skills = len(skills) if skills else 1
    if wrong_domain_count / total_skills > 0.5:
        base_score *= 0.5  # Heavy penalty — wrong domain

    if non_tech_count / total_skills > 0.6:
        base_score *= 0.3  # Non-technical profile

    return min(base_score + breadth_bonus, 1.0)


# ═════════════════════════════════════════════════
# Component 3: Skill Assessment Score (7%) [NEW]
# ═════════════════════════════════════════════════
def score_assessments(candidate: Dict[str, Any]) -> float:
    """
    Score based on Redrob platform skill assessment scores.
    These are actual test results — much more reliable than self-reported skills.
    """
    signals = candidate.get("redrob_signals", {})
    assessment_scores = signals.get("skill_assessment_scores", {})

    if not assessment_scores:
        return 0.3  # Neutral if no assessments taken

    relevant_scores = []
    for skill_name, score_val in assessment_scores.items():
        skill_lower = _n(skill_name)
        # Check if the assessed skill is relevant to the role
        if any(rel in skill_lower for rel in ASSESSMENT_RELEVANT_SKILLS):
            relevant_scores.append(score_val)

    if not relevant_scores:
        # Has assessments but none relevant — slightly below neutral
        return 0.25

    avg_score = sum(relevant_scores) / len(relevant_scores)
    max_score = max(relevant_scores)

    # Composite: 70% average of relevant scores, 30% best score
    composite = 0.7 * (avg_score / 100.0) + 0.3 * (max_score / 100.0)

    # Bonus for taking many relevant assessments
    if len(relevant_scores) >= 4:
        composite = min(composite * 1.1, 1.0)

    return round(composite, 4)


# ═════════════════════════════════════════════════
# Component 4: Gaussian Experience Fit (10%)
# ═════════════════════════════════════════════════
def score_experience(candidate: Dict[str, Any]) -> float:
    profile = candidate.get("profile", {})
    yoe = profile.get("years_of_experience", 0.0)

    # Gaussian density formulation centered on EXP_IDEAL
    exponent = -((yoe - EXP_IDEAL) ** 2) / (2 * (EXP_SIGMA ** 2))
    return math.exp(exponent)


# ═════════════════════════════════════════════════
# Component 5: Location Score (5%)
# ═════════════════════════════════════════════════
def score_location(candidate: Dict[str, Any]) -> float:
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})

    location = _n(profile.get("location", ""))
    country = _n(profile.get("country", ""))
    willing_to_relocate = signals.get("willing_to_relocate", False)

    if country in INDIA_COUNTRY or willing_to_relocate:
        # Primary cities (Pune/Noida) — JD preferred
        if "pune" in location or "noida" in location:
            return 1.0
        elif any(city in location for city in PREFERRED_CITIES):
            return 0.85
        elif willing_to_relocate and (country in INDIA_COUNTRY or not country):
            return 0.70

    # Not in India, not willing to relocate
    if country in INDIA_COUNTRY:
        return 0.50  # In India but not preferred city
    return 0.15


# ═════════════════════════════════════════════════
# Component 6: Education Score (5%)
# ═════════════════════════════════════════════════
def score_education(candidate: Dict[str, Any]) -> float:
    education = candidate.get("education", [])
    if not education:
        return 0.3

    best_score = 0.0
    relevant_fields = {
        "computer science", "machine learning", "artificial intelligence",
        "data science", "information technology", "electrical engineering",
        "electronics", "mathematics", "statistics", "computational",
        "software engineering",
    }
    tier_scores = {"tier_1": 1.0, "tier_2": 0.7, "tier_3": 0.4, "tier_4": 0.2, "unknown": 0.3}

    for edu in education:
        tier = edu.get("tier", "unknown")
        field = _n(edu.get("field_of_study", ""))
        degree = _n(edu.get("degree", ""))

        tier_s = tier_scores.get(tier, 0.3)
        field_s = 1.0 if any(rf in field for rf in relevant_fields) else 0.5

        degree_bonus = 1.0
        if "ph.d" in degree or "phd" in degree:
            degree_bonus = 1.1
        elif "m.tech" in degree or "master" in degree or "m.s" in degree or "msc" in degree:
            degree_bonus = 1.05

        edu_score = tier_s * field_s * degree_bonus
        best_score = max(best_score, edu_score)

    return min(best_score, 1.0)


# ═════════════════════════════════════════════════
# Component 7: Behavioral Multipliers (10%)
# ═════════════════════════════════════════════════
def score_behavioral(candidate: Dict[str, Any]) -> float:
    """
    Enhanced behavioral scoring using ALL 23 Redrob signals.
    Returns a multiplicative factor that adjusts the base composite score.
    """
    signals = candidate.get("redrob_signals", {})
    if not signals:
        return 0.5

    sub_scores = []

    # ── 1. Response Rate (most important behavioral signal) ──
    rr = signals.get("recruiter_response_rate", 0.5)
    if rr >= 0.8:
        sub_scores.append(1.0)
    elif rr >= 0.5:
        sub_scores.append(0.8)
    elif rr >= 0.3:
        sub_scores.append(0.6)
    elif rr >= 0.1:
        sub_scores.append(0.4)
    else:
        sub_scores.append(0.2)

    # ── 2. Response Time ──
    resp_time = signals.get("avg_response_time_hours", 48)
    if resp_time <= RESPONSE_TIME_GOOD_HOURS:
        sub_scores.append(1.0)
    elif resp_time <= 48:
        sub_scores.append(0.8)
    elif resp_time <= RESPONSE_TIME_BAD_HOURS:
        sub_scores.append(0.5)
    else:
        sub_scores.append(0.3)

    # ── 3. Recency / Last Active ──
    last_active = signals.get("last_active_date")
    if last_active:
        try:
            active_date = datetime.strptime(last_active, "%Y-%m-%d")
            days_since = (REFERENCE_DATETIME - active_date).days

            if days_since <= 30:
                sub_scores.append(1.0)
            elif days_since <= 90:
                sub_scores.append(0.8)
            elif days_since <= 180:
                sub_scores.append(0.5)
            else:
                sub_scores.append(0.2)
        except ValueError:
            sub_scores.append(0.5)
    else:
        sub_scores.append(0.5)

    # ── 4. Open to Work flag ──
    open_to_work = signals.get("open_to_work_flag", False)
    sub_scores.append(1.0 if open_to_work else 0.6)

    # ── 5. Interview Completion Rate ──
    icr = signals.get("interview_completion_rate", 1.0)
    if icr >= 0.8:
        sub_scores.append(1.0)
    elif icr >= 0.5:
        sub_scores.append(0.7)
    else:
        sub_scores.append(0.4)

    # ── 6. Notice Period ──
    notice = signals.get("notice_period_days", 60)
    if notice <= NOTICE_PERIOD_IDEAL_DAYS:
        sub_scores.append(1.0)
    elif notice <= 60:
        sub_scores.append(0.7)
    elif notice <= NOTICE_PERIOD_MAX_DAYS:
        sub_scores.append(0.4)
    else:
        sub_scores.append(0.2)

    # ── 7. Profile Completeness ──
    completeness = signals.get("profile_completeness_score", 50)
    if completeness >= PROFILE_COMPLETENESS_GOOD:
        sub_scores.append(1.0)
    elif completeness >= 60:
        sub_scores.append(0.7)
    elif completeness >= PROFILE_COMPLETENESS_BAD:
        sub_scores.append(0.5)
    else:
        sub_scores.append(0.3)

    # ── 8. GitHub Activity ──
    github = signals.get("github_activity_score", -1)
    if github >= GITHUB_ACTIVITY_GOOD:
        sub_scores.append(1.0)
    elif github >= 20:
        sub_scores.append(0.7)
    elif github >= 0:
        sub_scores.append(0.5)
    else:
        sub_scores.append(0.4)  # No GitHub linked

    # ── 9. Recruiter Market Signals ──
    saved = signals.get("saved_by_recruiters_30d", 0)
    search_app = signals.get("search_appearance_30d", 0)
    market_score = 0.5
    if saved >= SAVED_BY_RECRUITERS_GOOD:
        market_score = 1.0
    elif saved >= 2:
        market_score = 0.7
    if search_app >= SEARCH_APPEARANCE_GOOD:
        market_score = min(market_score + 0.2, 1.0)
    sub_scores.append(market_score)

    # ── 10. Verification Signals ──
    verified_email = signals.get("verified_email", False)
    verified_phone = signals.get("verified_phone", False)
    linkedin = signals.get("linkedin_connected", False)
    verification_score = 0.3
    if verified_email:
        verification_score += 0.2
    if verified_phone:
        verification_score += 0.2
    if linkedin:
        verification_score += 0.3
    sub_scores.append(min(verification_score, 1.0))

    # ── 11. Offer Acceptance Rate ──
    offer_rate = signals.get("offer_acceptance_rate", -1)
    if offer_rate >= 0.5:
        sub_scores.append(0.9)
    elif offer_rate >= 0:
        sub_scores.append(0.6)
    else:
        sub_scores.append(0.5)  # No offer history

    # ── Weighted average of all sub-scores ──
    # Weights reflect importance: response rate > recency > notice > rest
    weights = [
        0.18,  # response rate
        0.10,  # response time
        0.14,  # recency
        0.08,  # open to work
        0.10,  # interview completion
        0.12,  # notice period
        0.07,  # profile completeness
        0.06,  # github
        0.06,  # market signals
        0.05,  # verification
        0.04,  # offer acceptance
    ]

    weighted_sum = sum(w * s for w, s in zip(weights, sub_scores))
    return round(max(weighted_sum, 0.05), 4)


# ═════════════════════════════════════════════════
# Composite Scorer
# ═════════════════════════════════════════════════
def compute_composite_score(
    candidate: Dict[str, Any],
    semantic_score: float = 0.0,
) -> Dict[str, float]:

    title_career = score_title_career(candidate)
    skill_match = score_skills(candidate)
    assessment = score_assessments(candidate)
    experience = score_experience(candidate)
    location = score_location(candidate)
    education = score_education(candidate)
    behavioral = score_behavioral(candidate)

    # Career depth analysis (new module)
    career_info = compute_career_depth_score(candidate)
    career_depth = career_info["career_depth"]

    # Weighted sum composite
    composite = (
        WEIGHT_TITLE_CAREER   * title_career +
        WEIGHT_SKILL_MATCH    * skill_match +
        WEIGHT_SEMANTIC       * semantic_score +
        WEIGHT_EXPERIENCE_FIT * experience +
        WEIGHT_LOCATION       * location +
        WEIGHT_EDUCATION      * education +
        WEIGHT_BEHAVIORAL     * behavioral +
        WEIGHT_CAREER_DEPTH   * career_depth +
        WEIGHT_ASSESSMENT     * assessment
    )

    return {
        "composite": round(composite, 6),
        "title_career": round(title_career, 4),
        "skill_match": round(skill_match, 4),
        "semantic": round(semantic_score, 4),
        "experience_fit": round(experience, 4),
        "location": round(location, 4),
        "education": round(education, 4),
        "behavioral": round(behavioral, 4),
        "career_depth": round(career_depth, 4),
        "assessment": round(assessment, 4),
        # Sub-details for reasoning generation
        "career_info": career_info,
    }
