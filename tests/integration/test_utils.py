import os
import requests
import uuid
from integration.test_auth_utils import auth_utils


class EntityTestUtils:
    """Base utility class for testing entity CRUD operations."""
    
    def __init__(self, entity_name, endpoint_path):
        """
        Initialize the test utilities for an entity.
        
        Args:
            entity_name: Display name of the entity (for error messages)
            endpoint_path: API path for this entity (e.g., 'unitati' or 'tipuri-livrare')
        """
        self.entity_name = entity_name
        self.endpoint_path = endpoint_path
        self.api_base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")
        self.api_v1_str = "/api/v1"
        self.base_url = f"{self.api_base_url}{self.api_v1_str}/{endpoint_path}"
    
    def generate_unique_name(self, prefix="Test"):
        """Generate a unique name for test entities."""
        return f"{prefix}-{uuid.uuid4()}"
    
    def create_entity(self, name=None):
        """
        Create a new entity with the given name.
        
        Args:
            name: Name for the entity, will generate unique if None
            
        Returns:
            Tuple of (entity_data, entity_id)
        """
        if name is None:
            name = self.generate_unique_name()
        
        # Ensure we're authenticated
        if not auth_utils.access_token:
            auth_utils.login()
            
        # Special-case payloads per entity
        payload = {"denumire": name}
        if self.endpoint_path == "tipuri-livrare":
            # delivery types require unique order_index in [1,127]
            import random
            base_idx = random.randint(1, 127)
            attempt = 0
            status = None
            response = None
            while attempt < 127:
                idx = ((base_idx + attempt - 1) % 127) + 1
                payload_with_index = dict(payload)
                payload_with_index["order_index"] = idx
                response = auth_utils.make_authenticated_request(
                    "POST",
                    f"{self.base_url}/",
                    json=payload_with_index
                )
                status = response.status_code
                if status == 201:
                    create_response = response
                    break
                if status == 409:
                    attempt += 1
                    continue
                # any other error - break and assert below
                create_response = response
                break
        else:
            create_response = auth_utils.make_authenticated_request(
                "POST",
                f"{self.base_url}/",
                json=payload
            )
        assert create_response.status_code == 201, (
            f"Failed to create {self.entity_name}. "
            f"Expected 201, got {create_response.status_code}: {create_response.text}"
        )
        
        created_entity = create_response.json()
        assert "id" in created_entity
        assert created_entity["denumire"] == name
        
        return created_entity, created_entity["id"]
    
    def get_entity(self, entity_id, expected_status=200):
        """
        Get an entity by ID.
        
        Args:
            entity_id: ID of the entity to retrieve
            expected_status: Expected HTTP status code
            
        Returns:
            Entity data if found, None if expected_status is not 200
        """
        get_response = requests.get(f"{self.base_url}/{entity_id}")
        assert get_response.status_code == expected_status, (
            f"Failed to get {self.entity_name}. "
            f"Expected {expected_status}, got {get_response.status_code}: {get_response.text}"
        )
        
        if expected_status == 200:
            return get_response.json()
        return None
    
    def update_entity(self, entity_id, name):
        """
        Update an entity by ID.
        
        Args:
            entity_id: ID of the entity to update
            name: New name for the entity
            
        Returns:
            Updated entity data
        """
        # Ensure we're authenticated
        if not auth_utils.access_token:
            auth_utils.login()
            
        update_response = auth_utils.make_authenticated_request(
            "PUT",
            f"{self.base_url}/{entity_id}",
            json={"denumire": name}
        )
        assert update_response.status_code == 200, (
            f"Failed to update {self.entity_name}. "
            f"Expected 200, got {update_response.status_code}: {update_response.text}"
        )
        
        updated_entity = update_response.json()
        assert updated_entity["denumire"] == name
        
        return updated_entity
    
    def delete_entity(self, entity_id):
        """
        Delete an entity by ID.
        
        Args:
            entity_id: ID of the entity to delete
        """
        # Ensure we're authenticated
        if not auth_utils.access_token:
            auth_utils.login()
            
        delete_response = auth_utils.make_authenticated_request(
            "DELETE",
            f"{self.base_url}/{entity_id}"
        )
        assert delete_response.status_code == 204, (
            f"Failed to delete {self.entity_name}. "
            f"Expected 204, got {delete_response.status_code}: {delete_response.text}"
        )
    
    def test_crud_workflow(self):
        """
        Test the full CRUD workflow for an entity.
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
        assert updated_entity["denumire"] == updated_name
        
        # 4. DELETE
        self.delete_entity(entity_id)
        
        # 5. VERIFY deletion
        self.get_entity(entity_id, expected_status=404)
    
    def test_validation(self):
        """
        Test basic validation rules.
        """
        # Test invalid ID
        invalid_id_response = requests.get(f"{self.base_url}/-1")
        assert invalid_id_response.status_code == 422
        
        # Test empty name
        # Ensure we're authenticated
        if not auth_utils.access_token:
            auth_utils.login()
            
        invalid_name_response = auth_utils.make_authenticated_request(
            "POST",
            f"{self.base_url}/",
            json={"denumire": ""}
        )
        assert invalid_name_response.status_code == 422
        
        # Test duplicate name validation
        unique_name = self.generate_unique_name("Unique")
        created_entity, entity_id = self.create_entity(unique_name)
        
        try:
            # Try to create another entity with the same name
            duplicate_response = auth_utils.make_authenticated_request(
                "POST",
                f"{self.base_url}/",
                json={"denumire": unique_name, **({"order_index": 127} if self.endpoint_path == "tipuri-livrare" else {})}
            )
            expected_dup_status = 409 if self.endpoint_path == "tipuri-livrare" else 400
            assert duplicate_response.status_code == expected_dup_status, "Should not allow duplicate names"
            
        finally:
            # Clean up
            self.delete_entity(entity_id)
    
    def test_list_and_pagination(self):
        """
        Test listing entities with pagination.
        """
        # Create an entity to ensure we have at least one
        created_entity, entity_id = self.create_entity()
        
        try:
            # Test basic listing
            list_response = requests.get(f"{self.base_url}/")
            assert list_response.status_code == 200
            entities = list_response.json()
            assert isinstance(entities, list)
            assert len(entities) > 0
            
            # Test pagination
            pagination_response = requests.get(f"{self.base_url}/?skip=1&limit=1")
            assert pagination_response.status_code == 200
            paginated_entities = pagination_response.json()
            assert isinstance(paginated_entities, list)
            assert len(paginated_entities) <= 1
            
        finally:
            # Clean up
            self.delete_entity(entity_id)
