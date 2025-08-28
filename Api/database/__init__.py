import os
import logging
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

from .base_repository import BaseRepository
from .supabase_repository import SupabaseRepository
from .postgres_repository import PostgresRepository

load_dotenv()
logger = logging.getLogger(__name__)


class RepositoryFactory:
    """Factory class for creating database repository instances."""
    
    _instance: Optional[BaseRepository] = None
    
    @classmethod
    def get_repository(cls) -> BaseRepository:
        """Get or create a repository instance based on configuration."""
        if cls._instance is None:
            cls._instance = cls._create_repository()
        return cls._instance
    
    @classmethod
    def _create_repository(cls) -> BaseRepository:
        """Create repository instance based on DATABASE_PROVIDER environment variable."""
        provider = os.environ.get("DATABASE_PROVIDER", "supabase").lower()
        
        if provider == "supabase":
            return cls._create_supabase_repository()
        elif provider == "postgres":
            return cls._create_postgres_repository()
        else:
            logger.warning(f"Unknown database provider '{provider}', falling back to Supabase")
            return cls._create_supabase_repository()
    
    @classmethod
    def _create_supabase_repository(cls) -> SupabaseRepository:
        """Create Supabase repository instance."""
        url = os.environ.get("SUPABASE_URL")
        service_key = os.environ.get("SUPABASE_SERVICE_KEY")
        
        if not url or not service_key:
            raise ValueError("Supabase URL or Service Key not found in environment variables.")
        
        # Using service_key for direct database access only (no auth features)
        supabase_client = create_client(url, service_key)
        return SupabaseRepository(supabase_client)
    
    @classmethod
    def _create_postgres_repository(cls) -> PostgresRepository:
        """Create PostgreSQL repository instance."""
        connection_string = os.environ.get("POSTGRES_CONNECTION_STRING")
        
        if not connection_string:
            # Build connection string from individual components
            host = os.environ.get("POSTGRES_HOST", "localhost")
            port = os.environ.get("POSTGRES_PORT", "5432")
            database = os.environ.get("POSTGRES_DB", "postgres")
            user = os.environ.get("POSTGRES_USER", "postgres")
            password = os.environ.get("POSTGRES_PASSWORD", "")
            
            if not password:
                raise ValueError("PostgreSQL connection details not found in environment variables.")
            
            connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        
        return PostgresRepository(connection_string)
    
    @classmethod
    def reset(cls):
        """Reset the singleton instance. Useful for testing."""
        cls._instance = None


# Convenience function to get repository
def get_repository() -> BaseRepository:
    """Get the database repository instance."""
    return RepositoryFactory.get_repository()


# For backward compatibility with existing imports
def get_supabase_client() -> Client:
    """
    Get Supabase client for backward compatibility.
    
    NOTE: This function is deprecated and will be removed in future versions.
    Use get_repository() instead.
    """
    logger.warning("get_supabase_client() is deprecated. Use get_repository() instead.")
    
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY")
    
    if not url or not service_key:
        raise ValueError("Supabase URL or Service Key not found in environment variables.")
    
    return create_client(url, service_key)


# Keep the global supabase client for backward compatibility
# This will be removed in future versions
try:
    supabase = get_supabase_client()
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    supabase = None