#!/bin/bash

# Docker Run Script for User Management System
# Loads and runs Docker images from tar files

set -e  # Exit on any error

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
IMAGES_DIR="$PROJECT_ROOT/docker-images"

# Default image names and ports
API_IMAGE_NAME="user-management-api"
WEBUI_IMAGE_NAME="user-management-webui"
API_PORT="8001"
WEBUI_PORT="4201"
DEFAULT_TAG="latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

log_separator() {
    echo -e "${BLUE}================================================${NC}"
}

# Help function
show_help() {
    cat << EOF
User Management System Docker Run Script

USAGE:
    $0 [COMMAND] [OPTIONS]

COMMANDS:
    load                    Load Docker images from tar files
    run                     Run Docker containers
    stop                    Stop running containers
    status                  Show status of containers
    logs                    Show container logs
    clean                   Remove containers and images

OPTIONS:
    -h, --help              Show this help message
    -t, --tag TAG           Docker image tag (default: $DEFAULT_TAG)
    -d, --dir DIR           Directory containing tar files (default: $IMAGES_DIR)
    --api-port PORT         API port mapping (default: $API_PORT)
    --webui-port PORT       WebUI port mapping (default: $WEBUI_PORT)
    --api-only              Work with API container only
    --webui-only            Work with WebUI container only
    --detach                Run containers in background (default for run command)
    --follow                Follow logs output (for logs command)

EXAMPLES:
    $0 load                              # Load images from tar files
    $0 run                               # Run both containers
    $0 run --api-only                    # Run only API container
    $0 stop                              # Stop all containers
    $0 logs --api-only --follow          # Follow API logs
    $0 status                            # Show container status
    $0 clean                             # Clean up everything

CONTAINER NAMES:
    - user-management-api-container
    - user-management-webui-container

ACCESS URLS:
    - API: http://localhost:$API_PORT
    - WebUI: http://localhost:$WEBUI_PORT
EOF
}

# Parse command line arguments
parse_args() {
    COMMAND=""
    TAG="$DEFAULT_TAG"
    IMAGES_DIR="$IMAGES_DIR"
    API_PORT="$API_PORT"
    WEBUI_PORT="$WEBUI_PORT"
    WORK_WITH_API=true
    WORK_WITH_WEBUI=true
    DETACH=true
    FOLLOW=false

    # First argument is the command
    if [[ $# -gt 0 && ! "$1" =~ ^- ]]; then
        COMMAND="$1"
        shift
    fi

    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -t|--tag)
                TAG="$2"
                shift 2
                ;;
            -d|--dir)
                IMAGES_DIR="$2"
                shift 2
                ;;
            --api-port)
                API_PORT="$2"
                shift 2
                ;;
            --webui-port)
                WEBUI_PORT="$2"
                shift 2
                ;;
            --api-only)
                WORK_WITH_API=true
                WORK_WITH_WEBUI=false
                shift
                ;;
            --webui-only)
                WORK_WITH_API=false
                WORK_WITH_WEBUI=true
                shift
                ;;
            --detach)
                DETACH=true
                shift
                ;;
            --follow)
                FOLLOW=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done

    # Default to help if no command specified
    if [[ -z "$COMMAND" ]]; then
        show_help
        exit 0
    fi
}

# Container names
get_api_container_name() {
    echo "user-management-api-container"
}

get_webui_container_name() {
    echo "user-management-webui-container"
}

# Load Docker images from tar files
load_images() {
    log_separator
    log_info "Loading Docker images from tar files..."
    log_info "  Source directory: $IMAGES_DIR"
    log_info "  Tag: $TAG"
    
    if [[ ! -d "$IMAGES_DIR" ]]; then
        log_error "Images directory not found: $IMAGES_DIR"
        exit 1
    fi
    
    if [[ "$WORK_WITH_API" == true ]]; then
        local api_tar="$IMAGES_DIR/${API_IMAGE_NAME}_${TAG}.tar"
        if [[ -f "$api_tar" ]]; then
            log_info "Loading API image from: $api_tar"
            docker load -i "$api_tar"
            log_success "API image loaded successfully"
        else
            log_warning "API tar file not found: $api_tar"
        fi
    fi
    
    if [[ "$WORK_WITH_WEBUI" == true ]]; then
        local webui_tar="$IMAGES_DIR/${WEBUI_IMAGE_NAME}_${TAG}.tar"
        if [[ -f "$webui_tar" ]]; then
            log_info "Loading WebUI image from: $webui_tar"
            docker load -i "$webui_tar"
            log_success "WebUI image loaded successfully"
        else
            log_warning "WebUI tar file not found: $webui_tar"
        fi
    fi
    
    log_separator
}

# Run Docker containers
run_containers() {
    log_separator
    log_info "Starting Docker containers..."
    log_info "  API Port: $API_PORT"
    log_info "  WebUI Port: $WEBUI_PORT"
    log_info "  Tag: $TAG"
    
    if [[ "$WORK_WITH_API" == true ]]; then
        local api_container=$(get_api_container_name)
        
        # Stop and remove existing container if it exists
        docker stop "$api_container" 2>/dev/null || true
        docker rm "$api_container" 2>/dev/null || true
        
        log_info "Starting API container..."
        docker run -d \
            --name "$api_container" \
            -p "$API_PORT:8001" \
            "${API_IMAGE_NAME}:${TAG}"
        
        log_success "API container started: http://localhost:$API_PORT"
    fi
    
    if [[ "$WORK_WITH_WEBUI" == true ]]; then
        local webui_container=$(get_webui_container_name)
        
        # Stop and remove existing container if it exists
        docker stop "$webui_container" 2>/dev/null || true
        docker rm "$webui_container" 2>/dev/null || true
        
        log_info "Starting WebUI container..."
        docker run -d \
            --name "$webui_container" \
            -p "$WEBUI_PORT:80" \
            "${WEBUI_IMAGE_NAME}:${TAG}"
        
        log_success "WebUI container started: http://localhost:$WEBUI_PORT"
    fi
    
    log_separator
    show_status
}

# Stop containers
stop_containers() {
    log_separator
    log_info "Stopping Docker containers..."
    
    if [[ "$WORK_WITH_API" == true ]]; then
        local api_container=$(get_api_container_name)
        if docker ps -q -f name="$api_container" | grep -q .; then
            docker stop "$api_container"
            log_success "API container stopped"
        else
            log_info "API container is not running"
        fi
    fi
    
    if [[ "$WORK_WITH_WEBUI" == true ]]; then
        local webui_container=$(get_webui_container_name)
        if docker ps -q -f name="$webui_container" | grep -q .; then
            docker stop "$webui_container"
            log_success "WebUI container stopped"
        else
            log_info "WebUI container is not running"
        fi
    fi
    
    log_separator
}

# Show container status
show_status() {
    log_separator
    log_info "Container Status:"
    
    if [[ "$WORK_WITH_API" == true ]]; then
        local api_container=$(get_api_container_name)
        if docker ps -q -f name="$api_container" | grep -q .; then
            echo -e "  ${GREEN}✓${NC} API Container: Running (http://localhost:$API_PORT)"
        elif docker ps -aq -f name="$api_container" | grep -q .; then
            echo -e "  ${RED}✗${NC} API Container: Stopped"
        else
            echo -e "  ${YELLOW}?${NC} API Container: Not created"
        fi
    fi
    
    if [[ "$WORK_WITH_WEBUI" == true ]]; then
        local webui_container=$(get_webui_container_name)
        if docker ps -q -f name="$webui_container" | grep -q .; then
            echo -e "  ${GREEN}✓${NC} WebUI Container: Running (http://localhost:$WEBUI_PORT)"
        elif docker ps -aq -f name="$webui_container" | grep -q .; then
            echo -e "  ${RED}✗${NC} WebUI Container: Stopped"
        else
            echo -e "  ${YELLOW}?${NC} WebUI Container: Not created"
        fi
    fi
    
    log_separator
}

# Show container logs
show_logs() {
    if [[ "$WORK_WITH_API" == true ]]; then
        local api_container=$(get_api_container_name)
        if docker ps -aq -f name="$api_container" | grep -q .; then
            log_info "API Container Logs:"
            if [[ "$FOLLOW" == true ]]; then
                docker logs -f "$api_container"
            else
                docker logs --tail 50 "$api_container"
            fi
        else
            log_warning "API container not found"
        fi
    fi
    
    if [[ "$WORK_WITH_WEBUI" == true ]]; then
        local webui_container=$(get_webui_container_name)
        if docker ps -aq -f name="$webui_container" | grep -q .; then
            log_info "WebUI Container Logs:"
            if [[ "$FOLLOW" == true ]]; then
                docker logs -f "$webui_container"
            else
                docker logs --tail 50 "$webui_container"
            fi
        else
            log_warning "WebUI container not found"
        fi
    fi
}

# Clean up containers and images
clean_containers() {
    log_separator
    log_warning "This will remove all containers and images for the User Management System"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Operation cancelled"
        return
    fi
    
    log_info "Cleaning up containers and images..."
    
    # Stop and remove containers
    if [[ "$WORK_WITH_API" == true ]]; then
        local api_container=$(get_api_container_name)
        docker stop "$api_container" 2>/dev/null || true
        docker rm "$api_container" 2>/dev/null || true
        docker rmi "${API_IMAGE_NAME}:${TAG}" 2>/dev/null || true
        docker rmi "${API_IMAGE_NAME}:latest" 2>/dev/null || true
    fi
    
    if [[ "$WORK_WITH_WEBUI" == true ]]; then
        local webui_container=$(get_webui_container_name)
        docker stop "$webui_container" 2>/dev/null || true
        docker rm "$webui_container" 2>/dev/null || true
        docker rmi "${WEBUI_IMAGE_NAME}:${TAG}" 2>/dev/null || true
        docker rmi "${WEBUI_IMAGE_NAME}:latest" 2>/dev/null || true
    fi
    
    log_success "Cleanup completed"
    log_separator
}

# Main function
main() {
    # Show header
    log_separator
    log_info "User Management System Docker Run Script"
    log_info "Timestamp: $(date)"
    log_separator
    
    # Parse arguments
    parse_args "$@"
    
    # Validate Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    # Execute command
    case "$COMMAND" in
        load)
            load_images
            ;;
        run)
            run_containers
            ;;
        stop)
            stop_containers
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        clean)
            clean_containers
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"