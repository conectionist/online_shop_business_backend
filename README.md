# Online Shop Business Backend

## Overview
This is a FastAPI-based backend API for an online shop business application. It provides a RESTful API for managing products, orders, and other e-commerce related functionalities.

## Technology Stack
- Python
- FastAPI
- SQLAlchemy
- MySQL
- Docker
- Pydantic

## Project Structure
```
online_shop_business_backend/
├── app/                      # Main application code
│   ├── api/                  # API endpoints
│   │   ├── v1/               # Version 1 of the API
│   │   └── dependencies/     # Dependency injection
│   ├── core/                 # Core application components
│   │   └── config/           # Application configuration
│   ├── models/               # SQLAlchemy models
│   ├── schemas/              # Pydantic models
│   ├── services/             # Business logic
│   ├── utils/                # Utility functions
│   └── main.py               # Application entry point
├── db/                       # Database-related files
│   ├── migrations/           # Alembic migrations
│   ├── docker-entrypoint-initdb.d/ # MySQL Docker initialization scripts
│   ├── init_db.py            # Database initialization script
│   └── schema.sql            # Database schema
├── test/                     # Test directory
├── docker-compose.yml        # Docker Compose configuration
├── .env.example              # Example environment variables
├── setup_env.sh              # Script to set up environment variables
├── requirements.txt          # Project dependencies
└── README.md                 # Project documentation
```

## Getting Started

### Setting up the Database

1. **Configure Environment Variables**
   ```bash
   # Run the setup script to create your .env file
   ./setup_env.sh
   
   # Edit the .env file with your preferred settings
   nano .env
   ```

2. **Start the MySQL Database**
   ```bash
   # Start the MySQL container
   docker-compose up -d db
   ```

3. **Verify Database Setup**
   ```bash
   # Check that the container is running
   docker-compose ps
   
   # Check the logs to ensure proper initialization
   docker-compose logs db
   ```

### Database Features

- **Automatic Schema Initialization**: The database schema from `db/schema.sql` will be automatically applied when the container starts with an empty database.
  
- **Data Persistence**: The database data is persisted in a Docker volume (`mysql_data`) and will survive container restarts.

- **Safe Schema Handling**: The initialization script will only apply the schema if the database is empty. It will never overwrite an existing database.

- **Configurable Connection**: You can customize the MySQL username, password, and port through the `.env` file.

### Connecting to the Database

```bash
# Connect using mysql client from your host machine
mysql -h 127.0.0.1 -P ${MYSQL_PORT} -u ${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DATABASE}

# Or connect from inside the container
docker-compose exec db mysql -u${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DATABASE}
```
