FROM python:3.14-slim

WORKDIR /app

# Copy dependency specification and install system packages
COPY requirements.txt .

RUN apt-get update && apt-get install -y curl default-mysql-client && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the application code and required assets
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY db/ ./db/
COPY alembic.ini.template logging.ini docker-entrypoint.sh ./
COPY test/test_data/seed_data_complete.sql ./test/test_data/seed_data_complete.sql

ARG UID=1000
ARG GID=1000

RUN groupadd --gid $GID appuser \
 && useradd --uid $UID --gid $GID --create-home appuser \
 && mkdir -p /app/logs /app/uploads \
 && chown -R appuser:appuser /app \
 && chmod +x docker-entrypoint.sh

# Run the application as the unprivileged user
USER appuser

# Use our custom entrypoint script
ENTRYPOINT ["./docker-entrypoint.sh"]
