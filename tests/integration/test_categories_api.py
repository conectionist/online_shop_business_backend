import os
import requests
import uuid
from integration.test_utils import EntityTestUtils

# Create a custom test utils class for categories to handle the different field names
class CategoryTestUtils(EntityTestUtils):
    """Test utilities for the Categories API."""
    
    def __init__(self):
        """Initialize with the Categories endpoint."""
        super().__init__(entity_name="Category", endpoint_path="categories")
        
    def generate_unique_name(self, prefix="Test"):
        """Generate a unique name for test entities with shorter UUID to fit 45 char limit."""
        short_uuid = str(uuid.uuid4())[:8]
        return f"{prefix}-{short_uuid}"
    
    def create_entity(self, name=None, image_path=None):
        """
        Create a new category with the given name and image path.
        
        Args:
            name: Name for the category, will generate unique if None
            image_path: Image path for the category, will generate if None
            
        Returns:
            Tuple of (entity_data, entity_id)
        """
        if name is None:
            name = self.generate_unique_name()
            
        if image_path is None:
            image_path = f"/images/categories/{uuid.uuid4()}.jpg"
            
        create_response = requests.post(
            f"{self.base_url}/",
            json={"name": name, "image_path": image_path}
        )
        assert create_response.status_code == 201, (
            f"Failed to create {self.entity_name}. "
            f"Expected 201, got {create_response.status_code}: {create_response.text}"
        )
        
        created_entity = create_response.json()
        assert "id" in created_entity
        assert created_entity["name"] == name
        assert created_entity["image_path"] == image_path
        
        return created_entity, created_entity["id"]
    
    def update_entity(self, entity_id, name=None, image_path=None):
        """
        Update a category by ID.
        
        Args:
            entity_id: ID of the category to update
            name: New name for the category (optional)
            image_path: New image path for the category (optional)
            
        Returns:
            Updated entity data
        """
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if image_path is not None:
            update_data["image_path"] = image_path
            
        update_response = requests.put(
            f"{self.base_url}/{entity_id}",
            json=update_data
        )
        assert update_response.status_code == 200, (
            f"Failed to update {self.entity_name}. "
            f"Expected 200, got {update_response.status_code}: {update_response.text}"
        )
        
        updated_entity = update_response.json()
        if name is not None:
            assert updated_entity["name"] == name
        if image_path is not None:
            assert updated_entity["image_path"] == image_path
        
        return updated_entity
    
    def hard_delete_entity(self, entity_id):
        """
        Hard delete a category by ID.
        
        Args:
            entity_id: ID of the category to delete
        """
        delete_response = requests.delete(f"{self.base_url}/{entity_id}?permanent=true")
        assert delete_response.status_code == 204, (
            f"Failed to hard delete {self.entity_name}. "
            f"Expected 204, got {delete_response.status_code}: {delete_response.text}"
        )
    
    def soft_delete_entity(self, entity_id):
        """
        Soft delete a category by ID.
        
        Args:
            entity_id: ID of the category to soft delete
        """
        delete_response = requests.delete(f"{self.base_url}/{entity_id}")
        assert delete_response.status_code == 204, (
            f"Failed to soft delete {self.entity_name}. "
            f"Expected 204, got {delete_response.status_code}: {delete_response.text}"
        )
    
    def get_entity_with_deleted(self, entity_id, include_deleted=True, expected_status=200):
        """
        Get a category by ID, including soft-deleted ones if specified.
        
        Args:
            entity_id: ID of the category to retrieve
            include_deleted: Whether to include soft-deleted categories
            expected_status: Expected HTTP status code
            
        Returns:
            Entity data if found, None if expected_status is not 200
        """
        get_response = requests.get(f"{self.base_url}/{entity_id}?include_deleted={str(include_deleted).lower()}")
        assert get_response.status_code == expected_status, (
            f"Failed to get {self.entity_name}. "
            f"Expected {expected_status}, got {get_response.status_code}: {get_response.text}"
        )
        
        if expected_status == 200:
            return get_response.json()
        return None
    
    def list_entities_with_deleted(self, include_deleted=True):
        """
        List categories, including soft-deleted ones if specified.
        
        Args:
            include_deleted: Whether to include soft-deleted categories
            
        Returns:
            List of categories
        """
        list_response = requests.get(f"{self.base_url}/?include_deleted={str(include_deleted).lower()}")
        assert list_response.status_code == 200, (
            f"Failed to list {self.entity_name}s. "
            f"Expected 200, got {list_response.status_code}: {list_response.text}"
        )
        
        return list_response.json()
    
    def test_crud_workflow(self):
        """
        Test the full CRUD workflow for a category.
        """
        # 1. CREATE
        initial_name = self.generate_unique_name()
        initial_image_path = f"/images/categories/{uuid.uuid4()}.jpg"
        created_entity, entity_id = self.create_entity(initial_name, initial_image_path)
        
        # 2. READ
        retrieved_entity = self.get_entity(entity_id)
        assert retrieved_entity == created_entity
        
        # 3. UPDATE
        updated_name = self.generate_unique_name("Updated")
        updated_image_path = f"/images/categories/updated-{uuid.uuid4()}.jpg"
        updated_entity = self.update_entity(entity_id, updated_name, updated_image_path)
        assert updated_entity["name"] == updated_name
        assert updated_entity["image_path"] == updated_image_path
        
        # 4. DELETE (soft delete)
        self.soft_delete_entity(entity_id)
        
        # 5. VERIFY soft deletion
        self.get_entity(entity_id, expected_status=404)  # Should not be found with default params
        
        # 6. VERIFY can still get with include_deleted=true
        deleted_entity = self.get_entity_with_deleted(entity_id, include_deleted=True)
        assert deleted_entity["is_deleted"] is True
        
        # 7. HARD DELETE
        self.hard_delete_entity(entity_id)
        
        # 8. VERIFY hard deletion
        # Should not be found even with include_deleted=true
        get_response = requests.get(f"{self.base_url}/{entity_id}?include_deleted=true")
        assert get_response.status_code == 404
    
    def test_validation(self):
        """
        Test basic validation rules.
        """
        # Test invalid ID
        invalid_id_response = requests.get(f"{self.base_url}/-1")
        assert invalid_id_response.status_code == 422
        
        # Test empty name
        invalid_name_response = requests.post(
            f"{self.base_url}/",
            json={"name": "", "image_path": "/images/test.jpg"}
        )
        assert invalid_name_response.status_code == 422
        
        # Test empty image path
        invalid_image_response = requests.post(
            f"{self.base_url}/",
            json={"name": "Test Category", "image_path": ""}
        )
        assert invalid_image_response.status_code == 422
        
        # Test duplicate name validation
        unique_name = self.generate_unique_name("Unique")
        created_entity, entity_id = self.create_entity(unique_name)
        
        try:
            # Try to create another entity with the same name
            duplicate_response = requests.post(
                f"{self.base_url}/",
                json={"name": unique_name, "image_path": "/images/different.jpg"}
            )
            assert duplicate_response.status_code == 400, "Should not allow duplicate names"
            
        finally:
            # Clean up
            self.hard_delete_entity(entity_id)
    
    def test_list_and_pagination(self):
        """
        Test listing categories with pagination.
        """
        # Create a category to ensure we have at least one
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
            self.hard_delete_entity(entity_id)
    
    def test_soft_delete_and_restore(self):
        """
        Test soft delete functionality and restoration of soft-deleted categories.
        """
        # 1. Create a category
        name = self.generate_unique_name("SoftDelete")
        created_entity, entity_id = self.create_entity(name)
        
        # 2. Soft delete it
        self.soft_delete_entity(entity_id)
        
        # 3. Verify it's not in the regular list
        regular_list = requests.get(f"{self.base_url}/").json()
        assert not any(c["id"] == entity_id for c in regular_list)
        
        # 4. Verify it is in the list with include_deleted=true
        deleted_list = self.list_entities_with_deleted(include_deleted=True)
        assert any(c["id"] == entity_id and c["is_deleted"] is True for c in deleted_list)
        
        # 5. Try to create a new category with the same name (should restore the soft-deleted one)
        restore_response = requests.post(
            f"{self.base_url}/",
            json={"name": name, "image_path": "/images/restored.jpg"}
        )
        assert restore_response.status_code == 201
        restored_entity = restore_response.json()
        
        # 6. Verify it has the same ID as the original (restored, not new)
        assert restored_entity["id"] == entity_id
        assert restored_entity["is_deleted"] is False
        
        # 7. Clean up
        self.hard_delete_entity(entity_id)
    
    def test_error_handling(self):
        """
        Test error handling for various scenarios.
        """
        # Test non-existent category
        non_existent_id = 99999  # Assuming this ID doesn't exist
        not_found_response = requests.get(f"{self.base_url}/{non_existent_id}")
        assert not_found_response.status_code == 404
        
        # Create a category for update tests
        created_entity, entity_id = self.create_entity()
        
        try:
            # Test updating with invalid data
            invalid_update_response = requests.put(
                f"{self.base_url}/{entity_id}",
                json={"name": "", "image_path": "/images/test.jpg"}
            )
            assert invalid_update_response.status_code == 422
            
            # Test updating non-existent category
            non_existent_update_response = requests.put(
                f"{self.base_url}/{non_existent_id}",
                json={"name": "Non-existent", "image_path": "/images/non-existent.jpg"}
            )
            assert non_existent_update_response.status_code == 404
            
        finally:
            # Clean up
            self.hard_delete_entity(entity_id)


# Create a test utils instance for categories
category_utils = CategoryTestUtils()

def test_category_crud_workflow():
    """
    Tests the full Create, Read, Update, and Delete (CRUD) workflow for categories.
    """
    category_utils.test_crud_workflow()

def test_category_list_and_pagination():
    """
    Tests listing categories with pagination.
    """
    category_utils.test_list_and_pagination()

def test_category_validation():
    """
    Tests validation for category endpoints.
    """
    category_utils.test_validation()

def test_category_soft_delete_and_restore():
    """
    Tests soft delete functionality and restoration of soft-deleted categories.
    """
    category_utils.test_soft_delete_and_restore()

def test_category_error_handling():
    """
    Tests error handling for various scenarios.
    """
    category_utils.test_error_handling()
