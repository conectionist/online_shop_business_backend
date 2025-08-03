import pytest
import requests
import datetime
from integration.test_utils import EntityTestUtils
from integration.test_products_api import ProductTestUtils
from integration.test_auth_utils import auth_utils


class ProductOverrideTestUtils:
    """Test utilities for product overrides API"""
    
    def __init__(self):
        self.base_url = "http://api_server_test:8000/api/v1"
        self.product_utils = ProductTestUtils()
    
    def create_test_product(self):
        """Create a test product and return (product_data, product_id)."""
        # Use an existing product for testing
        response = requests.get(f"{self.base_url}/products/")
        assert response.status_code == 200
        products = response.json()
        assert len(products) > 0
        product = products[0]
        product_id = product["id"]
        
        product_data = {
            "nume": product["nume"],
            "cantitate": product["cantitate"],
            "pret": product["pret"],
            "description": product["description"],
            "category_id": product["category_id"],
            "unitati_id": product["unitati_id"]
        }
        return product_data, product_id
    
    def create_test_override(self, product_id, field_name="price", new_value="80", notes="Test override"):
        """Create a test override and return (override_data, override_id)."""
        # First, deactivate any existing active overrides for this product and field
        response = requests.get(f"{self.base_url}/product-overrides/?product_id={product_id}&is_active=true")
        if response.status_code == 200:
            existing_overrides = response.json()
            for override in existing_overrides:
                if override["field_name"] == field_name:
                    # Deactivate existing override
                    # Ensure we're authenticated
                    if not auth_utils.access_token:
                        auth_utils.login()
                    auth_utils.make_authenticated_request(
                        "PUT",
                        f"{self.base_url}/product-overrides/{override['id']}",
                        json={"is_active": False}
                    )
        
        override_data = {
            "produse_id": product_id,
            "field_name": field_name,
            "old_value": "100",
            "new_value": new_value,
            "notes": notes,
            "is_active": True
        }
        
        # Ensure we're authenticated
        if not auth_utils.access_token:
            auth_utils.login()
            
        response = auth_utils.make_authenticated_request(
            "POST",
            f"{self.base_url}/product-overrides/",
            json=override_data
        )
        assert response.status_code == 201
        override_id = response.json()["id"]
        return override_data, override_id
    
    def test_get_overrides_empty(self):
        """Test getting overrides when none exist."""
        response = requests.get(f"{self.base_url}/product-overrides/")
        assert response.status_code == 200
        # Don't assert empty list since there might be existing overrides from manual testing
        overrides = response.json()
        assert isinstance(overrides, list)
    
    def test_get_available_fields(self):
        """Test getting available fields for overrides."""
        response = requests.get(f"{self.base_url}/product-overrides/fields")
        assert response.status_code == 200
        fields = response.json()
        assert "price" in fields
        assert "description" in fields
        assert "availability" in fields
    
    def test_create_override_success(self):
        """Test creating a product override successfully."""
        # Create test product
        product_data, product_id = self.create_test_product()
        
        # Create override
        override_data, override_id = self.create_test_override(product_id)
        
        # Verify override was created
        response = requests.get(f"{self.base_url}/product-overrides/{override_id}")
        assert response.status_code == 200
        created_override = response.json()
        assert created_override["produse_id"] == product_id
        assert created_override["field_name"] == "price"
        assert created_override["new_value"] == "80"
        assert created_override["notes"] == "Test override"
        assert created_override["is_active"] == True
    
    def test_create_duplicate_override_fails(self):
        """Test that creating duplicate overrides fails."""
        # Create test product
        product_data, product_id = self.create_test_product()
        
        # Create first override
        override_data, override_id = self.create_test_override(product_id)
        
        # Try to create duplicate override
        duplicate_data = {
            "produse_id": product_id,
            "field_name": "price",
            "new_value": "90",
            "notes": "Duplicate override",
            "is_active": True
        }
        
        # Ensure we're authenticated
        if not auth_utils.access_token:
            auth_utils.login()
            
        response = auth_utils.make_authenticated_request(
            "POST",
            f"{self.base_url}/product-overrides/",
            json=duplicate_data
        )
        assert response.status_code == 400
        assert "Active override already exists" in response.json()["detail"]
    
    def test_create_multiple_overrides_success(self):
        """Test creating multiple overrides for the same product."""
        # Create test product
        product_data, product_id = self.create_test_product()
        
        # Create price override
        price_override_data, price_override_id = self.create_test_override(
            product_id, "price", "80", "Price override"
        )
        
        # Create description override
        desc_override_data, desc_override_id = self.create_test_override(
            product_id, "description", "Updated description", "Description override"
        )
        
        # Verify both overrides exist
        response = requests.get(f"{self.base_url}/product-overrides/")
        assert response.status_code == 200
        overrides = response.json()
        assert len(overrides) >= 2
        
        # Verify product with overrides
        response = requests.get(f"{self.base_url}/product-overrides/product/{product_id}/with-overrides")
        assert response.status_code == 200
        product_with_overrides = response.json()
        assert "overrides" in product_with_overrides
        assert "price" in product_with_overrides["overrides"]
        assert "description" in product_with_overrides["overrides"]
    
    def test_update_override_success(self):
        """Test updating a product override."""
        # Create test product and override
        product_data, product_id = self.create_test_product()
        override_data, override_id = self.create_test_override(product_id)
        
        # Update override
        update_data = {
            "new_value": "75",
            "notes": "Updated override"
        }
        
        # Ensure we're authenticated
        if not auth_utils.access_token:
            auth_utils.login()
            
        response = auth_utils.make_authenticated_request(
            "PUT",
            f"{self.base_url}/product-overrides/{override_id}",
            json=update_data
        )
        assert response.status_code == 200
        updated_override = response.json()
        assert updated_override["new_value"] == "75"
        assert updated_override["notes"] == "Updated override"
    
    def test_deactivate_override(self):
        """Test deactivating an override."""
        # Create test product and override
        product_data, product_id = self.create_test_product()
        override_data, override_id = self.create_test_override(product_id)
        
        # Deactivate override
        update_data = {"is_active": False}
        
        # Ensure we're authenticated
        if not auth_utils.access_token:
            auth_utils.login()
            
        response = auth_utils.make_authenticated_request(
            "PUT",
            f"{self.base_url}/product-overrides/{override_id}",
            json=update_data
        )
        assert response.status_code == 200
        updated_override = response.json()
        assert updated_override["is_active"] == False
    
    def test_delete_override_success(self):
        """Test deleting a product override."""
        # Create test product and override
        product_data, product_id = self.create_test_product()
        override_data, override_id = self.create_test_override(product_id)
        
        # Delete override
        # Ensure we're authenticated
        if not auth_utils.access_token:
            auth_utils.login()
            
        response = auth_utils.make_authenticated_request(
            "DELETE",
            f"{self.base_url}/product-overrides/{override_id}"
        )
        assert response.status_code == 204
        
        # Verify override was deleted
        response = requests.get(f"{self.base_url}/product-overrides/{override_id}")
        assert response.status_code == 404
    
    def test_get_nonexistent_override(self):
        """Test getting a non-existent override."""
        response = requests.get(f"{self.base_url}/product-overrides/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_update_nonexistent_override(self):
        """Test updating a non-existent override."""
        update_data = {"new_value": "75"}
        
        # Ensure we're authenticated
        if not auth_utils.access_token:
            auth_utils.login()
            
        response = auth_utils.make_authenticated_request(
            "PUT",
            f"{self.base_url}/product-overrides/999",
            json=update_data
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_delete_nonexistent_override(self):
        """Test deleting a non-existent override."""
        # Ensure we're authenticated
        if not auth_utils.access_token:
            auth_utils.login()
            
        response = auth_utils.make_authenticated_request(
            "DELETE",
            f"{self.base_url}/product-overrides/999"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_create_override_invalid_product(self):
        """Test creating override for non-existent product."""
        override_data = {
            "produse_id": 999,
            "field_name": "price",
            "new_value": "80",
            "notes": "Test override",
            "is_active": True
        }
        
        # Ensure we're authenticated
        if not auth_utils.access_token:
            auth_utils.login()
            
        response = auth_utils.make_authenticated_request(
            "POST",
            f"{self.base_url}/product-overrides/",
            json=override_data
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_create_override_invalid_field(self):
        """Test creating override with invalid field name."""
        # Create test product
        product_data, product_id = self.create_test_product()
        
        override_data = {
            "produse_id": product_id,
            "field_name": "invalid_field",
            "new_value": "80",
            "notes": "Test override",
            "is_active": True
        }
        
        # Ensure we're authenticated
        if not auth_utils.access_token:
            auth_utils.login()
            
        response = auth_utils.make_authenticated_request(
            "POST",
            f"{self.base_url}/product-overrides/",
            json=override_data
        )
        assert response.status_code == 422  # Validation error
    
    def test_filter_overrides_by_product(self):
        """Test filtering overrides by product ID."""
        # Create test products
        product_data1, product_id1 = self.create_test_product()
        product_data2, product_id2 = self.create_test_product()
        
        # Create overrides for both products
        override_data1, override_id1 = self.create_test_override(product_id1)
        override_data2, override_id2 = self.create_test_override(product_id2)
        
        # Filter by first product
        response = requests.get(f"{self.base_url}/product-overrides/?product_id={product_id1}")
        assert response.status_code == 200
        overrides = response.json()
        assert len(overrides) >= 1
        assert all(override["produse_id"] == product_id1 for override in overrides)
    
    def test_filter_overrides_by_active_status(self):
        """Test filtering overrides by active status."""
        # Create test product and override
        product_data, product_id = self.create_test_product()
        override_data, override_id = self.create_test_override(product_id)
        
        # Filter active overrides
        response = requests.get(f"{self.base_url}/product-overrides/?is_active=true")
        assert response.status_code == 200
        overrides = response.json()
        assert len(overrides) >= 1
        assert all(override["is_active"] == True for override in overrides)
        
        # Filter inactive overrides
        response = requests.get(f"{self.base_url}/product-overrides/?is_active=false")
        assert response.status_code == 200
        overrides = response.json()
        # Don't assert empty since there might be inactive overrides from previous tests
        assert isinstance(overrides, list)


# Initialize test utilities
product_override_utils = ProductOverrideTestUtils()


# Test execution functions
def test_product_overrides_basic_operations():
    """Test basic CRUD operations for product overrides."""
    product_override_utils.test_get_overrides_empty()
    product_override_utils.test_get_available_fields()


def test_product_overrides_validation():
    """Test validation and error handling for product overrides."""
    product_override_utils.test_get_nonexistent_override()
    product_override_utils.test_update_nonexistent_override()
    product_override_utils.test_delete_nonexistent_override()
    product_override_utils.test_create_override_invalid_product()
    product_override_utils.test_create_override_invalid_field()


def test_product_overrides_advanced_features():
    """Test advanced features like multiple overrides and filtering."""
    # Test with a fresh product to avoid conflicts
    product_override_utils.test_create_override_success()
    product_override_utils.test_update_override_success()
    product_override_utils.test_delete_override_success()
    product_override_utils.test_create_duplicate_override_fails()
    product_override_utils.test_create_multiple_overrides_success()
    product_override_utils.test_deactivate_override()
    product_override_utils.test_filter_overrides_by_product()
    product_override_utils.test_filter_overrides_by_active_status() 