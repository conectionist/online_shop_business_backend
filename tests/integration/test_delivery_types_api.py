from integration.test_utils import EntityTestUtils

# Create a test utils instance for delivery types
delivery_type_utils = EntityTestUtils(entity_name="Delivery Type", endpoint_path="tipuri-livrare")

def test_delivery_type_crud_workflow():
    """
    Tests the full Create, Read, Update, and Delete (CRUD) workflow for delivery types.
    """
    delivery_type_utils.test_crud_workflow()

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
