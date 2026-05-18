import pytest
from unittest.mock import patch

try:
    from api.production import app
except ImportError:
    app = None

@pytest.mark.skipif(app is None, reason="api.production not found")
def test_production_app_init():
    assert app is not None
    assert app.title == "STCOK API" or "API" in app.title
