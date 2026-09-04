"""Shared helpers for async AI job assertions."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

_TERMINAL = frozenset({"succeeded", "failed"})


def assert_ai_job_terminal(
    client: TestClient,
    *,
    detail_url: str,
    headers: dict[str, str],
) -> dict[str, Any]:
    """GET detail until status is succeeded/failed (TestClient runs BackgroundTasks after POST)."""
    response = client.get(detail_url, headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] in _TERMINAL, body
    return body


def post_ai_job(
    client: TestClient,
    *,
    collection_url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
) -> dict[str, Any]:
    """POST create then return terminal job via GET detail."""
    created = client.post(collection_url, headers=headers, json=payload)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["status"] in {"pending", "running", "succeeded", "failed"}
    detail_url = f"{collection_url}/{body['id']}"
    return assert_ai_job_terminal(client, detail_url=detail_url, headers=headers)
