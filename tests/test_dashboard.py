"""Smoke test: the dashboard script runs top to bottom without raising (needs Postgres; API optional)."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parent.parent / "dashboard" / "app.py"


@pytest.mark.integration
def test_dashboard_renders_without_exceptions():
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not at.exception, [e.message for e in at.exception]
    assert any("four numbers" in m.value for m in at.markdown)
