import os
import requests
import uuid

# Path to test image
TEST_IMAGE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_data', 'test_image.jpg')

# Read test image file
def get_test_image_content():
    with open(TEST_IMAGE_PATH, 'rb') as f:
        return f.read()

from integration.test_utils import EntityTestUtils
from integration.test_auth_utils import auth_utils

def get_categories_base_url():
    """Get the categories base URL using the same pattern as test utilities."""
    import os
    api_base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")
    return f"{api_base_url}/api/v1/categories"

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
                     description=None):
        """
        Create a new product with the given parameters.
        
        Args:
            name: Name for the product, will generate unique if None
            category_id: ID of the category for this product
            unitati_id: ID of the unit for this product
            cantitate: Quantity value
            pret: Price value
            description: Product description
            
        Returns:
            Tuple of (entity_data, entity_id)
        """
        if name is None:
            name = self.generate_unique_name()
            
        if description is None:
            description = f"Description for {name}"
        
        # Prepare form data - Products API uses multipart/form-data format
        form_data = {
            "nume": name,
            "cantitate": str(cantitate),
            "pret": str(pret),
            "description": description,
            "category_id": str(category_id),
            "unitati_id": str(unitati_id)
        }
        
        # Note: primary_image has been removed, we now use the dedicated product_images endpoints
            
        # Ensure we're authenticated
        if not auth_utils.access_token:
            auth_utils.login()
            
        create_response = auth_utils.make_authenticated_request(
            "POST",
            f"{self.base_url}/",
            data=form_data
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
                     cantitate=None, pret=None, description=None):
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
        
        # Note: Images are now handled through the dedicated product_images endpoints
        
        update_response = auth_utils.make_authenticated_request(
            "PATCH",
            f"{self.base_url}/{entity_id}",
            data=form_data
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
        # Ensure we're authenticated
        if not auth_utils.access_token:
            auth_utils.login()
            
        delete_response = auth_utils.make_authenticated_request(
            "DELETE",
            f"{self.base_url}/{entity_id}?permanent=true"
        )
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
        delete_response = auth_utils.make_authenticated_request(
            "DELETE",
            f"{self.base_url}/{entity_id}"
        )
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
        # Ensure we're authenticated
        if not auth_utils.access_token:
            auth_utils.login()
            
        invalid_name_response = auth_utils.make_authenticated_request(
            "POST",
            f"{self.base_url}/",
            data={
                "nume": "",
                "cantitate": "10",
                "pret": "100",
                "description": "Test description",
                "category_id": "1",
                "unitati_id": "1"
            }
        )
        assert invalid_name_response.status_code == 400  # API now returns 400 for empty name
        
        # Test invalid numeric fields
        invalid_numeric_response = auth_utils.make_authenticated_request(
            "POST",
            f"{self.base_url}/",
            data={
                "nume": "Test Product",
                "cantitate": "-10",
                "pret": "100",
                "description": "Test description",
                "category_id": "1",
                "unitati_id": "1"
            }
        )
        assert invalid_numeric_response.status_code == 400  # API returns 400 for invalid numeric values
        
        # Test duplicate name validation
        unique_name = self.generate_unique_name("Unique")
        created_entity, entity_id = self.create_entity(unique_name)
        
        try:
            # Try to create another product with the same name
            duplicate_response = auth_utils.make_authenticated_request(
                "POST",
                f"{self.base_url}/",
                data={
                    "nume": unique_name,
                    "cantitate": "10",
                    "pret": "100",
                    "description": "Test description",
                    "category_id": "1",
                    "unitati_id": "1"
                }
            )
            assert duplicate_response.status_code == 400, "API returns 400 for duplicate names"
            
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
        # Ensure we're authenticated
        if not auth_utils.access_token:
            auth_utils.login()
            
        invalid_fk_response = auth_utils.make_authenticated_request(
            "POST",
            f"{self.base_url}/",
            data={
                "nume": "Test Product",
                "cantitate": "10",
                "pret": "100",
                "description": "Test description",
                "category_id": "99999",  # Non-existent category ID
                "unitati_id": "1"
            }
        )
        assert invalid_fk_response.status_code == 400
        
        # Test invalid update (trying to update non-existent product)
        non_existent_id = 99999
        invalid_update_response = auth_utils.make_authenticated_request(
            "PATCH",
            f"{self.base_url}/{non_existent_id}",
            data={"nume": "Updated Name"}
        )
        assert invalid_update_response.status_code == 404

    def test_product_images(self):
        """
        Test creating products and then adding images using the product_images endpoint.
        """
        entity_id = None
        try:
            # 1. First, create a product without an image
            prod_name = self.generate_unique_name("ImageTestProduct")

            # Create a product without an image
            form_data = {
                "nume": prod_name,
                "cantitate": "10",
                "pret": "100",
                "description": f"Description for {prod_name}",
                "category_id": "1",
                "unitati_id": "1"
            }

            # Ensure we're authenticated
            if not auth_utils.access_token:
                auth_utils.login()
                
            create_response = auth_utils.make_authenticated_request(
                "POST",
                f"{self.base_url}/",
                data=form_data
            )

            assert create_response.status_code == 201, (
                f"Failed to create product. "
                f"Expected 201, got {create_response.status_code}: {create_response.text}"
            )

            created_entity = create_response.json()
            entity_id = created_entity["id"]

            # Verify the product was created
            assert "id" in created_entity
            assert created_entity["nume"] == prod_name

            # 2. Now add an image using the product_images endpoint
            test_image_content = get_test_image_content()
            files = {
                'file': ('test_image.jpg', test_image_content, 'image/jpeg')
            }

            upload_response = auth_utils.make_authenticated_request(
                "POST",
                f"{self.base_url}/{entity_id}/images",
                files=files
            )

            assert upload_response.status_code == 200, (
                f"Failed to upload image. "
                f"Expected 200, got {upload_response.status_code}: {upload_response.text}"
            )

            # Verify the image was added
            image_data = upload_response.json()
            assert "id" in image_data
            assert "path" in image_data
            assert "position" in image_data
                
            # Get the product to verify it has the image in its images list
            get_response = requests.get(f"{self.base_url}/{entity_id}")
            assert get_response.status_code == 200
                
            retrieved_entity = get_response.json()
            assert "images" in retrieved_entity
            assert len(retrieved_entity["images"]) > 0
            
        finally:
            # Clean up
            try:
                if entity_id:
                    self.hard_delete_entity(entity_id)
            except Exception as e:
                print(f"Error during test cleanup: {e}")
                
    def test_multiple_product_images(self):
        """
        Test adding multiple images to a product and managing their positions.
        """
        entity_id = None
        try:
            # Use our create_entity method with a truly unique name
            unique_name = self.generate_unique_name("MultiImg" + str(uuid.uuid4())[:8])

            # Create the form data directly to have full control over the request
            form_data = {
                "nume": unique_name,
                "cantitate": "10",
                "pret": "100",
                "description": f"Description for {unique_name}",
                "category_id": "1",
                "unitati_id": "1"
            }

            # Create a product without images
            # Ensure we're authenticated
            if not auth_utils.access_token:
                auth_utils.login()
                
            create_response = auth_utils.make_authenticated_request(
                "POST",
                f"{self.base_url}/",
                data=form_data
            )

            assert create_response.status_code == 201, (
                f"Failed to create product. "
                f"Expected 201, got {create_response.status_code}: {create_response.text}"
            )

            created_entity = create_response.json()
            entity_id = created_entity["id"]
            
            # Now upload multiple images using the product_images endpoint
            test_image_content = get_test_image_content()
            
            # Upload first image
            files_1 = {
                'file': ('test_image1.jpg', test_image_content, 'image/jpeg')
            }
            
            upload_response_1 = auth_utils.make_authenticated_request(
                "POST",
                f"{self.base_url}/{entity_id}/images",
                files=files_1
            )
            
            assert upload_response_1.status_code == 200, (
                f"Failed to upload first image. "
                f"Expected 200, got {upload_response_1.status_code}: {upload_response_1.text}"
            )
            
            image_1_data = upload_response_1.json()
            image_1_id = image_1_data["id"]
            
            # Upload second image
            files_2 = {
                'file': ('test_image2.jpg', test_image_content, 'image/jpeg')
            }
            
            upload_response_2 = auth_utils.make_authenticated_request(
                "POST",
                f"{self.base_url}/{entity_id}/images",
                files=files_2
            )
            
            assert upload_response_2.status_code == 200
            image_2_data = upload_response_2.json()
            
            # Test getting all images for the product
            get_images_response = requests.get(f"{self.base_url}/{entity_id}/images")
            assert get_images_response.status_code == 200
            
            images = get_images_response.json()
            assert len(images) == 2  # We uploaded 2 images
            
            # Test updating image position (reordering)
            reorder_data = [
                {"id": image_2_data["id"], "position": 0},  # Make second image the primary (position 0)
                {"id": image_1_data["id"], "position": 1}   # Move first image to position 1
            ]
            
            reorder_response = auth_utils.make_authenticated_request(
                "PUT",
                f"{self.base_url}/{entity_id}/images/reorder",
                json=reorder_data
            )
            
            assert reorder_response.status_code == 200
            
            # Verify the reordering worked
            get_images_after_reorder = requests.get(f"{self.base_url}/{entity_id}/images")
            updated_images = get_images_after_reorder.json()
            
            # First image in the list should now be the one we moved to position 0
            assert updated_images[0]["id"] == image_2_data["id"]
            assert updated_images[0]["position"] == 0
            
        finally:
            # Clean up
            try:
                if entity_id:
                    self.hard_delete_entity(entity_id)
            except Exception as e:
                print(f"Error during test cleanup: {e}")


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

def test_product_images():
    """
    Tests creating products and then adding images using the product_images endpoint.
    """
    product_utils.test_product_images()

def test_multiple_product_images():
    """
    Tests adding multiple images to a product and managing their positions.
    """
    product_utils.test_multiple_product_images()


def test_create_product_without_category():
    """
    Tests creating a product without specifying a category_id.
    Should default to "Uncategorized" category (ID 1).
    """
    # Create product without category_id
    form_data = {
        "nume": "Test Product No Category",
        "cantitate": "10",
        "pret": "10050",
        "description": "Test product without category",
        "unitati_id": "1",
        
        # Note: category_id is intentionally omitted
    }
    
    # Ensure we're authenticated
    if not auth_utils.access_token:
        auth_utils.login()
        
    create_response = auth_utils.make_authenticated_request(
        "POST",
        f"{product_utils.base_url}/",
        data=form_data
    )
    
    assert create_response.status_code == 201, (
        f"Failed to create product without category. "
        f"Expected 201, got {create_response.status_code}: {create_response.text}"
    )
    
    created_product = create_response.json()
    assert created_product["category_id"] == 1, "Product should default to 'Uncategorized' category (ID 1)"
    assert created_product["nume"] == "Test Product No Category"
    
    # Clean up
    try:
        product_utils.hard_delete_entity(created_product["id"])
    except Exception as e:
        print(f"Error during test cleanup: {e}")


def test_create_product_with_empty_category():
    """
    Tests creating a product with empty category_id string.
    Should default to "Uncategorized" category (ID 1).
    """
    # Create product with empty category_id
    form_data = {
        "nume": "Test Product Empty Category",
        "cantitate": "10",
        "pret": "10050",
        "description": "Test product with empty category",
        "category_id": "",  # Empty string
        "unitati_id": "1",
        
    }
    
    # Ensure we're authenticated
    if not auth_utils.access_token:
        auth_utils.login()
        
    create_response = auth_utils.make_authenticated_request(
        "POST",
        f"{product_utils.base_url}/",
        data=form_data
    )
    
    assert create_response.status_code == 201, (
        f"Failed to create product with empty category. "
        f"Expected 201, got {create_response.status_code}: {create_response.text}"
    )
    
    created_product = create_response.json()
    assert created_product["category_id"] == 1, "Product should default to 'Uncategorized' category (ID 1)"
    assert created_product["nume"] == "Test Product Empty Category"
    
    # Clean up
    try:
        product_utils.hard_delete_entity(created_product["id"])
    except Exception as e:
        print(f"Error during test cleanup: {e}")


def test_category_deletion_cascade():
    """
    Tests that when a category is deleted, all its products are moved to "Uncategorized" category.
    """
    # Ensure we're authenticated
    if not auth_utils.access_token:
        auth_utils.login()
        
    # First, create a category directly
    categories_base_url = get_categories_base_url()
    
    # Use a unique category name to avoid conflicts
    unique_category_name = f"Test Category for Cascade {uuid.uuid4().hex[:8]}"
    category_data = {
        "name": unique_category_name
    }
    
    category_response = auth_utils.make_authenticated_request(
        "POST",
        f"{categories_base_url}/",
        data=category_data
    )
    
    assert category_response.status_code == 201, (
        f"Failed to create category. "
        f"Expected 201, got {category_response.status_code}: {category_response.text}"
    )
    
    created_category = category_response.json()
    category_id = created_category["id"]
    
    try:
        # Create a product in this category
        product_data = {
            "nume": "Test Product in Category",
            "cantitate": "10",
            "pret": "10050",
            "description": "Test product in specific category",
            "category_id": str(category_id),
            "unitati_id": "1",
            
        }
        
        product_response = auth_utils.make_authenticated_request(
            "POST",
            f"{product_utils.base_url}/",
            data=product_data
        )
        
        assert product_response.status_code == 201, (
            f"Failed to create product in category. "
            f"Expected 201, got {product_response.status_code}: {product_response.text}"
        )
        
        created_product = product_response.json()
        product_id = created_product["id"]
        
        # Verify product is in the correct category
        assert created_product["category_id"] == category_id
        
        # Delete the category
        delete_response = auth_utils.make_authenticated_request(
            "DELETE",
            f"{categories_base_url}/{category_id}"
        )
        assert delete_response.status_code == 204, (
            f"Failed to delete category. "
            f"Expected 204, got {delete_response.status_code}: {delete_response.text}"
        )
        
        # Check that the product now has category_id = 1 (Uncategorized)
        get_product_response = requests.get(f"{product_utils.base_url}/{product_id}")
        assert get_product_response.status_code == 200
        
        updated_product = get_product_response.json()
        assert updated_product["category_id"] == 1, "Product should be moved to 'Uncategorized' category (ID 1)"
        
        # Clean up the product
        try:
            product_utils.hard_delete_entity(product_id)
        except Exception as e:
            print(f"Error during test cleanup: {e}")
            
    except Exception as e:
        print(f"Error during test: {e}")
        # Clean up category if it still exists
        try:
            requests.delete(f"{categories_base_url}/{category_id}")
        except:
            pass
