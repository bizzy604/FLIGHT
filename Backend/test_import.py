#!/usr/bin/env python3
"""Test script to check if build_ordercreate_rq imports correctly"""

import sys
import os

# Add the scripts directory to the path
scripts_path = os.path.join(os.path.dirname(__file__), 'scripts')
sys.path.append(scripts_path)

try:
    from build_ordercreate_rq import generate_order_create_rq
    print("✅ Successfully imported generate_order_create_rq")
    print(f"Function type: {type(generate_order_create_rq)}")
    print(f"Function docstring: {generate_order_create_rq.__doc__[:100]}...")
except ImportError as e:
    print(f"❌ Failed to import: {e}")
    print(f"Scripts path: {scripts_path}")
    print(f"Scripts path exists: {os.path.exists(scripts_path)}")
    
    # List files in scripts directory
    if os.path.exists(scripts_path):
        print(f"Files in scripts directory: {os.listdir(scripts_path)}")
    
    # Check if the specific file exists
    build_file = os.path.join(scripts_path, 'build_ordercreate_rq.py')
    print(f"build_ordercreate_rq.py exists: {os.path.exists(build_file)}")
