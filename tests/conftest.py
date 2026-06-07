import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'

# Add the server source directory to sys.path so imports resolve
sys.path.insert(0, str(SRC))

# Import the FastAPI app after adding src to sys.path and using correct cwd for config loading
_cwd = os.getcwd()
os.chdir(SRC)
import server as server_module  # noqa: E402
os.chdir(_cwd)

#set fallback db creds so running db diles dont crash if .env is missing
os.environ.setdefault("DB_USER", "test_dummy")
os.environ.setdefault("DB_PASSWORD", "test_dummy")

@pytest.fixture(scope='session')
def app():
    return server_module.app

@pytest.fixture
def client(app):
    return TestClient(app)

@pytest.fixture(autouse=True)
def app_config(app):
    app.state.config = {
        'un_min_len': 1,
        'un_max_len': 20,
        'pw_min_len': 1,
        'pw_max_len': 50,
    }
    yield
    app.dependency_overrides.clear()
