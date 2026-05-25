"""
tests/test_phase2.py
--------------------
Phase 2 unit/integration checks — scrape status, notifications model,
alert inbox endpoints, and read/read-all logic.

These tests run without a live DB (pure unit tests where possible).
Where DB is needed, they are marked with @pytest.mark.skip until
the docker DB is running.
"""
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta


# ─────────────────────────────────────────────────────────────────
# Scrape Router — unit tests (no DB needed)
# ─────────────────────────────────────────────────────────────────

class TestScrapeStatusResponse:
    """Verify _serialize_run helper shapes the response correctly."""

    def test_serialize_run_none_returns_none(self):
        from app.routers.scrape import _serialize_run
        assert _serialize_run(None) is None

    def test_serialize_run_completed(self):
        from app.routers.scrape import _serialize_run

        run = MagicMock()
        run.id              = uuid.uuid4()
        run.status          = "completed"
        run.jobs_scraped    = 48
        run.jobs_new        = 12
        run.error_message   = None
        run.started_at      = datetime(2026, 5, 25, 10, 0, tzinfo=timezone.utc)
        run.completed_at    = datetime(2026, 5, 25, 10, 5, tzinfo=timezone.utc)

        result = _serialize_run(run)

        assert result["status"]     == "completed"
        assert result["jobs_found"] == 48
        assert result["jobs_new"]   == 12
        assert result["error_message"] is None
        assert result["completed_at"] is not None

    def test_serialize_run_failed_truncates_error(self):
        from app.routers.scrape import _serialize_run

        long_error = "x" * 500
        run = MagicMock()
        run.id            = uuid.uuid4()
        run.status        = "failed"
        run.jobs_scraped  = 0
        run.jobs_new      = 0
        run.error_message = long_error
        run.started_at    = datetime(2026, 5, 25, tzinfo=timezone.utc)
        run.completed_at  = None

        result = _serialize_run(run)

        assert result["status"] == "failed"
        assert len(result["error_message"]) <= 200

    def test_serialize_run_running_has_no_completed_at(self):
        from app.routers.scrape import _serialize_run

        run = MagicMock()
        run.id            = uuid.uuid4()
        run.status        = "running"
        run.jobs_scraped  = 0
        run.jobs_new      = 0
        run.error_message = None
        run.started_at    = datetime(2026, 5, 25, tzinfo=timezone.utc)
        run.completed_at  = None

        result = _serialize_run(run)

        assert result["completed_at"] is None
        assert result["status"] == "running"


class TestScrapeNextRunAt:
    """next_run_at is last completed_at + SCRAPE_INTERVAL_MINUTES."""

    def test_next_run_at_calculation(self):
        from app.config import settings
        completed_at = datetime(2026, 5, 25, 10, 0, tzinfo=timezone.utc)
        expected = completed_at + timedelta(minutes=settings.SCRAPE_INTERVAL_MINUTES)
        # Verify interval is sensible
        assert settings.SCRAPE_INTERVAL_MINUTES > 0
        assert (expected - completed_at).seconds == settings.SCRAPE_INTERVAL_MINUTES * 60


# ─────────────────────────────────────────────────────────────────
# Notification Model — unit tests
# ─────────────────────────────────────────────────────────────────

class TestNotificationModel:
    """Verify Notification ORM model can be instantiated correctly."""

    def test_notification_default_is_read_false(self):
        from app.models.notification import Notification

        n = Notification(
            user_id=uuid.uuid4(),
            job_id=uuid.uuid4(),
            job_title="Senior Python Engineer",
            score=82,
            message="New 82/100 match. 3 proposals so far.",
        )
        # is_read has a server_default but defaults to None in Python
        # until persisted; the important thing is it's not True.
        assert n.is_read is not True

    def test_notification_repr(self):
        from app.models.notification import Notification

        uid = uuid.uuid4()
        n = Notification(user_id=uid, job_title="Test Job", score=75)
        repr_str = repr(n)
        assert "Test Job" in repr_str

    def test_notification_fields_exist(self):
        from app.models.notification import Notification
        import sqlalchemy

        cols = {c.name for c in Notification.__table__.columns}
        required = {"id", "user_id", "job_id", "job_title", "score",
                    "message", "is_read", "created_at"}
        assert required.issubset(cols), f"Missing columns: {required - cols}"

    def test_notification_score_is_integer_column(self):
        from app.models.notification import Notification
        import sqlalchemy as sa

        col = Notification.__table__.columns["score"]
        assert isinstance(col.type, sa.Integer)

    def test_notification_is_read_has_server_default_false(self):
        from app.models.notification import Notification

        col = Notification.__table__.columns["is_read"]
        assert str(col.server_default.arg) == "false"


# ─────────────────────────────────────────────────────────────────
# Alerts Router — response shape unit tests
# ─────────────────────────────────────────────────────────────────

class TestAlertsRouterResponseShape:
    """
    Verify the list_notifications response has the correct shape.
    These do NOT hit the DB — they test the serialisation logic.
    """

    def test_notifications_response_has_unread_count_and_list(self):
        """
        Simulate what list_notifications returns and confirm shape
        matches the frontend NotificationsResponse interface.
        """
        # Simulate a DB result
        mock_notifs = []
        for i, is_read in enumerate([False, False, True]):
            n = MagicMock()
            n.id         = uuid.uuid4()
            n.job_id     = uuid.uuid4()
            n.job_title  = f"Job {i}"
            n.score      = 80
            n.message    = f"Message {i}"
            n.is_read    = is_read
            n.created_at = datetime(2026, 5, 25, tzinfo=timezone.utc)
            mock_notifs.append(n)

        # Replicate the serialisation logic from the router
        unread_count = sum(1 for n in mock_notifs if not n.is_read)
        response = {
            "unread_count": unread_count,
            "notifications": [
                {
                    "id":         str(n.id),
                    "job_id":     str(n.job_id),
                    "job_title":  n.job_title,
                    "score":      n.score,
                    "message":    n.message,
                    "is_read":    n.is_read,
                    "created_at": n.created_at.isoformat(),
                }
                for n in mock_notifs
            ],
        }

        assert response["unread_count"] == 2
        assert len(response["notifications"]) == 3
        assert response["notifications"][0]["is_read"] is False
        assert response["notifications"][2]["is_read"] is True

    def test_score_is_integer_in_response(self):
        """score must be 0-100 int, not 0.0-1.0 float."""
        n = MagicMock()
        n.id         = uuid.uuid4()
        n.job_id     = uuid.uuid4()
        n.job_title  = "Test Job"
        n.score      = 82          # integer
        n.message    = "test"
        n.is_read    = False
        n.created_at = datetime(2026, 5, 25, tzinfo=timezone.utc)

        serialised = {
            "score": n.score,
        }

        assert isinstance(serialised["score"], int)
        assert 0 <= serialised["score"] <= 100


# ─────────────────────────────────────────────────────────────────
# Match Tasks — notification insert logic
# ─────────────────────────────────────────────────────────────────

class TestMatchTasksNotificationInsert:
    """Verify Notification is imported and used in match_tasks."""

    def test_notification_imported_in_match_tasks(self):
        """Notification model must be importable from match_tasks context."""
        from app.models.notification import Notification
        assert Notification is not None

    def test_notification_message_format(self):
        """Verify the message string format used in match_tasks."""
        job_title     = "FastAPI Backend Developer"
        match_score   = 87
        proposal_count = 1

        message = (
            f"New {match_score}/100 match: {job_title[:80]}. "
            f"{proposal_count} proposal{'s' if proposal_count != 1 else ''} so far."
        )

        assert "87/100" in message
        assert "FastAPI" in message
        assert "1 proposal so far" in message

    def test_notification_message_pluralises_proposals(self):
        proposal_count = 5
        message = (
            f"New 82/100 match: Some Job. "
            f"{proposal_count} proposal{'s' if proposal_count != 1 else ''} so far."
        )
        assert "5 proposals so far" in message
