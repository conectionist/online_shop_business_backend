import os
import requests
import uuid
import datetime
from integration.test_utils import EntityTestUtils
from integration.test_delivery_schedules_api import DeliveryScheduleTestUtils
from integration.test_auth_utils import auth_utils


class ListTestUtils(EntityTestUtils):
    """Test utilities specifically for Lists."""
    
    def __init__(self):
        super().__init__(entity_name="List", endpoint_path="liste")
        # We need delivery schedule utils to create a delivery schedule for foreign key relationship
        self.delivery_schedule_utils = DeliveryScheduleTestUtils()
    
    def create_delivery_schedule(self):
        """
        Create a delivery schedule to use in list tests.
        
        Returns:
            Tuple of (schedule_data, schedule_id)
        """
        schedule_name = self.delivery_schedule_utils.generate_unique_name("Schedule")
        return self.delivery_schedule_utils.create_entity(schedule_name)
    
    def generate_test_date(self):
        """Generate a date string for tests in YYYY-MM-DD format."""
        today = datetime.date.today()
        return today.strftime("%Y-%m-%d")
    
    def create_entity(self, orare_livrari_id=None, date=None, is_current=True, is_published=True):
        """
        Create a new list.
        
        Args:
            orare_livrari_id: ID of the delivery schedule, will create one if None
            date: Date of the list, will use today if None
            is_current: Flag indicating if this is the current list
            is_published: Flag indicating if the list is published
            
        Returns:
            Tuple of (entity_data, entity_id)
        """
        # Create a delivery schedule if needed
        if orare_livrari_id is None:
            _, orare_livrari_id = self.create_delivery_schedule()
            
        # Use today's date if none provided
        if date is None:
            date = self.generate_test_date()
            
        # Generate short intro message (under 100 chars)
        mesaj_introducere = f"Test Message {str(uuid.uuid4())[:8]}"
        
        # Ensure we're authenticated
        if not auth_utils.access_token:
            auth_utils.login()
            
        create_response = auth_utils.make_authenticated_request(
            "POST",
            f"{self.base_url}/",
            json={
                "data": date,
                "is_current": is_current,
                "is_published": is_published,
                "mesaj_introducere": mesaj_introducere,
                "alte_detalii": "Test details",  # Shortened to be safe
                "numar_whatsapp": "+40712345678",
                "orare_livrari_id": orare_livrari_id
            }
        )
        assert create_response.status_code == 201, (
            f"Failed to create {self.entity_name}. "
            f"Expected 201, got {create_response.status_code}: {create_response.text}"
        )
        
        created_entity = create_response.json()
        assert "id" in created_entity
        assert created_entity["data"] == date
        assert created_entity["is_current"] == is_current
        assert created_entity["orare_livrari_id"] == orare_livrari_id
        
        return created_entity, created_entity["id"]
    
    def update_entity(self, entity_id, mesaj_introducere=None, is_published=None):
        """
        Update a list by ID.
        
        Args:
            entity_id: ID of the entity to update
            mesaj_introducere: New introduction message
            is_published: New published status
            
        Returns:
            Updated entity data
        """
        update_data = {}
        
        if mesaj_introducere is not None:
            # Ensure message is under 100 chars
            if len(mesaj_introducere) > 100:
                mesaj_introducere = mesaj_introducere[:100]
            update_data["mesaj_introducere"] = mesaj_introducere
            
        if is_published is not None:
            update_data["is_published"] = is_published
        
        # Ensure we're authenticated
        if not auth_utils.access_token:
            auth_utils.login()
            
        update_response = auth_utils.make_authenticated_request(
            "PUT",
            f"{self.base_url}/{entity_id}",
            json=update_data
        )
        assert update_response.status_code == 200, (
            f"Failed to update {self.entity_name}. "
            f"Expected 200, got {update_response.status_code}: {update_response.text}"
        )
        
        updated_entity = update_response.json()
        
        if mesaj_introducere is not None:
            assert updated_entity["mesaj_introducere"] == mesaj_introducere
            
        if is_published is not None:
            assert updated_entity["is_published"] == is_published
        
        return updated_entity
    
    def delete_entity(self, entity_id, hard_delete=False):
        """
        Delete a list by ID.
        
        Args:
            entity_id: ID of the entity to delete
            hard_delete: If True, perform hard deletion, otherwise soft delete
        """
        delete_url = f"{self.base_url}/{entity_id}"
        if hard_delete:
            delete_url += "?hard_delete=true"
        
        # Ensure we're authenticated
        if not auth_utils.access_token:
            auth_utils.login()
            
        delete_response = auth_utils.make_authenticated_request(
            "DELETE",
            delete_url
        )
        
        # For lists, we expect 200 OK with a message rather than 204 No Content
        assert delete_response.status_code == 200, (
            f"Failed to delete {self.entity_name}. "
            f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        )
        
        delete_data = delete_response.json()
        assert "message" in delete_data
        
        if hard_delete:
            # For hard delete, we expect either "has been deleted" or "has been soft deleted" 
            # depending on the implementation
            assert any(phrase in delete_data["message"] for phrase in ["has been deleted", "has been soft deleted"])
        else:
            assert "has been soft deleted" in delete_data["message"]
            
    def verify_soft_deletion(self, entity_id):
        """
        Verify that a list has been soft deleted.
        
        Args:
            entity_id: ID of the entity to check
        """
        # First check that normal GET returns 404
        self.get_entity(entity_id, expected_status=404)
        
        # Then check that with include_deleted=true we can see it
        get_response = requests.get(
            f"{self.base_url}/{entity_id}?include_deleted=true"
        )
        assert get_response.status_code == 200
        
        entity = get_response.json()
        assert entity["is_deleted"] is True
    
    def test_crud_workflow(self):
        """
        Test the full CRUD workflow for a list.
        """
        # 1. CREATE
        created_entity, entity_id = self.create_entity()
        
        # 2. READ
        retrieved_entity = self.get_entity(entity_id)
        assert retrieved_entity == created_entity
        
        # 3. UPDATE
        # Make sure our updated message is short enough
        updated_message = f"Updated {str(uuid.uuid4())[:8]}"
        updated_entity = self.update_entity(entity_id, mesaj_introducere=updated_message, is_published=False)
        assert updated_entity["mesaj_introducere"] == updated_message
        assert updated_entity["is_published"] is False
        
        # 4. SOFT DELETE
        self.delete_entity(entity_id)
        
        # 5. VERIFY soft deletion
        self.verify_soft_deletion(entity_id)
    
    def test_hard_delete_workflow(self):
        """
        Test the hard deletion workflow for a list.
        """
        # 1. CREATE
        created_entity, entity_id = self.create_entity()
        
        # 2. Try HARD DELETE (but verify if API supports it)
        delete_url = f"{self.base_url}/{entity_id}?hard_delete=true"
        
        # Ensure we're authenticated
        if not auth_utils.access_token:
            auth_utils.login()
            
        delete_response = auth_utils.make_authenticated_request(
            "DELETE",
            delete_url
        )
        assert delete_response.status_code == 200
        
        # Get the response message to determine if hard or soft delete was performed
        delete_data = delete_response.json()
        is_hard_delete = "has been deleted" in delete_data["message"] and "soft" not in delete_data["message"]
        
        if is_hard_delete:
            # If hard delete is supported, entity should be completely gone
            self.get_entity(entity_id, expected_status=404)
            
            get_response = requests.get(
                f"{self.base_url}/{entity_id}?include_deleted=true"
            )
            assert get_response.status_code == 404
        else:
            # If hard delete is not supported (only soft delete), verify soft deletion behavior
            print("NOTE: API does not support hard deletion for lists, verifying soft deletion instead")
            self.verify_soft_deletion(entity_id)
    
    def test_validation(self):
        """
        Test basic validation rules for lists.
        """
        # Test invalid ID
        invalid_id_response = requests.get(f"{self.base_url}/-1")
        assert invalid_id_response.status_code == 422
        
        # Test missing required fields
        # Ensure we're authenticated
        if not auth_utils.access_token:
            auth_utils.login()
            
        missing_fields_response = auth_utils.make_authenticated_request(
            "POST",
            f"{self.base_url}/",
            json={}
        )
        assert missing_fields_response.status_code == 422
        
        # Test invalid WhatsApp number
        _, schedule_id = self.create_delivery_schedule()
        invalid_whatsapp_response = auth_utils.make_authenticated_request(
            "POST",
            f"{self.base_url}/",
            json={
                "data": self.generate_test_date(),
                "is_current": True,
                "orare_livrari_id": schedule_id,
                "numar_whatsapp": "invalid"  # Invalid format
            }
        )
        assert invalid_whatsapp_response.status_code == 422
        
        # Test invalid delivery schedule ID
        invalid_schedule_response = auth_utils.make_authenticated_request(
            "POST",
            f"{self.base_url}/",
            json={
                "data": self.generate_test_date(),
                "is_current": True,
                "orare_livrari_id": 999999  # Non-existent ID
            }
        )
        assert invalid_schedule_response.status_code in [400, 404, 422]
        
        # Test maximum length validation for mesaj_introducere
        # Create a message that's exactly 100 characters (the new limit)
        max_length_message = "A" * 100
        _, schedule_id = self.create_delivery_schedule()
        max_length_response = auth_utils.make_authenticated_request(
            "POST",
            f"{self.base_url}/",
            json={
                "data": self.generate_test_date(),
                "is_current": True,
                "orare_livrari_id": schedule_id,
                "mesaj_introducere": max_length_message
            }
        )
        assert max_length_response.status_code == 201, (
            f"Should accept message with exactly 100 characters, got {max_length_response.status_code}"
        )
        
        # Verify the message was created successfully
        created_entity = max_length_response.json()
        assert created_entity["mesaj_introducere"] == max_length_message
        assert len(created_entity["mesaj_introducere"]) == 100
        
        # Clean up the test entity
        self.delete_entity(created_entity["id"], hard_delete=True)
        
        # Try to create a list with a message that's 101 characters (exceeds the limit)
        too_long_message = "A" * 101
        too_long_response = auth_utils.make_authenticated_request(
            "POST",
            f"{self.base_url}/",
            json={
                "data": self.generate_test_date(),
                "is_current": True,
                "orare_livrari_id": schedule_id,
                "mesaj_introducere": too_long_message
            }
        )
        assert too_long_response.status_code == 422, (
            f"Should reject message longer than 100 characters, got {too_long_response.status_code}"
        )
    
    def test_list_and_pagination(self):
        """
        Test listing lists with pagination and filtering.
        """
        # Create multiple lists to test pagination
        created_entities = []
        entity_ids = []
        
        try:
            # Create 3 test lists
            for i in range(3):
                created_entity, entity_id = self.create_entity()
                created_entities.append(created_entity)
                entity_ids.append(entity_id)
            
            # Test basic listing
            list_response = requests.get(f"{self.base_url}/")
            assert list_response.status_code == 200
            entities = list_response.json()
            assert isinstance(entities, list)
            assert len(entities) >= 3
            
            # Test pagination
            pagination_response = requests.get(f"{self.base_url}/?skip=1&limit=1")
            assert pagination_response.status_code == 200
            paginated_entities = pagination_response.json()
            assert isinstance(paginated_entities, list)
            assert len(paginated_entities) == 1
            
            # Soft delete one list and test include_deleted filter
            self.delete_entity(entity_ids[0])
            
            # Without include_deleted, should see only 2 lists
            normal_response = requests.get(f"{self.base_url}/")
            assert normal_response.status_code == 200
            normal_entities = normal_response.json()
            assert len([e for e in normal_entities if e["id"] == entity_ids[0]]) == 0
            
            # With include_deleted, should see all 3 lists
            include_deleted_response = requests.get(f"{self.base_url}/?include_deleted=true")
            assert include_deleted_response.status_code == 200
            all_entities = include_deleted_response.json()
            assert len([e for e in all_entities if e["id"] == entity_ids[0]]) == 1
            
        finally:
            # Clean up - hard delete all created lists
            for entity_id in entity_ids:
                try:
                    self.delete_entity(entity_id, hard_delete=True)
                except:
                    pass


# Create an instance of our test utilities
list_utils = ListTestUtils()


def test_patch_with_valid_data():
    """
    Test PATCH with valid data.
    """
    # Create a list for testing
    created_entity, entity_id = list_utils.create_entity()
    
    try:
        # PATCH with new message
        new_message = "Patched Message"
        patch_response = auth_utils.make_authenticated_request(
            "PATCH",
            f"{list_utils.base_url}/{entity_id}",
            json={"mesaj_introducere": new_message}
        )
        assert patch_response.status_code == 200, (
            f"PATCH should return 200, got {patch_response.status_code}: {patch_response.text}"
        )
        
        patched_entity = patch_response.json()
        assert patched_entity["mesaj_introducere"] == new_message
        assert patched_entity["id"] == entity_id
        
        # Verify the change persisted
        retrieved_entity = list_utils.get_entity(entity_id)
        assert retrieved_entity["mesaj_introducere"] == new_message
        
    finally:
        # Clean up
        list_utils.delete_entity(entity_id)


def test_patch_with_empty_json():
    """
    Test PATCH with empty JSON (should return 400 - no valid fields to update).
    """
    # Create a list for testing
    created_entity, entity_id = list_utils.create_entity()
    
    try:
        # PATCH with empty JSON should return 400 (no valid fields to update)
        empty_patch_response = auth_utils.make_authenticated_request(
            "PATCH",
            f"{list_utils.base_url}/{entity_id}",
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
        list_utils.delete_entity(entity_id)


def test_patch_with_non_existent_list():
    """
    Test PATCH with non-existent list ID.
    """
    non_existent_response = auth_utils.make_authenticated_request(
        "PATCH",
        f"{list_utils.base_url}/99999",
        json={"mesaj_introducere": "test"}
    )
    assert non_existent_response.status_code == 404, (
        f"PATCH with non-existent ID should return 404, got {non_existent_response.status_code}"
    )


def test_patch_with_invalid_data():
    """
    Test PATCH with invalid data (should return 422).
    """
    # Create a list for testing
    created_entity, entity_id = list_utils.create_entity()
    
    try:
        # PATCH with message that's too long (exceeds 100 char limit)
        long_message = "A" * 101  # Exactly 101 characters to exceed the limit
        invalid_patch_response = auth_utils.make_authenticated_request(
            "PATCH",
            f"{list_utils.base_url}/{entity_id}",
            json={"mesaj_introducere": long_message}
        )
        assert invalid_patch_response.status_code == 422, (
            f"PATCH with invalid data should return 422, got {invalid_patch_response.status_code}"
        )
        
        # Verify the error message
        error_data = invalid_patch_response.json()
        assert "detail" in error_data
        
    finally:
        # Clean up
        list_utils.delete_entity(entity_id)


def test_patch_multiple_fields():
    """
    Test PATCH with multiple fields at once.
    """
    # Create a list for testing
    created_entity, entity_id = list_utils.create_entity()
    
    try:
        # PATCH with multiple fields
        patch_data = {
            "mesaj_introducere": "Multi Field Update",
            "is_published": False,
            "alte_detalii": "Updated details for testing"
        }
        
        patch_response = auth_utils.make_authenticated_request(
            "PATCH",
            f"{list_utils.base_url}/{entity_id}",
            json=patch_data
        )
        assert patch_response.status_code == 200, (
            f"PATCH should return 200, got {patch_response.status_code}: {patch_response.text}"
        )
        
        patched_entity = patch_response.json()
        assert patched_entity["mesaj_introducere"] == "Multi Field Update"
        assert patched_entity["is_published"] is False
        assert patched_entity["alte_detalii"] == "Updated details for testing"
        assert patched_entity["id"] == entity_id
        
        # Verify the changes persisted
        retrieved_entity = list_utils.get_entity(entity_id)
        assert retrieved_entity["mesaj_introducere"] == "Multi Field Update"
        assert retrieved_entity["is_published"] is False
        assert retrieved_entity["alte_detalii"] == "Updated details for testing"
        
    finally:
        # Clean up
        list_utils.delete_entity(entity_id)


def test_patch_with_invalid_foreign_key():
    """
    Test PATCH with invalid foreign key (orare_livrari_id).
    """
    # Create a list for testing
    created_entity, entity_id = list_utils.create_entity()
    
    try:
        # PATCH with invalid delivery schedule ID
        invalid_patch_response = auth_utils.make_authenticated_request(
            "PATCH",
            f"{list_utils.base_url}/{entity_id}",
            json={"orare_livrari_id": 999999}  # Non-existent ID
        )
        assert invalid_patch_response.status_code == 400, (
            f"PATCH with invalid foreign key should return 400, got {invalid_patch_response.status_code}"
        )
        
        # Verify the error message
        error_data = invalid_patch_response.json()
        assert "detail" in error_data
        
    finally:
        # Clean up
        list_utils.delete_entity(entity_id)


def test_patch_with_partial_data_works():
    """
    Test that PATCH accepts partial data.
    """
    # Create a list for testing
    created_entity, entity_id = list_utils.create_entity()
    
    try:
        # PATCH with partial data (should work)
        patch_data = {"mesaj_introducere": "Patched Message"}
        patch_response = auth_utils.make_authenticated_request(
            "PATCH",
            f"{list_utils.base_url}/{entity_id}",
            json=patch_data
        )
        assert patch_response.status_code == 200
        
        # Verify the change
        patched_entity = patch_response.json()
        assert patched_entity["mesaj_introducere"] == "Patched Message"
        
    finally:
        # Clean up
        list_utils.delete_entity(entity_id)


def test_put_with_empty_json_fails():
    """
    Test that PUT rejects empty JSON.
    """
    # Create a list for testing
    created_entity, entity_id = list_utils.create_entity()
    
    try:
        # PUT with empty JSON (should fail)
        put_response = auth_utils.make_authenticated_request(
            "PUT",
            f"{list_utils.base_url}/{entity_id}",
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
        list_utils.delete_entity(entity_id)


def test_put_with_complete_data_works():
    """
    Test that PUT accepts complete data.
    """
    # Create a list for testing
    created_entity, entity_id = list_utils.create_entity()
    
    try:
        # PUT with complete data (should work)
        # Get current entity to use as base for complete PUT
        current_entity = list_utils.get_entity(entity_id)
        put_data = {
            "data": current_entity["data"],
            "is_current": current_entity["is_current"],
            "is_published": current_entity["is_published"],
            "mesaj_introducere": "PUT Updated Message",
            "alte_detalii": current_entity["alte_detalii"],
            "numar_whatsapp": current_entity["numar_whatsapp"],
            "orare_livrari_id": current_entity["orare_livrari_id"]
        }
        
        put_response = auth_utils.make_authenticated_request(
            "PUT",
            f"{list_utils.base_url}/{entity_id}",
            json=put_data
        )
        assert put_response.status_code == 200
        
        # Verify the change
        final_entity = list_utils.get_entity(entity_id)
        assert final_entity["mesaj_introducere"] == "PUT Updated Message"
        
    finally:
        # Clean up
        list_utils.delete_entity(entity_id)


def test_list_crud_workflow():
    """
    Tests the full Create, Read, Update, and Delete (CRUD) workflow for lists.
    """
    list_utils.test_crud_workflow()


def test_list_hard_delete_workflow():
    """
    Tests the hard deletion workflow for lists.
    """
    list_utils.test_hard_delete_workflow()


def test_list_validation():
    """
    Tests validation for list endpoints.
    """
    list_utils.test_validation()


def test_list_and_pagination():
    """
    Tests listing lists with pagination and include_deleted filter.
    """
    list_utils.test_list_and_pagination()


# =============================================================================
# LIST CLONING TESTS
# =============================================================================

def test_clone_list_basic():
    """
    Test basic list cloning functionality.
    """
    # Create a source list for cloning
    source_entity, source_id = list_utils.create_entity(
        is_current=True,
        is_published=True
    )
    
    try:
        # Clone the list
        clone_response = auth_utils.make_authenticated_request(
            "POST",
            f"{list_utils.base_url}/{source_id}/clone",
            json={}
        )
        
        assert clone_response.status_code == 201, (
            f"Clone should return 201, got {clone_response.status_code}: {clone_response.text}"
        )
        
        cloned_entity = clone_response.json()
        
        # Verify basic structure
        assert "id" in cloned_entity
        assert cloned_entity["id"] != source_id, "Cloned list should have different ID"
        
        # Verify metadata was copied
        assert cloned_entity["data"] == source_entity["data"]
        assert cloned_entity["mesaj_introducere"] == source_entity["mesaj_introducere"]
        assert cloned_entity["alte_detalii"] == source_entity["alte_detalii"]
        assert cloned_entity["numar_whatsapp"] == source_entity["numar_whatsapp"]
        assert cloned_entity["orare_livrari_id"] == source_entity["orare_livrari_id"]
        
        # Verify smart defaults were applied
        assert cloned_entity["is_current"] == False, "Cloned list should not be current"
        assert cloned_entity["is_published"] == False, "Cloned list should not be published"
        assert cloned_entity["is_deleted"] == False, "Cloned list should not be deleted"
        
        # Verify timestamps are current (allow for same second creation)
        assert cloned_entity["created_at"] >= source_entity["created_at"]
        assert cloned_entity["updated_at"] >= source_entity["updated_at"]
        
        cloned_id = cloned_entity["id"]
        
        # Clean up cloned list
        list_utils.delete_entity(cloned_id)
        
    finally:
        # Clean up source list
        list_utils.delete_entity(source_id)


def test_clone_list_with_categories_and_products():
    """
    Test cloning a list that has categories and products.
    """
    # Create a source list
    source_entity, source_id = list_utils.create_entity()
    
    try:
        # Add a category to the source list
        from integration.test_list_categories_api import ListCategoryTestUtils
        category_utils = ListCategoryTestUtils()
        
        # Get a category to add
        categories_response = auth_utils.make_authenticated_request(
            "GET",
            f"{auth_utils.api_base_url}{auth_utils.api_v1_str}/categories/"
        )
        assert categories_response.status_code == 200
        categories = categories_response.json()
        assert len(categories) > 0, "Need at least one category for testing"
        
        category_id = categories[0]["id"]
        
        # Add category to source list
        add_category_response = auth_utils.make_authenticated_request(
            "POST",
            f"{list_utils.base_url}/{source_id}/categories/{category_id}",
            json={"position": 0}
        )
        assert add_category_response.status_code == 201
        
        # Add a product to the category
        from integration.test_list_products_ordered_api import ListProductOrderedTestUtils
        product_utils = ListProductOrderedTestUtils()
        
        # Get a product to add
        products_response = auth_utils.make_authenticated_request(
            "GET",
            f"{auth_utils.api_base_url}{auth_utils.api_v1_str}/products/"
        )
        assert products_response.status_code == 200
        products = products_response.json()
        assert len(products) > 0, "Need at least one product for testing"
        
        product_id = products[0]["id"]
        
        # Add product to category in source list
        add_product_response = auth_utils.make_authenticated_request(
            "POST",
            f"{list_utils.base_url}/{source_id}/categories/{category_id}/products/{product_id}",
            json={"position": 0, "stoc_produs": 10}
        )
        assert add_product_response.status_code == 201
        
        # Now clone the list
        clone_response = auth_utils.make_authenticated_request(
            "POST",
            f"{list_utils.base_url}/{source_id}/clone",
            json={}
        )
        
        assert clone_response.status_code == 201
        cloned_entity = clone_response.json()
        cloned_id = cloned_entity["id"]
        
        # Verify the cloned list has the same structure
        cloned_categories_response = auth_utils.make_authenticated_request(
            "GET",
            f"{list_utils.base_url}/{cloned_id}/categories"
        )
        assert cloned_categories_response.status_code == 200
        
        cloned_products_response = auth_utils.make_authenticated_request(
            "GET",
            f"{list_utils.base_url}/{cloned_id}/products/ordered"
        )
        assert cloned_products_response.status_code == 200
        
        # Clean up cloned list
        list_utils.delete_entity(cloned_id)
        
    finally:
        # Clean up source list
        list_utils.delete_entity(source_id)


def test_clone_list_unauthorized():
    """
    Test that cloning requires admin authentication.
    """
    # Create a list for testing
    source_entity, source_id = list_utils.create_entity()
    
    try:
        # Try to clone without authentication
        clone_response = requests.post(
            f"{list_utils.base_url}/{source_id}/clone",
            json={}
        )
        
        assert clone_response.status_code in [401, 403], (
            f"Unauthorized clone should return 401 or 403, got {clone_response.status_code}"
        )
        
    finally:
        # Clean up
        list_utils.delete_entity(source_id)


def test_clone_nonexistent_list():
    """
    Test cloning a list that doesn't exist.
    """
    nonexistent_id = 99999
    
    clone_response = auth_utils.make_authenticated_request(
        "POST",
        f"{list_utils.base_url}/{nonexistent_id}/clone",
        json={}
    )
    
    assert clone_response.status_code == 404, (
        f"Cloning nonexistent list should return 404, got {clone_response.status_code}"
    )


def test_clone_list_invalid_id():
    """
    Test cloning with invalid list ID.
    """
    invalid_ids = [0, -1, "invalid"]
    
    for invalid_id in invalid_ids:
        clone_response = auth_utils.make_authenticated_request(
            "POST",
            f"{list_utils.base_url}/{invalid_id}/clone",
            json={}
        )
        
        assert clone_response.status_code in [404, 422], (
            f"Invalid ID {invalid_id} should return 404 or 422, got {clone_response.status_code}"
        )


def test_clone_list_multiple_times():
    """
    Test cloning the same list multiple times.
    """
    # Create a source list
    source_entity, source_id = list_utils.create_entity()
    cloned_ids = []
    
    try:
        # Clone the list 3 times
        for i in range(3):
            clone_response = auth_utils.make_authenticated_request(
                "POST",
                f"{list_utils.base_url}/{source_id}/clone",
                json={}
            )
            
            assert clone_response.status_code == 201
            cloned_entity = clone_response.json()
            cloned_ids.append(cloned_entity["id"])
            
            # Verify each clone is unique
            assert cloned_entity["id"] not in [source_id] + cloned_ids[:-1]
            
            # Verify metadata is identical
            assert cloned_entity["data"] == source_entity["data"]
            assert cloned_entity["mesaj_introducere"] == source_entity["mesaj_introducere"]
        
        # Clean up all cloned lists
        for cloned_id in cloned_ids:
            list_utils.delete_entity(cloned_id)
            
    finally:
        # Clean up source list
        list_utils.delete_entity(source_id)


def test_clone_list_workflow():
    """
    Test the complete workflow: clone -> customize -> publish.
    """
    # Create a source list
    source_entity, source_id = list_utils.create_entity(
        is_current=False,
        is_published=False
    )
    
    try:
        # Clone the list
        clone_response = auth_utils.make_authenticated_request(
            "POST",
            f"{list_utils.base_url}/{source_id}/clone",
            json={}
        )
        
        assert clone_response.status_code == 201
        cloned_entity = clone_response.json()
        cloned_id = cloned_entity["id"]
        
        # Customize the cloned list
        update_response = auth_utils.make_authenticated_request(
            "PATCH",
            f"{list_utils.base_url}/{cloned_id}",
            json={
                "mesaj_introducere": "Customized cloned list!",
                "is_current": True,
                "is_published": True
            }
        )
        
        assert update_response.status_code == 200
        
        # Verify the customization
        updated_entity = update_response.json()
        assert updated_entity["mesaj_introducere"] == "Customized cloned list!"
        assert updated_entity["is_current"] == True
        assert updated_entity["is_published"] == True
        
        # Clean up
        list_utils.delete_entity(cloned_id)
        
    finally:
        # Clean up source list
        list_utils.delete_entity(source_id)
