"""Helpers for endpoint tests: drive /chat/stream with a recording stand-in for the model provider."""

import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app


def parse_sse(text: str) -> list[tuple[str, dict]]:
    events, name = [], None
    for line in text.splitlines():
        if line.startswith("event: "):
            name = line[7:]
        elif line.startswith("data: "):
            events.append((name, json.loads(line[6:])))
    return events


def streamed_text(events) -> str:
    return "".join(data["text"] for name, data in events if name == "token")


def event(events, name):
    return [data for event_name, data in events if event_name == name]


class FakeModel:
    """Stands in for llm.factory.answer_with_fallback and records every call."""

    def __init__(self, reply="Okay.", provider="ollama", error=None):
        self.reply, self.provider, self.error = reply, provider, error
        self.calls = []

    async def __call__(self, provider, agent, messages, **kwargs):
        self.calls.append({"provider": provider, "agent": agent, "messages": messages, **kwargs})
        if self.error is not None:
            raise self.error
        return self.reply, self.provider


def chat(payload: dict, model: FakeModel | None = None, patches=(), real_fallback=False):
    """POST a chat request. Returns (events, FakeModel). Retrieval is stubbed so tests never touch Chroma.

    With real_fallback=True the real llm.factory.answer_with_fallback runs and `patches` must stub the provider.
    """
    model = model or FakeModel()
    stack = [
        *([] if real_fallback else [patch("main.answer_with_fallback", model)]),
        patch("main.RAGRetriever", side_effect=RuntimeError("offline")),
        patch("main.search_local", return_value=payload.get("_context", "Hold the power button for 10 seconds.")),
        *patches,
    ]
    payload = {key: value for key, value in payload.items() if not key.startswith("_")}
    for item in stack:
        item.start()
    try:
        response = TestClient(app).post("/chat/stream", json=payload)
    finally:
        for item in reversed(stack):
            item.stop()
    assert response.status_code == 200, response.text
    return parse_sse(response.text), model
