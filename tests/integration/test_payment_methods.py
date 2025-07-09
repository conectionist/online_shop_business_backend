from integration.test_utils import EntityTestUtils

# Create a test utils instance for payment methods
payment_method_utils = EntityTestUtils(entity_name="Payment Method", endpoint_path="modalitati-plata")

def test_payment_method_crud_workflow():
    """
    Tests the full Create, Read, Update, and Delete (CRUD) workflow for payment methods.
    """
    payment_method_utils.test_crud_workflow()

def test_payment_method_list_and_pagination():
    """
    Tests listing payment methods with pagination.
    """
    payment_method_utils.test_list_and_pagination()

def test_payment_method_validation():
    """
    Tests validation for payment method endpoints.
    """
    payment_method_utils.test_validation()
