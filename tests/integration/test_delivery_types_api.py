import os
import requests

# Get the API base URL from the environment variable, with a default for local testing
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
API_V1_STR = "/api/v1"

def test_delivery_type_crud_workflow():
    """
    Tests the full Create, Read, Update, and Delete (CRUD) workflow for delivery types.
    """
    # 1. CREATE a new delivery type
    delivery_type_name = "Test Delivery Type"
    create_response = requests.post(
        f"{API_BASE_URL}{API_V1_STR}/tipuri-livrare/",
        json={"denumire": delivery_type_name}
    )
    assert create_response.status_code == 201, f"Expected 201, got {create_response.status_code}: {create_response.text}"
    created_delivery_type = create_response.json()
    assert "id" in created_delivery_type
    assert created_delivery_type["denumire"] == delivery_type_name
    delivery_type_id = created_delivery_type["id"]

    # 2. READ the created delivery type
    read_response = requests.get(f"{API_BASE_URL}{API_V1_STR}/tipuri-livrare/{delivery_type_id}")
    assert read_response.status_code == 200
    assert read_response.json() == created_delivery_type

    # 3. UPDATE the delivery type
    updated_delivery_type_name = "Updated Test Delivery Type"
    update_response = requests.put(
        f"{API_BASE_URL}{API_V1_STR}/tipuri-livrare/{delivery_type_id}",
        json={"denumire": updated_delivery_type_name}
    )
    assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}: {update_response.text}"
    updated_delivery_type = update_response.json()
    assert updated_delivery_type["denumire"] == updated_delivery_type_name

    # 4. DELETE the delivery type
    delete_response = requests.delete(f"{API_BASE_URL}{API_V1_STR}/tipuri-livrare/{delivery_type_id}")
    assert delete_response.status_code == 204

    # 5. VERIFY the delivery type is deleted
    verify_response = requests.get(f"{API_BASE_URL}{API_V1_STR}/tipuri-livrare/{delivery_type_id}")
    assert verify_response.status_code == 404

def test_delivery_type_list_and_pagination():
    """
    Tests listing delivery types with pagination.
    """
    # Create a test delivery type to ensure we have at least one in the database
    test_name = "Test Delivery Type for Pagination"
    create_response = requests.post(
        f"{API_BASE_URL}{API_V1_STR}/tipuri-livrare/",
        json={"denumire": test_name}
    )
    assert create_response.status_code == 201
    delivery_type_id = create_response.json()["id"]

    try:
        # Test basic listing
        list_response = requests.get(f"{API_BASE_URL}{API_V1_STR}/tipuri-livrare/")
        assert list_response.status_code == 200
        delivery_types = list_response.json()
        assert isinstance(delivery_types, list)
        assert len(delivery_types) > 0

        # Test pagination - skip 1, limit 1
        pagination_response = requests.get(f"{API_BASE_URL}{API_V1_STR}/tipuri-livrare/?skip=1&limit=1")
        assert pagination_response.status_code == 200
        paginated_types = pagination_response.json()
        assert isinstance(paginated_types, list)
        assert len(paginated_types) <= 1  # Should be exactly 1 unless there are no delivery types

    finally:
        # Clean up - delete the test delivery type
        requests.delete(f"{API_BASE_URL}{API_V1_STR}/tipuri-livrare/{delivery_type_id}")

def test_delivery_type_validation():
    """
    Tests validation for delivery type endpoints.
    """
    # Test invalid ID validation
    invalid_id_response = requests.get(f"{API_BASE_URL}{API_V1_STR}/tipuri-livrare/-1")
    assert invalid_id_response.status_code == 422

    # Test invalid name (empty string)
    invalid_name_response = requests.post(
        f"{API_BASE_URL}{API_V1_STR}/tipuri-livrare/",
        json={"denumire": ""}
    )
    assert invalid_name_response.status_code == 422

    # Test duplicate name validation
    # First, create a delivery type with a unique name
    unique_name = "Unique Delivery Type Name"
    create_response = requests.post(
        f"{API_BASE_URL}{API_V1_STR}/tipuri-livrare/",
        json={"denumire": unique_name}
    )
    assert create_response.status_code == 201
    delivery_type_id = create_response.json()["id"]

    try:
        # Try to create another one with the same name
        duplicate_response = requests.post(
            f"{API_BASE_URL}{API_V1_STR}/tipuri-livrare/",
            json={"denumire": unique_name}
        )
        assert duplicate_response.status_code == 400, "Should not allow duplicate names"

    finally:
        # Clean up - delete the test delivery type
        requests.delete(f"{API_BASE_URL}{API_V1_STR}/tipuri-livrare/{delivery_type_id}")
