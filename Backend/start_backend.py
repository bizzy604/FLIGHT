#!/usr/bin/env python3
"""
Backend startup script for Flight Booking Portal
"""
import os
import sys
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def setup_logging():
    """Configure logging for development"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('backend.log')
        ]
    )

def check_environment():
    """Check if required environment variables are set"""
    required_vars = [
        'VERTEIL_API_BASE_URL',
        'VERTEIL_USERNAME', 
        'VERTEIL_PASSWORD',
        'VERTEIL_OFFICE_ID',
        'VERTEIL_THIRD_PARTY_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease check your .env file in the Backend directory")
        return False
    
    print("Environment variables configured")
    return True

def check_dependencies():
    """Check if required dependencies are available"""
    try:
        import quart
        import quart_cors
        import redis
        print("Core dependencies available")
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False

async def start_backend():
    """Start the backend server"""
    try:
        # Import app after path is set up
        from app import create_app
        
        app = create_app()
        
        print("Starting Flight Booking Backend...")
        print("Server will be available at: http://localhost:5000")
        print("Health check: http://localhost:5000/api/health")
        print("API endpoints:")
        print("   - POST /api/verteil/air-shopping (Flight search)")
        print("   - POST /api/verteil/flight-price (Flight pricing)")
        print("   - POST /api/verteil/order-create (Flight booking)")
        print("   - GET /api/airports (Airport data)")
        print("\n" + "="*50)
        
        # Set environment for development
        os.environ['QUART_ENV'] = 'development'
        
        # Run the app
        await app.run_task(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False
        )
        
    except Exception as e:
        print(f"Failed to start backend: {e}")
        sys.exit(1)

def main():
    """Main entry point"""
    print("Flight Booking Portal - Backend Startup")
    print("="*50)
    
    # Load environment variables first
    env_path = Path(__file__).parent / '.env'
    load_dotenv(env_path)
    print(f"Loaded environment from: {env_path}")
    
    setup_logging()
    
    # Perform checks
    if not check_dependencies():
        sys.exit(1)
        
    if not check_environment():
        sys.exit(1)
    
    # Start the server
    try:
        asyncio.run(start_backend())
    except KeyboardInterrupt:
        print("\nBackend server stopped")
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()