from supabase import create_client, Client
import os

from dotenv import load_dotenv
load_dotenv()

def get_supabase_client() -> Client:
    """Initializes and returns a Supabase client."""
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    service_key: str = os.environ.get("SUPABASE_SERVICE_KEY") # Use service key for admin operations

    if not url or not key or not service_key:
        raise ValueError("Supabase URL, Key, or Service Key not found in environment variables.")

    # For operations requiring elevated privileges (e.g., creating users without signup)
    # or bypassing RLS for admin tasks, use the service_key.
    # For regular user operations, the anon key is sufficient.
    return create_client(url, service_key) # Using service_key for direct admin access

supabase: Client = get_supabase_client()
