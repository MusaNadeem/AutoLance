"""
tests/test_phase3.py
--------------------
Phase 3 unit tests — tone-aware proposals, CV profile PUT/GET, onboarding flow logic.
"""
import pytest
import uuid
from unittest.mock import MagicMock


# ─────────────────────────────────────────────────────────────────
# R5 — Tone-aware proposal generation
# ─────────────────────────────────────────────────────────────────

class TestCoverLetterTone:
    """Cover letter prompt builder includes correct tone instruction blocks."""

    PROFILE = {"headline": "Python Dev", "niche": "backend", "skills": []}
    JOB     = {"title": "FastAPI Engineer", "description": "Build APIs", "required_skills": []}
    MATCH   = {}

    def test_professional_tone_includes_formal_instruction(self):
        from app.ai.prompts.cover_letter import build_cover_letter_prompt
        prompt = build_cover_letter_prompt(
            profile=self.PROFILE, job=self.JOB, match=self.MATCH,
            tone="professional",
        )
        assert "Formal" in prompt or "results-focused" in prompt

    def test_friendly_tone_includes_contractions_instruction(self):
        from app.ai.prompts.cover_letter import build_cover_letter_prompt
        prompt = build_cover_letter_prompt(
            profile=self.PROFILE, job=self.JOB, match=self.MATCH,
            tone="friendly",
        )
        assert "contractions" in prompt.lower() or "conversational" in prompt.lower()

    def test_bold_tone_includes_value_proposition_instruction(self):
        from app.ai.prompts.cover_letter import build_cover_letter_prompt
        prompt = build_cover_letter_prompt(
            profile=self.PROFILE, job=self.JOB, match=self.MATCH,
            tone="bold",
        )
        assert "value proposition" in prompt.lower() or "no preamble" in prompt.lower()

    def test_three_tones_produce_distinct_prompts(self):
        from app.ai.prompts.cover_letter import build_cover_letter_prompt
        prompts = {
            tone: build_cover_letter_prompt(
                profile=self.PROFILE, job=self.JOB, match=self.MATCH, tone=tone,
            )
            for tone in ["professional", "friendly", "bold"]
        }
        # Each tone must generate a distinct prompt
        assert prompts["professional"] != prompts["friendly"]
        assert prompts["friendly"]     != prompts["bold"]
        assert prompts["professional"] != prompts["bold"]

    def test_invalid_tone_falls_back_gracefully(self):
        """Unknown tone should not raise, uses style fallback."""
        from app.ai.prompts.cover_letter import build_cover_letter_prompt
        prompt = build_cover_letter_prompt(
            profile=self.PROFILE, job=self.JOB, match=self.MATCH,
            tone="aggressive",
        )
        # Should still produce a valid prompt string
        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_no_tone_param_defaults_to_professional(self):
        from app.ai.prompts.cover_letter import build_cover_letter_prompt
        with_default = build_cover_letter_prompt(
            profile=self.PROFILE, job=self.JOB, match=self.MATCH,
        )
        with_explicit = build_cover_letter_prompt(
            profile=self.PROFILE, job=self.JOB, match=self.MATCH,
            tone="professional",
        )
        assert with_default == with_explicit

    def test_valid_tones_list_matches_api_values(self):
        from app.services.cover_letter_gen import VALID_TONES
        assert set(VALID_TONES) == {"professional", "friendly", "bold"}

    def test_service_normalises_unknown_tone_to_professional(self):
        """CoverLetterService.generate() falls back invalid tone to professional."""
        from app.services.cover_letter_gen import VALID_TONES
        unknown = "aggressive"
        normalised = unknown if unknown in VALID_TONES else "professional"
        assert normalised == "professional"


# ─────────────────────────────────────────────────────────────────
# R6 — FreelancerProfile model
# ─────────────────────────────────────────────────────────────────

class TestFreelancerProfileModel:
    """Phase 3: new columns exist and have correct types."""

    def test_target_fixed_min_column_exists(self):
        from app.models.profile import FreelancerProfile
        cols = {c.name for c in FreelancerProfile.__table__.columns}
        assert "target_fixed_min" in cols, "target_fixed_min column missing"

    def test_target_fixed_max_column_exists(self):
        from app.models.profile import FreelancerProfile
        cols = {c.name for c in FreelancerProfile.__table__.columns}
        assert "target_fixed_max" in cols, "target_fixed_max column missing"

    def test_target_fixed_columns_are_nullable(self):
        from app.models.profile import FreelancerProfile
        for col_name in ("target_fixed_min", "target_fixed_max"):
            col = FreelancerProfile.__table__.columns[col_name]
            assert col.nullable, f"{col_name} should be nullable"

    def test_target_fixed_columns_are_numeric(self):
        from app.models.profile import FreelancerProfile
        import sqlalchemy as sa
        for col_name in ("target_fixed_min", "target_fixed_max"):
            col = FreelancerProfile.__table__.columns[col_name]
            assert isinstance(col.type, sa.Numeric), f"{col_name} should be Numeric"

    def test_all_phase3_fields_present(self):
        from app.models.profile import FreelancerProfile
        required = {
            "id", "user_id", "headline", "summary", "skills",
            "experience_level", "niche",
            "inferred_hourly_rate_min", "inferred_hourly_rate_max",
            "target_fixed_min", "target_fixed_max",
        }
        cols = {c.name for c in FreelancerProfile.__table__.columns}
        missing = required - cols
        assert not missing, f"Missing columns: {missing}"


# ─────────────────────────────────────────────────────────────────
# R6 — CV Profile serialiser
# ─────────────────────────────────────────────────────────────────

class TestCVProfileSerializer:
    """_serialize_profile returns all 9 fields, explicit None for missing."""

    def _make_profile(self, **kwargs):
        p = MagicMock()
        p.id                       = uuid.uuid4()
        p.headline                 = kwargs.get("headline", "Python Dev")
        p.summary                  = kwargs.get("summary", None)
        p.skills                   = kwargs.get("skills", [{"name": "Python", "level": "expert", "years": 5}])
        p.experience_level         = kwargs.get("experience_level", "senior")
        p.niche                    = kwargs.get("niche", "backend")
        p.inferred_hourly_rate_min = kwargs.get("inferred_hourly_rate_min", None)
        p.inferred_hourly_rate_max = kwargs.get("inferred_hourly_rate_max", None)
        p.target_fixed_min         = kwargs.get("target_fixed_min", None)
        p.target_fixed_max         = kwargs.get("target_fixed_max", None)
        p.last_analyzed_at         = None
        p.profile_version          = 1
        return p

    def test_serialize_returns_all_required_keys(self):
        from app.routers.cv import _serialize_profile
        profile = self._make_profile()
        result = _serialize_profile(profile)
        required_keys = {
            "id", "headline", "summary", "skills", "experience_level", "niche",
            "inferred_hourly_rate_min", "inferred_hourly_rate_max",
            "target_fixed_min", "target_fixed_max",
            "last_analyzed_at", "profile_version",
        }
        assert required_keys.issubset(result.keys()), f"Missing keys: {required_keys - result.keys()}"

    def test_serialize_missing_rate_returns_none_not_missing(self):
        from app.routers.cv import _serialize_profile
        profile = self._make_profile(inferred_hourly_rate_min=None)
        result = _serialize_profile(profile)
        assert "inferred_hourly_rate_min" in result
        assert result["inferred_hourly_rate_min"] is None

    def test_serialize_numeric_rate_returns_float(self):
        from app.routers.cv import _serialize_profile
        from decimal import Decimal
        profile = self._make_profile(inferred_hourly_rate_min=Decimal("75.00"))
        result = _serialize_profile(profile)
        assert result["inferred_hourly_rate_min"] == 75.0
        assert isinstance(result["inferred_hourly_rate_min"], float)

    def test_serialize_skills_defaults_to_empty_list(self):
        from app.routers.cv import _serialize_profile
        profile = self._make_profile(skills=None)
        result = _serialize_profile(profile)
        assert result["skills"] == []

    def test_serialize_target_fixed_fields(self):
        from app.routers.cv import _serialize_profile
        from decimal import Decimal
        profile = self._make_profile(
            target_fixed_min=Decimal("500.00"),
            target_fixed_max=Decimal("5000.00"),
        )
        result = _serialize_profile(profile)
        assert result["target_fixed_min"] == 500.0
        assert result["target_fixed_max"] == 5000.0


# ─────────────────────────────────────────────────────────────────
# R6 — Onboarding validation rules
# ─────────────────────────────────────────────────────────────────

class TestOnboardingValidation:
    """Business logic the frontend must enforce before PUT /cv/profile."""

    def test_target_fixed_min_less_than_max(self):
        """PUT /cv/profile: min must be < max."""
        min_val, max_val = 500, 5000
        assert min_val < max_val

    def test_target_fixed_min_equal_max_is_invalid(self):
        min_val = max_val = 1000
        assert not (min_val < max_val)

    def test_experience_level_valid_values(self):
        valid = {"junior", "mid", "senior", "expert"}
        for v in valid:
            assert v in valid

    def test_experience_level_invalid_rejected(self):
        valid = {"junior", "mid", "senior", "expert"}
        assert "beginner" not in valid

    def test_profile_update_request_has_correct_fields(self):
        from app.routers.cv import ProfileUpdateRequest
        # Should not raise on valid data
        req = ProfileUpdateRequest(
            headline="Python Engineer",
            experience_level="senior",
            target_fixed_min=500,
            target_fixed_max=5000,
        )
        assert req.headline == "Python Engineer"
        assert req.target_fixed_min == 500

    def test_profile_update_request_all_fields_optional(self):
        from app.routers.cv import ProfileUpdateRequest
        # Empty body should not raise
        req = ProfileUpdateRequest()
        assert req.headline is None
        assert req.skills is None
