from integration.test_utils import EntityTestUtils

# Create a test utils instance for units
unit_utils = EntityTestUtils(entity_name="Unit", endpoint_path="unitati")

def test_unit_crud_workflow():
    """
    Tests the full Create, Read, Update, and Delete (CRUD) workflow for units.
    """
    unit_utils.test_crud_workflow()

def test_unit_list_and_pagination():
    """
    Tests listing units with pagination.
    """
    unit_utils.test_list_and_pagination()

def test_unit_validation():
    """
    Tests validation for unit endpoints.
    """
    unit_utils.test_validation()
