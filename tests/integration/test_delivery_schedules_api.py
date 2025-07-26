import os
import requests
import uuid
from integration.test_utils import EntityTestUtils


class DeliveryScheduleTestUtils(EntityTestUtils):
    """Test utilities specifically for delivery schedules."""
    
    def __init__(self):
        super().__init__(entity_name="Delivery Schedule", endpoint_path="orare-livrari")
    
    def create_entity(self, name=None):
        """
        Create a new delivery schedule.
        
        Args:
            name: Content for orar_livrari field, will generate unique if None
            
        Returns:
            Tuple of (entity_data, entity_id)
        """
        if name is None:
            name = self.generate_unique_name()
            
        create_response = requests.post(
            f"{self.base_url}/",
            json={"orar_livrari": name}
        )
        assert create_response.status_code == 201, (
            f"Failed to create {self.entity_name}. "
            f"Expected 201, got {create_response.status_code}: {create_response.text}"
        )
        
        created_entity = create_response.json()
        assert "id" in created_entity
        assert created_entity["orar_livrari"] == name
        
        return created_entity, created_entity["id"]
    
    def update_entity(self, entity_id, name):
        """
        Update a delivery schedule by ID.
        
        Args:
            entity_id: ID of the entity to update
            name: New content for orar_livrari field
            
        Returns:
            Updated entity data
        """
        update_response = requests.put(
            f"{self.base_url}/{entity_id}",
            json={"orar_livrari": name}
        )
        assert update_response.status_code == 200, (
            f"Failed to update {self.entity_name}. "
            f"Expected 200, got {update_response.status_code}: {update_response.text}"
        )
        
        updated_entity = update_response.json()
        assert updated_entity["orar_livrari"] == name
        
        return updated_entity
    
    def test_crud_workflow(self):
        """
        Test the full CRUD workflow for a delivery schedule.
        """
        # 1. CREATE
        initial_name = self.generate_unique_name()
        created_entity, entity_id = self.create_entity(initial_name)
        
        # 2. READ
        retrieved_entity = self.get_entity(entity_id)
        assert retrieved_entity == created_entity
        
        # 3. UPDATE
        updated_name = self.generate_unique_name("Updated")
        updated_entity = self.update_entity(entity_id, updated_name)
        assert updated_entity["orar_livrari"] == updated_name
        
        # 4. DELETE
        self.delete_entity(entity_id)
        
        # 5. VERIFY deletion
        self.get_entity(entity_id, expected_status=404)
    
    def test_validation(self):
        """
        Test basic validation rules for delivery schedules.
        """
        # Test invalid ID
        invalid_id_response = requests.get(f"{self.base_url}/-1")
        assert invalid_id_response.status_code == 422
        
        # Test empty orar_livrari
        invalid_data_response = requests.post(
            f"{self.base_url}/",
            json={"orar_livrari": ""}
        )
        assert invalid_data_response.status_code == 422


# Create an instance of our test utilities
delivery_schedule_utils = DeliveryScheduleTestUtils()


def test_delivery_schedule_crud_workflow():
    """
    Tests the full Create, Read, Update, and Delete (CRUD) workflow for delivery schedules.
    """
    delivery_schedule_utils.test_crud_workflow()


def test_delivery_schedule_list_and_pagination():
    """
    Tests listing delivery schedules with pagination.
    """
    delivery_schedule_utils.test_list_and_pagination()


def test_delivery_schedule_validation():
    """
    Tests validation for delivery schedule endpoints.
    """
    delivery_schedule_utils.test_validation()


def test_patch_with_valid_data():
    """
    Test PATCH with valid data.
    """
    # Create a delivery schedule for testing
    initial_schedule = "Monday-Friday: 9:00-18:00"  # Short schedule for testing
    created_entity, entity_id = delivery_schedule_utils.create_entity(initial_schedule)
    
    try:
        # PATCH with new schedule
        new_schedule = "Monday-Friday: 9:00-18:00, Saturday: 10:00-14:00"
        patch_response = requests.patch(
            f"{delivery_schedule_utils.base_url}/{entity_id}",
            json={"orar_livrari": new_schedule}
        )
        assert patch_response.status_code == 200, (
            f"PATCH should return 200, got {patch_response.status_code}: {patch_response.text}"
        )
        
        patched_entity = patch_response.json()
        assert patched_entity["orar_livrari"] == new_schedule
        assert patched_entity["id"] == entity_id
        
        # Verify the change persisted
        retrieved_entity = delivery_schedule_utils.get_entity(entity_id)
        assert retrieved_entity["orar_livrari"] == new_schedule
        
    finally:
        # Clean up
        delivery_schedule_utils.delete_entity(entity_id)


def test_patch_with_empty_json():
    """
    Test PATCH with empty JSON (should return 400 - no valid fields to update).
    """
    # Create a delivery schedule for testing
    initial_schedule = "Monday-Friday: 9:00-18:00"  # Short schedule for testing
    created_entity, entity_id = delivery_schedule_utils.create_entity(initial_schedule)
    
    try:
        # PATCH with empty JSON should return 400 (no valid fields to update)
        empty_patch_response = requests.patch(
            f"{delivery_schedule_utils.base_url}/{entity_id}",
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
        delivery_schedule_utils.delete_entity(entity_id)


def test_patch_with_non_existent_delivery_schedule():
    """
    Test PATCH with non-existent delivery schedule ID.
    """
    non_existent_response = requests.patch(
        f"{delivery_schedule_utils.base_url}/99999",
        json={"orar_livrari": "test"}
    )
    assert non_existent_response.status_code == 404, (
        f"PATCH with non-existent ID should return 404, got {non_existent_response.status_code}"
    )


def test_patch_with_partial_data():
    
    """
    Test PATCH with partial data (should work).
    """
    # Create a delivery schedule for testing
    initial_schedule = "Monday-Friday: 9:00-18:00"
    created_entity, entity_id = delivery_schedule_utils.create_entity(initial_schedule)
    
    try:
        # PATCH with partial data (should work)
        patch_schedule = "Monday-Friday: 9:00-18:00, Saturday: 10:00-14:00"
        patch_response = requests.patch(
            f"{delivery_schedule_utils.base_url}/{entity_id}",
            json={"orar_livrari": patch_schedule}
        )
        assert patch_response.status_code == 200
        
        # Verify the change
        patched_entity = patch_response.json()
        assert patched_entity["orar_livrari"] == patch_schedule
        
    finally:
        # Clean up
        delivery_schedule_utils.delete_entity(entity_id)


def test_put_with_empty_json():
    """
    Test PUT with empty JSON (should fail - PUT requires all fields).
    """
    # Create a delivery schedule for testing
    initial_schedule = "Monday-Friday: 9:00-18:00"
    created_entity, entity_id = delivery_schedule_utils.create_entity(initial_schedule)
    
    try:
        # PUT with empty JSON should fail
        put_response = requests.put(
            f"{delivery_schedule_utils.base_url}/{entity_id}",
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
        delivery_schedule_utils.delete_entity(entity_id)


def test_put_with_complete_data():
    """
    Test PUT with complete data (should work).
    """
    # Create a delivery schedule for testing
    initial_schedule = "Monday-Friday: 9:00-18:00"
    created_entity, entity_id = delivery_schedule_utils.create_entity(initial_schedule)
    
    try:
        # PUT with complete data (should work)
        put_schedule = "Monday-Sunday: 8:00-20:00"
        put_response = requests.put(
            f"{delivery_schedule_utils.base_url}/{entity_id}",
            json={"orar_livrari": put_schedule}
        )
        assert put_response.status_code == 200
        
        # Verify the change
        put_entity = put_response.json()
        assert put_entity["orar_livrari"] == put_schedule
        
    finally:
        # Clean up
        delivery_schedule_utils.delete_entity(entity_id)
