#!/usr/bin/env python3
"""
API Logging Management Script

This script helps manage API request/response logging for debugging purposes.
"""
import os
import sys
import argparse
from pathlib import Path

# Add the Backend directory to Python path so we can import utils
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, skip loading

def enable_logging():
    """Enable API logging by setting environment variable."""
    print("Enabling API logging...")
    
    # For current session
    os.environ['API_DEBUG_LOGGING'] = 'true'
    
    # Create/update .env file for persistence
    env_file = Path('.env')
    env_lines = []
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_lines = f.readlines()
    
    # Remove existing API_DEBUG_LOGGING line if present
    env_lines = [line for line in env_lines if not line.startswith('API_DEBUG_LOGGING=')]
    
    # Add the new setting
    env_lines.append('API_DEBUG_LOGGING=true\n')
    
    with open(env_file, 'w') as f:
        f.writelines(env_lines)
    
    print("[SUCCESS] API logging enabled!")
    print("Logs will be written to: api_logs/")
    print("Restart your application to apply changes.")

def disable_logging():
    """Disable API logging by removing/setting environment variable."""
    print("Disabling API logging...")
    
    # For current session
    os.environ.pop('API_DEBUG_LOGGING', None)
    
    # Update .env file
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_lines = f.readlines()
        
        # Remove API_DEBUG_LOGGING line
        env_lines = [line for line in env_lines if not line.startswith('API_DEBUG_LOGGING=')]
        
        with open(env_file, 'w') as f:
            f.writelines(env_lines)
    
    print("[SUCCESS] API logging disabled!")
    print("Restart your application to apply changes.")

def status():
    """Show current logging status."""
    is_enabled = os.getenv('API_DEBUG_LOGGING', 'false').lower() in ('true', '1', 'yes', 'on')
    
    print(f"API Logging Status: {'[ENABLED]' if is_enabled else '[DISABLED]'}")
    
    if is_enabled:
        logs_dir = Path('api_logs')
        if logs_dir.exists():
            # Count log files
            air_shopping_logs = len(list((logs_dir / 'air_shopping').glob('*.json'))) if (logs_dir / 'air_shopping').exists() else 0
            flight_price_logs = len(list((logs_dir / 'flight_price').glob('*.json'))) if (logs_dir / 'flight_price').exists() else 0
            booking_logs = len(list((logs_dir / 'booking').glob('*.json'))) if (logs_dir / 'booking').exists() else 0
            service_list_logs = len(list((logs_dir / 'service_list').glob('*.json'))) if (logs_dir / 'service_list').exists() else 0
            seat_availability_logs = len(list((logs_dir / 'seat_availability').glob('*.json'))) if (logs_dir / 'seat_availability').exists() else 0
            
            print(f"Logs directory: {logs_dir.absolute()}")
            print(f"Log files:")
            print(f"   - Air Shopping: {air_shopping_logs} files")
            print(f"   - Flight Price: {flight_price_logs} files")
            print(f"   - Booking: {booking_logs} files")
            print(f"   - Service List: {service_list_logs} files")
            print(f"   - Seat Availability: {seat_availability_logs} files")
        else:
            print("Logs directory: Not created yet (will be created on first API call)")

def cleanup_logs(days=7):
    """Clean up old log files."""
    try:
        from utils.api_logger import api_logger
        print(f"Cleaning up log files older than {days} days...")
        api_logger.cleanup_old_logs(days_to_keep=days)
        print("✅ Cleanup completed!")
    except ImportError:
        # Fallback implementation if import fails
        print(f"Cleaning up log files older than {days} days...")
        _cleanup_logs_fallback(days)
        print("✅ Cleanup completed!")

def _cleanup_logs_fallback(days_to_keep=7):
    """Fallback cleanup implementation."""
    import time
    from datetime import datetime

    logs_dir = Path('api_logs')
    if not logs_dir.exists():
        print("📁 No logs directory found.")
        return

    try:
        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
        cleaned_count = 0

        for log_file in logs_dir.rglob("*.json"):
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
                cleaned_count += 1
                print(f"🗑️  Removed: {log_file.name}")

        if cleaned_count == 0:
            print(f"📁 No log files older than {days_to_keep} days found.")
        else:
            print(f"🗑️  Removed {cleaned_count} old log files.")

    except Exception as e:
        print(f"❌ Failed to cleanup logs: {e}")

def main():
    parser = argparse.ArgumentParser(description='Manage API request/response logging')
    parser.add_argument('action', choices=['enable', 'disable', 'status', 'cleanup'], 
                       help='Action to perform')
    parser.add_argument('--days', type=int, default=7, 
                       help='Days to keep logs (for cleanup action)')
    
    args = parser.parse_args()
    
    if args.action == 'enable':
        enable_logging()
    elif args.action == 'disable':
        disable_logging()
    elif args.action == 'status':
        status()
    elif args.action == 'cleanup':
        cleanup_logs(args.days)

if __name__ == '__main__':
    main()
