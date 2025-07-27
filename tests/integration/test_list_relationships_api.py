import os
import requests
import uuid
import datetime
from integration.test_utils import EntityTestUtils
from integration.test_lists_api import ListTestUtils
from integration.test_products_api import ProductTestUtils
from integration.test_delivery_types_api import delivery_type_utils


class ListRelationshipTestUtils:
    """Test utilities for List many-to-many relationships."""
    
    def __init__(self):
        self.api_base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")
        self.api_v1_str = "/api/v1"
        self.base_url = f"{self.api_base_url}{self.api_v1_str}/liste"
        
        # Initialize other test utilities
        self.list_utils = ListTestUtils()
        self.product_utils = ProductTestUtils()
        self.delivery_type_utils = delivery_type_utils
    
    def create_test_list(self):
        """Create a test list and return (list_data, list_id)."""
        return self.list_utils.create_entity()
    
    def create_test_product(self):
        """Create a test product and return (product_data, product_id)."""
        return self.product_utils.create_entity()
    
    def create_test_delivery_type(self):
        """Create a test delivery type and return (delivery_type_data, delivery_type_id)."""
        return self.delivery_type_utils.create_entity()
    
    def get_list_products(self, list_id, expected_status=200):
        """Get all products for a list."""
        response = requests.get(f"{self.base_url}/{list_id}/products")
        assert response.status_code == expected_status, (
            f"Failed to get products for list {list_id}. "
            f"Expected {expected_status}, got {response.status_code}: {response.text}"
        )
        return response.json() if expected_status == 200 else None
    
    def get_list_delivery_types(self, list_id, expected_status=200):
        """Get all delivery types for a list."""
        response = requests.get(f"{self.base_url}/{list_id}/delivery-types")
        assert response.status_code == expected_status, (
            f"Failed to get delivery types for list {list_id}. "
            f"Expected {expected_status}, got {response.status_code}: {response.text}"
        )
        return response.json() if expected_status == 200 else None
    
    def add_product_to_list(self, list_id, product_id, expected_status=201):
        """Add a product to a list."""
        response = requests.post(f"{self.base_url}/{list_id}/products/{product_id}")
        assert response.status_code == expected_status, (
            f"Failed to add product {product_id} to list {list_id}. "
            f"Expected {expected_status}, got {response.status_code}: {response.text}"
        )
        return response.json() if expected_status == 201 else None
    
    def add_delivery_type_to_list(self, list_id, delivery_type_id, expected_status=201):
        """Add a delivery type to a list."""
        response = requests.post(f"{self.base_url}/{list_id}/delivery-types/{delivery_type_id}")
        assert response.status_code == expected_status, (
            f"Failed to add delivery type {delivery_type_id} to list {list_id}. "
            f"Expected {expected_status}, got {response.status_code}: {response.text}"
        )
        return response.json() if expected_status == 201 else None
    
    def remove_product_from_list(self, list_id, product_id, expected_status=204):
        """Remove a product from a list."""
        response = requests.delete(f"{self.base_url}/{list_id}/products/{product_id}")
        assert response.status_code == expected_status, (
            f"Failed to remove product {product_id} from list {list_id}. "
            f"Expected {expected_status}, got {response.status_code}: {response.text}"
        )
    
    def remove_delivery_type_from_list(self, list_id, delivery_type_id, expected_status=204):
        """Remove a delivery type from a list."""
        response = requests.delete(f"{self.base_url}/{list_id}/delivery-types/{delivery_type_id}")
        assert response.status_code == expected_status, (
            f"Failed to remove delivery type {delivery_type_id} from list {list_id}. "
            f"Expected {expected_status}, got {response.status_code}: {response.text}"
        )
    
    def replace_list_products(self, list_id, product_ids, expected_status=200):
        """Replace all products in a list."""
        response = requests.put(f"{self.base_url}/{list_id}/products", json=product_ids)
        assert response.status_code == expected_status, (
            f"Failed to replace products for list {list_id}. "
            f"Expected {expected_status}, got {response.status_code}: {response.text}"
        )
        return response.json() if expected_status == 200 else None
    
    def replace_list_delivery_types(self, list_id, delivery_type_ids, expected_status=200):
        """Replace all delivery types in a list."""
        response = requests.put(f"{self.base_url}/{list_id}/delivery-types", json=delivery_type_ids)
        assert response.status_code == expected_status, (
            f"Failed to replace delivery types for list {list_id}. "
            f"Expected {expected_status}, got {response.status_code}: {response.text}"
        )
        return response.json() if expected_status == 200 else None


# Initialize test utilities
list_relationship_utils = ListRelationshipTestUtils()


def test_list_products_basic_operations():
    """Test basic CRUD operations for list-product relationships."""
    
    # 1. Create test entities
    list_data, list_id = list_relationship_utils.create_test_list()
    product_data, product_id = list_relationship_utils.create_test_product()
    
    # 2. Initially, list should have no products
    products = list_relationship_utils.get_list_products(list_id)
    assert len(products) == 0, "New list should have no products"
    
    # 3. Add product to list
    add_response = list_relationship_utils.add_product_to_list(list_id, product_id)
    assert add_response["list_id"] == list_id
    assert add_response["product_id"] == product_id
    
    # 4. Verify product is in list
    products = list_relationship_utils.get_list_products(list_id)
    assert len(products) == 1, "List should have one product"
    assert products[0]["id"] == product_id
    
    # 5. Try to add the same product again (should fail)
    list_relationship_utils.add_product_to_list(list_id, product_id, expected_status=400)
    
    # 6. Remove product from list
    list_relationship_utils.remove_product_from_list(list_id, product_id)
    
    # 7. Verify product is removed
    products = list_relationship_utils.get_list_products(list_id)
    assert len(products) == 0, "List should have no products after removal"


def test_list_delivery_types_basic_operations():
    """Test basic CRUD operations for list-delivery type relationships."""
    
    # 1. Create test entities
    list_data, list_id = list_relationship_utils.create_test_list()
    delivery_type_data, delivery_type_id = list_relationship_utils.create_test_delivery_type()
    
    # 2. Initially, list should have no delivery types
    delivery_types = list_relationship_utils.get_list_delivery_types(list_id)
    assert len(delivery_types) == 0, "New list should have no delivery types"
    
    # 3. Add delivery type to list
    add_response = list_relationship_utils.add_delivery_type_to_list(list_id, delivery_type_id)
    assert add_response["list_id"] == list_id
    assert add_response["delivery_type_id"] == delivery_type_id
    
    # 4. Verify delivery type is in list
    delivery_types = list_relationship_utils.get_list_delivery_types(list_id)
    assert len(delivery_types) == 1, "List should have one delivery type"
    assert delivery_types[0]["id"] == delivery_type_id
    
    # 5. Try to add the same delivery type again (should fail)
    list_relationship_utils.add_delivery_type_to_list(list_id, delivery_type_id, expected_status=400)
    
    # 6. Remove delivery type from list
    list_relationship_utils.remove_delivery_type_from_list(list_id, delivery_type_id)
    
    # 7. Verify delivery type is removed
    delivery_types = list_relationship_utils.get_list_delivery_types(list_id)
    assert len(delivery_types) == 0, "List should have no delivery types after removal"


def test_list_products_replace_operations():
    """Test replace operations for list-product relationships."""
    
    # 1. Create test entities
    list_data, list_id = list_relationship_utils.create_test_list()
    product1_data, product1_id = list_relationship_utils.create_test_product()
    product2_data, product2_id = list_relationship_utils.create_test_product()
    product3_data, product3_id = list_relationship_utils.create_test_product()
    
    # 2. Add initial products
    list_relationship_utils.add_product_to_list(list_id, product1_id)
    list_relationship_utils.add_product_to_list(list_id, product2_id)
    
    # 3. Verify initial state
    products = list_relationship_utils.get_list_products(list_id)
    assert len(products) == 2, "List should have 2 products"
    product_ids = [p["id"] for p in products]
    assert product1_id in product_ids
    assert product2_id in product_ids
    
    # 4. Replace with different products
    new_products = list_relationship_utils.replace_list_products(list_id, [product2_id, product3_id])
    assert len(new_products) == 2, "Should return 2 products"
    
    # 5. Verify replacement
    products = list_relationship_utils.get_list_products(list_id)
    assert len(products) == 2, "List should have 2 products after replacement"
    product_ids = [p["id"] for p in products]
    assert product2_id in product_ids
    assert product3_id in product_ids
    assert product1_id not in product_ids, "Product 1 should be removed"
    
    # 6. Replace with empty list
    list_relationship_utils.replace_list_products(list_id, [])
    
    # 7. Verify empty state
    products = list_relationship_utils.get_list_products(list_id)
    assert len(products) == 0, "List should have no products after empty replacement"


def test_list_delivery_types_replace_operations():
    """Test replace operations for list-delivery type relationships."""
    
    # 1. Create test entities
    list_data, list_id = list_relationship_utils.create_test_list()
    delivery_type1_data, delivery_type1_id = list_relationship_utils.create_test_delivery_type()
    delivery_type2_data, delivery_type2_id = list_relationship_utils.create_test_delivery_type()
    delivery_type3_data, delivery_type3_id = list_relationship_utils.create_test_delivery_type()
    
    # 2. Add initial delivery types
    list_relationship_utils.add_delivery_type_to_list(list_id, delivery_type1_id)
    list_relationship_utils.add_delivery_type_to_list(list_id, delivery_type2_id)
    
    # 3. Verify initial state
    delivery_types = list_relationship_utils.get_list_delivery_types(list_id)
    assert len(delivery_types) == 2, "List should have 2 delivery types"
    delivery_type_ids = [dt["id"] for dt in delivery_types]
    assert delivery_type1_id in delivery_type_ids
    assert delivery_type2_id in delivery_type_ids
    
    # 4. Replace with different delivery types
    new_delivery_types = list_relationship_utils.replace_list_delivery_types(list_id, [delivery_type2_id, delivery_type3_id])
    assert len(new_delivery_types) == 2, "Should return 2 delivery types"
    
    # 5. Verify replacement
    delivery_types = list_relationship_utils.get_list_delivery_types(list_id)
    assert len(delivery_types) == 2, "List should have 2 delivery types after replacement"
    delivery_type_ids = [dt["id"] for dt in delivery_types]
    assert delivery_type2_id in delivery_type_ids
    assert delivery_type3_id in delivery_type_ids
    assert delivery_type1_id not in delivery_type_ids, "Delivery type 1 should be removed"
    
    # 6. Replace with empty list
    list_relationship_utils.replace_list_delivery_types(list_id, [])
    
    # 7. Verify empty state
    delivery_types = list_relationship_utils.get_list_delivery_types(list_id)
    assert len(delivery_types) == 0, "List should have no delivery types after empty replacement"


def test_list_relationships_error_handling():
    """Test error handling for list relationships."""
    
    # 1. Test with non-existent list
    list_relationship_utils.get_list_products(999, expected_status=404)
    list_relationship_utils.get_list_delivery_types(999, expected_status=404)
    list_relationship_utils.add_product_to_list(999, 1, expected_status=404)
    list_relationship_utils.add_delivery_type_to_list(999, 1, expected_status=404)
    list_relationship_utils.remove_product_from_list(999, 1, expected_status=404)
    list_relationship_utils.remove_delivery_type_from_list(999, 1, expected_status=404)
    list_relationship_utils.replace_list_products(999, [1], expected_status=404)
    list_relationship_utils.replace_list_delivery_types(999, [1], expected_status=404)
    
    # 2. Create a real list and test with non-existent related entities
    list_data, list_id = list_relationship_utils.create_test_list()
    
    # Test with non-existent product
    list_relationship_utils.add_product_to_list(list_id, 999, expected_status=404)
    list_relationship_utils.remove_product_from_list(list_id, 999, expected_status=404)
    
    # Test with non-existent delivery type
    list_relationship_utils.add_delivery_type_to_list(list_id, 999, expected_status=404)
    list_relationship_utils.remove_delivery_type_from_list(list_id, 999, expected_status=404)
    
    # 3. Test replace with non-existent entities
    list_relationship_utils.replace_list_products(list_id, [999], expected_status=404)
    list_relationship_utils.replace_list_delivery_types(list_id, [999], expected_status=404)


def test_list_relationships_complex_scenarios():
    """Test complex scenarios for list relationships."""
    
    # 1. Create test entities
    list_data, list_id = list_relationship_utils.create_test_list()
    product1_data, product1_id = list_relationship_utils.create_test_product()
    product2_data, product2_id = list_relationship_utils.create_test_product()
    delivery_type1_data, delivery_type1_id = list_relationship_utils.create_test_delivery_type()
    delivery_type2_data, delivery_type2_id = list_relationship_utils.create_test_delivery_type()
    
    # 2. Test adding multiple products and delivery types
    list_relationship_utils.add_product_to_list(list_id, product1_id)
    list_relationship_utils.add_product_to_list(list_id, product2_id)
    list_relationship_utils.add_delivery_type_to_list(list_id, delivery_type1_id)
    list_relationship_utils.add_delivery_type_to_list(list_id, delivery_type2_id)
    
    # 3. Verify both relationships
    products = list_relationship_utils.get_list_products(list_id)
    delivery_types = list_relationship_utils.get_list_delivery_types(list_id)
    
    assert len(products) == 2, "List should have 2 products"
    assert len(delivery_types) == 2, "List should have 2 delivery types"
    
    # 4. Test removing one of each
    list_relationship_utils.remove_product_from_list(list_id, product1_id)
    list_relationship_utils.remove_delivery_type_from_list(list_id, delivery_type1_id)
    
    # 5. Verify partial removal
    products = list_relationship_utils.get_list_products(list_id)
    delivery_types = list_relationship_utils.get_list_delivery_types(list_id)
    
    assert len(products) == 1, "List should have 1 product after removal"
    assert len(delivery_types) == 1, "List should have 1 delivery type after removal"
    assert products[0]["id"] == product2_id
    assert delivery_types[0]["id"] == delivery_type2_id
    
    # 6. Test replacing with mixed valid/invalid IDs
    list_relationship_utils.replace_list_products(list_id, [product1_id, 999], expected_status=404)
    list_relationship_utils.replace_list_delivery_types(list_id, [delivery_type1_id, 999], expected_status=404)


def test_list_relationships_edge_cases():
    """Test edge cases for list relationships."""
    
    # 1. Test with empty arrays in replace operations
    list_data, list_id = list_relationship_utils.create_test_list()
    product_data, product_id = list_relationship_utils.create_test_product()
    delivery_type_data, delivery_type_id = list_relationship_utils.create_test_delivery_type()
    
    # Add some items first
    list_relationship_utils.add_product_to_list(list_id, product_id)
    list_relationship_utils.add_delivery_type_to_list(list_id, delivery_type_id)
    
    # Replace with empty arrays
    list_relationship_utils.replace_list_products(list_id, [])
    list_relationship_utils.replace_list_delivery_types(list_id, [])
    
    # Verify they're empty
    products = list_relationship_utils.get_list_products(list_id)
    delivery_types = list_relationship_utils.get_list_delivery_types(list_id)
    
    assert len(products) == 0, "Products should be empty after empty replace"
    assert len(delivery_types) == 0, "Delivery types should be empty after empty replace"
    
    # 2. Test removing non-existent items (should return 404)
    list_relationship_utils.remove_product_from_list(list_id, 999, expected_status=404)
    list_relationship_utils.remove_delivery_type_from_list(list_id, 999, expected_status=404)
    
    # 3. Test adding duplicate items (should return 400)
    list_relationship_utils.add_product_to_list(list_id, product_id)
    list_relationship_utils.add_product_to_list(list_id, product_id, expected_status=400)
    
    list_relationship_utils.add_delivery_type_to_list(list_id, delivery_type_id)
    list_relationship_utils.add_delivery_type_to_list(list_id, delivery_type_id, expected_status=400)


# Initialize test utilities
list_relationship_utils = ListRelationshipTestUtils() 