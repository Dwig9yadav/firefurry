from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import _mock_setup as _ms
import routers.analytics as analytics_router
import routers.auth as auth_router


_client = _ms.client


class _FakeQuery:
    def __init__(self, data):
        self._data = data

    def select(self, *args, **kwargs):
        return self

    def eq(self, *args, **kwargs):
        return self

    def in_(self, *args, **kwargs):
        return self

    def order(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def gte(self, *args, **kwargs):
        return self

    def execute(self):
        return SimpleNamespace(data=self._data)


class _FakeSupabase:
    def __init__(self, users=None, student_feedback=None):
        self.users = users or []
        self.student_feedback = student_feedback or []

    def table(self, name):
        if name == "users":
            return _FakeQuery(self.users)
        if name == "student_feedback":
            return _FakeQuery(self.student_feedback)
        return _FakeQuery([])


def _admin_token():
    from jose import jwt as j

    payload = {
        "user_id": 1,
        "institution_id": "admin001",
        "role": "admin",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
    }
    return j.encode(payload, "your-secret-key", algorithm="HS256")


def test_feedback_sentiment_breakdown(monkeypatch):
    fake_sb = _FakeSupabase(
        users=[{"id": 1, "name": "Admin", "institution_id": "admin001", "role": "admin", "avatar": "male", "status": "active"}],
        student_feedback=[
            {"message": "Great helpful class"},
            {"message": "Bad and confusing upload flow"},
            {"message": "Okay"},
        ],
    )
    monkeypatch.setattr(auth_router, "get_supabase", lambda: fake_sb)
    monkeypatch.setattr(analytics_router, "get_supabase", lambda: fake_sb)

    response = _client.get(
        "/api/analytics/feedback-sentiment",
        headers={"Authorization": f"Bearer {_admin_token()}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    assert payload["positive"] == 1
    assert payload["negative"] == 1
    assert payload["neutral"] == 1
