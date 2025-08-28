# This file is deprecated. Use the database repository pattern instead.
# Import from database package: from database import get_repository

import logging
from supabase import create_client, Client
import os

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

def get_supabase_client() -> Client:
    """
    Initializes and returns a Supabase client for data storage only.
    
    DEPRECATED: This function is deprecated. Use get_repository() from the database package instead.
    """
    logger.warning("get_supabase_client() is deprecated. Use get_repository() from database package instead.")
    
    url: str = os.environ.get("SUPABASE_URL")
    service_key: str = os.environ.get("SUPABASE_SERVICE_KEY")

    if not url or not service_key:
        raise ValueError("Supabase URL or Service Key not found in environment variables.")

    # Using service_key for direct database access only (no auth features)
    return create_client(url, service_key)

# DEPRECATED: Use get_repository() from database package instead
supabase: Client = get_supabase_client()

# For new code, use this:
# from database import get_repository
# repo = get_repository()
