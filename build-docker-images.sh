#!/bin/bash

# Docker Build Script for User Management System
# Builds both API and WebUI Docker images and exports them as tar files

set -e  # Exit on any error

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
API_DIR="$PROJECT_ROOT/Api"
WEBUI_DIR="$PROJECT_ROOT/WebUI/user-management-app"
OUTPUT_DIR="$PROJECT_ROOT/docker-images"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Docker image names and tags
API_IMAGE_NAME="user-management-api"
WEBUI_IMAGE_NAME="user-management-webui"
DEFAULT_TAG="latest"
TIMESTAMPED_TAG="$TIMESTAMP"

# Build arguments for WebUI
DEFAULT_API_URL="http://localhost:8001"

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
User Management System Docker Build Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -h, --help              Show this help message
    -t, --tag TAG           Docker image tag (default: $DEFAULT_TAG)
    -a, --api-url URL       API URL for WebUI build (default: $DEFAULT_API_URL)
    -o, --output DIR        Output directory for tar files (default: $OUTPUT_DIR)
    --api-only              Build only the API image
    --webui-only            Build only the WebUI image
    --no-export             Don't export images to tar files
    --clean                 Clean existing images before building
    --verbose               Enable verbose output

EXAMPLES:
    $0                                          # Build both images with default settings
    $0 -t v1.0.0 -a https://api.myapp.com     # Build with custom tag and API URL
    $0 --api-only -t dev                       # Build only API with dev tag
    $0 --clean --verbose                       # Clean and build with verbose output

OUTPUT:
    Images will be saved as tar files in: $OUTPUT_DIR/
    - user-management-api_TAG.tar
    - user-management-webui_TAG.tar
EOF
}

# Parse command line arguments
parse_args() {
    TAG="$DEFAULT_TAG"
    API_URL="$DEFAULT_API_URL"
    BUILD_API=true
    BUILD_WEBUI=true
    EXPORT_IMAGES=true
    CLEAN_IMAGES=false
    VERBOSE=false

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
            -a|--api-url)
                API_URL="$2"
                shift 2
                ;;
            -o|--output)
                OUTPUT_DIR="$2"
                shift 2
                ;;
            --api-only)
                BUILD_API=true
                BUILD_WEBUI=false
                shift
                ;;
            --webui-only)
                BUILD_API=false
                BUILD_WEBUI=true
                shift
                ;;
            --no-export)
                EXPORT_IMAGES=false
                shift
                ;;
            --clean)
                CLEAN_IMAGES=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
}

# Validate environment
validate_environment() {
    log_info "Validating environment..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    # Check if directories exist
    if [[ "$BUILD_API" == true && ! -d "$API_DIR" ]]; then
        log_error "API directory not found: $API_DIR"
        exit 1
    fi
    
    if [[ "$BUILD_WEBUI" == true && ! -d "$WEBUI_DIR" ]]; then
        log_error "WebUI directory not found: $WEBUI_DIR"
        exit 1
    fi
    
    # Check for required files
    if [[ "$BUILD_API" == true && ! -f "$API_DIR/Dockerfile" ]]; then
        log_error "API Dockerfile not found: $API_DIR/Dockerfile"
        exit 1
    fi
    
    if [[ "$BUILD_WEBUI" == true && ! -f "$WEBUI_DIR/Dockerfile" ]]; then
        log_error "WebUI Dockerfile not found: $WEBUI_DIR/Dockerfile"
        exit 1
    fi
    
    log_success "Environment validation completed"
}

# Clean existing images
clean_images() {
    if [[ "$CLEAN_IMAGES" == true ]]; then
        log_info "Cleaning existing Docker images..."
        
        if [[ "$BUILD_API" == true ]]; then
            docker rmi "${API_IMAGE_NAME}:${TAG}" 2>/dev/null || true
            docker rmi "${API_IMAGE_NAME}:latest" 2>/dev/null || true
        fi
        
        if [[ "$BUILD_WEBUI" == true ]]; then
            docker rmi "${WEBUI_IMAGE_NAME}:${TAG}" 2>/dev/null || true
            docker rmi "${WEBUI_IMAGE_NAME}:latest" 2>/dev/null || true
        fi
        
        log_success "Image cleanup completed"
    fi
}

# Build API Docker image
build_api() {
    log_separator
    log_info "Building API Docker image..."
    log_info "  Directory: $API_DIR"
    log_info "  Image: ${API_IMAGE_NAME}:${TAG}"
    
    cd "$API_DIR"
    
    local build_cmd="docker build -t ${API_IMAGE_NAME}:${TAG} ."
    if [[ "$TAG" != "latest" ]]; then
        build_cmd="$build_cmd -t ${API_IMAGE_NAME}:latest"
    fi
    
    if [[ "$VERBOSE" == true ]]; then
        log_info "Running: $build_cmd"
    fi
    
    if [[ "$VERBOSE" == true ]]; then
        eval "$build_cmd"
    else
        eval "$build_cmd" > /dev/null 2>&1
    fi
    
    log_success "API image built successfully: ${API_IMAGE_NAME}:${TAG}"
}

# Build WebUI Docker image
build_webui() {
    log_separator
    log_info "Building WebUI Docker image..."
    log_info "  Directory: $WEBUI_DIR"
    log_info "  Image: ${WEBUI_IMAGE_NAME}:${TAG}"
    log_info "  API URL: $API_URL"
    
    cd "$WEBUI_DIR"
    
    local build_cmd="docker build --build-arg API_URL='$API_URL' -t ${WEBUI_IMAGE_NAME}:${TAG} ."
    if [[ "$TAG" != "latest" ]]; then
        build_cmd="$build_cmd -t ${WEBUI_IMAGE_NAME}:latest"
    fi
    
    if [[ "$VERBOSE" == true ]]; then
        log_info "Running: $build_cmd"
    fi
    
    if [[ "$VERBOSE" == true ]]; then
        eval "$build_cmd"
    else
        eval "$build_cmd" > /dev/null 2>&1
    fi
    
    log_success "WebUI image built successfully: ${WEBUI_IMAGE_NAME}:${TAG}"
}

# Export images to tar files
export_images() {
    if [[ "$EXPORT_IMAGES" == false ]]; then
        return
    fi
    
    log_separator
    log_info "Exporting Docker images to tar files..."
    log_info "  Output directory: $OUTPUT_DIR"
    
    # Create output directory
    mkdir -p "$OUTPUT_DIR"
    
    if [[ "$BUILD_API" == true ]]; then
        local api_tar_file="$OUTPUT_DIR/${API_IMAGE_NAME}_${TAG}.tar"
        log_info "Exporting API image to: $api_tar_file"
        
        if [[ "$VERBOSE" == true ]]; then
            docker save -o "$api_tar_file" "${API_IMAGE_NAME}:${TAG}"
        else
            docker save -o "$api_tar_file" "${API_IMAGE_NAME}:${TAG}" > /dev/null 2>&1
        fi
        
        log_success "API image exported: $api_tar_file ($(du -h "$api_tar_file" | cut -f1))"
    fi
    
    if [[ "$BUILD_WEBUI" == true ]]; then
        local webui_tar_file="$OUTPUT_DIR/${WEBUI_IMAGE_NAME}_${TAG}.tar"
        log_info "Exporting WebUI image to: $webui_tar_file"
        
        if [[ "$VERBOSE" == true ]]; then
            docker save -o "$webui_tar_file" "${WEBUI_IMAGE_NAME}:${TAG}"
        else
            docker save -o "$webui_tar_file" "${WEBUI_IMAGE_NAME}:${TAG}" > /dev/null 2>&1
        fi
        
        log_success "WebUI image exported: $webui_tar_file ($(du -h "$webui_tar_file" | cut -f1))"
    fi
}

# Display build summary
show_summary() {
    log_separator
    log_success "Build completed successfully!"
    
    echo ""
    log_info "BUILT IMAGES:"
    if [[ "$BUILD_API" == true ]]; then
        echo "  • ${API_IMAGE_NAME}:${TAG}"
        if [[ "$TAG" != "latest" ]]; then
            echo "  • ${API_IMAGE_NAME}:latest"
        fi
    fi
    
    if [[ "$BUILD_WEBUI" == true ]]; then
        echo "  • ${WEBUI_IMAGE_NAME}:${TAG}"
        if [[ "$TAG" != "latest" ]]; then
            echo "  • ${WEBUI_IMAGE_NAME}:latest"
        fi
    fi
    
    if [[ "$EXPORT_IMAGES" == true ]]; then
        echo ""
        log_info "EXPORTED TAR FILES:"
        if [[ "$BUILD_API" == true ]]; then
            echo "  • $OUTPUT_DIR/${API_IMAGE_NAME}_${TAG}.tar"
        fi
        if [[ "$BUILD_WEBUI" == true ]]; then
            echo "  • $OUTPUT_DIR/${WEBUI_IMAGE_NAME}_${TAG}.tar"
        fi
    fi
    
    echo ""
    log_info "NEXT STEPS:"
    echo "  • Load images: docker load -i <tar-file>"
    echo "  • Run API: docker run -p 8001:8001 ${API_IMAGE_NAME}:${TAG}"
    echo "  • Run WebUI: docker run -p 80:80 ${WEBUI_IMAGE_NAME}:${TAG}"
    echo "  • View images: docker images | grep -E '${API_IMAGE_NAME}|${WEBUI_IMAGE_NAME}'"
    
    log_separator
}

# Error handling
handle_error() {
    local exit_code=$?
    log_error "Build failed with exit code: $exit_code"
    log_error "Check the output above for details"
    exit $exit_code
}

# Main function
main() {
    # Set up error handling
    trap handle_error ERR
    
    # Show header
    log_separator
    log_info "User Management System Docker Build Script"
    log_info "Timestamp: $(date)"
    log_separator
    
    # Parse arguments
    parse_args "$@"
    
    # Show configuration
    log_info "BUILD CONFIGURATION:"
    echo "  • Tag: $TAG"
    echo "  • API URL: $API_URL"
    echo "  • Build API: $BUILD_API"
    echo "  • Build WebUI: $BUILD_WEBUI"
    echo "  • Export images: $EXPORT_IMAGES"
    echo "  • Clean images: $CLEAN_IMAGES"
    echo "  • Verbose: $VERBOSE"
    echo "  • Output directory: $OUTPUT_DIR"
    
    # Start build process
    validate_environment
    clean_images
    
    # Build images
    if [[ "$BUILD_API" == true ]]; then
        build_api
    fi
    
    if [[ "$BUILD_WEBUI" == true ]]; then
        build_webui
    fi
    
    # Export images
    export_images
    
    # Show summary
    show_summary
}

# Run main function with all arguments
main "$@"