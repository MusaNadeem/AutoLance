"""
app/services/bid_strategy.py
----------------------------
Intelligent Bid Strategy Engine — Phase 1, R2.

Pure Python: no DB, no async, no external calls.
Each of the 8 calculation steps is documented inline.

Usage:
    from app.services.bid_strategy import bid_strategy_engine
    result = bid_strategy_engine.calculate(...)
"""
from __future__ import annotations
from typing import Optional


class BidStrategyEngine:
    """
    Calculates an optimal bid recommendation for an Upwork job posting
    using an 8-step deterministic logic chain.

    All inputs are plain scalars. The engine is completely stateless.
    """

    def calculate(
        self,
        budget_type: str,                   # "fixed" | "hourly"
        budget_min: Optional[float],
        budget_max: Optional[float],
        hourly_rate_min: Optional[float],
        hourly_rate_max: Optional[float],
        user_target_rate: float,            # freelancer's expected rate
        proposals_count: int,               # number of existing proposals
        client_quality: float,              # 0.0 – 1.0 from scoring.py
    ) -> dict:
        """
        Run the 8-step bid calculation.

        Returns:
            {
                "recommended_bid": float,
                "bid_range_min":   float,
                "bid_range_max":   float,
                "bid_strategy":    "Competitive" | "Value" | "Premium",
                "bid_rationale":   str,
                "bid_confidence":  float,  # 0.0 – 1.0
            }
        """

        # ── STEP 1: Anchor Determination ─────────────────────────────────────
        # Use the highest client-stated budget as the starting anchor.
        # Prefer budget_max (fixed) or hourly_rate_max (hourly).
        # Fall back to the min if max is absent, then to user_target_rate.
        if budget_type == "hourly":
            anchor = (
                float(hourly_rate_max) if hourly_rate_max
                else float(hourly_rate_min) if hourly_rate_min
                else float(user_target_rate)
            )
        else:  # fixed
            anchor = (
                float(budget_max) if budget_max
                else float(budget_min) if budget_min
                else float(user_target_rate)
            )

        # ── STEP 2: User Rate Alignment Check ────────────────────────────────
        # Measure how far the client's anchor deviates from the freelancer's target.
        # Positive ratio → client pays more than expected (good).
        # Negative ratio → client pays less than expected (risky).
        if user_target_rate > 0:
            rate_diff_ratio = (anchor - user_target_rate) / user_target_rate
        else:
            rate_diff_ratio = 0.0

        # Start bidding at the anchor; subsequent steps may adjust it.
        bid = anchor

        # ── STEP 3: Competition Adjustment ───────────────────────────────────
        # In saturated markets, shave the bid slightly to improve visibility.
        # High competition (≥ 20 proposals)     → −10 %
        # Moderate competition (10–19 proposals) → −5 %
        # Low competition (< 10 proposals)       → no adjustment
        if proposals_count >= 20:
            comp_factor = 0.90
            comp_label = f"high competition ({proposals_count} proposals)"
        elif proposals_count >= 10:
            comp_factor = 0.95
            comp_label = f"moderate competition ({proposals_count} proposals)"
        else:
            comp_factor = 1.00
            comp_label = f"low competition ({proposals_count} proposals)"

        bid = bid * comp_factor

        # ── STEP 4: Client Quality Adjustment ────────────────────────────────
        # Premium clients who consistently hire and rate well can afford a
        # higher-confidence bid. Low-quality clients get a defensive discount.
        # High quality (≥ 0.75) → +5 %   (they value quality, so bid confidently)
        # Low quality  (< 0.40) → −5 %   (reduce risk on a risky client)
        # Mid-tier              → no adjustment
        if client_quality >= 0.75:
            quality_factor = 1.05
            quality_label = f"high-quality client ({int(client_quality * 100)}% score)"
        elif client_quality < 0.40:
            quality_factor = 0.95
            quality_label = f"low-quality client ({int(client_quality * 100)}% score)"
        else:
            quality_factor = 1.00
            quality_label = f"mid-tier client ({int(client_quality * 100)}% score)"

        bid = bid * quality_factor

        # ── STEP 5: Floor / Ceiling Enforcement ──────────────────────────────
        # Never underbid below 75 % of the client's stated minimum.
        # Never overbid above 115 % of the client's stated maximum.
        # Hard absolute floor: $5.00 (prevents nonsensical bids on tiny budgets).
        if budget_type == "hourly":
            floor   = float(hourly_rate_min) * 0.75 if hourly_rate_min else 5.0
            ceiling = float(hourly_rate_max) * 1.15 if hourly_rate_max else bid * 2.0
        else:
            floor   = float(budget_min) * 0.75 if budget_min else 5.0
            ceiling = float(budget_max) * 1.15 if budget_max else bid * 2.0

        bid = max(floor, min(ceiling, bid))
        bid = max(5.0, round(bid, 2))

        # ── STEP 6: Acceptable Range Calculation ─────────────────────────────
        # Give the freelancer a narrow window around the recommended bid:
        #   lower bound = recommended − 10 %
        #   upper bound = recommended + 10 %
        range_min = round(bid * 0.90, 2)
        range_max = round(bid * 1.10, 2)

        # ── STEP 7: Strategy Label + Rationale ───────────────────────────────
        # Label the strategy based on how the anchor compares to the user's rate.
        # rate_diff_ratio ≥ +10 %  → "Value"       (client offers more than expected)
        # rate_diff_ratio ≤ −10 %  → "Premium"     (bidding above client's typical)
        # otherwise                → "Competitive" (anchored near market rate)
        suffix = "/hr" if budget_type == "hourly" else ""

        if proposals_count >= 20:
            strategy = "Competitive"
        elif rate_diff_ratio >= 0.10:
            strategy = "Value"
        elif rate_diff_ratio <= -0.10:
            strategy = "Premium"
        else:
            strategy = "Competitive"

        parts = [
            f"Bidding ${bid:.2f}{suffix} using a {strategy} strategy "
            f"based on the client's budget anchor of ${anchor:.2f}{suffix}."
        ]
        if comp_factor != 1.0:
            parts.append(f"Adjusted down for {comp_label}.")
        else:
            parts.append(f"No adjustment needed — {comp_label}.")

        if quality_factor > 1.0:
            parts.append(
                f"Bid raised slightly for a {quality_label}; "
                f"they hire consistently and value quality work."
            )
        elif quality_factor < 1.0:
            parts.append(
                f"Bid trimmed slightly to reduce exposure on a {quality_label}."
            )

        rationale = " ".join(parts)

        # ── STEP 8: Win Confidence Estimation ────────────────────────────────
        # Start at full confidence (1.0) and subtract for each risk factor:
        #   −0.30 if anchor is much lower than user's target rate (budget mismatch)
        #   −0.25 if high competition; −0.15 if moderate competition
        #   −0.20 if client quality is low; −0.10 if client quality is mediocre
        # Clamp final value to [0.10, 1.00].
        confidence = 1.0

        if rate_diff_ratio < -0.20:   # budget is significantly below user rate
            confidence -= 0.30

        if proposals_count >= 20:
            confidence -= 0.25
        elif proposals_count >= 10:
            confidence -= 0.15

        if client_quality < 0.40:
            confidence -= 0.20
        elif client_quality < 0.60:
            confidence -= 0.10

        confidence = round(max(0.10, min(1.0, confidence)), 2)

        return {
            "recommended_bid": bid,
            "bid_range_min":   range_min,
            "bid_range_max":   range_max,
            "bid_strategy":    strategy,
            "bid_rationale":   rationale,
            "bid_confidence":  confidence,
        }


# Module-level singleton — import this throughout the codebase.
bid_strategy_engine = BidStrategyEngine()
