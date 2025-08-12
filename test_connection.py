#!/usr/bin/env python3
"""
Connection test script for Flight Booking Portal
Tests backend-frontend connectivity
"""
import asyncio
import json
import sys
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent / "Backend"))

async def test_backend_health():
    """Test if backend health endpoint responds"""
    try:
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:5000/api/health') as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Backend Health Check: PASSED")
                    print(f"   Response: {data}")
                    return True
                else:
                    print(f"❌ Backend Health Check: FAILED (Status: {response.status})")
                    return False
    except Exception as e:
        print(f"❌ Backend Health Check: FAILED (Error: {e})")
        return False

async def test_frontend_api():
    """Test if frontend API routes work"""
    try:
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            # Test Next.js health endpoint
            async with session.get('http://localhost:3000/api/health') as response:
                if response.status == 200:
                    print("✅ Frontend API Routes: PASSED")
                    return True
                else:
                    print(f"❌ Frontend API Routes: FAILED (Status: {response.status})")
                    return False
    except Exception as e:
        print(f"❌ Frontend API Routes: FAILED (Error: {e})")
        return False

async def test_cors_headers():
    """Test CORS headers from backend"""
    try:
        import aiohttp
        
        headers = {
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'content-type'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.options('http://localhost:5000/api/health', headers=headers) as response:
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                }
                
                if cors_headers['Access-Control-Allow-Origin']:
                    print("✅ CORS Configuration: PASSED")
                    print(f"   CORS Headers: {json.dumps(cors_headers, indent=4)}")
                    return True
                else:
                    print("❌ CORS Configuration: FAILED")
                    print(f"   Missing CORS headers in response")
                    return False
    except Exception as e:
        print(f"❌ CORS Configuration: FAILED (Error: {e})")
        return False

async def test_environment_config():
    """Test environment configuration"""
    print("🔧 Environment Configuration:")
    
    # Check backend env
    backend_env_path = Path(__file__).parent / "Backend" / ".env"
    if backend_env_path.exists():
        print("   ✅ Backend .env file exists")
    else:
        print("   ❌ Backend .env file missing")
        return False
    
    # Check frontend env
    frontend_env_path = Path(__file__).parent / "Frontend" / ".env"
    if frontend_env_path.exists():
        print("   ✅ Frontend .env file exists")
        
        # Check API base URL
        with open(frontend_env_path, 'r') as f:
            content = f.read()
            if 'NEXT_PUBLIC_API_BASE_URL=http://localhost:5000' in content:
                print("   ✅ Frontend API base URL correctly configured")
                return True
            else:
                print("   ⚠️  Frontend API base URL may need verification")
                return True
    else:
        print("   ❌ Frontend .env file missing")
        return False

def print_connection_summary():
    """Print connection setup summary"""
    print("="*60)
    print("🔗 Flight Booking Portal - Connection Setup")
    print("="*60)
    print("📋 Architecture Overview:")
    print("   🔧 Backend (Python/Quart):  http://localhost:5000")
    print("   ⚛️  Frontend (Next.js):      http://localhost:3000")
    print("   🔄 Connection Flow: Frontend → Next.js API → Backend")
    print("="*60)
    print("🧪 Running Connection Tests...")
    print("="*60)

async def main():
    """Main test runner"""
    print_connection_summary()
    
    # Install aiohttp if not available
    try:
        import aiohttp
    except ImportError:
        print("Installing aiohttp for testing...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "aiohttp"])
        import aiohttp
    
    tests = [
        ("Environment Configuration", test_environment_config),
        ("Backend Health Check", test_backend_health),
        ("Frontend API Routes", test_frontend_api),
        ("CORS Configuration", test_cors_headers),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Testing {test_name}...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}: ERROR ({e})")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Results Summary:")
    print("="*60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print("="*60)
    print(f"📈 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All connection tests passed! Backend and frontend are properly connected.")
    else:
        print("⚠️  Some tests failed. Check the configuration above.")
        print("\n💡 Troubleshooting Tips:")
        print("   1. Make sure both backend and frontend services are running")
        print("   2. Check .env files for correct configuration") 
        print("   3. Verify CORS settings in backend/config.py")
        print("   4. Ensure ports 3000 and 5000 are available")

if __name__ == "__main__":
    asyncio.run(main())