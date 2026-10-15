# Constants for the application

# Category constants
UNCATEGORIZED_CATEGORY_ID = 1
UNCATEGORIZED_CATEGORY_NAME = "Uncategorized"

# URL paths the static file mounts are served at (see system_config.mount_static_files)
PLACEHOLDER_URL_BASE = "/api/v1/static/placeholders"
UPLOADS_URL_BASE = "/api/v1/static/uploads"

# Payment type constants
class PaymentType:
    CUSTOM = 0
    CASH = 1
    PHYSICAL_CARD = 2
    ONLINE_CARD = 3
    REVOLUT = 4
    BANK_TRANSFER = 5 