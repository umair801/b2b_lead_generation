# tests/test_supabase.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client
from config import settings
from loguru import logger

def test_connection() -> None:
    try:
        client = create_client(settings.supabase_url, settings.supabase_key)
        response = client.table("leads").select("count", count="exact").execute()
        logger.success(f"Supabase connected. Leads table row count: {response.count}")
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        raise

if __name__ == "__main__":
    test_connection()