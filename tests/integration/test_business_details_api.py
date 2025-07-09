import os
import requests
import uuid
from integration.test_utils import EntityTestUtils


class BusinessDetailsTestUtils(EntityTestUtils):
    """Test utilities specifically for business details."""
    
    def __init__(self):
        super().__init__(entity_name="Business Details", endpoint_path="detalii-business")
    
    def create_entity(self, adresa=None, telefon=None, motto=None):
        """
        Create a new business details record.
        
        Args:
            adresa: Business address, will generate unique if None
            telefon: Business phone number, will generate unique if None
            motto: Business motto, will generate unique if None
            
        Returns:
            Tuple of (entity_data, entity_id)
        """
        # Generate unique test data if not provided
        if adresa is None:
            adresa = f"Strada Test {uuid.uuid4()}"
        if telefon is None:
            telefon = f"07{uuid.uuid4().hex[:8]}"
        if motto is None:
            motto = f"Test Motto {uuid.uuid4().hex[:10]}"
            
        create_data = {
            "adresa": adresa,
            "telefon": telefon,
            "motto": motto
        }
        
        create_response = requests.post(
            f"{self.base_url}/",
            json=create_data
        )
        assert create_response.status_code == 201, (
            f"Failed to create {self.entity_name}. "
            f"Expected 201, got {create_response.status_code}: {create_response.text}"
        )
        
        created_entity = create_response.json()
        assert "id" in created_entity
        assert created_entity["adresa"] == adresa
        assert created_entity["telefon"] == telefon
        assert created_entity["motto"] == motto
        
        return created_entity, created_entity["id"]
    
    def update_entity(self, entity_id, adresa=None, telefon=None, motto=None, alte_detalii=None):
        """
        Update a business details record by ID.
        
        Args:
            entity_id: ID of the entity to update
            adresa: New business address
            telefon: New phone number
            motto: New business motto
            alte_detalii: Additional details
            
        Returns:
            Updated entity data
        """
        update_data = {}
        if adresa is not None:
            update_data["adresa"] = adresa
        if telefon is not None:
            update_data["telefon"] = telefon
        if motto is not None:
            update_data["motto"] = motto
        if alte_detalii is not None:
            update_data["alte_detalii"] = alte_detalii
            
        update_response = requests.put(
            f"{self.base_url}/{entity_id}",
            json=update_data
        )
        assert update_response.status_code == 200, (
            f"Failed to update {self.entity_name}. "
            f"Expected 200, got {update_response.status_code}: {update_response.text}"
        )
        
        updated_entity = update_response.json()
        for key, value in update_data.items():
            assert updated_entity[key] == value
        
        return updated_entity
    
    def test_crud_workflow(self):
        """
        Test the full CRUD workflow for business details.
        """
        # 1. CREATE
        initial_adresa = f"Strada Test {uuid.uuid4()}"
        initial_telefon = f"07{uuid.uuid4().hex[:8]}"
        initial_motto = f"Test Motto {uuid.uuid4().hex[:10]}"
        
        created_entity, entity_id = self.create_entity(
            adresa=initial_adresa,
            telefon=initial_telefon,
            motto=initial_motto
        )
        
        # 2. READ
        retrieved_entity = self.get_entity(entity_id)
        assert retrieved_entity == created_entity
        
        # 3. UPDATE
        updated_motto = f"Updated Motto {uuid.uuid4().hex[:10]}"
        updated_alte_detalii = f"Additional details {uuid.uuid4().hex[:15]}"
        
        updated_entity = self.update_entity(
            entity_id, 
            motto=updated_motto,
            alte_detalii=updated_alte_detalii
        )
        assert updated_entity["motto"] == updated_motto
        assert updated_entity["alte_detalii"] == updated_alte_detalii
        assert updated_entity["adresa"] == initial_adresa  # Should remain unchanged
        assert updated_entity["telefon"] == initial_telefon  # Should remain unchanged
        
        # 4. DELETE
        self.delete_entity(entity_id)
        
        # 5. VERIFY deletion
        self.get_entity(entity_id, expected_status=404)
    
    def test_validation(self):
        """
        Test basic validation rules for business details.
        """
        # Test invalid ID
        invalid_id_response = requests.get(f"{self.base_url}/-1")
        assert invalid_id_response.status_code == 422
        
        # Test field length validation
        # Create very long strings that exceed max length
        long_adresa = "A" * 201  # adresa max_length=200
        long_telefon = "1" * 21  # telefon max_length=20
        
        invalid_data_response = requests.post(
            f"{self.base_url}/",
            json={
                "adresa": long_adresa,
                "telefon": long_telefon
            }
        )
        assert invalid_data_response.status_code == 422


# Create an instance of our test utilities
business_details_utils = BusinessDetailsTestUtils()


def test_business_details_crud_workflow():
    """
    Tests the full Create, Read, Update, and Delete (CRUD) workflow for business details.
    """
    business_details_utils.test_crud_workflow()


def test_business_details_list_and_pagination():
    """
    Tests listing business details with pagination.
    """
    business_details_utils.test_list_and_pagination()


def test_business_details_validation():
    """
    Tests validation for business details endpoints.
    """
    business_details_utils.test_validation()
