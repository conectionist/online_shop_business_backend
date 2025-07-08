import os
import requests

# Get the API base URL from the environment variable, with a default for local testing
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8001")
API_V1_STR = "/api/v1"

def test_get_units_returns_200():
    """
    Tests that the /units endpoint returns a 200 OK status.
    """
    response = requests.get(f"{API_BASE_URL}{API_V1_STR}/unitati")
    assert response.status_code == 200
