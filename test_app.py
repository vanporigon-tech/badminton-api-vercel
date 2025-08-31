#!/usr/bin/env python3
"""
Simple test script for Badminton Rating Mini App
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Health check: {response.status_code}")
        print(f"Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_api_endpoints():
    """Test basic API endpoints"""
    endpoints = [
        ("GET", "/"),
        ("GET", "/health"),
    ]
    
    for method, endpoint in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}")
            else:
                response = requests.post(f"{BASE_URL}{endpoint}")
            
            print(f"✅ {method} {endpoint}: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
                except:
                    print(f"   Response: {response.text[:100]}...")
            
        except Exception as e:
            print(f"❌ {method} {endpoint} failed: {e}")

def test_mini_app_page():
    """Test Mini App HTML page"""
    try:
        response = requests.get(f"{BASE_URL}/app")
        print(f"✅ Mini App page: {response.status_code}")
        
        if response.status_code == 200:
            html = response.text
            if "Badminton Rating" in html and "🏸" in html:
                print("   ✅ HTML content looks good")
            else:
                print("   ⚠️ HTML content might be incomplete")
        else:
            print(f"   ❌ Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Mini App page test failed: {e}")

def main():
    """Run all tests"""
    print("🧪 Testing Badminton Rating Mini App...")
    print("=" * 50)
    
    # Test basic functionality
    if not test_health():
        print("❌ Basic health check failed. Is the server running?")
        return
    
    print("\n📊 Testing API endpoints...")
    test_api_endpoints()
    
    print("\n📱 Testing Mini App page...")
    test_mini_app_page()
    
    print("\n" + "=" * 50)
    print("🎉 Testing completed!")
    print("\nTo start the server, run:")
    print("  python run.py")
    print("\nOr:")
    print("  uvicorn main:app --reload")

if __name__ == "__main__":
    main()

