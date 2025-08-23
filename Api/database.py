from supabase import create_client, Client
import os

from dotenv import load_dotenv
load_dotenv()

def get_supabase_client() -> Client:
    """Initializes and returns a Supabase client for data storage only."""
    url: str = os.environ.get("SUPABASE_URL")
    service_key: str = os.environ.get("SUPABASE_SERVICE_KEY")

    if not url or not service_key:
        raise ValueError("Supabase URL or Service Key not found in environment variables.")

    # Using service_key for direct database access only (no auth features)
    return create_client(url, service_key)

supabase: Client = get_supabase_client()
