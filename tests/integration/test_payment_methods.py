import requests
from integration.test_utils import EntityTestUtils

# Create a test utils instance for payment methods
payment_method_utils = EntityTestUtils(entity_name="Payment Method", endpoint_path="modalitati-plata")


def test_patch_with_valid_data():
    """
    Test PATCH with valid data.
    """
    # Create a payment method for testing
    created_entity, entity_id = payment_method_utils.create_entity("Test Payment Method")
    
    try:
        # PATCH with new name
        new_name = "Patched Payment Method"
        patch_response = requests.patch(
            f"{payment_method_utils.base_url}/{entity_id}",
            json={"denumire": new_name}
        )
        assert patch_response.status_code == 200, (
            f"PATCH should return 200, got {patch_response.status_code}: {patch_response.text}"
        )
        
        patched_entity = patch_response.json()
        assert patched_entity["denumire"] == new_name
        assert patched_entity["id"] == entity_id
        
        # Verify the change persisted
        retrieved_entity = payment_method_utils.get_entity(entity_id)
        assert retrieved_entity["denumire"] == new_name
        
    finally:
        # Clean up
        payment_method_utils.delete_entity(entity_id)


def test_patch_with_empty_json():
    """
    Test PATCH with empty JSON (should return the original object).
    """
    # Create a payment method for testing
    created_entity, entity_id = payment_method_utils.create_entity("Test Payment Method")
    
    try:
        # PATCH with empty JSON should return the original object
        empty_patch_response = requests.patch(
            f"{payment_method_utils.base_url}/{entity_id}",
            json={}
        )
        assert empty_patch_response.status_code == 200, (
            f"PATCH with empty JSON should return 200, got {empty_patch_response.status_code}"
        )
        
        # Verify the original object is returned unchanged
        original_entity = empty_patch_response.json()
        assert original_entity["denumire"] == "Test Payment Method"
        assert original_entity["id"] == entity_id
        
    finally:
        # Clean up
        payment_method_utils.delete_entity(entity_id)


def test_patch_with_non_existent_payment_method():
    """
    Test PATCH with non-existent payment method ID.
    """
    non_existent_response = requests.patch(
        f"{payment_method_utils.base_url}/99999",
        json={"denumire": "test"}
    )
    assert non_existent_response.status_code == 404, (
        f"PATCH with non-existent ID should return 404, got {non_existent_response.status_code}"
    )


def test_patch_with_invalid_data():
    """
    Test PATCH with invalid data (should return 422).
    """
    # Create a payment method for testing
    created_entity, entity_id = payment_method_utils.create_entity("Test Payment Method")
    
    try:
        # PATCH with empty string (should fail validation)
        invalid_patch_response = requests.patch(
            f"{payment_method_utils.base_url}/{entity_id}",
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
        payment_method_utils.delete_entity(entity_id)


def test_patch_with_duplicate_name():
    """
    Test PATCH with duplicate name (should fail).
    """
    # Create two payment methods
    first_name = "First Payment Method"
    second_name = "Second Payment Method"

    first_entity, first_id = payment_method_utils.create_entity(first_name)
    second_entity, second_id = payment_method_utils.create_entity(second_name)

    try:
        # Try to PATCH first payment method to use the same name as second payment method
        duplicate_patch_response = requests.patch(
            f"{payment_method_utils.base_url}/{first_id}",
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
        payment_method_utils.delete_entity(second_id)
        payment_method_utils.delete_entity(first_id)


def test_patch_with_partial_data_works():
    """
    Test that PATCH accepts partial data.
    """
    # Create a payment method for testing
    created_entity, entity_id = payment_method_utils.create_entity("Test Payment Method")
    
    try:
        # PATCH with partial data (should work)
        patch_data = {"denumire": "Patched Payment Method"}
        patch_response = requests.patch(
            f"{payment_method_utils.base_url}/{entity_id}",
            json=patch_data
        )
        assert patch_response.status_code == 200
        
        # Verify the change
        patched_entity = patch_response.json()
        assert patched_entity["denumire"] == "Patched Payment Method"
        
    finally:
        # Clean up
        payment_method_utils.delete_entity(entity_id)


def test_put_with_empty_json_returns_original():
    """
    Test that PUT with empty JSON returns the original object unchanged.
    """
    # Create a payment method for testing
    created_entity, entity_id = payment_method_utils.create_entity("Test Payment Method")
    
    try:
        # PUT with empty JSON should return the original object
        put_response = requests.put(
            f"{payment_method_utils.base_url}/{entity_id}",
            json={}  # Empty JSON for PUT should return original
        )
        assert put_response.status_code == 200, (
            f"PUT with empty JSON should return 200, got {put_response.status_code}"
        )
        
        # Verify the original object is returned unchanged
        original_entity = put_response.json()
        assert original_entity["denumire"] == "Test Payment Method"
        assert original_entity["id"] == entity_id
        
    finally:
        # Clean up
        payment_method_utils.delete_entity(entity_id)


def test_put_with_complete_data_works():
    """
    Test that PUT accepts complete data.
    """
    # Create a payment method for testing
    created_entity, entity_id = payment_method_utils.create_entity("Test Payment Method")
    
    try:
        # PUT with complete data (should work)
        put_data = {"denumire": "PUT Updated Payment Method"}
        put_response = requests.put(
            f"{payment_method_utils.base_url}/{entity_id}",
            json=put_data
        )
        assert put_response.status_code == 200
        
        # Verify the change
        final_entity = payment_method_utils.get_entity(entity_id)
        assert final_entity["denumire"] == "PUT Updated Payment Method"
        
    finally:
        # Clean up
        payment_method_utils.delete_entity(entity_id)


def test_payment_method_crud_workflow():
    """
    Tests the full Create, Read, Update, and Delete (CRUD) workflow for payment methods.
    """
    payment_method_utils.test_crud_workflow()


def test_payment_method_list_and_pagination():
    """
    Tests listing payment methods with pagination.
    """
    payment_method_utils.test_list_and_pagination()


def test_payment_method_validation():
    """
    Tests validation for payment method endpoints.
    """
    payment_method_utils.test_validation()
