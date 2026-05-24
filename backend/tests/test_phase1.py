"""
tests/test_phase1.py
--------------------
Phase 1 QA unit tests — Musa's backend checks 4–8.

Run with:  pytest tests/test_phase1.py -v

No database or network required — all functions under test are pure Python.
"""
import os
import sys

# Allow running without a real .env by stubbing required env vars.
os.environ.setdefault("SECRET_KEY",       "test-secret-key-for-unit-tests")
os.environ.setdefault("JWT_SECRET",       "test-jwt-secret-for-unit-tests")
os.environ.setdefault("DATABASE_URL",     "postgresql+asyncpg://localhost/test")
os.environ.setdefault("ANTHROPIC_API_KEY","test-anthropic-key-for-unit-tests")

from app.services.scoring import client_quality_score, aggregate_score
from app.services.bid_strategy import bid_strategy_engine


# ── QA Check 4 ───────────────────────────────────────────────────────────────
# client_quality_score(hire_rate=0.85, avg_rating=4.9, jobs_posted=12)
# Manual:
#   hire_rate   → 0.85 × 0.40 = 0.3400
#   avg_rating  → (4.9 / 5.0) × 0.40 = 0.3920
#   jobs_posted → (12 / 50) × 0.20 = 0.0480
#   total       → 0.7800
class TestClientQualityScore:

    def test_roadmap_example(self):
        """Roadmap QA-4: hire_rate=0.85, avg_rating=4.9, jobs_posted=12 → ≈ 0.78"""
        score = client_quality_score(hire_rate=0.85, avg_rating=4.9, jobs_posted=12)
        assert abs(score - 0.78) < 1e-4, f"Expected ≈ 0.78, got {score}"

    def test_perfect_client(self):
        """All signals at maximum → 1.0"""
        score = client_quality_score(hire_rate=1.0, avg_rating=5.0, jobs_posted=50)
        assert score == 1.0

    def test_zero_client(self):
        """All signals at zero → 0.0"""
        score = client_quality_score(hire_rate=0.0, avg_rating=0.0, jobs_posted=0)
        assert score == 0.0

    def test_hire_rate_as_percentage(self):
        """Accepts hire_rate as 0-100 and normalises correctly"""
        score_decimal = client_quality_score(hire_rate=0.50, avg_rating=3.0, jobs_posted=10)
        score_pct     = client_quality_score(hire_rate=50.0,  avg_rating=3.0, jobs_posted=10)
        assert abs(score_decimal - score_pct) < 1e-6

    def test_avg_rating_as_05_scale(self):
        """Accepts avg_rating on 0-5 scale and normalises correctly"""
        score = client_quality_score(hire_rate=1.0, avg_rating=5.0, jobs_posted=0)
        assert abs(score - 0.80) < 1e-6  # 0.40 + 0.40 + 0.0

    def test_jobs_posted_capped_at_50(self):
        """jobs_posted ≥ 50 gives the same contribution as exactly 50"""
        score_50  = client_quality_score(hire_rate=0.0, avg_rating=0.0, jobs_posted=50)
        score_100 = client_quality_score(hire_rate=0.0, avg_rating=0.0, jobs_posted=100)
        assert score_50 == score_100

    def test_output_clamped_to_0_1(self):
        """Score must never exceed 1.0 regardless of inputs"""
        score = client_quality_score(hire_rate=2.0, avg_rating=10.0, jobs_posted=9999)
        assert 0.0 <= score <= 1.0


# ── QA Check 5 ───────────────────────────────────────────────────────────────
# aggregate_score with default weights (0.35, 0.30, 0.20, 0.15)
# Manual with skill=80, roi=70, competition=90, client_quality=60:
#   0.80 × 0.35 = 0.280
#   0.70 × 0.30 = 0.210
#   0.90 × 0.20 = 0.180
#   0.60 × 0.15 = 0.090
#   total       = 0.760
class TestAggregateScore:

    def test_known_values(self):
        """Manual weighted sum: skill=80, roi=70, comp=90, cq=60 → 0.76"""
        score = aggregate_score(
            skill_match=80.0,
            roi=70.0,
            competition=90.0,
            client_quality=60.0,
        )
        assert abs(score - 0.76) < 1e-4, f"Expected ≈ 0.76, got {score}"

    def test_weights_sum_to_1(self):
        """All inputs at 100 → output should be 1.0 (weights sum to 1.0)"""
        score = aggregate_score(
            skill_match=100.0,
            roi=100.0,
            competition=100.0,
            client_quality=100.0,
        )
        assert abs(score - 1.0) < 1e-5

    def test_all_zero(self):
        """All zero inputs → 0.0"""
        score = aggregate_score(0, 0, 0, 0)
        assert score == 0.0

    def test_accepts_decimal_inputs(self):
        """Inputs in 0-1 range are handled the same as 0-100"""
        score_pct = aggregate_score(80.0, 70.0, 90.0, 60.0)
        score_dec = aggregate_score(0.80,  0.70,  0.90,  0.60)
        assert abs(score_pct - score_dec) < 1e-6

    def test_output_clamped(self):
        """Output must always be in [0.0, 1.0]"""
        score = aggregate_score(200.0, 200.0, 200.0, 200.0)
        assert 0.0 <= score <= 1.0


# ── QA Check 6 ───────────────────────────────────────────────────────────────
# BidStrategyEngine: high-competition fixed job, user rate > budget
class TestBidStrategyHighCompetition:

    def test_strategy_is_competitive(self):
        """High competition + budget < user rate → strategy = Competitive"""
        result = bid_strategy_engine.calculate(
            budget_type="fixed",
            budget_min=100.0,
            budget_max=150.0,
            hourly_rate_min=None,
            hourly_rate_max=None,
            user_target_rate=200.0,   # much higher than client's budget
            proposals_count=25,       # high competition
            client_quality=0.85,
        )
        assert result["bid_strategy"] == "Competitive"

    def test_bid_near_lower_anchor(self):
        """High competition should push the bid below the anchor"""
        result = bid_strategy_engine.calculate(
            budget_type="fixed",
            budget_min=100.0,
            budget_max=150.0,
            hourly_rate_min=None,
            hourly_rate_max=None,
            user_target_rate=200.0,
            proposals_count=25,
            client_quality=0.50,
        )
        # Bid should be well below the anchor (150) due to competition reduction
        assert result["recommended_bid"] < 150.0

    def test_rationale_references_competition(self):
        """Rationale must mention competition"""
        result = bid_strategy_engine.calculate(
            budget_type="fixed",
            budget_min=100.0,
            budget_max=150.0,
            hourly_rate_min=None,
            hourly_rate_max=None,
            user_target_rate=200.0,
            proposals_count=25,
            client_quality=0.50,
        )
        assert "competition" in result["bid_rationale"].lower()


# ── QA Check 7 ───────────────────────────────────────────────────────────────
# BidStrategyEngine: low-competition hourly job, budget max > user rate
class TestBidStrategyLowCompetition:

    def test_strategy_is_value_or_premium(self):
        """Low competition + budget above user rate → Value or Premium"""
        result = bid_strategy_engine.calculate(
            budget_type="hourly",
            budget_min=None,
            budget_max=None,
            hourly_rate_min=50.0,
            hourly_rate_max=80.0,
            user_target_rate=45.0,    # below client max → Value strategy
            proposals_count=3,        # low competition
            client_quality=0.90,
        )
        assert result["bid_strategy"] in ("Value", "Premium")

    def test_bid_at_or_above_user_target(self):
        """Bid should be at or above user's target rate"""
        result = bid_strategy_engine.calculate(
            budget_type="hourly",
            budget_min=None,
            budget_max=None,
            hourly_rate_min=50.0,
            hourly_rate_max=80.0,
            user_target_rate=45.0,
            proposals_count=3,
            client_quality=0.90,
        )
        assert result["recommended_bid"] >= 45.0


# ── QA Check 8 ───────────────────────────────────────────────────────────────
# BidStrategyEngine: floor and ceiling enforcement
class TestBidStrategyFloorCeiling:

    def test_bid_never_above_ceiling(self):
        """Bid must never exceed budget_max × 1.15"""
        budget_max = 500.0
        result = bid_strategy_engine.calculate(
            budget_type="fixed",
            budget_min=100.0,
            budget_max=budget_max,
            hourly_rate_min=None,
            hourly_rate_max=None,
            user_target_rate=10_000.0,   # absurdly high — should still be capped
            proposals_count=0,
            client_quality=1.0,
        )
        assert result["recommended_bid"] <= budget_max * 1.15

    def test_bid_never_below_floor(self):
        """Bid must never go below budget_min × 0.75"""
        budget_min = 100.0
        result = bid_strategy_engine.calculate(
            budget_type="fixed",
            budget_min=budget_min,
            budget_max=500.0,
            hourly_rate_min=None,
            hourly_rate_max=None,
            user_target_rate=0.01,   # absurdly low — should still be floored
            proposals_count=100,
            client_quality=0.0,
        )
        assert result["recommended_bid"] >= budget_min * 0.75

    def test_absolute_floor_is_5(self):
        """No bid can be lower than $5.00 under any circumstances"""
        result = bid_strategy_engine.calculate(
            budget_type="fixed",
            budget_min=None,
            budget_max=None,
            hourly_rate_min=None,
            hourly_rate_max=None,
            user_target_rate=0.0,
            proposals_count=999,
            client_quality=0.0,
        )
        assert result["recommended_bid"] >= 5.0

    def test_range_is_10pct_around_recommended(self):
        """range_min = bid × 0.90 and range_max = bid × 1.10"""
        result = bid_strategy_engine.calculate(
            budget_type="fixed",
            budget_min=200.0,
            budget_max=400.0,
            hourly_rate_min=None,
            hourly_rate_max=None,
            user_target_rate=300.0,
            proposals_count=5,
            client_quality=0.70,
        )
        bid = result["recommended_bid"]
        assert abs(result["bid_range_min"] - round(bid * 0.90, 2)) < 0.01
        assert abs(result["bid_range_max"] - round(bid * 1.10, 2)) < 0.01

    def test_confidence_clamped(self):
        """Confidence must always be in [0.10, 1.0]"""
        result = bid_strategy_engine.calculate(
            budget_type="fixed",
            budget_min=10.0,
            budget_max=20.0,
            hourly_rate_min=None,
            hourly_rate_max=None,
            user_target_rate=5000.0,   # massive mismatch
            proposals_count=999,
            client_quality=0.0,
        )
        assert 0.10 <= result["bid_confidence"] <= 1.0
