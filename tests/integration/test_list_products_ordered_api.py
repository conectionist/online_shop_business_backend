import os
import requests
import uuid
import datetime
from integration.test_utils import EntityTestUtils
from integration.test_lists_api import ListTestUtils
from integration.test_categories_api import CategoryTestUtils
from integration.test_products_api import ProductTestUtils
from integration.test_auth_utils import auth_utils


class ListProductOrderedTestUtils(EntityTestUtils):
    """Test utilities specifically for List Products Ordered."""
    
    def __init__(self):
        super().__init__(entity_name="ListProductOrdered", endpoint_path="liste")
        self.list_utils = ListTestUtils()
        self.category_utils = CategoryTestUtils()
        self.product_utils = ProductTestUtils()
    
    def create_test_list(self):
        """Create a test list for product operations."""
        return self.list_utils.create_entity()
    
    def create_test_category(self):
        """Create a test category for product operations."""
        category_name = f"Test Category {str(uuid.uuid4())[:8]}"
        return self.category_utils.create_entity(category_name)
    
    def create_test_product(self, category_id=1):
        """Create a test product for list operations."""
        product_name = f"Test Product {str(uuid.uuid4())[:8]}"
        return self.product_utils.create_entity(product_name, category_id=category_id)
    
    def get_list_products_ordered(self, list_id):
        """Get all products in a list, grouped by category and ordered."""
        if not auth_utils.access_token:
            auth_utils.login()
        
        response = auth_utils.make_authenticated_request(
            "GET",
            f"{self.base_url}/{list_id}/products/ordered"
        )
        return response
    
    def add_product_to_category(self, list_id, category_id, product_id, position=None, stoc_produs=None):
        """
        Add a product to a specific category within a list.
        
        Args:
            list_id: ID of the list
            category_id: ID of the category
            product_id: ID of the product
            position: Optional position within the category
            stoc_produs: Optional stock quantity
            
        Returns:
            Response data
        """
        if not auth_utils.access_token:
            auth_utils.login()
        
        request_data = {}
        if position is not None:
            request_data["position"] = position
        if stoc_produs is not None:
            request_data["stoc_produs"] = stoc_produs
        
        response = auth_utils.make_authenticated_request(
            "POST",
            f"{self.base_url}/{list_id}/categories/{category_id}/products/{product_id}",
            json=request_data
        )
        return response
    
    def update_product_position(self, list_id, product_id, new_position):
        """Update the position of a product within its category."""
        if not auth_utils.access_token:
            auth_utils.login()
        
        response = auth_utils.make_authenticated_request(
            "PATCH",
            f"{self.base_url}/{list_id}/products/{product_id}/position",
            json={"new_position": new_position}
        )
        return response
    
    def move_product_between_categories(self, list_id, product_id, new_category_id, new_position=None):
        """Move a product from its current category to a new category."""
        if not auth_utils.access_token:
            auth_utils.login()
        
        request_data = {"new_category_id": new_category_id}
        if new_position is not None:
            request_data["new_position"] = new_position
        
        response = auth_utils.make_authenticated_request(
            "PATCH",
            f"{self.base_url}/{list_id}/products/{product_id}/move",
            json=request_data
        )
        return response
    
    def remove_product_from_list(self, list_id, product_id):
        """Remove a product from a list."""
        if not auth_utils.access_token:
            auth_utils.login()
        
        response = auth_utils.make_authenticated_request(
            "DELETE",
            f"{self.base_url}/{list_id}/products/{product_id}"
        )
        return response


# Test utilities instance
list_product_ordered_utils = ListProductOrderedTestUtils()


def add_category_to_list(list_id, category_id, position=None):
    """Helper function to add a category to a list."""
    if not auth_utils.access_token:
        auth_utils.login()
    
    request_data = {}
    if position is not None:
        request_data["position"] = position
    
    response = auth_utils.make_authenticated_request(
        "POST",
        f"{list_product_ordered_utils.base_url}/{list_id}/categories/{category_id}",
        json=request_data
    )
    return response


def test_get_list_products_ordered_empty():
    """Test getting products from an empty list."""
    # Create a test list
    list_data, list_id = list_product_ordered_utils.create_test_list()
    
    # Get products (should be empty)
    response = list_product_ordered_utils.get_list_products_ordered(list_id)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    products_data = response.json()
    assert "list_id" in products_data
    assert "categories" in products_data
    assert len(products_data["categories"]) == 0, "Empty list should return empty categories array"


def test_add_product_to_category():
    """Test adding a product to a specific category."""
    # Create test list, category, and product
    list_data, list_id = list_product_ordered_utils.create_test_list()
    category_data, category_id = list_product_ordered_utils.create_test_category()
    product_data, product_id = list_product_ordered_utils.create_test_product(category_id)
    
    # Add product to category
    response = list_product_ordered_utils.add_product_to_category(list_id, category_id, product_id)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    
    response_data = response.json()
    assert response_data["list_id"] == list_id
    assert response_data["category_id"] == category_id
    assert response_data["product_id"] == product_id
    assert "position" in response_data
    assert response_data["position"] >= 0


def test_add_product_to_category_with_position_and_stock():
    """Test adding a product to a category with specific position and stock."""
    # Create test data
    list_data, list_id = list_product_ordered_utils.create_test_list()
    category_data, category_id = list_product_ordered_utils.create_test_category()
    product_data, product_id = list_product_ordered_utils.create_test_product(category_id)
    
    # Add product with position and stock
    response = list_product_ordered_utils.add_product_to_category(
        list_id, category_id, product_id, position=3, stoc_produs=50
    )
    assert response.status_code == 201
    
    response_data = response.json()
    assert response_data["position"] == 3
    assert response_data["stoc_produs"] == 50


def test_add_duplicate_product_fails():
    """Test that adding the same product twice fails."""
    # Create test data
    list_data, list_id = list_product_ordered_utils.create_test_list()
    category_data, category_id = list_product_ordered_utils.create_test_category()
    product_data, product_id = list_product_ordered_utils.create_test_product(category_id)
    
    # Add product first time (should succeed)
    response1 = list_product_ordered_utils.add_product_to_category(list_id, category_id, product_id)
    assert response1.status_code == 201
    
    # Add same product again (should fail)
    response2 = list_product_ordered_utils.add_product_to_category(list_id, category_id, product_id)
    assert response2.status_code == 400, f"Expected 400, got {response2.status_code}: {response2.text}"


def test_get_list_products_ordered_by_category():
    """Test getting products grouped by category with proper ordering."""
    # Create test list
    list_data, list_id = list_product_ordered_utils.create_test_list()
    
    # Create categories
    category1_data, category1_id = list_product_ordered_utils.create_test_category()
    category2_data, category2_id = list_product_ordered_utils.create_test_category()
    
    # Create products in different categories
    product1_data, product1_id = list_product_ordered_utils.create_test_product(category1_id)
    product2_data, product2_id = list_product_ordered_utils.create_test_product(category1_id)
    product3_data, product3_id = list_product_ordered_utils.create_test_product(category2_id)
    
    # Add products in specific order
    list_product_ordered_utils.add_product_to_category(list_id, category1_id, product1_id, position=2)
    list_product_ordered_utils.add_product_to_category(list_id, category1_id, product2_id, position=1)
    list_product_ordered_utils.add_product_to_category(list_id, category2_id, product3_id, position=1)
    
    # Get products and verify structure
    response = list_product_ordered_utils.get_list_products_ordered(list_id)
    assert response.status_code == 200
    
    products_data = response.json()
    assert "list_id" in products_data
    assert "categories" in products_data
    assert len(products_data["categories"]) == 2
    
    # Verify category order and product order within categories
    category1 = products_data["categories"][0]
    category2 = products_data["categories"][1]
    
    assert len(category1["products"]) == 2
    assert len(category2["products"]) == 1
    
    # Verify product order within category1
    assert category1["products"][0]["position"] == 1
    assert category1["products"][1]["position"] == 2


def test_update_product_position():
    """Test updating a product's position within its category."""
    # Create test data
    list_data, list_id = list_product_ordered_utils.create_test_list()
    category_data, category_id = list_product_ordered_utils.create_test_category()
    product_data, product_id = list_product_ordered_utils.create_test_product(category_id)
    
    # Add product at position 1
    add_response = list_product_ordered_utils.add_product_to_category(list_id, category_id, product_id, position=1)
    assert add_response.status_code == 201
    
    # Update position to 5
    update_response = list_product_ordered_utils.update_product_position(list_id, product_id, 5)
    assert update_response.status_code == 200
    
    response_data = update_response.json()
    assert response_data["new_position"] == 5
    
    # Verify the change
    get_response = list_product_ordered_utils.get_list_products_ordered(list_id)
    products_data = get_response.json()
    category = products_data["categories"][0]
    assert category["products"][0]["position"] == 5


def test_move_product_between_categories():
    """Test moving a product from one category to another."""
    # Create test data
    list_data, list_id = list_product_ordered_utils.create_test_list()
    category1_data, category1_id = list_product_ordered_utils.create_test_category()
    category2_data, category2_id = list_product_ordered_utils.create_test_category()
    product_data, product_id = list_product_ordered_utils.create_test_product(category1_id)
    
    # Add both categories to the list first
    add_category_to_list(list_id, category1_id, position=1)
    add_category_to_list(list_id, category2_id, position=2)
    
    # Add product to first category
    add_response = list_product_ordered_utils.add_product_to_category(list_id, category1_id, product_id, position=1)
    assert add_response.status_code == 201
    
    # Move product to second category
    move_response = list_product_ordered_utils.move_product_between_categories(list_id, product_id, category2_id, new_position=2)
    assert move_response.status_code == 200
    
    response_data = move_response.json()
    assert response_data["new_category_id"] == category2_id
    assert response_data["new_position"] == 2
    
    # Verify the move
    get_response = list_product_ordered_utils.get_list_products_ordered(list_id)
    products_data = get_response.json()
    
    # Should have 2 categories now
    assert len(products_data["categories"]) == 2
    
    # Product should be in category2 at position 2
    category2 = products_data["categories"][1]  # Assuming category2 comes second
    assert len(category2["products"]) == 1
    assert category2["products"][0]["position"] == 2


def test_remove_product_from_list():
    """Test removing a product from a list."""
    # Create test data
    list_data, list_id = list_product_ordered_utils.create_test_list()
    category_data, category_id = list_product_ordered_utils.create_test_category()
    product_data, product_id = list_product_ordered_utils.create_test_product(category_id)
    
    # Add product to list
    add_response = list_product_ordered_utils.add_product_to_category(list_id, category_id, product_id)
    assert add_response.status_code == 201
    
    # Remove product from list
    remove_response = list_product_ordered_utils.remove_product_from_list(list_id, product_id)
    assert remove_response.status_code == 204
    
    # Verify product is removed
    get_response = list_product_ordered_utils.get_list_products_ordered(list_id)
    products_data = get_response.json()
    assert len(products_data["categories"]) == 0


def test_remove_nonexistent_product_fails():
    """Test that removing a product that's not in the list fails."""
    # Create test data
    list_data, list_id = list_product_ordered_utils.create_test_list()
    product_data, product_id = list_product_ordered_utils.create_test_product()
    
    # Try to remove product that's not in the list
    response = list_product_ordered_utils.remove_product_from_list(list_id, product_id)
    assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"


def test_position_shifting_on_product_removal():
    """Test that removing a product shifts positions of remaining products in the same category."""
    # Create test data
    list_data, list_id = list_product_ordered_utils.create_test_list()
    category_data, category_id = list_product_ordered_utils.create_test_category()
    
    # Create and add multiple products
    product1_data, product1_id = list_product_ordered_utils.create_test_product(category_id)
    product2_data, product2_id = list_product_ordered_utils.create_test_product(category_id)
    product3_data, product3_id = list_product_ordered_utils.create_test_product(category_id)
    
    # Add products at positions 1, 2, 3
    list_product_ordered_utils.add_product_to_category(list_id, category_id, product1_id, position=1)
    list_product_ordered_utils.add_product_to_category(list_id, category_id, product2_id, position=2)
    list_product_ordered_utils.add_product_to_category(list_id, category_id, product3_id, position=3)
    
    # Verify initial order
    get_response = list_product_ordered_utils.get_list_products_ordered(list_id)
    products_data = get_response.json()
    category = products_data["categories"][0]
    assert len(category["products"]) == 3
    assert category["products"][0]["position"] == 1
    assert category["products"][1]["position"] == 2
    assert category["products"][2]["position"] == 3
    
    # Remove product at position 2
    list_product_ordered_utils.remove_product_from_list(list_id, product2_id)
    
    # Verify remaining products are shifted
    get_response = list_product_ordered_utils.get_list_products_ordered(list_id)
    products_data = get_response.json()
    category = products_data["categories"][0]
    assert len(category["products"]) == 2
    assert category["products"][0]["position"] == 1
    assert category["products"][1]["position"] == 2


def test_nonexistent_list_operations():
    """Test operations on nonexistent list."""
    nonexistent_list_id = 99999
    category_data, category_id = list_product_ordered_utils.create_test_category()
    product_data, product_id = list_product_ordered_utils.create_test_product(category_id)
    
    # Test getting products from nonexistent list
    response = list_product_ordered_utils.get_list_products_ordered(nonexistent_list_id)
    assert response.status_code == 404
    
    # Test adding product to nonexistent list
    response = list_product_ordered_utils.add_product_to_category(nonexistent_list_id, category_id, product_id)
    assert response.status_code == 404
    
    # Test updating position in nonexistent list
    response = list_product_ordered_utils.update_product_position(nonexistent_list_id, product_id, 1)
    assert response.status_code == 404
    
    # Test moving product in nonexistent list
    response = list_product_ordered_utils.move_product_between_categories(nonexistent_list_id, product_id, category_id)
    assert response.status_code == 404
    
    # Test removing product from nonexistent list
    response = list_product_ordered_utils.remove_product_from_list(nonexistent_list_id, product_id)
    assert response.status_code == 404


def test_nonexistent_product_operations():
    """Test operations with nonexistent product."""
    list_data, list_id = list_product_ordered_utils.create_test_list()
    category_data, category_id = list_product_ordered_utils.create_test_category()
    nonexistent_product_id = 99999
    
    # Test adding nonexistent product
    response = list_product_ordered_utils.add_product_to_category(list_id, category_id, nonexistent_product_id)
    assert response.status_code == 404
    
    # Test updating position of nonexistent product
    response = list_product_ordered_utils.update_product_position(list_id, nonexistent_product_id, 1)
    assert response.status_code == 404
    
    # Test moving nonexistent product
    response = list_product_ordered_utils.move_product_between_categories(list_id, nonexistent_product_id, category_id)
    assert response.status_code == 404
    
    # Test removing nonexistent product
    response = list_product_ordered_utils.remove_product_from_list(list_id, nonexistent_product_id)
    assert response.status_code == 404


def test_unauthorized_access():
    """Test that unauthorized access is properly rejected."""
    # Create test data
    list_data, list_id = list_product_ordered_utils.create_test_list()
    category_data, category_id = list_product_ordered_utils.create_test_category()
    product_data, product_id = list_product_ordered_utils.create_test_product(category_id)
    
    # Clear authentication
    auth_utils.access_token = None
    
    # Test unauthorized GET
    response = requests.get(f"{list_product_ordered_utils.base_url}/{list_id}/products/ordered")
    assert response.status_code == 403
    
    # Test unauthorized POST
    response = requests.post(f"{list_product_ordered_utils.base_url}/{list_id}/categories/{category_id}/products/{product_id}")
    assert response.status_code == 403
    
    # Test unauthorized PATCH (position)
    response = requests.patch(f"{list_product_ordered_utils.base_url}/{list_id}/products/{product_id}/position")
    assert response.status_code == 403
    
    # Test unauthorized PATCH (move)
    response = requests.patch(f"{list_product_ordered_utils.base_url}/{list_id}/products/{product_id}/move")
    assert response.status_code == 403
    
    # Test unauthorized DELETE
    response = requests.delete(f"{list_product_ordered_utils.base_url}/{list_id}/products/{product_id}")
    assert response.status_code == 403
    
    # Restore authentication
    auth_utils.login() 