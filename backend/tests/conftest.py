import os
import pytest
from fastapi.testclient import TestClient

# Ensure the app uses the repo's demo_data by default during tests.
os.environ.setdefault("ASMA_DATA_DIR", "demo_data")

from backend.app.main import app  # noqa: E402 (import after env set)


@pytest.fixture(scope="session")
def client():
    return TestClient(app)
