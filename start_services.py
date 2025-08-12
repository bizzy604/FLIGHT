#!/usr/bin/env python3
"""
Unified startup script for Flight Booking Portal
Starts both backend and frontend services
"""
import os
import sys
import time
import subprocess
import signal
import threading
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent

def run_backend():
    """Run the backend server"""
    print("🔧 Starting Backend (Python Quart)...")
    backend_dir = PROJECT_ROOT / "Backend"
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    try:
        # Run the backend using the startup script
        subprocess.run([sys.executable, "start_backend.py"], cwd=backend_dir)
    except KeyboardInterrupt:
        print("\n🛑 Backend stopped")

def run_frontend():
    """Run the frontend server"""
    print("⚛️  Starting Frontend (Next.js)...")
    frontend_dir = PROJECT_ROOT / "Frontend"
    
    # Wait a bit for backend to start
    time.sleep(3)
    
    # Change to frontend directory
    os.chdir(frontend_dir)
    
    try:
        # Run the frontend dev server
        subprocess.run(["npm", "run", "dev"], cwd=frontend_dir)
    except KeyboardInterrupt:
        print("\n🛑 Frontend stopped")

def print_startup_info():
    """Print startup information"""
    print("🚀 Flight Booking Portal - Full Stack Startup")
    print("="*60)
    print("📋 Services Starting:")
    print("   🔧 Backend (Python/Quart):  http://localhost:5000")
    print("   ⚛️  Frontend (Next.js):      http://localhost:3000")
    print("="*60)
    print("🏥 Health Checks:")
    print("   Backend:  http://localhost:5000/api/health")
    print("   Frontend: http://localhost:3000")
    print("="*60)
    print("📊 Key Features:")
    print("   ✈️  Flight Search & Booking")
    print("   💳 Payment Processing (Stripe)")
    print("   👤 User Authentication (Clerk)")
    print("   📱 Responsive Design")
    print("="*60)
    print("⚠️  Press Ctrl+C to stop all services")
    print("="*60)

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n👋 Shutting down all services...")
    sys.exit(0)

def main():
    """Main entry point"""
    print_startup_info()
    
    # Handle Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start backend in a separate thread
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    backend_thread.start()
    
    # Start frontend in main thread
    try:
        run_frontend()
    except KeyboardInterrupt:
        print("\n👋 All services stopped")

if __name__ == "__main__":
    main()