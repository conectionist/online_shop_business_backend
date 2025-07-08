import os
import requests

# Get the API base URL from the environment variable, with a default for local testing
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8001")
API_V1_STR = "/api/v1"

def test_unit_crud_workflow():
    """
    Tests the full Create, Read, Update, and Delete (CRUD) workflow for units.
    """
    # 1. CREATE a new unit
    unit_name = "Test Unit"
    create_response = requests.post(
        f"{API_BASE_URL}{API_V1_STR}/unitati",
        json={"denumire": unit_name}
    )
    assert create_response.status_code == 201, f"Expected 201, got {create_response.status_code}: {create_response.text}"
    created_unit = create_response.json()
    assert "id" in created_unit
    assert created_unit["denumire"] == unit_name
    unit_id = created_unit["id"]

    # 2. READ the created unit
    read_response = requests.get(f"{API_BASE_URL}{API_V1_STR}/unitati/{unit_id}")
    assert read_response.status_code == 200
    assert read_response.json() == created_unit

    # 3. UPDATE the unit
    updated_unit_name = "Updated Test Unit"
    update_response = requests.put(
        f"{API_BASE_URL}{API_V1_STR}/unitati/{unit_id}",
        json={"denumire": updated_unit_name}
    )
    assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}: {update_response.text}"
    updated_unit = update_response.json()
    assert updated_unit["denumire"] == updated_unit_name

    # 4. DELETE the unit
    delete_response = requests.delete(f"{API_BASE_URL}{API_V1_STR}/unitati/{unit_id}")
    assert delete_response.status_code == 204

    # 5. VERIFY the unit is deleted
    verify_response = requests.get(f"{API_BASE_URL}{API_V1_STR}/unitati/{unit_id}")
    assert verify_response.status_code == 404
