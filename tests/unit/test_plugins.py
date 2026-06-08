import asyncio

import pytest

from app.config import settings
from app.tools import bootstrap_tools
from app.tools.registry import arun_tool, list_tools


def test_example_promo_plugin(isolated_env, monkeypatch):
    monkeypatch.setattr(settings, "plugin_module", "plugins.example_promo")
    bootstrap_tools()
    assert "lookup_promo" in list_tools()
    result = asyncio.run(arun_tool("lookup_promo", code="SAVE10", tenant_id="default"))
    assert result["found"] is True
    assert result["discount_pct"] == 10


def test_missing_register_raises(isolated_env, monkeypatch):
    monkeypatch.setattr(settings, "plugin_module", "plugins")
    with pytest.raises(RuntimeError, match="register"):
        bootstrap_tools()
