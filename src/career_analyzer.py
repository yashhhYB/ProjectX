"""
career_analyzer.py — Deep career analysis module.

Analyzes career trajectory, product vs consulting ratio, job-hopper detection,
production keyword density, and tenure stability. These signals go beyond
simple title matching to understand the candidate's actual career narrative.
"""

import math
from datetime import datetime
from typing import Dict, Any, List, Tuple

from src.config import (
    CONSULTING_FIRMS,
    PRODUCTION_KEYWORDS,
    TECH_INDUSTRIES,
    PRODUCT_COMPANY_SIGNALS,
    RELEVANT_CERT_KEYWORDS,
    STRONG_CERT_ISSUERS,
    JOB_HOPPER_AVG_TENURE_MONTHS,
    MIN_TENURE_STABLE,
    REFERENCE_DATETIME,
)


def _n(text: str) -> str:
    return text.strip().lower()


def calculate_average_tenure(candidate: Dict[str, Any]) -> float:
    """
    Calculate average tenure in months across all career positions.
    Returns 0.0 if no career history.
    """
    career = candidate.get("career_history", [])
    if not career:
        return 0.0

    durations = []
    for job in career:
        dur = job.get("duration_months", 0)
        if dur > 0:
            durations.append(dur)

    if not durations:
        return 0.0

    return sum(durations) / len(durations)


def detect_job_hopper(candidate: Dict[str, Any]) -> Tuple[bool, float]:
    """
    Detect if the candidate is a job-hopper (JD disqualifier:
    "title-chasers switching every 1.5 years").

    Returns:
        Tuple of (is_job_hopper: bool, avg_tenure_months: float)
    """
    avg_tenure = calculate_average_tenure(candidate)

    # If we can't determine, be generous
    if avg_tenure == 0.0:
        return False, 0.0

    is_hopper = avg_tenure < JOB_HOPPER_AVG_TENURE_MONTHS
    return is_hopper, avg_tenure


def calculate_consulting_ratio(candidate: Dict[str, Any]) -> float:
    """
    Calculate what fraction of career was spent at consulting firms.
    Returns float in [0.0, 1.0].

    Unlike the binary prefilter check, this gives partial credit
    for mixed careers (some consulting + some product).
    """
    career = candidate.get("career_history", [])
    if not career:
        return 0.0

    total_months = 0
    consulting_months = 0

    for job in career:
        company = _n(job.get("company", ""))
        dur = job.get("duration_months", 0)
        total_months += dur

        if any(firm in company for firm in CONSULTING_FIRMS):
            consulting_months += dur

    if total_months == 0:
        return 0.0

    return consulting_months / total_months


def calculate_product_company_ratio(candidate: Dict[str, Any]) -> float:
    """
    Estimate the fraction of career spent at product companies.
    Uses company_size, industry, and company name as signals.

    Small companies (1-50 employees) in tech are likely startups.
    """
    career = candidate.get("career_history", [])
    if not career:
        return 0.0

    total_months = 0
    product_months = 0

    for job in career:
        dur = job.get("duration_months", 0)
        total_months += dur

        company = _n(job.get("company", ""))
        industry = _n(job.get("industry", ""))
        company_size = job.get("company_size", "")
        desc = _n(job.get("description", ""))

        is_product = False

        # Check if company name signals product company
        if any(signal in company for signal in PRODUCT_COMPANY_SIGNALS):
            is_product = True

        # Check industry
        if any(ind in industry for ind in TECH_INDUSTRIES):
            is_product = True

        # Small tech companies are likely product companies
        if company_size in ("1-10", "11-50", "51-200"):
            if any(ind in industry for ind in TECH_INDUSTRIES):
                is_product = True

        # If description mentions product/shipping keywords
        if any(kw in desc for kw in ("product", "shipped", "users", "customers", "platform")):
            is_product = True

        # Exclude known consulting firms
        if any(firm in company for firm in CONSULTING_FIRMS):
            is_product = False

        if is_product:
            product_months += dur

    if total_months == 0:
        return 0.0

    return product_months / total_months


def calculate_production_keyword_density(candidate: Dict[str, Any]) -> float:
    """
    Score how many production-related keywords appear in career descriptions.
    Candidates who actually built and shipped things will have terms like
    "deployed", "production", "scale", "pipeline", "A/B testing", etc.

    Returns normalized score [0.0, 1.0].
    """
    career = candidate.get("career_history", [])
    profile = candidate.get("profile", {})

    all_text = _n(profile.get("summary", ""))
    for job in career:
        all_text += " " + _n(job.get("description", ""))

    if not all_text.strip():
        return 0.0

    hit_count = 0
    for keyword in PRODUCTION_KEYWORDS:
        if keyword in all_text:
            hit_count += 1

    # Normalize — having 8+ production keywords is excellent
    return min(hit_count / 8.0, 1.0)


def calculate_career_trajectory_score(candidate: Dict[str, Any]) -> float:
    """
    Score career progression. A candidate who progressed from
    junior/mid to senior/lead roles gets a bonus. Static career
    or backwards progression is penalized.
    """
    career = candidate.get("career_history", [])
    if len(career) < 2:
        return 0.5  # Not enough data

    seniority_map = {
        "intern": 0, "trainee": 0, "fresher": 0,
        "junior": 1, "associate": 1,
        "engineer": 2, "developer": 2, "analyst": 2, "scientist": 2,
        "senior": 3, "lead": 3, "staff": 3,
        "principal": 4, "architect": 4, "manager": 4,
        "director": 5, "vp": 5, "head": 5, "chief": 6,
    }

    # Sort by start_date to get chronological order
    sorted_career = sorted(career, key=lambda j: j.get("start_date", ""))

    levels = []
    for job in sorted_career:
        title = _n(job.get("title", ""))
        max_level = 2  # default to mid-level
        for keyword, level in seniority_map.items():
            if keyword in title:
                max_level = max(max_level, level)
        levels.append(max_level)

    if not levels:
        return 0.5

    # Check if career is progressing
    first_level = levels[0]
    last_level = levels[-1]

    if last_level > first_level:
        # Upward trajectory — good
        return min(0.6 + (last_level - first_level) * 0.1, 1.0)
    elif last_level == first_level:
        # Flat — neutral
        return 0.5
    else:
        # Downward — slightly negative
        return 0.3


def score_certifications(candidate: Dict[str, Any]) -> float:
    """
    Score certifications for AI/ML relevance.
    Returns [0.0, 1.0].
    """
    certs = candidate.get("certifications", [])
    if not certs:
        return 0.0

    score = 0.0
    for cert in certs:
        name = _n(cert.get("name", ""))
        issuer = _n(cert.get("issuer", ""))

        # Check if certification is relevant
        is_relevant = any(kw in name for kw in RELEVANT_CERT_KEYWORDS)
        is_strong_issuer = any(iss in issuer for iss in STRONG_CERT_ISSUERS)

        if is_relevant:
            if is_strong_issuer:
                score += 0.3  # Strong cert from recognized issuer
            else:
                score += 0.15  # Relevant but lesser-known issuer

    return min(score, 1.0)


def score_industry_alignment(candidate: Dict[str, Any]) -> float:
    """
    Score industry alignment based on current and past industries.
    """
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])

    current_industry = _n(profile.get("current_industry", ""))

    # Current industry match
    current_match = any(ind in current_industry for ind in TECH_INDUSTRIES)

    # Historical industry alignment
    tech_jobs = 0
    total_jobs = len(career) if career else 1

    for job in career:
        industry = _n(job.get("industry", ""))
        if any(ind in industry for ind in TECH_INDUSTRIES):
            tech_jobs += 1

    industry_ratio = tech_jobs / total_jobs if total_jobs > 0 else 0.0

    if current_match:
        return min(0.6 + industry_ratio * 0.4, 1.0)
    else:
        return industry_ratio * 0.5


def compute_career_depth_score(candidate: Dict[str, Any]) -> Dict[str, float]:
    """
    Compute the comprehensive career depth score and return
    all sub-components for use in reasoning.
    """
    is_hopper, avg_tenure = detect_job_hopper(candidate)
    consulting_ratio = calculate_consulting_ratio(candidate)
    product_ratio = calculate_product_company_ratio(candidate)
    production_density = calculate_production_keyword_density(candidate)
    trajectory = calculate_career_trajectory_score(candidate)
    certs = score_certifications(candidate)
    industry = score_industry_alignment(candidate)

    # Weighted combination of career depth signals
    base_score = (
        0.20 * product_ratio +
        0.25 * production_density +
        0.15 * trajectory +
        0.10 * certs +
        0.10 * industry +
        0.20 * (1.0 - consulting_ratio)  # Inverse of consulting ratio
    )

    # Job-hopper penalty (multiplicative)
    if is_hopper and avg_tenure > 0:
        # Scale penalty: avg 18mo = 0.7x, avg 12mo = 0.5x, avg 6mo = 0.3x
        hopper_mult = min(avg_tenure / JOB_HOPPER_AVG_TENURE_MONTHS, 1.0)
        base_score *= hopper_mult

    return {
        "career_depth": round(min(base_score, 1.0), 4),
        "avg_tenure_months": round(avg_tenure, 1),
        "is_job_hopper": is_hopper,
        "consulting_ratio": round(consulting_ratio, 4),
        "product_ratio": round(product_ratio, 4),
        "production_density": round(production_density, 4),
        "trajectory": round(trajectory, 4),
        "certifications": round(certs, 4),
        "industry_alignment": round(industry, 4),
    }
