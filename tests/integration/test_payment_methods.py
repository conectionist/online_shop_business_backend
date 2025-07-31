import os
import requests
from integration.test_utils import EntityTestUtils

# Create a custom test utils class for payment methods
class PaymentMethodTestUtils:
    """Custom test utilities for payment methods with name and description fields."""
    
    def __init__(self):
        self.entity_name = "Payment Method"
        self.endpoint_path = "modalitati-plata"
        self.api_base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")
        self.api_v1_str = "/api/v1"
        self.base_url = f"{self.api_base_url}{self.api_v1_str}/{self.endpoint_path}"
    
    def generate_unique_name(self, prefix="pm"):
        """Generate a unique name for test entities within the 20-character limit."""
        import uuid
        # Generate a shorter UUID to stay within 20 chars: prefix (2-4 chars) + "-" + 8 chars = ~11-13 chars
        short_uuid = str(uuid.uuid4())[:8]
        return f"{prefix}-{short_uuid}"
    
    def create_entity(self, name=None, description=None):
        """
        Create a new payment method with the given name and description.
        
        Args:
            name: Internal name for the payment method, will generate unique if None
            description: Display description, will use name if None
            
        Returns:
            Tuple of (entity_data, entity_id)
        """
        if name is None:
            name = self.generate_unique_name("pm")
        if description is None:
            description = f"Test Payment Method: {name}"
            
        create_response = requests.post(
            f"{self.base_url}/",
            json={"name": name, "description": description}
        )
        assert create_response.status_code == 201, (
            f"Failed to create {self.entity_name}. "
            f"Expected 201, got {create_response.status_code}: {create_response.text}"
        )
        
        created_entity = create_response.json()
        assert "id" in created_entity
        assert created_entity["name"] == name
        assert created_entity["description"] == description
        
        return created_entity, created_entity["id"]
    
    def get_entity(self, entity_id, expected_status=200):
        """
        Get a payment method by ID.
        
        Args:
            entity_id: ID of the payment method to retrieve
            expected_status: Expected HTTP status code
            
        Returns:
            Payment method data if found, None if expected_status is not 200
        """
        get_response = requests.get(f"{self.base_url}/{entity_id}")
        assert get_response.status_code == expected_status, (
            f"Failed to get {self.entity_name}. "
            f"Expected {expected_status}, got {get_response.status_code}: {get_response.text}"
        )
        
        if expected_status == 200:
            return get_response.json()
        return None
    
    def update_entity(self, entity_id, name=None, description=None):
        """
        Update a payment method by ID.
        
        Args:
            entity_id: ID of the payment method to update
            name: New internal name for the payment method
            description: New display description for the payment method
            
        Returns:
            Updated payment method data
        """
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
            
        update_response = requests.put(
            f"{self.base_url}/{entity_id}",
            json=update_data
        )
        assert update_response.status_code == 200, (
            f"Failed to update {self.entity_name}. "
            f"Expected 200, got {update_response.status_code}: {get_response.text}"
        )
        
        updated_entity = update_response.json()
        if name is not None:
            assert updated_entity["name"] == name
        if description is not None:
            assert updated_entity["description"] == description
        
        return updated_entity
    
    def delete_entity(self, entity_id):
        """
        Delete a payment method by ID.
        
        Args:
            entity_id: ID of the payment method to delete
        """
        delete_response = requests.delete(f"{self.base_url}/{entity_id}")
        assert delete_response.status_code == 204, (
            f"Failed to delete {self.entity_name}. "
            f"Expected 204, got {delete_response.status_code}: {delete_response.text}"
        )

# Create a test utils instance for payment methods
payment_method_utils = PaymentMethodTestUtils()


def test_patch_with_valid_data():
    """
    Test PATCH with valid data.
    """
    # Create a payment method for testing
    created_entity, entity_id = payment_method_utils.create_entity("test_pm", "Test Payment Method")
    
    try:
        # PATCH with new name and description
        new_name = "patched_pm"
        new_description = "Patched Payment Method"
        patch_response = requests.patch(
            f"{payment_method_utils.base_url}/{entity_id}",
            json={"name": new_name, "description": new_description}
        )
        assert patch_response.status_code == 200, (
            f"PATCH should return 200, got {patch_response.status_code}: {patch_response.text}"
        )
        
        patched_entity = patch_response.json()
        assert patched_entity["name"] == new_name
        assert patched_entity["description"] == new_description
        assert patched_entity["id"] == entity_id
        
        # Verify the change persisted
        retrieved_entity = payment_method_utils.get_entity(entity_id)
        assert retrieved_entity["name"] == new_name
        assert retrieved_entity["description"] == new_description
        
    finally:
        # Clean up
        payment_method_utils.delete_entity(entity_id)


def test_patch_with_empty_json():
    """
    Test PATCH with empty JSON (should return 400 - no valid fields to update).
    """
    # Create a payment method for testing
    created_entity, entity_id = payment_method_utils.create_entity("test_pm", "Test Payment Method")
    
    try:
        # PATCH with empty JSON should return 400 (no valid fields to update)
        empty_patch_response = requests.patch(
            f"{payment_method_utils.base_url}/{entity_id}",
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
        payment_method_utils.delete_entity(entity_id)


def test_patch_with_non_existent_payment_method():
    """
    Test PATCH with non-existent payment method ID.
    """
    non_existent_response = requests.patch(
        f"{payment_method_utils.base_url}/99999",
        json={"name": "test"}
    )
    assert non_existent_response.status_code == 404, (
        f"PATCH with non-existent ID should return 404, got {non_existent_response.status_code}"
    )


def test_patch_with_invalid_data():
    """
    Test PATCH with invalid data (should return 422).
    """
    # Create a payment method for testing
    created_entity, entity_id = payment_method_utils.create_entity("test_pm", "Test Payment Method")
    
    try:
        # PATCH with empty string (should fail validation)
        invalid_patch_response = requests.patch(
            f"{payment_method_utils.base_url}/{entity_id}",
            json={"name": ""}
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
    first_name = "first_pm"
    second_name = "second_pm"
    first_description = "First Payment Method"
    second_description = "Second Payment Method"

    first_entity, first_id = payment_method_utils.create_entity(first_name, first_description)
    second_entity, second_id = payment_method_utils.create_entity(second_name, second_description)

    try:
        # Try to PATCH first payment method to use the same name as second payment method
        duplicate_patch_response = requests.patch(
            f"{payment_method_utils.base_url}/{first_id}",
            json={"name": second_name}
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
    created_entity, entity_id = payment_method_utils.create_entity("test_pm", "Test Payment Method")
    
    try:
        # PATCH with partial data (should work)
        patch_data = {"name": "patched_pm"}
        patch_response = requests.patch(
            f"{payment_method_utils.base_url}/{entity_id}",
            json=patch_data
        )
        assert patch_response.status_code == 200
        
        # Verify the change
        patched_entity = patch_response.json()
        assert patched_entity["name"] == "patched_pm"
        
    finally:
        # Clean up
        payment_method_utils.delete_entity(entity_id)


def test_put_with_empty_json_fails():
    """
    Test that PUT rejects empty JSON.
    """
    # Create a payment method for testing
    created_entity, entity_id = payment_method_utils.create_entity("test_pm", "Test Payment Method")
    
    try:
        # PUT with empty JSON (should fail)
        put_response = requests.put(
            f"{payment_method_utils.base_url}/{entity_id}",
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
        payment_method_utils.delete_entity(entity_id)


def test_put_with_complete_data_works():
    """
    Test that PUT accepts complete data.
    """
    # Create a payment method for testing
    created_entity, entity_id = payment_method_utils.create_entity("test_pm", "Test Payment Method")
    
    try:
        # PUT with complete data (should work)
        put_data = {"name": "put_updated_pm", "description": "PUT Updated Payment Method"}
        put_response = requests.put(
            f"{payment_method_utils.base_url}/{entity_id}",
            json=put_data
        )
        assert put_response.status_code == 200
        
        # Verify the change
        final_entity = payment_method_utils.get_entity(entity_id)
        assert final_entity["name"] == "put_updated_pm"
        assert final_entity["description"] == "PUT Updated Payment Method"
        
    finally:
        # Clean up
        payment_method_utils.delete_entity(entity_id)


def test_payment_method_crud_workflow():
    """
    Tests the full Create, Read, Update, and Delete (CRUD) workflow for payment methods.
    """
    # 1. CREATE
    initial_name = payment_method_utils.generate_unique_name("pm")
    initial_description = f"Test Payment Method: {initial_name}"
    created_entity, entity_id = payment_method_utils.create_entity(initial_name, initial_description)
    
    # 2. READ
    retrieved_entity = payment_method_utils.get_entity(entity_id)
    assert retrieved_entity == created_entity
    
    # 3. UPDATE
    updated_name = payment_method_utils.generate_unique_name("updated_pm")
    updated_description = f"Updated Payment Method: {updated_name}"
    updated_entity = payment_method_utils.update_entity(entity_id, updated_name, updated_description)
    assert updated_entity["name"] == updated_name
    assert updated_entity["description"] == updated_description
    
    # 4. DELETE
    payment_method_utils.delete_entity(entity_id)
    
    # 5. VERIFY deletion
    payment_method_utils.get_entity(entity_id, expected_status=404)


def test_payment_method_list_and_pagination():
    """
    Tests listing payment methods with pagination.
    """
    # Create a payment method to ensure we have at least one
    created_entity, entity_id = payment_method_utils.create_entity()
    
    try:
        # Test basic listing
        list_response = requests.get(f"{payment_method_utils.base_url}/")
        assert list_response.status_code == 200
        entities = list_response.json()
        assert isinstance(entities, list)
        assert len(entities) > 0
        
        # Test pagination
        pagination_response = requests.get(f"{payment_method_utils.base_url}/?skip=1&limit=1")
        assert pagination_response.status_code == 200
        paginated_entities = pagination_response.json()
        assert isinstance(paginated_entities, list)
        assert len(paginated_entities) <= 1
        
    finally:
        # Clean up
        payment_method_utils.delete_entity(entity_id)


def test_payment_method_validation():
    """
    Tests validation for payment method endpoints.
    """
    # Test invalid ID
    invalid_id_response = requests.get(f"{payment_method_utils.base_url}/-1")
    assert invalid_id_response.status_code == 422
    
    # Test empty name
    invalid_name_response = requests.post(
        f"{payment_method_utils.base_url}/",
        json={"name": "", "description": "Test"}
    )
    assert invalid_name_response.status_code == 422
    
    # Test duplicate name validation
    unique_name = payment_method_utils.generate_unique_name("unique_pm")
    created_entity, entity_id = payment_method_utils.create_entity(unique_name, "Unique Payment Method")
    
    try:
        # Try to create another payment method with the same name
        duplicate_response = requests.post(
            f"{payment_method_utils.base_url}/",
            json={"name": unique_name, "description": "Duplicate Payment Method"}
        )
        assert duplicate_response.status_code == 400, "Should not allow duplicate names"
        
    finally:
        # Clean up
        payment_method_utils.delete_entity(entity_id)
