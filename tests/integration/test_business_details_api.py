import os
import requests
import uuid
from integration.test_utils import EntityTestUtils
from integration.test_auth_utils import auth_utils


class BusinessDetailsTestUtils(EntityTestUtils):
    """Test utilities specifically for business details."""
    
    def __init__(self):
        super().__init__(entity_name="Business Details", endpoint_path="detalii-business")
    
    def create_entity(self, adresa=None, telefon=None, motto=None, delivery_tax=None,
                      business_name=None, registration_number=None, CUI=None, email=None,
                      operating_hours=None, representative=None):
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
        if delivery_tax is not None:
            create_data["delivery_tax"] = delivery_tax
        if business_name is not None:
            create_data["business_name"] = business_name
        if registration_number is not None:
            create_data["registration_number"] = registration_number
        if CUI is not None:
            create_data["CUI"] = CUI
        if email is not None:
            create_data["email"] = email
        if operating_hours is not None:
            create_data["operating_hours"] = operating_hours
        if representative is not None:
            create_data["representative"] = representative
        
        # Ensure we're authenticated
        if not auth_utils.access_token:
            auth_utils.login()
            
        # First, try to get existing business details
        existing_response = auth_utils.make_authenticated_request("GET", f"{self.base_url}/")
        if existing_response.status_code == 200 and existing_response.json():
            # If business details already exist, delete them first
            existing_id = existing_response.json()[0]["id"]
            auth_utils.make_authenticated_request("DELETE", f"{self.base_url}/{existing_id}")
            
        # Now create new business details
        create_response = auth_utils.make_authenticated_request(
            "POST",
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
        if delivery_tax is not None:
            assert created_entity.get("delivery_tax") == delivery_tax
        if business_name is not None:
            assert created_entity.get("business_name") == business_name
        if registration_number is not None:
            assert created_entity.get("registration_number") == registration_number
        if CUI is not None:
            assert created_entity.get("CUI") == CUI
        if email is not None:
            assert created_entity.get("email") == email
        if operating_hours is not None:
            assert created_entity.get("operating_hours") == operating_hours
        if representative is not None:
            assert created_entity.get("representative") == representative
        
        return created_entity, created_entity["id"]
    
    def update_entity(self, entity_id, adresa=None, telefon=None, motto=None, alte_detalii=None, delivery_tax=None,
                      business_name=None, registration_number=None, CUI=None, email=None,
                      operating_hours=None, representative=None):
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
        if delivery_tax is not None:
            update_data["delivery_tax"] = delivery_tax
        if business_name is not None:
            update_data["business_name"] = business_name
        if registration_number is not None:
            update_data["registration_number"] = registration_number
        if CUI is not None:
            update_data["CUI"] = CUI
        if email is not None:
            update_data["email"] = email
        if operating_hours is not None:
            update_data["operating_hours"] = operating_hours
        if representative is not None:
            update_data["representative"] = representative
            
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
            motto=initial_motto,
            business_name="PCMA SRL",
            registration_number="J22/1234/2020",
            CUI="RO12345678",
            email="contact@example.com",
            operating_hours="L-V 9-17",
            representative="John Doe - Administrator"
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
            alte_detalii=updated_alte_detalii,
            business_name="New Name SRL",
            email="office@example.com"
        )
        assert updated_entity["motto"] == updated_motto
        assert updated_entity["alte_detalii"] == updated_alte_detalii
        assert updated_entity["business_name"] == "New Name SRL"
        assert updated_entity["email"] == "office@example.com"
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
        
        # Ensure we're authenticated
        if not auth_utils.access_token:
            auth_utils.login()
            
        invalid_data_response = auth_utils.make_authenticated_request(
            "POST",
            f"{self.base_url}/",
            json={
                "adresa": long_adresa,
                "telefon": long_telefon
            }
        )
        assert invalid_data_response.status_code == 422

        # Test negative delivery_tax validation
        invalid_tax_response = auth_utils.make_authenticated_request(
            "POST",
            f"{self.base_url}/",
            json={
                "adresa": "Valid Address",
                "telefon": "0712345678",
                "delivery_tax": -1
            }
        )
        assert invalid_tax_response.status_code == 422


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


def test_patch_with_valid_data():
    """
    Test PATCH with valid data.
    """
    # Create a business details record for testing
    created_entity, entity_id = business_details_utils.create_entity()
    
    try:
        # PATCH with new address
        new_adresa = "Patched Address"
        # Ensure we're authenticated
        if not auth_utils.access_token:
            auth_utils.login()
            
        patch_response = auth_utils.make_authenticated_request(
            "PATCH",
            f"{business_details_utils.base_url}/{entity_id}",
            json={"adresa": new_adresa, "business_name": "Patched SRL"}
        )
        assert patch_response.status_code == 200, (
            f"PATCH should return 200, got {patch_response.status_code}: {patch_response.text}"
        )
        
        patched_entity = patch_response.json()
        assert patched_entity["adresa"] == new_adresa
        assert patched_entity.get("business_name") == "Patched SRL"
        assert patched_entity["id"] == entity_id
        
        # Verify the change persisted
        retrieved_entity = business_details_utils.get_entity(entity_id)
        assert retrieved_entity["adresa"] == new_adresa
        
    finally:
        # Clean up
        business_details_utils.delete_entity(entity_id)


def test_patch_with_empty_json():
    """
    Test PATCH with empty JSON (should return error).
    """
    # Create a business details record for testing
    created_entity, entity_id = business_details_utils.create_entity()
    
    try:
        # PATCH with empty JSON should return error
        empty_patch_response = auth_utils.make_authenticated_request(
            "PATCH",
            f"{business_details_utils.base_url}/{entity_id}",
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
        business_details_utils.delete_entity(entity_id)


def test_patch_with_non_existent_business_details():
    """
    Test PATCH with non-existent business details ID.
    """
    # Ensure we're authenticated
    if not auth_utils.access_token:
        auth_utils.login()
        
    non_existent_response = auth_utils.make_authenticated_request(
        "PATCH",
        f"{business_details_utils.base_url}/99999",
        json={"adresa": "test"}
    )
    assert non_existent_response.status_code == 404, (
        f"PATCH with non-existent ID should return 404, got {non_existent_response.status_code}"
    )


def test_patch_with_invalid_data():
    """
    Test PATCH with invalid data (should return 422).
    """
    # Create a business details record for testing
    created_entity, entity_id = business_details_utils.create_entity()
    
    try:
        # PATCH with empty strings should clear values to null (None)
        invalid_patch_response = auth_utils.make_authenticated_request(
            "PATCH",
            f"{business_details_utils.base_url}/{entity_id}",
            json={"adresa": "", "email": "   "}
        )
        assert invalid_patch_response.status_code == 200
        
        # Verify the empty strings were normalized to null
        patched_entity = invalid_patch_response.json()
        assert patched_entity["adresa"] is None
        assert patched_entity["email"] is None
        
    finally:
        # Clean up
        business_details_utils.delete_entity(entity_id)


def test_patch_multiple_fields():
    """
    Test PATCH with multiple fields.
    """
    # Create a business details record for testing
    created_entity, entity_id = business_details_utils.create_entity()
    
    try:
        # PATCH with multiple fields
        patch_data = {
            "adresa": "Multi Patched Address",
            "telefon": "987654321",
            "motto": "Patched Motto"
        }
        patch_response = auth_utils.make_authenticated_request(
            "PATCH",
            f"{business_details_utils.base_url}/{entity_id}",
            json=patch_data
        )
        assert patch_response.status_code == 200, (
            f"PATCH should return 200, got {patch_response.status_code}: {patch_response.text}"
        )
        
        patched_entity = patch_response.json()
        assert patched_entity["adresa"] == patch_data["adresa"]
        assert patched_entity["telefon"] == patch_data["telefon"]
        assert patched_entity["motto"] == patch_data["motto"]
        assert patched_entity["id"] == entity_id
        
        # Verify the changes persisted
        retrieved_entity = business_details_utils.get_entity(entity_id)
        assert retrieved_entity["adresa"] == patch_data["adresa"]
        assert retrieved_entity["telefon"] == patch_data["telefon"]
        assert retrieved_entity["motto"] == patch_data["motto"]
        
    finally:
        # Clean up
        business_details_utils.delete_entity(entity_id)


def test_patch_with_partial_data_works():
    """
    Test that PATCH accepts partial data.
    """
    # Create a business details record for testing
    created_entity, entity_id = business_details_utils.create_entity()
    
    try:
        # PATCH with partial data (should work)
        patch_data = {"adresa": "Partial Patch Address"}
        patch_response = auth_utils.make_authenticated_request(
            "PATCH",
            f"{business_details_utils.base_url}/{entity_id}",
            json=patch_data
        )
        assert patch_response.status_code == 200
        
        # Verify the change
        patched_entity = patch_response.json()
        assert patched_entity["adresa"] == "Partial Patch Address"
        
        # Verify other fields remain unchanged
        assert patched_entity["telefon"] == created_entity["telefon"]
        assert patched_entity["motto"] == created_entity["motto"]
        
    finally:
        # Clean up
        business_details_utils.delete_entity(entity_id)


def test_put_with_empty_json_fails():
    """
    Test that PUT with empty JSON fails.
    """
    # Create a business details record for testing
    created_entity, entity_id = business_details_utils.create_entity()
    
    try:
        # PUT with empty JSON should fail
        put_response = auth_utils.make_authenticated_request(
            "PUT",
            f"{business_details_utils.base_url}/{entity_id}",
            json={}
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
        business_details_utils.delete_entity(entity_id)


def test_put_with_complete_data_works():
    """
    Test that PUT accepts complete data.
    """
    # Create a business details record for testing
    created_entity, entity_id = business_details_utils.create_entity()
    
    try:
        # PUT with complete data (should work)
        put_data = {
            "adresa": "PUT Updated Address",
            "telefon": "111222333",
            "motto": "PUT Updated Motto",
            "delivery_tax": 250
        }
        put_response = auth_utils.make_authenticated_request(
            "PUT",
            f"{business_details_utils.base_url}/{entity_id}",
            json=put_data
        )
        assert put_response.status_code == 200
        
        # Verify the changes
        final_entity = business_details_utils.get_entity(entity_id)
        assert final_entity["adresa"] == put_data["adresa"]
        assert final_entity["telefon"] == put_data["telefon"]
        assert final_entity["motto"] == put_data["motto"]
        assert final_entity["delivery_tax"] == put_data["delivery_tax"]
    finally:
        # Clean up
        business_details_utils.delete_entity(entity_id)


def test_create_with_delivery_tax_sets_value():
    """
    Ensure creating business details with delivery_tax sets the value.
    """
    created_entity, entity_id = business_details_utils.create_entity(delivery_tax=175)
    try:
        assert created_entity["delivery_tax"] == 175
        retrieved = business_details_utils.get_entity(entity_id)
        assert retrieved["delivery_tax"] == 175
    finally:
        business_details_utils.delete_entity(entity_id)


def test_patch_delivery_tax_updates_value():
    """
    Ensure PATCH can update delivery_tax.
    """
    created_entity, entity_id = business_details_utils.create_entity()
    try:
        if not auth_utils.access_token:
            auth_utils.login()
        patch_response = auth_utils.make_authenticated_request(
            "PATCH",
            f"{business_details_utils.base_url}/{entity_id}",
            json={"delivery_tax": 300}
        )
        assert patch_response.status_code == 200
        patched = patch_response.json()
        assert patched["delivery_tax"] == 300
        retrieved = business_details_utils.get_entity(entity_id)
        assert retrieved["delivery_tax"] == 300
    finally:
        business_details_utils.delete_entity(entity_id)
