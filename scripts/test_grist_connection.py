#!/usr/bin/env python3
"""
Test Grist Connection

Quick script to verify connectivity to Grist instances.

Usage:
    uv run python test_grist_connection.py --env test
    uv run python test_grist_connection.py --env dev
"""

import argparse
import sys

import requests

from config import Config, get_config


def test_connection(env: str):
    """Test connection to Grist instance."""
    config = get_config(env)
    
    print(f"\n{'='*60}")
    print(f"Testing Grist Connection - Environment: {env}")
    print(f"{'='*60}")
    print(f"URL: {config.url}")
    print(f"Doc ID: {config.doc_id if config.doc_id else 'NOT SET'}")
    print(f"API Key: {'*' * 10}{config.api_key[-4:] if config.api_key else 'NOT SET'}")
    
    if not config.api_key or not config.doc_id:
        print("\n❌ Missing API key or Doc ID")
        return False
    
    # Test API connection
    base_url = config.url.rstrip('/')
    api_url = f"{base_url}/api/docs/{config.doc_id}/tables"
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }
    
    print(f"\nConnecting to: {api_url}")
    
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            tables = data.get("tables", [])
            print(f"\n✅ Connection successful!")
            print(f"   Found {len(tables)} tables:")
            for table in tables:
                print(f"   - {table.get('id')}")
            return True
        elif response.status_code == 401:
            print(f"\n❌ Authentication failed (401)")
            print("   Check your API key")
            return False
        elif response.status_code == 404:
            print(f"\n❌ Document not found (404)")
            print("   Check your Doc ID")
            return False
        else:
            print(f"\n❌ Error: HTTP {response.status_code}")
            print(f"   {response.text}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ Connection failed")
        print(f"   Error: {e}")
        print(f"\n   Possible causes:")
        print(f"   - Grist server is not running")
        print(f"   - URL is incorrect")
        print(f"   - Network/firewall issue")
        return False
    except requests.exceptions.Timeout:
        print(f"\n❌ Connection timed out")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test Grist connection")
    parser.add_argument(
        "--env",
        choices=["dev", "test", "production"],
        default="test",
        help="Environment to test (default: test)",
    )
    args = parser.parse_args()
    
    success = test_connection(args.env)
    
    print(f"\n{'='*60}")
    if success:
        print("✅ Grist connection test PASSED")
    else:
        print("❌ Grist connection test FAILED")
    print(f"{'='*60}\n")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
