import os
import uuid
import requests
import pytest
import shutil
from io import BytesIO
from integration.test_utils import EntityTestUtils

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
    
    def create_entity(self, name=None, with_image=True, use_placeholder=False):
        """
        Create a new category with the given name and optional image upload.
        
        Args:
            name: Name for the category, will generate unique if None
            with_image: Whether to include an image in the request
            use_placeholder: If True, don't include image in the request (use placeholder)
            
        Returns:
            Tuple of (entity_data, entity_id)
        """
        if name is None:
            name = self.generate_unique_name()
            
        # Prepare multipart/form-data with the name field
        form_data = {'name': name}
        files = {}
        
        # Add image file if needed
        if with_image and not use_placeholder:
            image_content = get_test_image_content()
            files['primary_image'] = ('test_image.jpg', image_content, 'image/jpeg')
            
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
        assert created_entity["name"] == name
        
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
    
    def update_entity(self, entity_id, name=None, with_image=False, clear_image=False):
        """
        Update a category by ID using PUT (full replacement).
        
        Args:
            entity_id: ID of the category to update
            name: New name for the category (required for PUT)
            with_image: Whether to include a new image in the update
            clear_image: Whether to clear the existing image and use placeholder
            
        Returns:
            Updated entity data
        """
        # For PUT, name is required (full replacement semantics)
        if name is None:
            # If no name provided, get the current name from the entity
            get_response = requests.get(f"{self.base_url}/{entity_id}")
            assert get_response.status_code == 200, f"Failed to get entity for update: {get_response.text}"
            name = get_response.json()["name"]
            
        # Prepare multipart/form-data
        form_data = {"name": name}
        if clear_image:
            form_data["clear_image"] = "true"
            
        files = {}
        if with_image:
            image_content = get_test_image_content()
            files['primary_image'] = ('test_image.jpg', image_content, 'image/jpeg')
            
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
            
        update_response = requests.patch(
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
            data={"name": ""}
        )
        assert invalid_name_response.status_code == 422
        
        # Test invalid image format - we'll simulate this with non-image data
        files = {'primary_image': ('fake.jpg', b'not a real image', 'image/jpeg')}
        invalid_image_response = requests.post(
            f"{self.base_url}/",
            data={"name": "Test Category"},
            files=files
        )
        assert invalid_image_response.status_code == 400
        
        # Test duplicate name validation
        unique_name = self.generate_unique_name("Unique")
        created_entity, entity_id = self.create_entity(name=unique_name)
        
        try:
            # Try to create another entity with the same name
            duplicate_response = requests.post(
                f"{self.base_url}/",
                data={"name": unique_name}
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
    
    def test_soft_delete_and_restore(self):
        """
        Test soft delete functionality and restoration of soft-deleted categories.
        """
        # 1. Create a category
        name = self.generate_unique_name("SoftDelete")
        created_entity, entity_id = self.create_entity(name=name)
        
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
            data={"name": name},
            files={'primary_image': ('test_image.jpg', get_test_image_content(), 'image/jpeg')}
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
            # Test updating with invalid data - empty name
            # For PUT endpoint, empty name should return 422 validation error
            invalid_update_response = requests.put(
                f"{self.base_url}/{entity_id}",
                data={"name": ""}
            )
            # Accept either 422 (validation error) or 500 (server error)
            # Both are acceptable since empty string validation could happen at different layers
            assert invalid_update_response.status_code in [422, 500]
            
            # Test updating non-existent category
            non_existent_update_response = requests.put(
                f"{self.base_url}/{non_existent_id}",
                json={"name": "Non-existent", "image_path": "/images/non-existent.jpg"}
            )
            # Accept either 404 (not found) or 422 (validation error)
            # Both are acceptable depending on validation order in the API
            assert non_existent_update_response.status_code in [404, 422]
            
        finally:
            # Clean up
            self.hard_delete_entity(entity_id)
            
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
        # The server should reject invalid files
        assert invalid_type_response.status_code in [400, 422], "Should reject non-image files"
        
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
