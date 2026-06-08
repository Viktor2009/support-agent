import asyncio

from app.async_admin import aget_analytics_stats, alist_sessions, asave_feedback
from app.async_gdpr import adelete_session_data, aexport_session_data
from app.async_session_store import asave_session


def test_alist_sessions_empty(isolated_env):
    sessions = asyncio.run(alist_sessions())
    assert sessions == []


def test_asave_feedback_and_stats(isolated_env):
    asyncio.run(
        asave_session(
            "admin-test",
            "cust_456",
            "summary",
            [{"role": "user", "content": "hi"}],
            status="active",
        )
    )
    asyncio.run(
        asave_feedback(
            "admin-test",
            rating=5,
            customer_id="cust_456",
            comment="great",
        )
    )
    stats = asyncio.run(aget_analytics_stats())
    assert stats["sessions_total"] == 1
    assert stats["feedback_count"] == 1
    assert stats["feedback_avg_rating"] == 5.0


def test_gdpr_export_and_delete(isolated_env):
    asyncio.run(
        asave_session(
            "gdpr-test",
            "cust_456",
            "summary",
            [{"role": "user", "content": "secret@email.com"}],
        )
    )
    payload = asyncio.run(
        aexport_session_data("gdpr-test", tenant_id="default", customer_id="cust_456")
    )
    assert payload["session"]["session_id"] == "gdpr-test"
    asyncio.run(
        adelete_session_data("gdpr-test", tenant_id="default", customer_id="cust_456")
    )
    sessions = asyncio.run(alist_sessions())
    assert all(item["session_id"] != "gdpr-test" for item in sessions)
