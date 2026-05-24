"""
app/services/scoring.py
-----------------------
Deterministic scoring functions for FreelanceIQ Phase 1.

All functions are pure Python (no DB, no async, no external calls).
They are called from job_scorer.py after Claude returns its raw scores,
and override the relevant fields with reproducible, weight-configured values.
"""
from __future__ import annotations


def client_quality_score(
    hire_rate: float,
    avg_rating: float,
    jobs_posted: int,
) -> float:
    """
    Calculate client quality score as a float in [0.0, 1.0].

    Weights (must sum to 1.0):
        hire_rate   → 40 %   (likelihood this client actually hires)
        avg_rating  → 40 %   (how past freelancers rated the client)
        jobs_posted → 20 %   (volume signal — active, experienced client)

    Args:
        hire_rate:    Raw hire rate. Accepted as either 0-1 (e.g. 0.85)
                      or 0-100 (e.g. 85.0) — normalised automatically.
        avg_rating:   Upwork star rating. Accepted as 0-5 or 0-1.
        jobs_posted:  Total jobs posted by the client. Capped at 50 for
                      max score (≥ 50 jobs → full 20 % contribution).

    Returns:
        float in [0.0, 1.0]
    """
    # ── Normalise hire_rate to [0, 1] ────────────────────────────────────────
    h = float(hire_rate or 0)
    if h > 1.0:
        h = h / 100.0
    h = max(0.0, min(1.0, h))

    # ── Normalise avg_rating to [0, 1] ───────────────────────────────────────
    r = float(avg_rating or 0)
    if r > 1.0:
        r = r / 5.0
    r = max(0.0, min(1.0, r))

    # ── Normalise jobs_posted to [0, 1], cap at 50 ───────────────────────────
    p = max(0.0, min(1.0, int(jobs_posted or 0) / 50.0))

    return round((h * 0.40) + (r * 0.40) + (p * 0.20), 6)


def aggregate_score(
    skill_match: float,
    roi: float,
    competition: float,
    client_quality: float,
) -> float:
    """
    Compute the weighted aggregate match score as a float in [0.0, 1.0].

    Reads weight constants from app.config.settings so they can be
    overridden via environment variables without code changes.

    Default weights (must sum to 1.0 — validated at startup):
        skill_match    → 35 %  (SCORE_WEIGHT_SKILL)
        roi            → 30 %  (SCORE_WEIGHT_ROI)
        competition    → 20 %  (SCORE_WEIGHT_COMPETITION)
        client_quality → 15 %  (SCORE_WEIGHT_CLIENT_QUALITY)

    Args:
        skill_match:    Skill match score. Accepted as 0-100 or 0-1.
        roi:            Semantic relevance / ROI score. Same range.
        competition:    Competition score. Same range.
        client_quality: Client quality score. Same range.

    Returns:
        float in [0.0, 1.0]
    """
    from app.config import settings

    # ── Normalise all inputs to [0, 1] ───────────────────────────────────────
    def _norm(v: float) -> float:
        v = float(v or 0)
        return max(0.0, min(1.0, v / 100.0 if v > 1.0 else v))

    s  = _norm(skill_match)
    r  = _norm(roi)
    c  = _norm(competition)
    cq = _norm(client_quality)

    score = (
        s  * settings.SCORE_WEIGHT_SKILL
        + r  * settings.SCORE_WEIGHT_ROI
        + c  * settings.SCORE_WEIGHT_COMPETITION
        + cq * settings.SCORE_WEIGHT_CLIENT_QUALITY
    )
    return round(max(0.0, min(1.0, score)), 6)
