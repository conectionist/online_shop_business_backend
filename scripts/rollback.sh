#!/bin/bash

# Production Rollback Script for Backend API
# Usage: ./scripts/rollback.sh [TAG] [OPTIONS]
# 
# Examples:
#   ./scripts/rollback.sh                    # List available versions
#   ./scripts/rollback.sh master-abc123      # Rollback to specific commit
#   ./scripts/rollback.sh 2024-01-15-14-30  # Rollback to specific timestamp
#   ./scripts/rollback.sh --latest           # Rollback to latest version
#   ./scripts/rollback.sh --previous         # Rollback to previous version

set -e

# Configuration
REGISTRY="ghcr.io"
REPOSITORY="conectionist/online_shop_business_backend"
IMAGE_NAME="$REGISTRY/$REPOSITORY"
COMPOSE_FILE="docker-compose.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    echo "Production Rollback Script for Backend API"
    echo ""
    echo "Usage: $0 [TAG] [OPTIONS]"
    echo ""
    echo "Arguments:"
    echo "  TAG                 Specific tag to rollback to (commit SHA, timestamp, etc.)"
    echo ""
    echo "Options:"
    echo "  --latest           Rollback to latest version"
    echo "  --previous         Rollback to previous version"
    echo "  --list             List available versions"
    echo "  --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                           # List available versions"
    echo "  $0 master-abc123             # Rollback to specific commit"
    echo "  $0 2024-01-15-14-30          # Rollback to specific timestamp"
    echo "  $0 --latest                  # Rollback to latest version"
    echo "  $0 --previous                # Rollback to previous version"
    echo ""
    echo "Note: This script requires GitHub CLI (gh) to be installed and authenticated."
    echo "      Run 'gh auth login' if you haven't already."
}

list_available_versions() {
    log_info "Fetching available image versions..."
    
    # Get available tags from GitHub Container Registry
    if command -v gh >/dev/null 2>&1; then
        PACKAGES=$(gh api "/user/packages?package_type=container" --jq '.[].name' 2>/dev/null || echo "")
        
        if [ -n "$PACKAGES" ]; then
            # Find the package that matches our repository name
            PACKAGE_NAME=$(echo "$PACKAGES" | grep -i "online_shop_business_backend" | head -1)
            if [ -z "$PACKAGE_NAME" ]; then
                # If exact match not found, use the first package
                PACKAGE_NAME=$(echo "$PACKAGES" | head -1)
            fi
            TAGS=$(gh api "/user/packages/container/$PACKAGE_NAME/versions" --jq '.[].metadata.container.tags[]' 2>/dev/null || echo "")
        else
            log_error "No container packages found for user"
            TAGS=""
        fi
    else
        log_warning "GitHub CLI not found. Cannot fetch private registry tags without it."
        log_info "Please install GitHub CLI or use manual rollback with known tags."
        log_info ""
        log_info "Manual rollback example:"
        log_info "  ./scripts/rollback.sh master-abc123"
        log_info "  ./scripts/rollback.sh 2024-01-15-14-30"
        return 1
    fi
    
    if [ -z "$TAGS" ]; then
        log_error "No versions found or unable to fetch versions"
        log_info "This might be because:"
        log_info "  1. GitHub CLI is not authenticated (run: gh auth login)"
        log_info "  2. Repository is private and you don't have access"
        log_info "  3. No images have been built yet"
        return 1
    fi
    
    echo ""
    log_info "Available versions:"
    echo "$TAGS" | sort -r | while read tag; do
        if [ -n "$tag" ]; then
            echo "  - $tag"
        fi
    done
    echo ""
}

get_previous_version() {
    if command -v gh >/dev/null 2>&1; then
        # Get container packages silently
        PACKAGES=$(gh api "/user/packages?package_type=container" --jq '.[].name' 2>/dev/null || echo "")
        
        if [ -n "$PACKAGES" ]; then
            # Find the package that matches our repository name
            PACKAGE_NAME=$(echo "$PACKAGES" | grep -i "online_shop_business_backend" | head -1)
            if [ -z "$PACKAGE_NAME" ]; then
                # If exact match not found, use the first package
                PACKAGE_NAME=$(echo "$PACKAGES" | head -1)
            fi
            
            # Get tags silently
            TAGS=$(gh api "/user/packages/container/$PACKAGE_NAME/versions" --jq '.[].metadata.container.tags[]' 2>/dev/null || echo "")
        else
            return 1
        fi
    else
        return 1
    fi
    
    if [ -z "$TAGS" ]; then
        return 1
    fi
    
    # Get the second most recent tag (skip latest and master)
    # Prefer timestamp-based tags for chronological sorting
    TIMESTAMP_TAGS=$(echo "$TAGS" | grep -E "^[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{2}-[0-9]{2}$" | sort -r)
    COMMIT_TAGS=$(echo "$TAGS" | grep -E "^master-[a-f0-9]+$" | sort -r)
    
    if [ -n "$TIMESTAMP_TAGS" ]; then
        # Use timestamp-based tags (they sort chronologically)
        PREVIOUS=$(echo "$TIMESTAMP_TAGS" | head -2 | tail -1)
    else
        # Fallback to commit tags (alphabetical sort)
        PREVIOUS=$(echo "$COMMIT_TAGS" | head -2 | tail -1)
    fi
    
    if [ -z "$PREVIOUS" ]; then
        return 1
    fi
    
    # Return only the version tag, no logging
    echo "$PREVIOUS"
}

rollback_to_version() {
    local target_tag="$1"
    local full_image_name="$IMAGE_NAME:$target_tag"
    
    log_info "Starting rollback to version: $target_tag"
    
    # Check if docker-compose file exists
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "Docker compose file not found: $COMPOSE_FILE"
        return 1
    fi
    
    # Pull the target image
    log_info "Pulling image: $full_image_name"
    if ! docker pull "$full_image_name"; then
        log_error "Failed to pull image: $full_image_name"
        return 1
    fi
    
    # Tag the target image as latest
    log_info "Tagging $full_image_name as latest"
    docker tag "$full_image_name" "$IMAGE_NAME:latest"
    
    # Stop current containers
    log_info "Stopping current containers..."
    docker compose down
    
    # Start with new image
    log_info "Starting containers with rolled back image..."
    docker compose up -d
    
    # Verify deployment
    log_info "Verifying deployment..."
    sleep 10  # Give more time for the API to start up
    
    # Check if containers are running
    if docker compose ps | grep -q "Up"; then
        log_success "Rollback completed successfully!"
        log_info "Current version: $target_tag"
        log_info "Containers status:"
        docker compose ps
        
        # Test API health endpoint
        log_info "Testing API health..."
        sleep 5
        if curl -f -s http://localhost:8000/ >/dev/null 2>&1; then
            log_success "API is responding correctly!"
        else
            log_warning "API health check failed, but containers are running"
            log_info "You may want to check the logs: docker compose logs api"
        fi
    else
        log_error "Rollback failed - containers are not running"
        log_info "Container status:"
        docker compose ps
        log_info "Check logs for more details:"
        log_info "  docker compose logs api"
        log_info "  docker compose logs db"
        return 1
    fi
}

# Main script logic
main() {
    log_info "Backend API Rollback script started with arguments: $*"
    
    case "${1:-}" in
        --help|-h)
            log_info "Showing help..."
            show_help
            exit 0
            ;;
        --list)
            log_info "Listing available versions..."
            list_available_versions
            exit 0
            ;;
        --latest)
            log_info "Rolling back to latest version..."
            rollback_to_version "latest"
            ;;
        --previous)
            log_info "Rolling back to previous version..."
            PREVIOUS_VERSION=$(get_previous_version)
            if [ -n "$PREVIOUS_VERSION" ]; then
                log_info "Previous version found: $PREVIOUS_VERSION"
                rollback_to_version "$PREVIOUS_VERSION"
            else
                log_error "Failed to get previous version"
                log_info "Let's try listing versions manually..."
                list_available_versions
                exit 1
            fi
            ;;
        "")
            log_info "No arguments provided, listing available versions..."
            list_available_versions
            ;;
        *)
            log_info "Rolling back to specific version: $1"
            rollback_to_version "$1"
            ;;
    esac
}

# Run main function with all arguments
main "$@"
