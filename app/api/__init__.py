# Make the API directory a Python package

# Import the API router to make it available when importing from app.api
from app.api.api import api_router  # noqa: F401
