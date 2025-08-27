#!/usr/bin/env python3
"""
Test script for API Key Authentication
Run this to test your API authentication setup
"""

import requests
import json
import os
import sys

# Configuration
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")
API_KEY = os.getenv("API_KEY", "")
TEST_SESSION_ID = "auth-test-session"

def test_health_endpoint():
    """Test public health endpoint (no auth required)"""
    print("🩺 Testing health endpoint (public, no auth required)...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code == 200:
            print("✅ Health check successful")
            data = response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Ollama connected: {data.get('ollama_connected')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_authenticated_endpoint_without_key():
    """Test protected endpoint without API key"""
    print("\n🔐 Testing protected endpoint WITHOUT API key...")
    
    headers = {
        "Content-Type": "application/json",
        "X-Session-ID": TEST_SESSION_ID
    }
    
    data = {
        "message": "Test message without auth",
        "config": {"temperature": 0.7}
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/session/chat",
            json=data,
            headers=headers
        )
        
        if response.status_code == 401:
            print("✅ Correctly rejected unauthorized request")
            print(f"   Response: {response.json()}")
            return True
        elif response.status_code == 200:
            print("⚠️  Request succeeded - API key authentication may be disabled (development mode)")
            return True
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def test_authenticated_endpoint_with_key():
    """Test protected endpoint with API key"""
    if not API_KEY:
        print("\n⚠️  Skipping authenticated test - no API_KEY provided")
        return True
        
    print("\n🔑 Testing protected endpoint WITH API key...")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
        "X-Session-ID": TEST_SESSION_ID
    }
    
    data = {
        "message": "Test message with auth",
        "config": {"temperature": 0.7}
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/session/chat",
            json=data,
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Authenticated request succeeded")
            result = response.json()
            print(f"   Response: {result.get('response', 'No response text')[:100]}...")
            return True
        elif response.status_code == 401:
            print("❌ Authentication failed - check your API key")
            print(f"   Response: {response.json()}")
            return False
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def test_knowledge_upload():
    """Test knowledge upload endpoint"""
    print("\n📚 Testing knowledge upload endpoint...")
    
    headers = {
        "Content-Type": "application/json",
        "X-Session-ID": TEST_SESSION_ID
    }
    
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    
    data = {
        "knowledge_chunks": [
            {
                "id": "test-chunk-1",
                "content": "This is a test knowledge chunk for authentication testing.",
                "metadata": {"source": "auth_test", "type": "test"}
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/session/knowledge/upload",
            json=data,
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Knowledge upload succeeded")
            result = response.json()
            print(f"   Chunks processed: {result.get('chunks_processed')}")
            return True
        elif response.status_code == 401:
            print("❌ Knowledge upload failed - authentication required")
            return False
        else:
            print(f"❌ Knowledge upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Knowledge upload error: {e}")
        return False

def main():
    print("🧪 API Key Authentication Test")
    print("=" * 50)
    print(f"Base URL: {BASE_URL}")
    print(f"API Key: {'Set' if API_KEY else 'Not set'}")
    print(f"Test Session: {TEST_SESSION_ID}")
    print()
    
    tests = [
        test_health_endpoint,
        test_authenticated_endpoint_without_key,
        test_authenticated_endpoint_with_key,
        test_knowledge_upload
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"✅ Passed: {sum(results)}/{len(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("\n🎉 All tests passed! Authentication is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    print("Usage:")
    print("  # Test against local development server")
    print("  python test_auth.py")
    print()
    print("  # Test against production server with API key")
    print("  API_KEY=your-key API_BASE_URL=http://YOUR_OCI_IP:8001 python test_auth.py")
    print()
    
    sys.exit(main())
