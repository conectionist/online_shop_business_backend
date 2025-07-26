import os
import requests
import json
from integration.test_utils import EntityTestUtils


class SystemConfigTestUtils:
    """Test utilities for the System Configuration API."""
    
    def __init__(self):
        """Initialize with the System Configuration endpoint."""
        self.api_base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")
        self.api_v1_str = "/api/v1"
        self.base_url = f"{self.api_base_url}{self.api_v1_str}/system"
    
    def get_system_config(self, expected_status=200):
        """
        Get system configuration.
        
        Args:
            expected_status: Expected HTTP status code
            
        Returns:
            System configuration data if found, None if expected_status is not 200
        """
        get_response = requests.get(f"{self.base_url}/config")
        assert get_response.status_code == expected_status, (
            f"Failed to get system configuration. "
            f"Expected {expected_status}, got {get_response.status_code}: {get_response.text}"
        )
        
        if expected_status == 200:
            return get_response.json()
        return None
    
    def check_placeholder_image(self, image_path, expected_status=200):
        """
        Check if a placeholder image is accessible.
        
        Args:
            image_path: Path to the image from the system config response
            expected_status: Expected HTTP status code
            
        Returns:
            True if the image is accessible, False otherwise
        """
        # Construct the full URL from the path
        image_url = f"{self.api_base_url}{image_path}"
        
        # Send a HEAD request to check if the image exists
        head_response = requests.head(image_url)
        assert head_response.status_code == expected_status, (
            f"Failed to access placeholder image at {image_url}. "
            f"Expected {expected_status}, got {head_response.status_code}"
        )
        
        # Check that the content type is an image
        if expected_status == 200:
            content_type = head_response.headers.get('content-type', '')
            assert content_type.startswith('image/'), (
                f"Expected image content type, got {content_type}"
            )
            return True
        return False
    
    def test_system_config_endpoint(self):
        """
        Test the system configuration endpoint.
        """
        # Get the system configuration
        config = self.get_system_config()
        
        # Verify the structure of the response
        assert "category_placeholder" in config, "Response should contain category_placeholder"
        assert "product_placeholder" in config, "Response should contain product_placeholder"
        assert "default_category_id" in config, "Response should contain default_category_id"
        assert "default_category_name" in config, "Response should contain default_category_name"
        
        # Verify that the paths are strings and have the expected format
        assert isinstance(config["category_placeholder"], str), "category_placeholder should be a string"
        assert isinstance(config["product_placeholder"], str), "product_placeholder should be a string"
        
        # Verify that the default category fields have the expected types and values
        assert isinstance(config["default_category_id"], int), "default_category_id should be an integer"
        assert config["default_category_id"] == 1, "default_category_id should be 1"
        assert isinstance(config["default_category_name"], str), "default_category_name should be a string"
        assert config["default_category_name"] == "Uncategorized", "default_category_name should be 'Uncategorized'"
        
        # Check that the paths start with the expected prefix
        assert config["category_placeholder"].startswith("/api/v1/static/placeholders/"), (
            f"Expected category_placeholder to start with '/api/v1/static/placeholders/', "
            f"got {config['category_placeholder']}"
        )
        assert config["product_placeholder"].startswith("/api/v1/static/placeholders/"), (
            f"Expected product_placeholder to start with '/api/v1/static/placeholders/', "
            f"got {config['product_placeholder']}"
        )
        
        # Verify that the placeholder images are accessible
        self.check_placeholder_image(config["category_placeholder"])
        self.check_placeholder_image(config["product_placeholder"])
    
    def test_static_file_serving(self):
        """
        Test that static files are properly served.
        """
        # Get the system configuration to get the paths
        config = self.get_system_config()
        
        # Test category placeholder image
        category_image_url = f"{self.api_base_url}{config['category_placeholder']}"
        category_response = requests.get(category_image_url)
        assert category_response.status_code == 200, (
            f"Failed to download category placeholder image. "
            f"Expected 200, got {category_response.status_code}"
        )
        assert len(category_response.content) > 0, "Category placeholder image should not be empty"
        
        # Test product placeholder image
        product_image_url = f"{self.api_base_url}{config['product_placeholder']}"
        product_response = requests.get(product_image_url)
        assert product_response.status_code == 200, (
            f"Failed to download product placeholder image. "
            f"Expected 200, got {product_response.status_code}"
        )
        assert len(product_response.content) > 0, "Product placeholder image should not be empty"


# Create a test utils instance for system configuration
system_config_utils = SystemConfigTestUtils()

def test_system_config_endpoint():
    """
    Tests the system configuration endpoint.
    """
    system_config_utils.test_system_config_endpoint()

def test_static_file_serving():
    """
    Tests that static files are properly served.
    """
    system_config_utils.test_static_file_serving()
