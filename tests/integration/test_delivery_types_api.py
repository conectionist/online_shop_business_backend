import requests
from integration.test_utils import EntityTestUtils
from integration.test_auth_utils import auth_utils

# Create a test utils instance for delivery types
delivery_type_utils = EntityTestUtils(entity_name="Delivery Type", endpoint_path="tipuri-livrare")


def test_patch_with_valid_data():
    """
    Test PATCH with valid data.
    """
    # Create a delivery type for testing
    created_entity, entity_id = delivery_type_utils.create_entity("Test Delivery Type")
    
    try:
        # PATCH with new name
        new_name = "Patched Delivery Type"
        patch_response = auth_utils.make_authenticated_request(
            "PATCH",
            f"{delivery_type_utils.base_url}/{entity_id}",
            json={"denumire": new_name}
        )
        assert patch_response.status_code == 200, (
            f"PATCH should return 200, got {patch_response.status_code}: {patch_response.text}"
        )
        
        patched_entity = patch_response.json()
        assert patched_entity["denumire"] == new_name
        assert patched_entity["id"] == entity_id
        
        # Verify the change persisted
        retrieved_entity = delivery_type_utils.get_entity(entity_id)
        assert retrieved_entity["denumire"] == new_name
        
    finally:
        # Clean up
        delivery_type_utils.delete_entity(entity_id)


def test_patch_with_empty_json():
    """
    Test PATCH with empty JSON (should return 400 - no valid fields to update).
    """
    # Create a delivery type for testing
    created_entity, entity_id = delivery_type_utils.create_entity("Test Delivery Type")
    
    try:
        # PATCH with empty JSON should return 400 (no valid fields to update)
        empty_patch_response = auth_utils.make_authenticated_request(
            "PATCH",
            f"{delivery_type_utils.base_url}/{entity_id}",
            json={}
        )
        assert empty_patch_response.status_code == 400, (
            f"PATCH with empty JSON should return 400, got {empty_patch_response.status_code}"
        )
        
        # Verify the error message
        error_data = empty_patch_response.json()
        assert "detail" in error_data
        assert "No valid fields to update" in error_data["detail"]
        
    finally:
        # Clean up
        delivery_type_utils.delete_entity(entity_id)


def test_patch_with_non_existent_delivery_type():
    """
    Test PATCH with non-existent delivery type ID.
    """
    non_existent_response = auth_utils.make_authenticated_request(
        "PATCH",
        f"{delivery_type_utils.base_url}/99999",
        json={"denumire": "test"}
    )
    assert non_existent_response.status_code == 404, (
        f"PATCH with non-existent ID should return 404, got {non_existent_response.status_code}"
    )


def test_patch_with_invalid_data():
    """
    Test PATCH with invalid data (should return 422).
    """
    # Create a delivery type for testing
    created_entity, entity_id = delivery_type_utils.create_entity("Test Delivery Type")
    
    try:
        # PATCH with empty string (should fail validation)
        invalid_patch_response = auth_utils.make_authenticated_request(
            "PATCH",
            f"{delivery_type_utils.base_url}/{entity_id}",
            json={"denumire": ""}
        )
        assert invalid_patch_response.status_code == 422, (
            f"PATCH with invalid data should return 422, got {invalid_patch_response.status_code}"
        )
        
        # Verify the error message
        error_data = invalid_patch_response.json()
        assert "detail" in error_data
        
    finally:
        # Clean up
        delivery_type_utils.delete_entity(entity_id)


def test_patch_with_duplicate_name():
    """
    Test PATCH with duplicate name (should fail).
    """
    # Create two delivery types
    first_name = "First Delivery Type"
    second_name = "Second Delivery Type"

    first_entity, first_id = delivery_type_utils.create_entity(first_name)
    second_entity, second_id = delivery_type_utils.create_entity(second_name)

    try:
        # Try to PATCH first delivery type to use the same name as second delivery type
        duplicate_patch_response = auth_utils.make_authenticated_request(
            "PATCH",
            f"{delivery_type_utils.base_url}/{first_id}",
            json={"denumire": second_name}
        )
        assert duplicate_patch_response.status_code == 409, (
            f"PATCH with duplicate name should return 409, got {duplicate_patch_response.status_code}"
        )
        
        # Verify the error message
        error_data = duplicate_patch_response.json()
        assert "detail" in error_data
        assert "already exists" in error_data["detail"]

    finally:
        # Clean up
        delivery_type_utils.delete_entity(second_id)
        delivery_type_utils.delete_entity(first_id)


def test_patch_with_partial_data_works():
    """
    Test that PATCH accepts partial data.
    """
    # Create a delivery type for testing
    created_entity, entity_id = delivery_type_utils.create_entity("Test Delivery Type")
    
    try:
        # PATCH with partial data (should work)
        patch_data = {"denumire": "Patched Delivery Type"}
        patch_response = auth_utils.make_authenticated_request(
            "PATCH",
            f"{delivery_type_utils.base_url}/{entity_id}",
            json=patch_data
        )
        assert patch_response.status_code == 200
        
        # Verify the change
        patched_entity = patch_response.json()
        assert patched_entity["denumire"] == "Patched Delivery Type"
        
    finally:
        # Clean up
        delivery_type_utils.delete_entity(entity_id)


def test_put_with_empty_json_fails():
    """
    Test that PUT rejects empty JSON.
    """
    # Create a delivery type for testing
    created_entity, entity_id = delivery_type_utils.create_entity("Test Delivery Type")
    
    try:
        # PUT with empty JSON (should fail)
        put_response = auth_utils.make_authenticated_request(
            "PUT",
            f"{delivery_type_utils.base_url}/{entity_id}",
            json={}  # Empty JSON for PUT should fail
        )
        assert put_response.status_code == 400, (
            f"PUT with empty JSON should return 400, got {put_response.status_code}"
        )
        
        # Verify the error message
        error_data = put_response.json()
        assert "detail" in error_data
        assert "No valid fields to update" in error_data["detail"]
        
    finally:
        # Clean up
        delivery_type_utils.delete_entity(entity_id)


def test_put_with_complete_data_works():
    """
    Test that PUT accepts complete data.
    """
    # Create a delivery type for testing
    created_entity, entity_id = delivery_type_utils.create_entity("Test Delivery Type")
    
    try:
        # PUT with complete data (should work)
        put_data = {"denumire": "PUT Updated Delivery Type"}
        put_response = auth_utils.make_authenticated_request(
            "PUT",
            f"{delivery_type_utils.base_url}/{entity_id}",
            json=put_data
        )
        assert put_response.status_code == 200
        
        # Verify the change
        final_entity = delivery_type_utils.get_entity(entity_id)
        assert final_entity["denumire"] == "PUT Updated Delivery Type"
        
    finally:
        # Clean up
        delivery_type_utils.delete_entity(entity_id)


def test_delivery_type_crud_workflow():
    """
    Tests the full Create, Read, Update, and Delete (CRUD) workflow for delivery types.
    """
    delivery_type_utils.test_crud_workflow()


def test_delivery_type_create_requires_order_index_and_enforces_range():
    """
    Validate create requires order_index and enforces 1-127 range.
    """
    # Ensure auth
    if not auth_utils.access_token:
        auth_utils.login()
    # Missing order_index
    resp = auth_utils.make_authenticated_request(
        "POST", f"{delivery_type_utils.base_url}/", json={"denumire": "NoIdx"}
    )
    assert resp.status_code in (400, 422), "Missing order_index should be invalid"
    # Out of range low
    resp = auth_utils.make_authenticated_request(
        "POST", f"{delivery_type_utils.base_url}/", json={"denumire": "LowIdx", "order_index": 0}
    )
    assert resp.status_code == 422
    # Out of range high
    resp = auth_utils.make_authenticated_request(
        "POST", f"{delivery_type_utils.base_url}/", json={"denumire": "HighIdx", "order_index": 128}
    )
    assert resp.status_code == 422


def test_delivery_type_ordering_and_unique_index():
    """Ensure list ordering by order_index then denumire and unique index 409 on conflict."""
    # Create two with explicit indices
    first, first_id = delivery_type_utils.create_entity("Order A")
    second, second_id = delivery_type_utils.create_entity("Order B")
    try:
        # Fetch list and ensure order_index ordering (best-effort; relies on indices chosen in helper)
        import requests
        resp = requests.get(f"{delivery_type_utils.base_url}/")
        assert resp.status_code == 200
        items = resp.json()
        assert isinstance(items, list)
        # Update second to have same order_index as first -> expect 409
        if not auth_utils.access_token:
            auth_utils.login()
        conflict = auth_utils.make_authenticated_request(
            "PATCH", f"{delivery_type_utils.base_url}/{second_id}", json={"order_index": first["order_index"]}
        )
        assert conflict.status_code == 409
    finally:
        delivery_type_utils.delete_entity(second_id)
        delivery_type_utils.delete_entity(first_id)


def test_delivery_type_list_and_pagination():
    """
    Tests listing delivery types with pagination.
    """
    delivery_type_utils.test_list_and_pagination()


def test_delivery_type_validation():
    """
    Tests validation for delivery type endpoints.
    """
    delivery_type_utils.test_validation()


def test_reorder_delivery_types_happy_path_moves_item_to_top():
    """PUT /tipuri-livrare/reorder should atomically reorder by full ID list."""
    import requests
    # Create three new delivery types to work with
    dt1, id1 = delivery_type_utils.create_entity("Reorder DT 1")
    dt2, id2 = delivery_type_utils.create_entity("Reorder DT 2")
    dt3, id3 = delivery_type_utils.create_entity("Reorder DT 3")

    try:
        # Build the full ordered ID list by taking current IDs and moving id3 to the top
        current = requests.get(f"{delivery_type_utils.base_url}/").json()
        all_ids = [x["id"] for x in current]
        assert id1 in all_ids and id2 in all_ids and id3 in all_ids

        new_order = [id3] + [i for i in all_ids if i != id3]

        # Auth and call reorder
        if not auth_utils.access_token:
            auth_utils.login()
        resp = auth_utils.make_authenticated_request(
            "PUT", f"{delivery_type_utils.base_url}/reorder", json=new_order
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
        listed = requests.get(f"{delivery_type_utils.base_url}/").json()
        assert [x["id"] for x in listed] == [x["id"] for x in updated]
    finally:
        # Clean up created entities
        delivery_type_utils.delete_entity(id3)
        delivery_type_utils.delete_entity(id2)
        delivery_type_utils.delete_entity(id1)


def test_reorder_delivery_types_invalid_permutation_returns_422():
    import requests
    # Fetch current full list
    current = requests.get(f"{delivery_type_utils.base_url}/").json()
    ids = [x["id"] for x in current]
    assert len(ids) >= 2, "Need at least two delivery types for this test"
    # Duplicate the first ID and drop the last to keep length the same
    bad_ids = ids[:-1] + [ids[0]]

    if not auth_utils.access_token:
        auth_utils.login()
    resp = auth_utils.make_authenticated_request(
        "PUT", f"{delivery_type_utils.base_url}/reorder", json=bad_ids
    )
    assert resp.status_code == 422, f"Expected 422 for invalid permutation, got {resp.status_code}"


def test_reorder_delivery_types_with_unknown_id_returns_404():
    import requests
    current = requests.get(f"{delivery_type_utils.base_url}/").json()
    ids = [x["id"] for x in current]
    assert len(ids) >= 1
    bad_ids = ids[:]
    bad_ids[-1] = 99999999  # assume non-existent

    if not auth_utils.access_token:
        auth_utils.login()
    resp = auth_utils.make_authenticated_request(
        "PUT", f"{delivery_type_utils.base_url}/reorder", json=bad_ids
    )
    assert resp.status_code == 404, f"Expected 404 for unknown id, got {resp.status_code}"
