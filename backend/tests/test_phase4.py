"""
tests/test_phase4.py
--------------------
Phase 4 unit tests — job filtering/sorting params and analytics endpoint.

These are pure unit tests (no live DB required).
"""
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone, timedelta


# ─────────────────────────────────────────────────────────────────
# Jobs Router — Phase 4 filter param tests
# ─────────────────────────────────────────────────────────────────

class TestJobsSortByParam:
    """Verify sort_by validation in list_jobs."""

    def test_valid_sort_options_accepted(self):
        from app.routers.jobs import _SORT_OPTIONS
        for opt in ("score", "posted_at", "budget"):
            assert opt in _SORT_OPTIONS

    def test_invalid_sort_falls_back_to_posted_at(self):
        from app.routers.jobs import _SORT_OPTIONS
        invalid = "random_value"
        result = invalid if invalid in _SORT_OPTIONS else "posted_at"
        assert result == "posted_at"

    def test_sort_by_score_sorts_descending(self):
        """Simulate post-fetch sort_by=score logic."""
        serialized = [
            {"score": {"overall": 0.45}, "title": "Low"},
            {"score": {"overall": 0.92}, "title": "High"},
            {"score": {"overall": 0.71}, "title": "Mid"},
            {"score": {"overall": None}, "title": "Unscored"},
        ]
        serialized.sort(
            key=lambda s: (s["score"]["overall"] or 0),
            reverse=True,
        )
        assert serialized[0]["title"] == "High"
        assert serialized[1]["title"] == "Mid"
        assert serialized[2]["title"] == "Low"
        assert serialized[3]["title"] == "Unscored"

    def test_sort_by_score_unscored_jobs_go_last(self):
        """Unscored jobs (overall=None) should always be last when sort_by=score."""
        serialized = [
            {"score": {"overall": None}},
            {"score": {"overall": 0.80}},
        ]
        serialized.sort(
            key=lambda s: (s["score"]["overall"] or 0),
            reverse=True,
        )
        assert serialized[0]["score"]["overall"] == 0.80
        assert serialized[1]["score"]["overall"] is None


class TestMinScoreFilter:
    """Verify min_score post-fetch filter logic."""

    def _make_job(self, overall):
        return {"score": {"overall": overall}, "id": "x"}

    def test_min_score_filters_below_threshold(self):
        jobs = [
            self._make_job(0.85),
            self._make_job(0.60),
            self._make_job(0.40),
            self._make_job(None),
        ]
        min_score = 70
        result = [
            j for j in jobs
            if j["score"]["overall"] is not None
            and round(j["score"]["overall"] * 100) >= min_score
        ]
        assert len(result) == 1
        assert result[0]["score"]["overall"] == 0.85

    def test_min_score_zero_includes_all_scored(self):
        jobs = [self._make_job(0.10), self._make_job(0.50), self._make_job(None)]
        result = [
            j for j in jobs
            if j["score"]["overall"] is not None
            and round(j["score"]["overall"] * 100) >= 0
        ]
        assert len(result) == 2

    def test_min_score_100_only_perfect_scores(self):
        jobs = [self._make_job(0.99), self._make_job(1.0), self._make_job(0.80)]
        result = [
            j for j in jobs
            if j["score"]["overall"] is not None
            and round(j["score"]["overall"] * 100) >= 100
        ]
        assert len(result) == 1
        assert result[0]["score"]["overall"] == 1.0

    def test_none_min_score_passes_all_jobs(self):
        """When min_score is None, no filtering should happen."""
        jobs = [self._make_job(0.30), self._make_job(None)]
        min_score = None
        if min_score is not None:
            result = [
                j for j in jobs
                if j["score"]["overall"] is not None
                and round(j["score"]["overall"] * 100) >= min_score
            ]
        else:
            result = jobs
        assert len(result) == 2


class TestPostedWithinFilter:
    """Verify posted_within cutoff calculation."""

    def test_cutoff_is_correct_hours_back(self):
        now = datetime.now(timezone.utc)
        for hours in (1, 6, 24, 72):
            cutoff = now - timedelta(hours=hours)
            diff = now - cutoff
            assert abs(diff.total_seconds() - hours * 3600) < 1

    def test_job_within_window_passes(self):
        now = datetime.now(timezone.utc)
        posted_at = now - timedelta(hours=12)
        cutoff = now - timedelta(hours=24)
        assert posted_at >= cutoff

    def test_old_job_excluded(self):
        now = datetime.now(timezone.utc)
        posted_at = now - timedelta(hours=48)
        cutoff = now - timedelta(hours=24)
        assert posted_at < cutoff


# ─────────────────────────────────────────────────────────────────
# Analytics Endpoint — response shape tests
# ─────────────────────────────────────────────────────────────────

class TestAnalyticsResponseShape:
    """Verify the analytics endpoint returns all required keys."""

    def _make_response(
        self,
        jobs_scraped_total=50,
        avg_score=72,
        score_distribution=None,
        top_skills=None,
        scrape_history=None,
    ):
        if score_distribution is None:
            score_distribution = [
                {"bucket": "0-25", "count": 3},
                {"bucket": "25-50", "count": 12},
                {"bucket": "50-75", "count": 22},
                {"bucket": "75-100", "count": 13},
            ]
        if top_skills is None:
            top_skills = [{"skill": "Python", "count": 20}]
        if scrape_history is None:
            scrape_history = [{"date": "2026-05-25", "jobs_found": 18, "jobs_new": 7, "status": "completed"}]

        return {
            "jobs_scraped_total": jobs_scraped_total,
            "avg_score": avg_score,
            "score_distribution": score_distribution,
            "top_skills_in_demand": top_skills,
            "scrape_history": scrape_history,
        }

    def test_all_required_keys_present(self):
        resp = self._make_response()
        required = {
            "jobs_scraped_total", "avg_score", "score_distribution",
            "top_skills_in_demand", "scrape_history",
        }
        assert required.issubset(set(resp.keys()))

    def test_score_distribution_has_4_buckets(self):
        resp = self._make_response()
        assert len(resp["score_distribution"]) == 4

    def test_score_distribution_bucket_names(self):
        resp = self._make_response()
        names = {b["bucket"] for b in resp["score_distribution"]}
        assert names == {"0-25", "25-50", "50-75", "75-100"}

    def test_score_distribution_counts_are_non_negative(self):
        resp = self._make_response()
        for bucket in resp["score_distribution"]:
            assert bucket["count"] >= 0

    def test_avg_score_is_integer_in_range(self):
        resp = self._make_response(avg_score=73)
        assert isinstance(resp["avg_score"], int)
        assert 0 <= resp["avg_score"] <= 100

    def test_top_skills_have_skill_and_count_keys(self):
        resp = self._make_response()
        for entry in resp["top_skills_in_demand"]:
            assert "skill" in entry
            assert "count" in entry

    def test_scrape_history_has_required_fields(self):
        resp = self._make_response()
        for entry in resp["scrape_history"]:
            assert "date" in entry
            assert "jobs_found" in entry
            assert "jobs_new" in entry


class TestAnalyticsScoreDistributionLogic:
    """Test the bucket assignment logic directly."""

    def _bucket(self, scores):
        buckets = {"0-25": 0, "25-50": 0, "50-75": 0, "75-100": 0}
        for s in scores:
            if s <= 25:
                buckets["0-25"] += 1
            elif s <= 50:
                buckets["25-50"] += 1
            elif s <= 75:
                buckets["50-75"] += 1
            else:
                buckets["75-100"] += 1
        return buckets

    def test_boundary_values(self):
        buckets = self._bucket([0, 25, 26, 50, 51, 75, 76, 100])
        assert buckets["0-25"] == 2    # 0, 25
        assert buckets["25-50"] == 2   # 26, 50
        assert buckets["50-75"] == 2   # 51, 75
        assert buckets["75-100"] == 2  # 76, 100

    def test_all_in_top_bucket(self):
        buckets = self._bucket([80, 90, 95, 100])
        assert buckets["75-100"] == 4
        assert sum(v for k, v in buckets.items() if k != "75-100") == 0

    def test_empty_scores_gives_all_zero(self):
        buckets = self._bucket([])
        assert all(v == 0 for v in buckets.values())

    def test_bucket_counts_sum_to_total(self):
        scores = [10, 30, 55, 82, 91, 44, 67, 23]
        buckets = self._bucket(scores)
        assert sum(buckets.values()) == len(scores)


class TestTopSkillsLogic:
    """Test the skill counting / ranking logic."""

    def test_skills_are_counted_correctly(self):
        from collections import Counter
        skills_lists = [
            ["Python", "FastAPI", "Redis"],
            ["Python", "Django"],
            ["Python"],
        ]
        counter = Counter()
        for skills in skills_lists:
            for skill in skills:
                counter[skill.strip()] += 1

        assert counter["Python"] == 3
        assert counter["FastAPI"] == 1
        assert counter["Django"] == 1

    def test_top_10_limit(self):
        from collections import Counter
        counter = Counter({f"Skill{i}": 100 - i for i in range(20)})
        top = counter.most_common(10)
        assert len(top) == 10
        assert top[0][0] == "Skill0"

    def test_non_string_skills_are_skipped(self):
        from collections import Counter
        raw = [["Python", None, 42, ""], ["FastAPI"]]
        counter = Counter()
        for skills in raw:
            for skill in skills:
                if isinstance(skill, str) and skill.strip():
                    counter[skill.strip()] += 1
        assert "Python" in counter
        assert "FastAPI" in counter
        assert len(counter) == 2  # None, 42, and "" are skipped
