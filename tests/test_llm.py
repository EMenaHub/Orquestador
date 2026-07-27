import pytest

from app.core.llm import _truncate_config


def test_truncate_config_short():
    config = "hostname TEST\n!"
    assert _truncate_config(config) == config


def test_truncate_config_long():
    config = "A" * 40000
    truncated = _truncate_config(config, max_tokens=100)
    assert len(truncated) == 100 + len("\n\n## [CONFIGURACIÓN TRUNCADA]")
    assert "TRUNCADA" in truncated



