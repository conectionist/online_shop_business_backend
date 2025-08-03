import requests
from integration.test_utils import EntityTestUtils
from integration.test_auth_utils import auth_utils

# Create a test utils instance for units
unit_utils = EntityTestUtils(entity_name="Unit", endpoint_path="unitati")

def test_unit_crud_workflow():
    """
    Tests the full Create, Read, Update, and Delete (CRUD) workflow for units.
    """
    unit_utils.test_crud_workflow()

def test_unit_list_and_pagination():
    """
    Tests listing units with pagination.
    """
    unit_utils.test_list_and_pagination()

def test_unit_validation():
    """
    Tests validation for unit endpoints.
    """
    unit_utils.test_validation()

def test_patch_with_valid_data():
    """
    Test PATCH with valid data.
    """
    # Create a unit for testing
    initial_name = "PatchValid"  # Short name for Units (max 45 chars)
    created_entity, entity_id = unit_utils.create_entity(initial_name)
    
    try:
        # PATCH with new name
        new_name = "PatchedUnit"  # Short name for Units (max 45 chars)
        patch_response = auth_utils.make_authenticated_request(
            "PATCH",
            f"{unit_utils.base_url}/{entity_id}",
            json={"denumire": new_name}
        )
        assert patch_response.status_code == 200, (
            f"PATCH should return 200, got {patch_response.status_code}: {patch_response.text}"
        )
        
        patched_entity = patch_response.json()
        assert patched_entity["denumire"] == new_name
        assert patched_entity["id"] == entity_id
        
        # Verify the change persisted
        retrieved_entity = unit_utils.get_entity(entity_id)
        assert retrieved_entity["denumire"] == new_name
        
    finally:
        # Clean up
        unit_utils.delete_entity(entity_id)


def test_patch_with_empty_json():
    """
    Test PATCH with empty JSON (should return 422 - no update data provided).
    """
    # Create a unit for testing
    initial_name = "PatchEmpty"  # Short name for Units (max 45 chars)
    created_entity, entity_id = unit_utils.create_entity(initial_name)
    
    try:
        # PATCH with empty JSON should return 422 (no update data provided)
        empty_patch_response = auth_utils.make_authenticated_request(
            "PATCH",
            f"{unit_utils.base_url}/{entity_id}",
            json={}
        )
        assert empty_patch_response.status_code == 422, (
            f"PATCH with empty JSON should return 422, got {empty_patch_response.status_code}"
        )
        
        # Verify the error message
        error_data = empty_patch_response.json()
        assert "detail" in error_data
        assert "No update data provided" in error_data["detail"]
        
    finally:
        # Clean up
        unit_utils.delete_entity(entity_id)


def test_patch_with_non_existent_unit():
    """
    Test PATCH with non-existent unit ID.
    """
    non_existent_response = auth_utils.make_authenticated_request(
        "PATCH",
        f"{unit_utils.base_url}/99999",
        json={"denumire": "test"}
    )
    assert non_existent_response.status_code == 404, (
        f"PATCH with non-existent ID should return 404, got {non_existent_response.status_code}"
    )


def test_patch_with_duplicate_name():
    """
    Test PATCH with duplicate name (should fail).
    """
    # Create two units
    first_name = "FirstUnit"  # Short name for Units (max 45 chars)
    second_name = "SecondUnit"  # Short name for Units (max 45 chars)
    
    first_entity, first_id = unit_utils.create_entity(first_name)
    second_entity, second_id = unit_utils.create_entity(second_name)
    
    try:
        # Try to PATCH first unit to use the same name as second unit
        duplicate_patch_response = auth_utils.make_authenticated_request(
            "PATCH",
            f"{unit_utils.base_url}/{first_id}",
            json={"denumire": second_name}
        )
        assert duplicate_patch_response.status_code == 400, (
            f"PATCH with duplicate name should return 400, got {duplicate_patch_response.status_code}"
        )
        
    finally:
        # Clean up
        unit_utils.delete_entity(first_id)
        unit_utils.delete_entity(second_id)

def test_unit_put_vs_patch_differences():
    """
    Tests the differences between PUT and PATCH operations.
    """
    # 1. CREATE a unit
    initial_name = "PutVsPatch"  # Short name for Units (max 45 chars)
    created_entity, entity_id = unit_utils.create_entity(initial_name)
    
    try:
        # 2. PATCH with partial data (should work)
        patch_name = "PatchedUnit"  # Short name for Units (max 45 chars)
        patch_response = auth_utils.make_authenticated_request(
            "PATCH",
            f"{unit_utils.base_url}/{entity_id}",
            json={"denumire": patch_name}
        )
        assert patch_response.status_code == 200
        
        # 3. PUT with partial data (should fail - PUT requires all fields)
        put_response = auth_utils.make_authenticated_request(
            "PUT",
            f"{unit_utils.base_url}/{entity_id}",
            json={}  # Empty JSON for PUT should fail
        )
        assert put_response.status_code == 422, (
            f"PUT with empty JSON should return 422, got {put_response.status_code}"
        )
        
        # 4. PUT with complete data (should work)
        put_name = "PutUpdated"  # Short name for Units (max 45 chars)
        put_response = auth_utils.make_authenticated_request(
            "PUT",
            f"{unit_utils.base_url}/{entity_id}",
            json={"denumire": put_name}
        )
        assert put_response.status_code == 200
        
        # 5. Verify final state
        final_entity = unit_utils.get_entity(entity_id)
        assert final_entity["denumire"] == put_name
        
    finally:
        # Clean up
        unit_utils.delete_entity(entity_id)
