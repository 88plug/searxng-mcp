from __future__ import annotations

from pathlib import Path
import asyncio

import orjson

from searxng_mcp.server import create_server

from test_service import make_settings


def test_server_exposes_guide_resource_and_research_prompts(tmp_path: Path) -> None:
    bundle = create_server(make_settings(tmp_path))

    config_contents = asyncio.run(bundle.server.read_resource("searxng://config"))
    assert len(config_contents) == 1
    assert config_contents[0].mime_type == "application/json"
    config = orjson.loads(config_contents[0].content)
    assert config["resources"] == ["searxng://config", "searxng://guide"]
    assert config["prompts"] == ["quick_lookup", "deep_research", "research_workflow"]
    assert config["agent_driven"] is True
    assert config["prompts_optional"] is True
    assert config["render_sandbox"] is False

    guide_contents = asyncio.run(bundle.server.read_resource("searxng://guide"))
    assert len(guide_contents) == 1
    assert guide_contents[0].mime_type == "application/json"
    guide = orjson.loads(guide_contents[0].content)
    assert guide["operating_mode"]["orchestration"] == "agent-driven"
    assert guide["operating_mode"]["primary_interface"] == "tools"
    assert guide["tool_selection"]["search_and_fetch"]
    assert guide["prompt_compatibility"]["quick_lookup"].startswith("Optional helper prompt")
    assert guide["default_behavior"]["default_interface"] == "tools"
    assert guide["default_behavior"]["raw_payload"] == "hidden in _meta"

    quick_prompt = asyncio.run(bundle.server.get_prompt("quick_lookup", {"topic": "python asyncio", "intent": "summary"}))
    assert len(quick_prompt.messages) == 1
    assert "Quick lookup topic: python asyncio" in quick_prompt.messages[0].content.text
    assert "search_and_fetch" in quick_prompt.messages[0].content.text

    deep_prompt = asyncio.run(bundle.server.get_prompt("deep_research", {"topic": "python asyncio", "scope": "wide"}))
    assert len(deep_prompt.messages) == 1
    assert "Preferred workflow: search_many -> research -> fetch_many" in deep_prompt.messages[0].content.text

    router_prompt = asyncio.run(bundle.server.get_prompt("research_workflow", {"topic": "python asyncio", "depth": "quick"}))
    assert len(router_prompt.messages) == 1
    assert "quick_lookup" in router_prompt.messages[0].content.text
