#!/bin/bash

# Database Tools for User Management System
# Convenience wrapper for database management scripts

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_CMD="python3"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}🗄️  User Management System - Database Tools${NC}"
    echo "=================================================="
}

print_usage() {
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  setup [filename] [--schema SCHEMA]     Generate database setup SQL script"
    echo "  inspect [connection_string]            Inspect existing database structure"
    echo "  export [format] [options]              Export database data"
    echo "  quick-setup [--schema SCHEMA]          Generate and show setup instructions"
    echo "  help                                   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup                                         # Generate in public schema"
    echo "  $0 setup --schema user_mgmt                      # Generate in user_mgmt schema"
    echo "  $0 setup my_db_setup.sql --schema company_data   # Custom file and schema"
    echo "  $0 inspect                                       # Use environment variables"
    echo "  $0 inspect \"postgresql://user:pass@host/db\"      # Use connection string"
    echo "  $0 export json                                   # Export as JSON"
    echo "  $0 export all --output /tmp/exports              # Export all formats"
    echo "  $0 quick-setup --schema test_env                 # Quick setup with custom schema"
    echo ""
    echo "Environment Variables:"
    echo "  DATABASE_URL or SUPABASE_URL  Database connection string"
    echo "  DB_HOST, DB_USER, DB_PASSWORD Individual connection parameters"
}

check_dependencies() {
    if ! command -v $PYTHON_CMD &> /dev/null; then
        echo -e "${RED}❌ Python 3 not found${NC}"
        echo "Please install Python 3 and try again"
        exit 1
    fi
    
    if [[ "$1" == "inspect" ]] || [[ "$1" == "export" ]]; then
        if ! $PYTHON_CMD -c "import asyncpg" 2>/dev/null; then
            echo -e "${YELLOW}⚠️  asyncpg not installed${NC}"
            echo "Installing asyncpg for database operations..."
            pip install asyncpg || {
                echo -e "${RED}❌ Failed to install asyncpg${NC}"
                echo "Please install manually: pip install asyncpg"
                exit 1
            }
        fi
    fi
}

run_setup() {
    print_header
    echo -e "${GREEN}🔧 Generating database setup script...${NC}"
    echo ""
    
    check_dependencies "setup"
    
    # Pass all arguments to the Python script
    $PYTHON_CMD "$SCRIPT_DIR/generate_database_setup.py" "$@"
}

run_inspect() {
    print_header
    echo -e "${GREEN}🔍 Inspecting database structure...${NC}"
    echo ""
    
    check_dependencies "inspect"
    
    if [[ -n "$1" ]]; then
        $PYTHON_CMD "$SCRIPT_DIR/inspect_database.py" "$1"
    else
        $PYTHON_CMD "$SCRIPT_DIR/inspect_database.py"
    fi
}

run_export() {
    print_header
    echo -e "${GREEN}📤 Exporting database data...${NC}"
    echo ""
    
    check_dependencies "export"
    
    local format="${1:-sql}"
    shift || true
    
    $PYTHON_CMD "$SCRIPT_DIR/export_database_data.py" --format "$format" "$@"
}

run_quick_setup() {
    print_header
    echo -e "${GREEN}🚀 Quick Database Setup${NC}"
    echo ""
    
    check_dependencies "setup"
    
    # Parse schema from arguments
    local schema_arg=""
    for arg in "$@"; do
        if [[ "$arg" == "--schema" ]]; then
            shift
            schema_arg="--schema $1"
            break
        fi
    done
    
    # Generate setup script
    local setup_file="quick_setup_$(date +%Y%m%d_%H%M%S).sql"
    echo "Generating setup script: $setup_file"
    if [[ -n "$schema_arg" ]]; then
        echo "Using schema: $(echo $schema_arg | cut -d' ' -f2)"
        $PYTHON_CMD "$SCRIPT_DIR/generate_database_setup.py" "$setup_file" $schema_arg
    else
        $PYTHON_CMD "$SCRIPT_DIR/generate_database_setup.py" "$setup_file"
    fi
    
    echo ""
    echo -e "${BLUE}📋 Setup Instructions:${NC}"
    echo ""
    echo "1. Create your database:"
    echo "   createdb your_database_name"
    echo ""
    echo "2. Apply the setup script:"
    echo "   psql -d your_database_name -f $setup_file"
    echo ""
    echo "3. Verify the setup:"
    echo "   $0 inspect \"postgresql://user:pass@host:port/your_database_name\""
    echo ""
    echo -e "${YELLOW}⚠️  Default Credentials:${NC}"
    echo "   Email: admin@example.com"
    echo "   Password: admin123"
    echo "   ${RED}IMPORTANT: Change these in production!${NC}"
    echo ""
    echo -e "${BLUE}🔗 Connection Examples:${NC}"
    echo "   Local:    postgresql://postgres@localhost:5432/your_db"
    echo "   Remote:   postgresql://user:pass@host:5432/database"
    echo "   Supabase: postgresql://postgres:pass@host:5432/postgres"
}

# Main script logic
case "${1:-help}" in
    "setup")
        shift
        run_setup "$@"
        ;;
    "inspect")
        shift
        run_inspect "$@"
        ;;
    "export")
        shift
        run_export "$@"
        ;;
    "quick-setup")
        run_quick_setup
        ;;
    "help"|"-h"|"--help")
        print_header
        echo ""
        print_usage
        ;;
    *)
        print_header
        echo ""
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo ""
        print_usage
        exit 1
        ;;
esac