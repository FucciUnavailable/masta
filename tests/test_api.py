"""The HTTP API exposes coaches, memory, and streaming chat without touching a real LLM."""

from __future__ import annotations

import asyncio
import json

import pytest
from fastapi.testclient import TestClient

from masta.agent import CoachingSession
from masta.api import create_app
from masta.api.routes import _sse, get_provider_resolver, get_repo
from masta.coaches.loader import load_coach
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


def test_chat_stream_abandoned_by_the_client_keeps_the_partial_reply(temp_repo):
    session = CoachingSession(
        coach=load_coach("backend-engineering"),
        provider=FakeProvider(response="one two three"),
        repo=temp_repo,
    )

    async def read_one_event_then_disconnect() -> str:
        events = _sse(session.stream("hi"))
        first = await events.__anext__()
        await events.aclose()
        return first

    assert json.loads(asyncio.run(read_one_event_then_disconnect())[6:])["text"] == "one "
    stored = temp_repo.recent_messages(coach="backend-engineering")
    assert [(m.role, m.content) for m in stored] == [("user", "hi"), ("assistant", "one ")]


def test_sessions_keep_conversations_apart(client, fake_provider):
    assert client.post("/api/sessions", json={"coach": "nope"}).status_code == 404

    first = client.post("/api/sessions", json={"coach": "backend-engineering"}).json()
    second = client.post("/api/sessions", json={"coach": "backend-engineering"}).json()
    assert first["title"] == ""

    for session, text in ((first, "about postgres"), (second, "about queues")):
        body = {"coach": "backend-engineering", "message": text, "session_id": session["id"]}
        assert client.post("/api/chat", json=body).status_code == 200

    # The second session's prompt never saw the first session's messages.
    assert "about postgres" not in [m.content for m in fake_provider.calls[-1]]

    listed = client.get("/api/sessions").json()
    assert [s["title"] for s in listed] == ["about queues", "about postgres"]

    thread = client.get(f"/api/sessions/{first['id']}/messages").json()
    assert [(m["role"], m["content"]) for m in thread] == [
        ("user", "about postgres"),
        ("assistant", "ok "),
    ]

    assert client.delete(f"/api/sessions/{first['id']}").status_code == 204
    assert client.get(f"/api/sessions/{first['id']}").status_code == 404
    assert client.get(f"/api/sessions/{first['id']}/messages").status_code == 404
    assert client.delete(f"/api/sessions/{first['id']}").status_code == 404


def test_chat_rejects_unknown_or_mismatched_session(client):
    body = {"coach": "backend-engineering", "message": "hi", "session_id": 999}
    assert client.post("/api/chat", json=body).status_code == 404

    session = client.post("/api/sessions", json={"coach": "weight-loss-safe"}).json()
    res = client.post("/api/chat", json={**body, "session_id": session["id"]})
    assert res.status_code == 409
    assert client.get(f"/api/sessions/{session['id']}/messages").json() == []


COACH = {
    "name": "sleep-coach",
    "display_name": "Sleep Coach",
    "description": "Helps you sleep.",
    "tags": ["health"],
    "persona": "You are a calm sleep coach.",
    "style": {"both_sides": True, "socratic": False, "rest_reminders": True},
    "guardrails": {"disclaimers": ["I am not a doctor."], "escalate_to_professional": ["apnea"]},
}


def test_coach_create_edit_delete(client, isolated_config):
    created = client.post("/api/coaches", json=COACH)
    assert created.status_code == 201
    assert created.json()["editable"] is True
    assert (isolated_config / "coaches" / "sleep-coach" / "coach.yaml").is_file()
    assert client.post("/api/coaches", json=COACH).status_code == 409

    # It is a real coach: listed, and its guardrails reach the system prompt.
    assert "sleep-coach" in [c["name"] for c in client.get("/api/coaches").json()]
    from masta.coaches.loader import load_coach

    assert "I am not a doctor." in load_coach("sleep-coach").system_prompt()

    update = {**COACH, "persona": "You are a strict sleep coach.", "tags": []}
    del update["name"]
    edited = client.put("/api/coaches/sleep-coach", json=update)
    assert edited.status_code == 200
    detail = client.get("/api/coaches/sleep-coach").json()
    assert detail["persona"] == "You are a strict sleep coach."
    assert detail["tags"] == []
    assert detail["guardrails"]["escalate_to_professional"] == ["apnea"]

    assert client.delete("/api/coaches/sleep-coach").status_code == 204
    assert client.get("/api/coaches/sleep-coach").status_code == 404
    assert not (isolated_config / "coaches" / "sleep-coach").exists()


def test_coach_writes_are_validated(client, isolated_config):
    for name in ("../evil", "Has Spaces", "", "trailing-", "a/b"):
        assert client.post("/api/coaches", json={**COACH, "name": name}).status_code == 422
    assert client.post("/api/coaches", json={**COACH, "persona": ""}).status_code == 422
    assert client.post("/api/coaches", json={**COACH, "model_profile": "nope"}).status_code == 400
    assert not (isolated_config / "coaches").exists()

    # Bundled coaches are read-only.
    assert client.get("/api/coaches/backend-engineering").json()["editable"] is False
    assert client.put("/api/coaches/backend-engineering", json=COACH).status_code == 403
    assert client.delete("/api/coaches/backend-engineering").status_code == 403
    assert client.put("/api/coaches/nope", json=COACH).status_code == 404


def test_profiles_are_saved_to_the_config_file(client, isolated_config, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    claude = next(p for p in client.get("/api/profiles").json() if p["name"] == "claude")
    assert claude["builtin"] and not claude["customized"]
    assert claude["missing_env"] == ["ANTHROPIC_API_KEY"] and not claude["configured"]

    body = {"model": "ollama/qwen3", "temperature": 0.2, "api_base": "http://localhost:11434"}
    saved = client.put("/api/profiles/qwen", json=body)
    assert saved.status_code == 200
    assert saved.json() == {
        "name": "qwen",
        "model": "ollama/qwen3",
        "provider": "ollama",
        "temperature": 0.2,
        "max_tokens": None,
        "api_base": "http://localhost:11434",
        "configured": True,
        "missing_env": [],
        "is_default": False,
        "builtin": False,
        "customized": True,
    }
    assert "ollama/qwen3" in (isolated_config / "config.toml").read_text()

    assert client.put("/api/profiles/qwen", json={"model": ""}).status_code == 422
    assert client.put("/api/profiles/bad name", json=body).status_code == 422

    # Overriding a built-in, then removing the override, restores the shipped model.
    client.put("/api/profiles/claude", json={"model": "anthropic/other"})
    assert client.delete("/api/profiles/claude").status_code == 204
    claude = next(p for p in client.get("/api/profiles").json() if p["name"] == "claude")
    assert claude["model"] != "anthropic/other"
    assert client.delete("/api/profiles/claude").status_code == 404


def test_default_profile_setting(client, monkeypatch):
    assert client.get("/api/settings").json()["default_profile"] == "claude"
    assert client.patch("/api/settings", json={"default_profile": "nope"}).status_code == 400

    client.put("/api/profiles/mine", json={"model": "ollama/llama3.1"})
    changed = client.patch("/api/settings", json={"default_profile": "mine"})
    assert changed.json()["default_profile"] == "mine"
    assert [p["name"] for p in client.get("/api/profiles").json() if p["is_default"]] == ["mine"]

    # The default can't be removed out from under itself.
    assert client.delete("/api/profiles/mine").status_code == 409

    monkeypatch.setenv("MASTA_DEFAULT_PROFILE", "local")
    assert client.patch("/api/settings", json={"default_profile": "claude"}).status_code == 409


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
