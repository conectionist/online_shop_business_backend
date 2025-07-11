import os
import requests
import uuid
from integration.test_utils import EntityTestUtils

# Create a custom test utils class for products
class ProductTestUtils(EntityTestUtils):
    """Test utilities for the Products API."""
    
    def __init__(self):
        """Initialize with the Products endpoint."""
        super().__init__(entity_name="Product", endpoint_path="products")
        
    def generate_unique_name(self, prefix="TestProduct"):
        """Generate a unique name for test products with shorter UUID to fit character limits."""
        short_uuid = str(uuid.uuid4())[:8]
        return f"{prefix}-{short_uuid}"
    
    def create_entity(self, name=None, category_id=1, unitati_id=1, cantitate=10, pret=100, 
                     description=None, image_path=None, stock=5, use_placeholder=False):
        """
        Create a new product with the given parameters.
        
        Args:
            name: Name for the product, will generate unique if None
            category_id: ID of the category for this product
            unitati_id: ID of the unit for this product
            cantitate: Quantity value
            pret: Price value
            description: Product description
            image_path: Image path for the product, will use placeholder if None or use_placeholder=True
            stock: Stock amount
            use_placeholder: If True, don't include image_path in the request (use placeholder)
            
        Returns:
            Tuple of (entity_data, entity_id)
        """
        if name is None:
            name = self.generate_unique_name()
            
        if description is None:
            description = f"Description for {name}"
            
        if image_path is None and not use_placeholder:
            image_path = f"products/{uuid.uuid4()}.jpg"
        
        # Prepare form data - Products API uses multipart/form-data format
        form_data = {
            "nume": name,
            "cantitate": str(cantitate),
            "pret": str(pret),
            "description": description,
            "category_id": str(category_id),
            "unitati_id": str(unitati_id),
            "stock": str(stock)
        }
        
        # Optionally include image if specified
        # In real tests, we would upload an actual file here
        files = {}
        if not use_placeholder and image_path:
            # For testing without actual file uploads, we'll create a simple file-like object
            # In a complete implementation, you would use an actual file
            dummy_file_content = b"test image content"
            files = {
                'primary_image': (f'test_image.jpg', dummy_file_content, 'image/jpeg')
            }
            
        create_response = requests.post(
            f"{self.base_url}/",
            data=form_data,
            files=files
        )
        assert create_response.status_code == 201, (
            f"Failed to create {self.entity_name}. "
            f"Expected 201, got {create_response.status_code}: {create_response.text}"
        )
        
        created_entity = create_response.json()
        assert "id" in created_entity
        assert created_entity["nume"] == name
        assert created_entity["category_id"] == category_id
        assert created_entity["unitati_id"] == unitati_id
        
        return created_entity, created_entity["id"]
    
    def update_entity(self, entity_id, name=None, category_id=None, unitati_id=None, 
                     cantitate=None, pret=None, description=None, image_path=None, stock=None):
        """
        Update a product by ID.
        
        Args:
            entity_id: ID of the product to update
            name: New name for the product (optional)
            category_id: New category ID (optional)
            unitati_id: New unit ID (optional)
            cantitate: New quantity value (optional)
            pret: New price value (optional)
            description: New description (optional)
            image_path: New image path (optional)
            stock: New stock amount (optional)
            
        Returns:
            Updated entity data
        """
        # Prepare form data - Products API uses multipart/form-data format for updates too
        form_data = {}
        if name is not None:
            form_data["nume"] = name
        if category_id is not None:
            form_data["category_id"] = str(category_id)
        if unitati_id is not None:
            form_data["unitati_id"] = str(unitati_id)
        if cantitate is not None:
            form_data["cantitate"] = str(cantitate)
        if pret is not None:
            form_data["pret"] = str(pret)
        if description is not None:
            form_data["description"] = description
        if stock is not None:
            form_data["stock"] = str(stock)
            
        # Handle image upload separately
        files = {}
        if image_path is not None:
            # For testing without actual file uploads, use a simple file-like object
            dummy_file_content = b"test image content"
            files = {
                'primary_image': (f'test_image.jpg', dummy_file_content, 'image/jpeg')
            }
            
        update_response = requests.put(
            f"{self.base_url}/{entity_id}",
            data=form_data,
            files=files
        )
        assert update_response.status_code == 200, (
            f"Failed to update {self.entity_name}. "
            f"Expected 200, got {update_response.status_code}: {update_response.text}"
        )
        
        updated_entity = update_response.json()
        if name is not None:
            assert updated_entity["nume"] == name
        if category_id is not None:
            assert updated_entity["category_id"] == category_id
        if unitati_id is not None:
            assert updated_entity["unitati_id"] == unitati_id
        
        return updated_entity
    
    def hard_delete_entity(self, entity_id):
        """
        Hard delete a product by ID.
        
        Args:
            entity_id: ID of the product to delete
        """
        delete_response = requests.delete(f"{self.base_url}/{entity_id}?permanent=true")
        assert delete_response.status_code == 204, (
            f"Failed to hard delete {self.entity_name}. "
            f"Expected 204, got {delete_response.status_code}: {delete_response.text}"
        )
    
    def soft_delete_entity(self, entity_id):
        """
        Soft delete a product by ID.
        
        Args:
            entity_id: ID of the product to soft delete
        """
        delete_response = requests.delete(f"{self.base_url}/{entity_id}")
        assert delete_response.status_code == 204, (
            f"Failed to soft delete {self.entity_name}. "
            f"Expected 204, got {delete_response.status_code}: {delete_response.text}"
        )
    
    def get_entity_with_deleted(self, entity_id, include_deleted=True, expected_status=200):
        """
        Get a product by ID, including soft-deleted ones if specified.
        
        Args:
            entity_id: ID of the product to retrieve
            include_deleted: Whether to include soft-deleted products
            expected_status: Expected HTTP status code
            
        Returns:
            Entity data if found, None if expected_status is not 200
        """
        params = {}
        if include_deleted:
            params["include_deleted"] = "true"
            
        get_response = requests.get(f"{self.base_url}/{entity_id}", params=params)
        assert get_response.status_code == expected_status, (
            f"Failed to get {self.entity_name}. "
            f"Expected {expected_status}, got {get_response.status_code}: {get_response.text}"
        )
        
        if expected_status == 200:
            return get_response.json()
        return None
    
    def list_entities_with_deleted(self, include_deleted=True, category_id=None):
        """
        List products, including soft-deleted ones if specified.
        
        Args:
            include_deleted: Whether to include soft-deleted products
            category_id: Optional category ID to filter by
            
        Returns:
            List of products
        """
        params = {}
        if include_deleted:
            params["include_deleted"] = "true"
        if category_id is not None:
            params["category_id"] = str(category_id)
            
        list_response = requests.get(f"{self.base_url}/", params=params)
        assert list_response.status_code == 200, (
            f"Failed to list {self.entity_name}s. "
            f"Expected 200, got {list_response.status_code}: {list_response.text}"
        )
        
        entities = list_response.json()
        return entities
    
    def test_crud_workflow(self):
        """
        Test the full CRUD workflow for a product.
        """
        # 1. CREATE
        initial_name = self.generate_unique_name()
        created_entity, entity_id = self.create_entity(name=initial_name)
        
        # 2. READ
        retrieved_entity = self.get_entity_with_deleted(entity_id, include_deleted=False)
        assert retrieved_entity["id"] == entity_id
        assert retrieved_entity["nume"] == initial_name
        
        # 3. UPDATE
        updated_name = self.generate_unique_name("Updated")
        updated_entity = self.update_entity(entity_id, name=updated_name, pret=150)
        assert updated_entity["nume"] == updated_name
        assert updated_entity["pret"] == 150
        
        # 4. DELETE (soft delete)
        self.soft_delete_entity(entity_id)
        
        # 5. VERIFY soft deletion
        # Should not be found with include_deleted=False
        self.get_entity_with_deleted(entity_id, include_deleted=False, expected_status=404)
        
        # Should be found with include_deleted=True
        deleted_entity = self.get_entity_with_deleted(entity_id, include_deleted=True)
        assert deleted_entity["id"] == entity_id
        assert deleted_entity["is_deleted"] == True
        
        # 6. HARD DELETE
        self.hard_delete_entity(entity_id)
        
        # 7. VERIFY hard deletion
        # Should not be found even with include_deleted=True
        self.get_entity_with_deleted(entity_id, include_deleted=True, expected_status=404)
    
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
            data={
                "nume": "",
                "cantitate": "10",
                "pret": "100",
                "description": "Test description",
                "category_id": "1",
                "unitati_id": "1",
                "stock": "5"
            }
        )
        assert invalid_name_response.status_code == 422
        
        # Test invalid numeric fields
        invalid_numeric_response = requests.post(
            f"{self.base_url}/",
            data={
                "nume": "Test Product",
                "cantitate": "-10",
                "pret": "100",
                "description": "Test description",
                "category_id": "1",
                "unitati_id": "1",
                "stock": "5"
            }
        )
        assert invalid_numeric_response.status_code == 422
        
        # Test duplicate name validation
        unique_name = self.generate_unique_name("Unique")
        created_entity, entity_id = self.create_entity(unique_name)
        
        try:
            # Try to create another product with the same name
            duplicate_response = requests.post(
                f"{self.base_url}/",
                data={
                    "nume": unique_name,
                    "cantitate": "10",
                    "pret": "100",
                    "description": "Test description",
                    "category_id": "1",
                    "unitati_id": "1",
                    "stock": "5"
                }
            )
            assert duplicate_response.status_code == 409, "Should not allow duplicate names"
            
        finally:
            # Clean up
            if entity_id:
                self.hard_delete_entity(entity_id)
    
    def test_list_and_pagination(self):
        """
        Test listing products with pagination and filtering.
        """
        # Create an entity to ensure we have at least one
        created_entity, entity_id = self.create_entity()
        category_id = created_entity["category_id"]
        
        try:
            # Test basic listing
            list_response = requests.get(f"{self.base_url}/")
            assert list_response.status_code == 200
            entities = list_response.json()
            assert isinstance(entities, list)
            assert len(entities) > 0
            
            # Test pagination
            pagination_response = requests.get(f"{self.base_url}/?skip=1&limit=2")
            assert pagination_response.status_code == 200
            paginated_entities = pagination_response.json()
            assert isinstance(paginated_entities, list)
            assert len(paginated_entities) <= 2
            
            # Test filtering by category
            filter_response = requests.get(f"{self.base_url}/?category_id={category_id}")
            assert filter_response.status_code == 200
            filtered_entities = filter_response.json()
            assert isinstance(filtered_entities, list)
            # All returned products should have the specified category
            for product in filtered_entities:
                assert product["category_id"] == category_id
            
        finally:
            # Clean up
            self.hard_delete_entity(entity_id)
    
    def test_soft_delete_and_restore(self):
        """
        Test soft delete functionality and restoration of soft-deleted products.
        """
        # 1. Create a product
        name = self.generate_unique_name()
        created_entity, entity_id = self.create_entity(name=name)
        
        try:
            # 2. Soft delete the product
            self.soft_delete_entity(entity_id)
            
            # 3. Verify soft deletion
            # Should not be found with include_deleted=False
            self.get_entity_with_deleted(entity_id, include_deleted=False, expected_status=404)
            
            # Should be found with include_deleted=True and have is_deleted=True
            deleted_entity = self.get_entity_with_deleted(entity_id, include_deleted=True)
            assert deleted_entity["is_deleted"] == True
            
            # 4. Create a new product with the same name
            # This should restore the soft-deleted product
            restored_entity, restored_id = self.create_entity(name=name)
            
            # 5. Verify the IDs match (same product was restored)
            assert restored_id == entity_id
            
            # 6. Verify the product is no longer marked as deleted
            assert restored_entity["is_deleted"] == False
            
        finally:
            # Clean up
            if entity_id:
                self.hard_delete_entity(entity_id)
    
    def test_error_handling(self):
        """
        Test error handling for various scenarios.
        """
        # Test invalid foreign keys
        invalid_fk_response = requests.post(
            f"{self.base_url}/",
            data={
                "nume": "Test Product",
                "cantitate": "10",
                "pret": "100",
                "description": "Test description",
                "category_id": "99999",  # Non-existent category ID
                "unitati_id": "1",
                "stock": "5"
            }
        )
        assert invalid_fk_response.status_code == 400
        
        # Test invalid update (trying to update non-existent product)
        non_existent_id = 99999
        invalid_update_response = requests.put(
            f"{self.base_url}/{non_existent_id}",
            data={"nume": "Updated Name"}
        )
        assert invalid_update_response.status_code == 404
        
        # Test invalid delete (trying to delete non-existent product)
        invalid_delete_response = requests.delete(f"{self.base_url}/{non_existent_id}")
        assert invalid_delete_response.status_code == 404

    def test_optional_image_path(self):
        """
        Test creating and updating products with optional image paths.
        """
        entity_id = None
        try:
            # 1. Create product without specifying image_path
            name = self.generate_unique_name("NoImage")
            created_entity, entity_id = self.create_entity(name=name, use_placeholder=True)
            
            # 2. Verify the primary_image_path is set when no image is provided
            # Could be a placeholder or default path
            assert created_entity["primary_image_path"] is not None
            initial_path = created_entity["primary_image_path"]
            
            # 3. Update the product to add an image path
            updated_entity = self.update_entity(entity_id, image_path="any_image.jpg")
            
            # 4. Check that image path is set (not checking exact value since the API generates a UUID)
            assert updated_entity["primary_image_path"] is not None
            
            # 5. Update with some other data but no image
            update_response = requests.put(
                f"{self.base_url}/{entity_id}",
                data={"nume": f"Updated-{name}"}
            )
            assert update_response.status_code == 200, (
                f"Failed to update product name. "
                f"Expected 200, got {update_response.status_code}: {update_response.text}"
            )
            
            # 6. Verify the update was successful
            updated_entity = update_response.json()
            assert updated_entity["nume"] == f"Updated-{name}"
            
            # The primary_image_path should still be present
            assert updated_entity["primary_image_path"] is not None
            
        finally:
            # Clean up
            if entity_id:
                self.hard_delete_entity(entity_id)


# Create a test utils instance for products
product_utils = ProductTestUtils()

def test_product_crud_workflow():
    """
    Tests the full Create, Read, Update, and Delete (CRUD) workflow for products.
    """
    product_utils.test_crud_workflow()

def test_product_list_and_pagination():
    """
    Tests listing products with pagination and filtering.
    """
    product_utils.test_list_and_pagination()

def test_product_validation():
    """
    Tests validation for product endpoints.
    """
    product_utils.test_validation()

def test_product_soft_delete_and_restore():
    """
    Tests soft delete functionality and restoration of soft-deleted products.
    """
    product_utils.test_soft_delete_and_restore()

def test_product_error_handling():
    """
    Tests error handling for various scenarios.
    """
    product_utils.test_error_handling()

def test_product_optional_image_path():
    """
    Tests creating and updating products with optional image paths.
    """
    product_utils.test_optional_image_path()
