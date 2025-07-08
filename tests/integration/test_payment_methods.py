import os
import requests
import uuid

# Get the API base URL from the environment variable
API_BASE_URL = os.environ.get("API_BASE_URL")
API_V1_STR = "/api/v1"

def test_payment_method_crud_workflow():
    """
    Tests the full Create, Read, Update, and Delete (CRUD) workflow for payment methods.
    """
    assert API_BASE_URL, "API_BASE_URL environment variable not set"

    # 1. CREATE a new payment method with a unique name
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

    # 2. READ the created payment method
    get_response = requests.get(f"{API_BASE_URL}{API_V1_STR}/modalitati-plata/{payment_method_id}")
    assert get_response.status_code == 200
    retrieved_data = get_response.json()
    assert retrieved_data["id"] == payment_method_id
    assert retrieved_data["denumire"] == unique_name

    # 3. UPDATE the payment method
    updated_name = f"Updated-{uuid.uuid4()}"
    update_data = {"denumire": updated_name}
    update_response = requests.put(
        f"{API_BASE_URL}{API_V1_STR}/modalitati-plata/{payment_method_id}",
        json=update_data
    )
    assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}. Body: {update_response.text}"
    updated_data = update_response.json()
    assert updated_data["denumire"] == updated_name

    # 4. DELETE the payment method
    delete_response = requests.delete(f"{API_BASE_URL}{API_V1_STR}/modalitati-plata/{payment_method_id}")
    assert delete_response.status_code == 204

    # 5. VERIFY the payment method is deleted
    verify_response = requests.get(f"{API_BASE_URL}{API_V1_STR}/modalitati-plata/{payment_method_id}")
    assert verify_response.status_code == 404
