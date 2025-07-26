import requests
from integration.test_utils import EntityTestUtils

# Create a test utils instance for delivery types
delivery_type_utils = EntityTestUtils(entity_name="Delivery Type", endpoint_path="tipuri-livrare")


def test_patch_with_valid_data():
    """
    Test PATCH with valid data.
    """
    # Create a delivery type for testing
    created_entity, entity_id = delivery_type_utils.create_entity("Test Delivery Type")
    
    try:
        # PATCH with new name
        new_name = "Patched Delivery Type"
        patch_response = requests.patch(
            f"{delivery_type_utils.base_url}/{entity_id}",
            json={"denumire": new_name}
        )
        assert patch_response.status_code == 200, (
            f"PATCH should return 200, got {patch_response.status_code}: {patch_response.text}"
        )
        
        patched_entity = patch_response.json()
        assert patched_entity["denumire"] == new_name
        assert patched_entity["id"] == entity_id
        
        # Verify the change persisted
        retrieved_entity = delivery_type_utils.get_entity(entity_id)
        assert retrieved_entity["denumire"] == new_name
        
    finally:
        # Clean up
        delivery_type_utils.delete_entity(entity_id)


def test_patch_with_empty_json():
    """
    Test PATCH with empty JSON (should return 400 - no valid fields to update).
    """
    # Create a delivery type for testing
    created_entity, entity_id = delivery_type_utils.create_entity("Test Delivery Type")
    
    try:
        # PATCH with empty JSON should return 400 (no valid fields to update)
        empty_patch_response = requests.patch(
            f"{delivery_type_utils.base_url}/{entity_id}",
            json={}
        )
        assert empty_patch_response.status_code == 400, (
            f"PATCH with empty JSON should return 400, got {empty_patch_response.status_code}"
        )
        
        # Verify the error message
        error_data = empty_patch_response.json()
        assert "detail" in error_data
        assert "No valid fields to update" in error_data["detail"]
        
    finally:
        # Clean up
        delivery_type_utils.delete_entity(entity_id)


def test_patch_with_non_existent_delivery_type():
    """
    Test PATCH with non-existent delivery type ID.
    """
    non_existent_response = requests.patch(
        f"{delivery_type_utils.base_url}/99999",
        json={"denumire": "test"}
    )
    assert non_existent_response.status_code == 404, (
        f"PATCH with non-existent ID should return 404, got {non_existent_response.status_code}"
    )


def test_patch_with_invalid_data():
    """
    Test PATCH with invalid data (should return 422).
    """
    # Create a delivery type for testing
    created_entity, entity_id = delivery_type_utils.create_entity("Test Delivery Type")
    
    try:
        # PATCH with empty string (should fail validation)
        invalid_patch_response = requests.patch(
            f"{delivery_type_utils.base_url}/{entity_id}",
            json={"denumire": ""}
        )
        assert invalid_patch_response.status_code == 422, (
            f"PATCH with invalid data should return 422, got {invalid_patch_response.status_code}"
        )
        
        # Verify the error message
        error_data = invalid_patch_response.json()
        assert "detail" in error_data
        
    finally:
        # Clean up
        delivery_type_utils.delete_entity(entity_id)


def test_patch_with_duplicate_name():
    """
    Test PATCH with duplicate name (should fail).
    """
    # Create two delivery types
    first_name = "First Delivery Type"
    second_name = "Second Delivery Type"

    first_entity, first_id = delivery_type_utils.create_entity(first_name)
    second_entity, second_id = delivery_type_utils.create_entity(second_name)

    try:
        # Try to PATCH first delivery type to use the same name as second delivery type
        duplicate_patch_response = requests.patch(
            f"{delivery_type_utils.base_url}/{first_id}",
            json={"denumire": second_name}
        )
        assert duplicate_patch_response.status_code == 400, (
            f"PATCH with duplicate name should return 400, got {duplicate_patch_response.status_code}"
        )
        
        # Verify the error message
        error_data = duplicate_patch_response.json()
        assert "detail" in error_data
        assert "already exists" in error_data["detail"]

    finally:
        # Clean up
        delivery_type_utils.delete_entity(second_id)
        delivery_type_utils.delete_entity(first_id)


def test_patch_with_partial_data_works():
    """
    Test that PATCH accepts partial data.
    """
    # Create a delivery type for testing
    created_entity, entity_id = delivery_type_utils.create_entity("Test Delivery Type")
    
    try:
        # PATCH with partial data (should work)
        patch_data = {"denumire": "Patched Delivery Type"}
        patch_response = requests.patch(
            f"{delivery_type_utils.base_url}/{entity_id}",
            json=patch_data
        )
        assert patch_response.status_code == 200
        
        # Verify the change
        patched_entity = patch_response.json()
        assert patched_entity["denumire"] == "Patched Delivery Type"
        
    finally:
        # Clean up
        delivery_type_utils.delete_entity(entity_id)


def test_put_with_empty_json_fails():
    """
    Test that PUT rejects empty JSON.
    """
    # Create a delivery type for testing
    created_entity, entity_id = delivery_type_utils.create_entity("Test Delivery Type")
    
    try:
        # PUT with empty JSON (should fail)
        put_response = requests.put(
            f"{delivery_type_utils.base_url}/{entity_id}",
            json={}  # Empty JSON for PUT should fail
        )
        assert put_response.status_code == 400, (
            f"PUT with empty JSON should return 400, got {put_response.status_code}"
        )
        
        # Verify the error message
        error_data = put_response.json()
        assert "detail" in error_data
        assert "No valid fields to update" in error_data["detail"]
        
    finally:
        # Clean up
        delivery_type_utils.delete_entity(entity_id)


def test_put_with_complete_data_works():
    """
    Test that PUT accepts complete data.
    """
    # Create a delivery type for testing
    created_entity, entity_id = delivery_type_utils.create_entity("Test Delivery Type")
    
    try:
        # PUT with complete data (should work)
        put_data = {"denumire": "PUT Updated Delivery Type"}
        put_response = requests.put(
            f"{delivery_type_utils.base_url}/{entity_id}",
            json=put_data
        )
        assert put_response.status_code == 200
        
        # Verify the change
        final_entity = delivery_type_utils.get_entity(entity_id)
        assert final_entity["denumire"] == "PUT Updated Delivery Type"
        
    finally:
        # Clean up
        delivery_type_utils.delete_entity(entity_id)


def test_delivery_type_crud_workflow():
    """
    Tests the full Create, Read, Update, and Delete (CRUD) workflow for delivery types.
    """
    delivery_type_utils.test_crud_workflow()


def test_delivery_type_list_and_pagination():
    """
    Tests listing delivery types with pagination.
    """
    delivery_type_utils.test_list_and_pagination()


def test_delivery_type_validation():
    """
    Tests validation for delivery type endpoints.
    """
    delivery_type_utils.test_validation()
