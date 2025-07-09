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
