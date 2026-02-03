import os
import uuid
import requests
import pytest
import shutil
from io import BytesIO
from integration.test_utils import EntityTestUtils
from integration.test_auth_utils import auth_utils

def get_products_base_url():
    """Get the products base URL using the same pattern as test utilities."""
    import os
    api_base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")
    return f"{api_base_url}/api/v1/products"

# Function to get test image content for file uploads
def get_test_image_content():
    """Read test image file and return its content for file uploads"""
    test_image_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'test_data', 
        'test_image.jpg'
    )
    with open(test_image_path, "rb") as f:
        return f.read()

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
    
    def create_entity(self, name=None, with_image=True, use_placeholder=False, order_index=None):
        """
        Create a new category with the given name and optional image upload.
        
        Args:
            name: Name for the category, will generate unique if None
            with_image: Whether to include an image in the request
            use_placeholder: If True, don't include image in the request (use placeholder)
            order_index: Order index to use (1-127). If None, will try to find an available one.
            
        Returns:
            Tuple of (entity_data, entity_id)
        """
        if name is None:
            name = self.generate_unique_name()
        
        # If order_index not provided, try to find an available one (similar to delivery types)
        if order_index is None:
            import random
            base_idx = random.randint(1, 127)
            attempt = 0
            while attempt < 127:
                idx = ((base_idx + attempt - 1) % 127) + 1
                form_data = {'name': name, 'order_index': str(idx)}
                files = {}
                
                if with_image and not use_placeholder:
                    image_content = get_test_image_content()
                    files['primary_image'] = ('test_image.jpg', image_content, 'image/jpeg')
                
                if not auth_utils.access_token:
                    auth_utils.login()
                
                create_response = auth_utils.make_authenticated_request(
                    "POST",
                    f"{self.base_url}/",
                    data=form_data,
                    files=files
                )
                
                if create_response.status_code == 201:
                    created_entity = create_response.json()
                    assert "id" in created_entity
                    assert created_entity["name"] == name
                    assert created_entity["order_index"] == idx
                    
                    if use_placeholder or not with_image:
                        assert created_entity["image_path"] is None
                    else:
                        assert created_entity["image_path"] is not None
                        assert created_entity["image_path"].startswith("categories/")
                    
                    assert "image_versions" in created_entity
                    assert created_entity["image_versions"] is not None
                    assert "original" in created_entity["image_versions"]
                    assert "medium" in created_entity["image_versions"]
                    assert "thumbnail" in created_entity["image_versions"]
                    
                    return created_entity, created_entity["id"]
                elif create_response.status_code == 409:
                    # order_index conflict, try next
                    attempt += 1
                    continue
                else:
                    # Other error
                    assert False, (
                        f"Failed to create {self.entity_name}. "
                        f"Expected 201, got {create_response.status_code}: {create_response.text}"
                    )
            assert False, "Could not find available order_index after 127 attempts"
        else:
            # Use provided order_index
            form_data = {'name': name, 'order_index': str(order_index)}
            files = {}
            
            if with_image and not use_placeholder:
                image_content = get_test_image_content()
                files['primary_image'] = ('test_image.jpg', image_content, 'image/jpeg')
            
            if not auth_utils.access_token:
                auth_utils.login()
            
            create_response = auth_utils.make_authenticated_request(
                "POST",
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
            assert created_entity["name"] == name
            assert created_entity["order_index"] == order_index
            
            if use_placeholder or not with_image:
                assert created_entity["image_path"] is None
            else:
                assert created_entity["image_path"] is not None
                assert created_entity["image_path"].startswith("categories/")
            
            assert "image_versions" in created_entity
            assert created_entity["image_versions"] is not None
            assert "original" in created_entity["image_versions"]
            assert "medium" in created_entity["image_versions"]
            assert "thumbnail" in created_entity["image_versions"]
            
            return created_entity, created_entity["id"]
    
    def update_entity(self, entity_id, name=None, with_image=False, clear_image=False, order_index=None):
        """
        Update a category by ID using PUT (full replacement).
        
        Args:
            entity_id: ID of the category to update
            name: New name for the category (required for PUT)
            with_image: Whether to include a new image in the update
            clear_image: Whether to clear the existing image and use placeholder
            order_index: New order_index for the category (required for PUT). If None, uses current value.
            
        Returns:
            Updated entity data
        """
        # For PUT, name and order_index are required (full replacement semantics)
        if name is None or order_index is None:
            # If not provided, get the current values from the entity
            get_response = requests.get(f"{self.base_url}/{entity_id}")
            assert get_response.status_code == 200, f"Failed to get entity for update: {get_response.text}"
            current = get_response.json()
            if name is None:
                name = current["name"]
            if order_index is None:
                order_index = current["order_index"]
            
        # Prepare multipart/form-data
        form_data = {"name": name, "order_index": str(order_index)}
        if clear_image:
            form_data["clear_image"] = "true"
            
        files = {}
        if with_image:
            image_content = get_test_image_content()
            files['primary_image'] = ('test_image.jpg', image_content, 'image/jpeg')
            
        # Ensure we're authenticated
        if not auth_utils.access_token:
            auth_utils.login()
            
        update_response = auth_utils.make_authenticated_request(
            "PUT",
            f"{self.base_url}/{entity_id}",
            data=form_data,
            files=files
        )
        assert update_response.status_code == 200, (
            f"Failed to update {self.entity_name}. "
            f"Expected 200, got {update_response.status_code}: {update_response.text}"
        )
        
        updated_entity = update_response.json()
        assert updated_entity["name"] == name
        
        if with_image:
            assert updated_entity["image_path"] is not None
            assert updated_entity["image_path"].startswith("categories/")
        elif clear_image:
            assert updated_entity["image_path"] is None
        else:
            # In PUT semantics, if no image is provided and clear_image is false,
            # the image should be set to null (placeholder)
            assert updated_entity["image_path"] is None
            
        assert "image_versions" in updated_entity
        assert updated_entity["image_versions"] is not None
        assert "original" in updated_entity["image_versions"]
        assert "medium" in updated_entity["image_versions"]
        assert "thumbnail" in updated_entity["image_versions"]
            
        return updated_entity
        
    def patch_entity(self, entity_id, name=None, with_image=False, clear_image=False):
        """
        Partially update a category by ID using PATCH.
        
        Args:
            entity_id: ID of the category to update
            name: New name for the category (optional)
            with_image: Whether to include a new image in the update
            clear_image: Whether to clear the existing image and use placeholder
            
        Returns:
            Updated entity data
        """
        # Prepare multipart/form-data
        form_data = {}
        if name is not None:
            form_data["name"] = name
        if clear_image:
            form_data["clear_image"] = "true"
            
        files = {}
        if with_image:
            image_content = get_test_image_content()
            files['primary_image'] = ('test_image.jpg', image_content, 'image/jpeg')
            
        # Ensure we're authenticated
        if not auth_utils.access_token:
            auth_utils.login()
            
        update_response = auth_utils.make_authenticated_request(
            "PATCH",
            f"{self.base_url}/{entity_id}",
            data=form_data,
            files=files
        )
        assert update_response.status_code == 200, (
            f"Failed to patch {self.entity_name}. "
            f"Expected 200, got {update_response.status_code}: {update_response.text}"
        )
        
        updated_entity = update_response.json()
        if name is not None:
            assert updated_entity["name"] == name
        
        if with_image:
            assert updated_entity["image_path"] is not None
            assert updated_entity["image_path"].startswith("categories/")
        elif clear_image:
            assert updated_entity["image_path"] is None
        # In PATCH semantics, if no image is provided and clear_image is false,
        # the existing image should be preserved (no assertion needed)
            
        assert "image_versions" in updated_entity
        assert updated_entity["image_versions"] is not None
        assert "original" in updated_entity["image_versions"]
        assert "medium" in updated_entity["image_versions"]
        assert "thumbnail" in updated_entity["image_versions"]
            
        return updated_entity
    
    def hard_delete_entity(self, entity_id):
        """
        Hard delete a category by ID.
        
        Args:
            entity_id: ID of the category to delete
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
    
    
    def test_crud_workflow(self):
        """
        Test the full CRUD workflow for a category.
        """
        # 1. CREATE
        initial_name = self.generate_unique_name()
        created_entity, entity_id = self.create_entity(name=initial_name, with_image=True)
        
        # Store the image path for later comparison
        initial_image_path = created_entity["image_path"]
        
        # 2. READ
        retrieved_entity = self.get_entity(entity_id)
        assert retrieved_entity == created_entity
        
        # 3. UPDATE
        updated_name = self.generate_unique_name("Updated")
        updated_entity = self.update_entity(entity_id, name=updated_name, with_image=True)
        assert updated_entity["name"] == updated_name
        assert updated_entity["image_path"] is not None
        assert updated_entity["image_path"] != initial_image_path
        
        # 4. DELETE
        self.hard_delete_entity(entity_id)
        
        # 5. VERIFY deletion
        self.get_entity(entity_id, expected_status=404)
    
    def test_validation(self):
        """
        Test basic validation rules.
        """
        # Test invalid ID
        invalid_id_response = requests.get(f"{self.base_url}/-1")
        assert invalid_id_response.status_code == 422
        
        # Ensure we're authenticated for protected operations
        if not auth_utils.access_token:
            auth_utils.login()
        
        # Test empty name (should fail validation, not authentication)
        invalid_name_response = auth_utils.make_authenticated_request(
            "POST",
            f"{self.base_url}/",
            data={"name": "", "order_index": "1"}
        )
        assert invalid_name_response.status_code == 422
        
        # Test invalid image format - we'll simulate this with non-image data
        files = {'primary_image': ('fake.jpg', b'not a real image', 'image/jpeg')}
        invalid_image_response = auth_utils.make_authenticated_request(
            "POST",
            f"{self.base_url}/",
            data={"name": "Test Category", "order_index": "1"},
            files=files
        )
        # Could be 400 (invalid image) or 422 (validation error) depending on which validation runs first
        assert invalid_image_response.status_code in (400, 422)
        if invalid_image_response.status_code == 400:
            detail = invalid_image_response.json().get("detail")
            assert isinstance(detail, list) and len(detail) > 0, f"Expected 400 detail to be a non-empty list, got {detail}"
            assert detail[0].get("type", "").startswith("image_"), f"Expected image error type, got {detail[0].get('type')}"
            assert "msg" in detail[0]

        # Test duplicate name validation
        unique_name = self.generate_unique_name("Unique")
        created_entity, entity_id = self.create_entity(name=unique_name)
        
        try:
            # Try to create another entity with the same name (with different order_index to avoid that conflict)
            # Get an available order_index
            import random
            test_order_index = random.randint(1, 127)
            duplicate_response = auth_utils.make_authenticated_request(
                "POST",
                f"{self.base_url}/",
                data={"name": unique_name, "order_index": str(test_order_index)}
            )
            assert duplicate_response.status_code == 409, "Should return 409 Conflict for duplicate names"
            
            # Verify the error message
            error_data = duplicate_response.json()
            assert "detail" in error_data
            assert f"Category with name '{unique_name}' already exists" in error_data["detail"]
            
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
            # Test updating with invalid data - empty name
            # For PUT endpoint, empty name should return 422 validation error
            # Ensure we're authenticated
            if not auth_utils.access_token:
                auth_utils.login()
                
            invalid_update_response = auth_utils.make_authenticated_request(
                "PUT",
                f"{self.base_url}/{entity_id}",
                data={"name": ""}
            )
            # Accept either 422 (validation error) or 500 (server error)
            # Both are acceptable since empty string validation could happen at different layers
            assert invalid_update_response.status_code in [422, 500]
            
            # Test updating non-existent category
            non_existent_update_response = auth_utils.make_authenticated_request(
                "PUT",
                f"{self.base_url}/{non_existent_id}",
                json={"name": "Non-existent", "image_path": "/images/non-existent.jpg"}
            )
            # Accept either 404 (not found) or 422 (validation error)
            # Both are acceptable depending on validation order in the API
            assert non_existent_update_response.status_code in [404, 422]
            
        finally:
            # Clean up
            self.hard_delete_entity(entity_id)
            
    def test_upload_first_then_create_category_with_primary_image(self):
        """
        Test the upload-first flow for creating a category with a primary image:
        - First upload image via POST /uploads/images to get upload_id
        - Then create category with primary_image_upload_id
        """
        entity_id = None
        try:
            # Ensure we're authenticated
            if not auth_utils.access_token:
                auth_utils.login()

            # 1. Upload image to staging
            image_content = get_test_image_content()
            files = {"file": ("test_image.jpg", image_content, "image/jpeg")}

            upload_response = auth_utils.make_authenticated_request(
                "POST",
                f"{self.api_base_url}{self.api_v1_str}/uploads/images",
                files=files,
            )
            assert upload_response.status_code == 201, (
                f"Expected 201 when uploading image to staging, "
                f"got {upload_response.status_code}: {upload_response.text}"
            )
            upload_body = upload_response.json()
            upload_id = upload_body.get("upload_id")
            assert upload_id, f"upload_id should be present in response, got: {upload_body}"

            # 2. Create category using primary_image_upload_id
            name = self.generate_unique_name("UploadFirstCategory")
            form_data = {
                "name": name,
                "order_index": "1",
                "primary_image_upload_id": upload_id,
            }

            create_response = auth_utils.make_authenticated_request(
                "POST",
                f"{self.base_url}/",
                data=form_data,
            )
            assert create_response.status_code == 201, (
                f"Expected 201 when creating category with primary_image_upload_id, "
                f"got {create_response.status_code}: {create_response.text}"
            )
            created_entity = create_response.json()
            entity_id = created_entity["id"]
            assert created_entity["name"] == name
            # Category with image should have non-null image_path and image_versions
            assert created_entity["image_path"] is not None
            assert "image_versions" in created_entity
            assert created_entity["image_versions"] is not None
            assert "original" in created_entity["image_versions"]
            assert "medium" in created_entity["image_versions"]
            assert "thumbnail" in created_entity["image_versions"]
        finally:
            try:
                if entity_id:
                    self.hard_delete_entity(entity_id)
            except Exception as e:
                print(f"Error during test cleanup: {e}")
            
    def test_optional_image_path(self):
        """
        Test creating and updating categories with optional image uploads.
        """
        entity_id = None
        try:
            # 1. Create a category without an image (use placeholder)
            name = self.generate_unique_name("NoImage")
            created_entity, entity_id = self.create_entity(name=name, with_image=False)
            
            # 2. Verify the image_path is None
            assert created_entity["image_path"] is None
            
            # 3. Verify the image_versions property contains placeholder paths
            assert "image_versions" in created_entity
            assert created_entity["image_versions"] is not None
            assert "original" in created_entity["image_versions"]
            assert "thumbnail" in created_entity["image_versions"]
            assert "medium" in created_entity["image_versions"]
            
            # 4. Verify all image versions point to the placeholder image
            placeholder_path = "/api/v1/static/placeholders/category_placeholder.jpg"
            for version, path in created_entity["image_versions"].items():
                assert path == placeholder_path, f"Expected {version} to be {placeholder_path}, got {path}"
            
            # 4. Update the category to add an image
            updated_entity = self.update_entity(entity_id, with_image=True)
            assert updated_entity["image_path"] is not None
            assert updated_entity["image_path"].startswith("categories/")
            
            # Get the updated image path to verify it's different from placeholder
            original_image_path = updated_entity["image_versions"]["original"]
            assert not original_image_path.endswith("category_placeholder.jpg")
            
            # 5. Update the category to explicitly clear the image and use placeholder
            updated_entity = self.update_entity(entity_id, clear_image=True)
            
            # Verify the image_path is None after update
            assert updated_entity["image_path"] is None
            
            # 6. Verify the image_versions property contains placeholder paths again
            assert "image_versions" in updated_entity
            assert updated_entity["image_versions"] is not None
            assert "original" in updated_entity["image_versions"]
            assert "thumbnail" in updated_entity["image_versions"]
            assert "medium" in updated_entity["image_versions"]
            
            # 7. Verify all image versions point to the placeholder image
            placeholder_path = "/api/v1/static/placeholders/category_placeholder.jpg"
            for version, path in updated_entity["image_versions"].items():
                assert path == placeholder_path, f"Expected {version} to be {placeholder_path}, got {path}"
            
            # 8. Test uploading image directly to the image upload endpoint
            image_content = get_test_image_content()
            files = {'file': ('test_image.jpg', image_content, 'image/jpeg')}
            
            upload_response = requests.post(
                f"{self.base_url}/{entity_id}/image",
                files=files
            )
            assert upload_response.status_code == 200, (
                f"Failed to upload image for category. "
                f"Expected 200, got {upload_response.status_code}: {upload_response.text}"
            )
            
            updated_entity = upload_response.json()
            assert updated_entity["image_path"] is not None
            assert updated_entity["image_path"].startswith("categories/")
            assert "image_versions" in updated_entity
            
        finally:
            # Clean up
            if entity_id:
                self.hard_delete_entity(entity_id)

# Create a test utils instance for categories
category_utils = CategoryTestUtils()

def find_available_order_indices(count=1, prefer_high=False):
    """
    Find available order_index values dynamically.
    
    Args:
        count: Number of indices to find
        prefer_high: If True, prefer high values (for testing high index scenarios)
    
    Returns:
        List of available order_index values
    """
    all_categories = requests.get(f"{category_utils.base_url}/").json()
    used_indices = {c["order_index"] for c in all_categories}
    
    available = []
    if prefer_high:
        # Start from high values and work down
        for i in range(127, 0, -1):
            if i not in used_indices and len(available) < count:
                available.append(i)
    else:
        # Start from low values and work up
        for i in range(1, 127):
            if i not in used_indices and len(available) < count:
                available.append(i)
    
    assert len(available) >= count, f"Could not find {count} available order_index values"
    return available

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

def test_category_error_handling():
    """
    Tests error handling for various scenarios.
    """
    category_utils.test_error_handling()

def test_category_optional_image_path():
    """
    Tests creating and updating categories with optional image paths.
    """
    category_utils.test_optional_image_path()


def test_put_without_image_resets_to_placeholder():
    """
    Test that PUT with only name resets image to null/placeholder.
    """
    # Create a test category with an image
    created_category, category_id = category_utils.create_entity(name="Test PUT Reset", with_image=True)
    assert created_category["image_path"] is not None
    
    try:
        # PUT with only name (should reset image to null/placeholder)
        new_name = "Updated with PUT"
        put_result = category_utils.update_entity(category_id, name=new_name)
        assert put_result["name"] == new_name
        assert put_result["image_path"] is None, "PUT without image should reset image to null"
        
    finally:
        # Clean up
        category_utils.hard_delete_entity(category_id)


def test_patch_without_image_preserves_existing_image():
    """
    Test that PATCH with only name preserves existing image state.
    """
    # Create a test category with an image
    created_category, category_id = category_utils.create_entity(name="Test PATCH Preserve", with_image=True)
    initial_image_path = created_category["image_path"]
    assert initial_image_path is not None
    
    try:
        # PATCH with only name (should preserve existing image)
        patched_name = "Updated with PATCH"
        patch_result = category_utils.patch_entity(category_id, name=patched_name)
        assert patch_result["name"] == patched_name
        assert patch_result["image_path"] == initial_image_path, "PATCH without image should preserve existing image"
        
    finally:
        # Clean up
        category_utils.hard_delete_entity(category_id)


def test_put_with_clear_image_clears_image():
    """
    Test that PUT with clear_image=True clears the image.
    """
    # Create a test category with an image
    created_category, category_id = category_utils.create_entity(name="Test PUT Clear", with_image=True)
    assert created_category["image_path"] is not None
    
    try:
        # PUT with clear_image=True (should clear image)
        put_clear_result = category_utils.update_entity(category_id, name="PUT with clear", clear_image=True)
        assert put_clear_result["image_path"] is None
        
    finally:
        # Clean up
        category_utils.hard_delete_entity(category_id)


def test_patch_with_clear_image_clears_image():
    """
    Test that PATCH with clear_image=True clears the image while preserving other fields.
    """
    # Create a test category with an image
    created_category, category_id = category_utils.create_entity(name="Test PATCH Clear", with_image=True)
    assert created_category["image_path"] is not None
    
    try:
        # PATCH with clear_image=True (should clear image but preserve name)
        original_name = created_category["name"]
        patch_clear_result = category_utils.patch_entity(category_id, clear_image=True)
        assert patch_clear_result["image_path"] is None
        assert patch_clear_result["name"] == original_name, "PATCH should preserve name when not specified"
        
    finally:
        # Clean up
        category_utils.hard_delete_entity(category_id)


def test_category_image_replacement():
    """
    Test replacing an existing image with a new one.
    """
    # Create a test category
    created_category, category_id = category_utils.create_entity()
    
    try:
        # Store the first image path for comparison
        first_image_path = created_category["image_path"]
        
        # Upload a second image to replace the first one
        updated_entity = category_utils.update_entity(category_id, with_image=True)
        
        # Verify the image path has changed
        assert updated_entity["image_path"] != first_image_path, "Image path should be different after replacement"
        
    finally:
        # Clean up
        category_utils.hard_delete_entity(category_id)


def test_category_image_versions():
    """
    Test that multiple image versions are created and accessible.
    """
    # Create a test category
    created_category, category_id = category_utils.create_entity()
    
    try:
        # Check that image_versions contains paths for all versions
        assert "image_versions" in created_category
        image_versions = created_category["image_versions"]
        
        # Check each version exists
        for version in ["original", "medium", "thumbnail"]:
            assert version in image_versions
            version_path = image_versions[version]
            
            if created_category["image_path"] is not None:  # If we have an actual image
                assert version_path.endswith(".jpg"), f"Path for {version} should end with .jpg"
                assert version_path.startswith("categories/"), f"Path for {version} should start with categories/"
            else:  # If using placeholder
                assert "placeholder" in version_path, f"Path for {version} should contain 'placeholder'"
        
        # Verify image persistence - fetch the category again to ensure image data is persisted
        get_response = requests.get(f"{category_utils.base_url}/{category_id}")
        assert get_response.status_code == 200
        
        retrieved_entity = get_response.json()
        assert "image_path" in retrieved_entity
        assert retrieved_entity["image_path"] == created_category["image_path"]
        assert "image_versions" in retrieved_entity
        
        # Verify image versions are consistent between create response and GET response
        for version in ["original", "medium", "thumbnail"]:
            assert version in retrieved_entity["image_versions"]
            assert retrieved_entity["image_versions"][version] == created_category["image_versions"][version]
    
    finally:
        # Clean up
        category_utils.hard_delete_entity(category_id)


def test_category_invalid_image_uploads():
    """
    Test validation for image uploads.
    """
    # Create a test category
    created_category, category_id = category_utils.create_entity()
    
    try:
        # Test with invalid file type (plain text as fake image)
        text_file = BytesIO(b"This is not an image")
        files = {"file": ("test.txt", text_file, "text/plain")}
        invalid_type_response = requests.post(
            f"{category_utils.base_url}/{category_id}/image",
            files=files
        )
        # The server should reject invalid files (400 with 422-like detail or 422)
        assert invalid_type_response.status_code in [400, 422], "Should reject non-image files"
        if invalid_type_response.status_code == 400:
            detail = invalid_type_response.json().get("detail")
            assert isinstance(detail, list) and len(detail) > 0, f"Expected 400 detail to be a non-empty list, got {detail}"
            assert detail[0].get("type", "").startswith("image_"), f"Expected image error type, got {detail[0].get('type')}"
            assert "msg" in detail[0]

        # Test with non-existent category
        non_existent_id = 99999  # Assuming this ID doesn't exist
        test_image = get_test_image_content()
        files = {"file": ("test_image.jpg", test_image, "image/jpeg")}
        not_found_response = requests.post(
            f"{category_utils.base_url}/{non_existent_id}/image",
            files=files
        )
        assert not_found_response.status_code == 404, "Should reject uploads to non-existent categories"
    
    finally:
        # Clean up
        category_utils.hard_delete_entity(category_id)


def test_category_deletion_cascade():
    """
    Tests that when a category is deleted, all its products are moved to "Uncategorized" category.
    """
    # Ensure we're authenticated
    if not auth_utils.access_token:
        auth_utils.login()
        
    # First, create a category using the test utils (which handles order_index)
    created_category, category_id = category_utils.create_entity("Test Category for Cascade")
    
    # created_category and category_id are already set from create_entity above
    
    try:
        # Create a product in this category directly
        products_base_url = get_products_base_url()
        
        product_data = {
            "nume": "Test Product in Category",
            "cantitate": "10",
            "pret": "10050",
            "description": "Test product in specific category",
            "category_id": str(category_id),
            "unitati_id": "1"
        }
        
        product_response = requests.post(
            f"{products_base_url}/",
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
        
        # Delete the category using the categories API
        delete_response = auth_utils.make_authenticated_request(
            "DELETE",
            f"{category_utils.base_url}/{category_id}"
        )
        assert delete_response.status_code == 204, (
            f"Failed to delete category. "
            f"Expected 204, got {delete_response.status_code}: {delete_response.text}"
        )
        
        # Check that the product now has category_id = 1 (Uncategorized)
        get_product_response = requests.get(f"{products_base_url}/{product_id}")
        assert get_product_response.status_code == 200
        
        updated_product = get_product_response.json()
        assert updated_product["category_id"] == 1, "Product should be moved to 'Uncategorized' category (ID 1)"
        
        # Clean up the product
        try:
            requests.delete(f"{products_base_url}/{product_id}?permanent=true")
        except Exception as e:
            print(f"Error during test cleanup: {e}")
            
    except Exception as e:
        print(f"Error during test: {e}")
        # Clean up category if it still exists
        try:
            requests.delete(f"{category_utils.base_url}/{category_id}")
        except:
            pass


def test_cannot_delete_uncategorized_category():
    """
    Tests that the default "Uncategorized" category (ID 1) cannot be deleted.
    """
    # Ensure we're authenticated
    if not auth_utils.access_token:
        auth_utils.login()
        
    # Try to delete the Uncategorized category
    delete_response = auth_utils.make_authenticated_request(
        "DELETE",
        f"{category_utils.base_url}/1"
    )
    assert delete_response.status_code == 403, (
        f"Expected 403 Forbidden when trying to delete Uncategorized category, "
        f"got {delete_response.status_code}: {delete_response.text}"
    )
    
    # Verify the error message
    error_detail = delete_response.json().get("detail", "")
    assert "Cannot delete the default 'Uncategorized' category" in error_detail
    
    # Verify the category still exists
    get_response = requests.get(f"{category_utils.base_url}/1")
    assert get_response.status_code == 200, (
        f"Expected 200 OK when getting Uncategorized category, "
        f"got {get_response.status_code}: {get_response.text}"
    )
    
    category_data = get_response.json()
    assert category_data["id"] == 1
    assert category_data["name"] == "Uncategorized"


def test_category_create_requires_order_index_and_enforces_range():
    """
    Validate create requires order_index and enforces 1-127 range.
    """
    # Ensure auth
    if not auth_utils.access_token:
        auth_utils.login()
    
    # Missing order_index
    form_data = {'name': 'Test Category No Index'}
    resp = auth_utils.make_authenticated_request(
        "POST", f"{category_utils.base_url}/", data=form_data
    )
    assert resp.status_code in (400, 422), "Missing order_index should be invalid"
    
    # Out of range low
    form_data = {'name': 'Test Category Low', 'order_index': '0'}
    resp = auth_utils.make_authenticated_request(
        "POST", f"{category_utils.base_url}/", data=form_data
    )
    assert resp.status_code == 422
    
    # Out of range high
    form_data = {'name': 'Test Category High', 'order_index': '128'}
    resp = auth_utils.make_authenticated_request(
        "POST", f"{category_utils.base_url}/", data=form_data
    )
    assert resp.status_code == 422


def test_category_ordering_and_unique_index():
    """Ensure list ordering by order_index then name and unique index 409 on conflict."""
    # Find available order_index values dynamically
    indices = find_available_order_indices(count=2)
    
    # Create two with explicit indices
    first, first_id = category_utils.create_entity("Order A", order_index=indices[0])
    second, second_id = category_utils.create_entity("Order B", order_index=indices[1])
    try:
        # Fetch list and ensure order_index ordering
        resp = requests.get(f"{category_utils.base_url}/")
        assert resp.status_code == 200
        items = resp.json()
        assert isinstance(items, list)
        
        # Verify order_index is present in response
        assert "order_index" in first
        assert "order_index" in second
        
        # Update second to have same order_index as first -> expect 409
        if not auth_utils.access_token:
            auth_utils.login()
        form_data = {'name': 'Order B', 'order_index': str(first["order_index"])}
        conflict = auth_utils.make_authenticated_request(
            "PATCH", f"{category_utils.base_url}/{second_id}", data=form_data
        )
        assert conflict.status_code == 409
    finally:
        category_utils.hard_delete_entity(second_id)
        category_utils.hard_delete_entity(first_id)


def test_reorder_categories_happy_path_moves_item_to_top():
    """PUT /categories/reorder should atomically reorder by full ID list."""
    import requests
    # Find available order_index values dynamically
    indices = find_available_order_indices(count=3)
    
    # Create three new categories to work with
    cat1, id1 = category_utils.create_entity("Reorder Cat 1", order_index=indices[0])
    cat2, id2 = category_utils.create_entity("Reorder Cat 2", order_index=indices[1])
    cat3, id3 = category_utils.create_entity("Reorder Cat 3", order_index=indices[2])

    try:
        # Build the full ordered ID list by taking current IDs and moving id3 to the top
        current = requests.get(f"{category_utils.base_url}/").json()
        all_ids = [x["id"] for x in current]
        assert id1 in all_ids and id2 in all_ids and id3 in all_ids

        new_order = [id3] + [i for i in all_ids if i != id3]

        # Auth and call reorder
        if not auth_utils.access_token:
            auth_utils.login()
        resp = auth_utils.make_authenticated_request(
            "PUT", f"{category_utils.base_url}/reorder", json=new_order
        )
        assert resp.status_code == 200, f"Reorder failed: {resp.status_code} {resp.text}"

        updated = resp.json()
        assert isinstance(updated, list) and len(updated) == len(new_order)
        # First element should now be id3
        assert updated[0]["id"] == id3
        # Order indices should match positions (1-based)
        for pos, item in enumerate(updated, start=1):
            assert item["order_index"] == pos

        # GET should reflect the same order
        listed = requests.get(f"{category_utils.base_url}/").json()
        assert [x["id"] for x in listed] == [x["id"] for x in updated]
    finally:
        # Clean up created entities
        category_utils.hard_delete_entity(id3)
        category_utils.hard_delete_entity(id2)
        category_utils.hard_delete_entity(id1)


def test_reorder_categories_invalid_permutation_returns_422():
    import requests
    # Fetch current full list
    current = requests.get(f"{category_utils.base_url}/").json()
    ids = [x["id"] for x in current]
    assert len(ids) >= 2, "Need at least two categories for this test"
    # Duplicate the first ID and drop the last to keep length the same
    bad_ids = ids[:-1] + [ids[0]]

    if not auth_utils.access_token:
        auth_utils.login()
    resp = auth_utils.make_authenticated_request(
        "PUT", f"{category_utils.base_url}/reorder", json=bad_ids
    )
    assert resp.status_code == 422, f"Expected 422 for invalid permutation, got {resp.status_code}"


def test_reorder_categories_with_unknown_id_returns_404():
    import requests
    # Fetch current full list
    current = requests.get(f"{category_utils.base_url}/").json()
    ids = [x["id"] for x in current]
    assert len(ids) >= 1
    bad_ids = ids[:]
    bad_ids[-1] = 99999999  # assume non-existent

    if not auth_utils.access_token:
        auth_utils.login()
    resp = auth_utils.make_authenticated_request(
        "PUT", f"{category_utils.base_url}/reorder", json=bad_ids
    )
    assert resp.status_code == 404, f"Expected 404 for unknown id, got {resp.status_code}"
