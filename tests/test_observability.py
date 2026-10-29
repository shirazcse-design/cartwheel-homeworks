"""Offline authentication tests for Homework 2."""

import asyncio
import pytest
from fastapi import HTTPException

from server import app as server_app


def test_session_rejects_wrong_role(world):
    # User 1 is a shopper in the database, not support.
    with pytest.raises(HTTPException) as error:
        server_app.create_session(
            server_app.SessionCreate(
                user_id=1,
                role="support",
            )
        )

    assert error.value.status_code == 403


def test_token_cannot_authorize_another_session(
    world, monkeypatch
):
    # Keep this test's sessions separate from other tests.
    monkeypatch.setattr(server_app, "_SESSIONS", {})

    first = server_app.create_session(
        server_app.SessionCreate(
            user_id=1,
            role="shopper",
        )
    )
    second = server_app.create_session(
        server_app.SessionCreate(
            user_id=1,
            role="shopper",
        )
    )

    def fail_if_agent_runs(*args, **kwargs):
        pytest.fail("Agent must not run for an unauthorized request")

    monkeypatch.setattr(
        server_app,
        "build_agent",
        fail_if_agent_runs,
    )

    with pytest.raises(HTTPException) as error:
          asyncio.run(
            server_app.post_message(
                session_id=second["session_id"],
                body=server_app.MessageIn(
                    message="Show me order 4127."
                ),
                authorization=f"Bearer {first['token']}",
            )
        )

    assert error.value.status_code == 403