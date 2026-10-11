"""The HTTP API exposes coaches, memory, and streaming chat without touching a real LLM."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from masta.api import create_app
from masta.api.routes import get_provider_resolver, get_repo
from tests.conftest import FakeProvider


class BrokenProvider(FakeProvider):
    def stream(self, messages, **overrides):
        yield "partial "
        raise RuntimeError("provider exploded")


@pytest.fixture
def app(temp_repo, fake_provider, tmp_path):
    # Point at an empty dir so a local web/dist build never leaks into API tests.
    app = create_app(static_dir=tmp_path / "no-dist")
    app.dependency_overrides[get_repo] = lambda: temp_repo
    app.dependency_overrides[get_provider_resolver] = lambda: lambda profile: fake_provider
    return app


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)


def _events(body: str) -> list[dict]:
    return [json.loads(line.removeprefix("data: ")) for line in body.split("\n\n") if line]


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_coaches_list_and_detail(client):
    names = [c["name"] for c in client.get("/api/coaches").json()]
    assert "backend-engineering" in names

    detail = client.get("/api/coaches/backend-engineering").json()
    assert detail["display_name"]
    assert client.get("/api/coaches/nope").status_code == 404


def test_profiles(client):
    rows = client.get("/api/profiles").json()
    assert any(p["is_default"] for p in rows)


def test_goal_lifecycle(client):
    created = client.post("/api/goals", json={"title": "Learn Postgres"})
    assert created.status_code == 201
    goal = created.json()
    assert goal["status"] == "active"
    assert goal["created_at"].endswith("Z")  # stored UTC is labelled as such

    patched = client.patch(f"/api/goals/{goal['id']}", json={"status": "achieved"})
    assert patched.json()["status"] == "achieved"

    assert client.get("/api/goals", params={"status": "active"}).json() == []
    assert len(client.get("/api/goals").json()) == 1


def test_goal_validation_and_missing(client):
    assert client.post("/api/goals", json={"title": ""}).status_code == 422
    assert client.patch("/api/goals/999", json={"status": "paused"}).status_code == 404


def test_checkins(client):
    assert client.post("/api/checkins", json={"energy": 9}).status_code == 422

    created = client.post("/api/checkins", json={"note": "tired", "energy": 2})
    assert created.status_code == 201
    assert client.get("/api/checkins").json()[0]["note"] == "tired"


def test_chat_streams_and_persists(client, fake_provider):
    fake_provider._response = "Start with data modeling."
    res = client.post("/api/chat", json={"coach": "backend-engineering", "message": "hi"})
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/event-stream")

    events = _events(res.text)
    assert events[-1] == {"type": "done"}
    text = "".join(e["text"] for e in events if e["type"] == "delta")
    assert text.strip() == "Start with data modeling."

    stored = client.get("/api/messages", params={"coach": "backend-engineering"}).json()
    assert [m["role"] for m in stored] == ["user", "assistant"]


def test_chat_unknown_coach_and_profile(app, client):
    assert client.post("/api/chat", json={"coach": "nope", "message": "hi"}).status_code == 404

    def unknown(profile):
        raise KeyError(f"Unknown model profile {profile!r}.")

    app.dependency_overrides[get_provider_resolver] = lambda: unknown
    res = client.post("/api/chat", json={"coach": "backend-engineering", "message": "hi"})
    assert res.status_code == 400


def test_chat_reports_provider_errors_in_stream(app, client):
    app.dependency_overrides[get_provider_resolver] = lambda: lambda profile: BrokenProvider()
    res = client.post("/api/chat", json={"coach": "backend-engineering", "message": "hi"})
    events = _events(res.text)
    assert events[0] == {"type": "delta", "text": "partial "}
    assert events[-1] == {"type": "error", "message": "provider exploded"}


def test_serves_built_frontend_with_spa_fallback(tmp_path, temp_repo):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html>shell</html>")
    (dist / "assets" / "app.js").write_text("console.log(1)")
    (tmp_path / "secret.txt").write_text("nope")

    client = TestClient(create_app(static_dir=dist))
    assert client.get("/").text == "<html>shell</html>"
    assert client.get("/goals").text == "<html>shell</html>"
    assert client.get("/assets/app.js").text == "console.log(1)"
    assert client.get("/api/nope").status_code == 404
    assert "nope" not in client.get("/%2e%2e/secret.txt").text
