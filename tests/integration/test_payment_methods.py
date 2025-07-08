import os
import requests
import uuid

# Get the API base URL from the environment variable
API_BASE_URL = os.environ.get("API_BASE_URL")
API_V1_STR = "/api/v1"

def test_create_and_get_payment_method():
    """
    Tests creating a new payment method and then retrieving it.
    """
    assert API_BASE_URL, "API_BASE_URL environment variable not set"
    
    # 1. Create a new payment method with a unique name
    # The generated name must be <= 45 chars.
    unique_name = f"Test-{uuid.uuid4()}"
    create_data = {"denumire": unique_name}
    create_response = requests.post(
        f"{API_BASE_URL}{API_V1_STR}/modalitati-plata/", 
        json=create_data
    )
    assert create_response.status_code == 201, f"Expected 201, got {create_response.status_code}. Body: {create_response.text}"
    
    created_data = create_response.json()
    assert created_data["denumire"] == unique_name
    assert "id" in created_data
    payment_method_id = created_data["id"]

    # 2. Retrieve the newly created payment method by its ID
    get_response = requests.get(f"{API_BASE_URL}{API_V1_STR}/modalitati-plata/{payment_method_id}")
    assert get_response.status_code == 200
    
    retrieved_data = get_response.json()
    assert retrieved_data["id"] == payment_method_id
    assert retrieved_data["denumire"] == unique_name
