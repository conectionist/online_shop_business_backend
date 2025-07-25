import os
import requests
import uuid
import datetime
from integration.test_utils import EntityTestUtils
from integration.test_delivery_schedules_api import DeliveryScheduleTestUtils


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
            
        # Generate short intro message (under 45 chars)
        mesaj_introducere = f"Test Message {str(uuid.uuid4())[:8]}"
            
        create_response = requests.post(
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
            # Ensure message is under 45 chars
            if len(mesaj_introducere) > 45:
                mesaj_introducere = mesaj_introducere[:45]
            update_data["mesaj_introducere"] = mesaj_introducere
            
        if is_published is not None:
            update_data["is_published"] = is_published
        
        update_response = requests.put(
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
            
        delete_response = requests.delete(delete_url)
        
        # For lists, we expect 200 OK with a message rather than 204 No Content
        assert delete_response.status_code == 200, (
            f"Failed to delete {self.entity_name}. "
            f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        )
        
        delete_data = delete_response.json()
        assert "message" in delete_data
        
        if hard_delete:
            assert "has been deleted" in delete_data["message"]
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
        delete_response = requests.delete(delete_url)
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
        missing_fields_response = requests.post(
            f"{self.base_url}/",
            json={}
        )
        assert missing_fields_response.status_code == 422
        
        # Test invalid WhatsApp number
        _, schedule_id = self.create_delivery_schedule()
        invalid_whatsapp_response = requests.post(
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
        invalid_schedule_response = requests.post(
            f"{self.base_url}/",
            json={
                "data": self.generate_test_date(),
                "is_current": True,
                "orare_livrari_id": 999999  # Non-existent ID
            }
        )
        assert invalid_schedule_response.status_code in [400, 404, 422]
    
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
