#!/usr/bin/env python3
"""
Test script for VSCode authentication flow
Run this to verify the API server is working correctly
"""

import requests
import json
import os

def test_api_server():
    """Test basic API server connectivity"""
    try:
        response = requests.get('http://127.0.0.1:5000/health', timeout=5)
        print(f"✅ API Server health check: {response.status_code} - {response.json()}")
        return True
    except Exception as e:
        print(f"❌ API Server not reachable: {e}")
        return False

def test_vscode_auth_flow():
    """Test the VSCode authentication flow"""
    try:
        # Step 1: Request a session ID (what VSCode extension does)
        print("\n🔄 Testing VSCode auth flow...")
        response = requests.get('http://127.0.0.1:5000/vscode-auth', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Session generation: {data}")
            
            if 'session_id' in data:
                session_id = data['session_id']
                print(f"📋 Session ID: {session_id}")
                
                # Step 2: Check session status
                status_response = requests.get(
                    f'http://127.0.0.1:5000/vscode-auth-status?session_id={session_id}',
                    timeout=5
                )
                print(f"📊 Session status: {status_response.json()}")
                
                return session_id
            else:
                print(f"❌ No session_id in response")
                return None
        else:
            print(f"❌ Session generation failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ VSCode auth flow test failed: {e}")
        return None

def test_analytics():
    """Test analytics endpoint"""
    try:
        # Set development mode for testing
        os.environ['DEVELOPMENT_MODE'] = 'true'
        
        response = requests.get(
            'http://127.0.0.1:5000/analytics',
            headers={'X-Test-User': 'testuser01'},
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"✅ Analytics endpoint: {response.json()}")
        else:
            print(f"❌ Analytics failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Analytics test failed: {e}")

def main():
    print("🧪 Testing CS 15 Tutor Authentication System")
    print("=" * 50)
    
    # Test 1: API Server connectivity
    if not test_api_server():
        print("\n❌ API Server is not running. Please start it with:")
        print("   cd responses-api-server && python index.py")
        return
    
    # Test 2: VSCode auth flow
    session_id = test_vscode_auth_flow()
    
    # Test 3: Analytics (with development mode)
    test_analytics()
    
    print("\n" + "=" * 50)
    if session_id:
        print("✅ Tests completed successfully!")
        print(f"🔗 Test login URL: http://127.0.0.1:3000/vscode-auth?session_id={session_id}")
        print("\nTo test the full flow:")
        print("1. Ensure the Next.js web app is running on port 3000")
        print("2. Open the login URL above in a browser")
        print("3. The authentication should work if .htaccess is configured")
    else:
        print("❌ Some tests failed. Check the API server logs for details.")

if __name__ == "__main__":
    main() 