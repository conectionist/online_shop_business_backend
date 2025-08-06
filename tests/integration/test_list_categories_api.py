import os
import requests
import uuid
import datetime
from integration.test_utils import EntityTestUtils
from integration.test_lists_api import ListTestUtils
from integration.test_categories_api import CategoryTestUtils
from integration.test_auth_utils import auth_utils


class ListCategoryTestUtils(EntityTestUtils):
    """Test utilities specifically for List Categories."""
    
    def __init__(self):
        super().__init__(entity_name="ListCategory", endpoint_path="liste")
        self.list_utils = ListTestUtils()
        self.category_utils = CategoryTestUtils()
    
    def create_test_list(self):
        """Create a test list for category operations."""
        return self.list_utils.create_entity()
    
    def create_test_category(self):
        """Create a test category for list operations."""
        category_name = f"Test Category {str(uuid.uuid4())[:8]}"
        return self.category_utils.create_entity(category_name)
    
    def add_category_to_list(self, list_id, category_id, position=None):
        """
        Add a category to a list at a specific position.
        
        Args:
            list_id: ID of the list
            category_id: ID of the category
            position: Optional position (if None, will be added at end)
            
        Returns:
            Response data
        """
        if not auth_utils.access_token:
            auth_utils.login()
        
        request_data = {}
        if position is not None:
            request_data["position"] = position
        
        response = auth_utils.make_authenticated_request(
            "POST",
            f"{self.base_url}/{list_id}/categories/{category_id}",
            json=request_data
        )
        return response
    
    def get_list_categories(self, list_id):
        """Get all categories in a list, ordered by position."""
        if not auth_utils.access_token:
            auth_utils.login()
        
        response = auth_utils.make_authenticated_request(
            "GET",
            f"{self.base_url}/{list_id}/categories"
        )
        return response
    
    def update_category_position(self, list_id, category_id, new_position):
        """Update the position of a category within a list."""
        if not auth_utils.access_token:
            auth_utils.login()
        
        response = auth_utils.make_authenticated_request(
            "PATCH",
            f"{self.base_url}/{list_id}/categories/{category_id}/position",
            json={"new_position": new_position}
        )
        return response
    
    def remove_category_from_list(self, list_id, category_id):
        """Remove a category from a list."""
        if not auth_utils.access_token:
            auth_utils.login()
        
        response = auth_utils.make_authenticated_request(
            "DELETE",
            f"{self.base_url}/{list_id}/categories/{category_id}"
        )
        return response


# Test utilities instance
list_category_utils = ListCategoryTestUtils()


def test_get_list_categories_empty():
    """Test getting categories from an empty list."""
    # Create a test list
    list_data, list_id = list_category_utils.create_test_list()
    
    # Get categories (should be empty)
    response = list_category_utils.get_list_categories(list_id)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    categories = response.json()
    assert isinstance(categories, list)
    assert len(categories) == 0, "Empty list should return empty categories array"


def test_add_category_to_list():
    """Test adding a category to a list."""
    # Create test list and category
    list_data, list_id = list_category_utils.create_test_list()
    category_data, category_id = list_category_utils.create_test_category()
    
    # Add category to list
    response = list_category_utils.add_category_to_list(list_id, category_id)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    
    response_data = response.json()
    assert response_data["list_id"] == list_id
    assert response_data["category_id"] == category_id
    assert "position" in response_data
    assert response_data["position"] >= 0


def test_add_category_to_list_with_position():
    """Test adding a category to a list at a specific position."""
    # Create test list and category
    list_data, list_id = list_category_utils.create_test_list()
    category_data, category_id = list_category_utils.create_test_category()
    
    # Add category to list at position 5
    response = list_category_utils.add_category_to_list(list_id, category_id, position=5)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    
    response_data = response.json()
    assert response_data["position"] == 5


def test_add_duplicate_category_fails():
    """Test that adding the same category twice fails."""
    # Create test list and category
    list_data, list_id = list_category_utils.create_test_list()
    category_data, category_id = list_category_utils.create_test_category()
    
    # Add category first time (should succeed)
    response1 = list_category_utils.add_category_to_list(list_id, category_id)
    assert response1.status_code == 201
    
    # Add same category again (should fail)
    response2 = list_category_utils.add_category_to_list(list_id, category_id)
    assert response2.status_code == 400, f"Expected 400, got {response2.status_code}: {response2.text}"


def test_get_list_categories_ordered():
    """Test getting categories from a list with proper ordering."""
    # Create test list
    list_data, list_id = list_category_utils.create_test_list()
    
    # Create multiple categories
    category1_data, category1_id = list_category_utils.create_test_category()
    category2_data, category2_id = list_category_utils.create_test_category()
    category3_data, category3_id = list_category_utils.create_test_category()
    
    # Add categories in specific order
    list_category_utils.add_category_to_list(list_id, category1_id, position=3)
    list_category_utils.add_category_to_list(list_id, category2_id, position=1)
    list_category_utils.add_category_to_list(list_id, category3_id, position=2)
    
    # Get categories and verify order
    response = list_category_utils.get_list_categories(list_id)
    assert response.status_code == 200
    
    categories = response.json()
    assert len(categories) == 3
    
    # Verify order: position 1, 2, 3
    assert categories[0]["position"] == 1
    assert categories[1]["position"] == 2
    assert categories[2]["position"] == 3


def test_update_category_position():
    """Test updating a category's position within a list."""
    # Create test list and category
    list_data, list_id = list_category_utils.create_test_list()
    category_data, category_id = list_category_utils.create_test_category()
    
    # Add category at position 1
    add_response = list_category_utils.add_category_to_list(list_id, category_id, position=1)
    assert add_response.status_code == 201
    
    # Update position to 5
    update_response = list_category_utils.update_category_position(list_id, category_id, 5)
    assert update_response.status_code == 200
    
    response_data = update_response.json()
    assert response_data["new_position"] == 5
    
    # Verify the change
    get_response = list_category_utils.get_list_categories(list_id)
    categories = get_response.json()
    assert len(categories) == 1
    assert categories[0]["position"] == 5


def test_remove_category_from_list():
    """Test removing a category from a list."""
    # Create test list and category
    list_data, list_id = list_category_utils.create_test_list()
    category_data, category_id = list_category_utils.create_test_category()
    
    # Add category to list
    add_response = list_category_utils.add_category_to_list(list_id, category_id)
    assert add_response.status_code == 201
    
    # Remove category from list
    remove_response = list_category_utils.remove_category_from_list(list_id, category_id)
    assert remove_response.status_code == 204
    
    # Verify category is removed
    get_response = list_category_utils.get_list_categories(list_id)
    categories = get_response.json()
    assert len(categories) == 0


def test_remove_nonexistent_category_fails():
    """Test that removing a category that's not in the list fails."""
    # Create test list and category
    list_data, list_id = list_category_utils.create_test_list()
    category_data, category_id = list_category_utils.create_test_category()
    
    # Try to remove category that's not in the list
    response = list_category_utils.remove_category_from_list(list_id, category_id)
    assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"


def test_position_shifting_on_removal():
    """Test that removing a category shifts positions of remaining categories."""
    # Create test list
    list_data, list_id = list_category_utils.create_test_list()
    
    # Create and add multiple categories
    category1_data, category1_id = list_category_utils.create_test_category()
    category2_data, category2_id = list_category_utils.create_test_category()
    category3_data, category3_id = list_category_utils.create_test_category()
    
    # Add categories at positions 1, 2, 3
    list_category_utils.add_category_to_list(list_id, category1_id, position=1)
    list_category_utils.add_category_to_list(list_id, category2_id, position=2)
    list_category_utils.add_category_to_list(list_id, category3_id, position=3)
    
    # Verify initial order
    get_response = list_category_utils.get_list_categories(list_id)
    categories = get_response.json()
    assert len(categories) == 3
    assert categories[0]["position"] == 1
    assert categories[1]["position"] == 2
    assert categories[2]["position"] == 3
    
    # Remove category at position 2
    list_category_utils.remove_category_from_list(list_id, category2_id)
    
    # Verify remaining categories are shifted
    get_response = list_category_utils.get_list_categories(list_id)
    categories = get_response.json()
    assert len(categories) == 2
    assert categories[0]["position"] == 1
    assert categories[1]["position"] == 2


def test_nonexistent_list_operations():
    """Test operations on nonexistent list."""
    nonexistent_list_id = 99999
    category_data, category_id = list_category_utils.create_test_category()
    
    # Test getting categories from nonexistent list
    response = list_category_utils.get_list_categories(nonexistent_list_id)
    assert response.status_code == 404
    
    # Test adding category to nonexistent list
    response = list_category_utils.add_category_to_list(nonexistent_list_id, category_id)
    assert response.status_code == 404
    
    # Test updating position in nonexistent list
    response = list_category_utils.update_category_position(nonexistent_list_id, category_id, 1)
    assert response.status_code == 404
    
    # Test removing category from nonexistent list
    response = list_category_utils.remove_category_from_list(nonexistent_list_id, category_id)
    assert response.status_code == 404


def test_nonexistent_category_operations():
    """Test operations with nonexistent category."""
    list_data, list_id = list_category_utils.create_test_list()
    nonexistent_category_id = 99999
    
    # Test adding nonexistent category
    response = list_category_utils.add_category_to_list(list_id, nonexistent_category_id)
    assert response.status_code == 404
    
    # Test updating position of nonexistent category
    response = list_category_utils.update_category_position(list_id, nonexistent_category_id, 1)
    assert response.status_code == 404
    
    # Test removing nonexistent category
    response = list_category_utils.remove_category_from_list(list_id, nonexistent_category_id)
    assert response.status_code == 404


def test_unauthorized_access():
    """Test that unauthorized access is properly rejected."""
    # Create test data
    list_data, list_id = list_category_utils.create_test_list()
    category_data, category_id = list_category_utils.create_test_category()
    
    # Clear authentication
    auth_utils.access_token = None
    
    # Test unauthorized GET
    response = requests.get(f"{list_category_utils.base_url}/{list_id}/categories")
    assert response.status_code == 401
    
    # Test unauthorized POST
    response = requests.post(f"{list_category_utils.base_url}/{list_id}/categories/{category_id}")
    assert response.status_code == 401
    
    # Test unauthorized PATCH
    response = requests.patch(f"{list_category_utils.base_url}/{list_id}/categories/{category_id}/position")
    assert response.status_code == 401
    
    # Test unauthorized DELETE
    response = requests.delete(f"{list_category_utils.base_url}/{list_id}/categories/{category_id}")
    assert response.status_code == 401
    
    # Restore authentication
    auth_utils.login() 