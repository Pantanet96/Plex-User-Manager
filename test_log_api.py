"""
Test script for log API endpoints
Run this while the Flask app is running
"""
import requests

BASE_URL = "http://127.0.0.1:5000"

# You'll need to login first and get the session cookie
# For now, this is just a reference script

def test_get_logs():
    """Test GET /api/logs endpoint"""
    
    # Test 1: Get app logs
    response = requests.get(f"{BASE_URL}/api/logs?file=app&lines=10")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {data['count']} log entries")
        if data['logs']:
            print(f"First log: {data['logs'][0]}")
    
    # Test 2: Get error logs
    response = requests.get(f"{BASE_URL}/api/logs?file=error&lines=10")
    print(f"\nError logs status: {response.status_code}")
    
    # Test 3: Filter by level
    response = requests.get(f"{BASE_URL}/api/logs?file=app&level=INFO&lines=5")
    print(f"\nFiltered logs status: {response.status_code}")

def test_download_logs():
    """Test GET /api/logs/download endpoint"""
    response = requests.get(f"{BASE_URL}/api/logs/download?file=app")
    print(f"\nDownload status: {response.status_code}")
    if response.status_code == 200:
        print(f"Content-Type: {response.headers.get('Content-Type')}")

if __name__ == "__main__":
    print("Note: You need to be logged in to test these endpoints")
    print("Use browser dev tools or Postman with session cookies")
    # test_get_logs()
    # test_download_logs()
