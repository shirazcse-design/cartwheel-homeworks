"""Public store lookup and SDK registration, without model calls."""

import asyncio
import json

import pytest
from agents.tool_context import ToolContext

from agent.agent import TOOLS_BY_ROLE
from agent.auth import AuthContext
from agent.tools import get_store_info


@pytest.mark.parametrize(
    "ctx",
    [
        AuthContext(user_id=1, role="shopper"),
        AuthContext(user_id=9002, role="merchant", store_id=2),
        AuthContext(user_id=9501, role="support"),
    ],
)
def test_public_store_lookup_through_registered_tool(world, ctx):
    assert get_store_info in TOOLS_BY_ROLE[ctx.role]
    result = asyncio.run(
        get_store_info.on_invoke_tool(ToolContext(ctx, tool_name="get_store_info", tool_call_id="test-call", tool_arguments='{"store_id": 1}'), '{"store_id": 1}')
    )
    if isinstance(result, str):
        result = json.loads(result)
    assert result["ok"] is True
    assert result["store"]["store_id"] == 1
    assert result["store"]["name"] == "Blue Heron Ceramics"
    assert set(result["store"]) == {"store_id", "name", "slug", "category"}


def test_unknown_store_returns_structured_error(world):
    result = asyncio.run(
        get_store_info.on_invoke_tool(
            ToolContext(AuthContext(user_id=1, role="shopper"), tool_name="get_store_info", tool_call_id="test-call", tool_arguments='{"store_id": 999999}'),
            '{"store_id": 999999}',
        )
    )
    if isinstance(result, str):
        result = json.loads(result)
    assert result == {
        "ok": False, "error": "not_found", "reason": "no store #999999"
    }
