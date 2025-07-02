#!/usr/bin/env python3
"""
Test script to check if the import works in the same context as the booking service.
"""

import sys
import os

# Add the same paths that the booking service uses
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

def test_import():
    """Test the import exactly like the booking service does."""
    
    print("=== Testing Import in Booking Service Context ===")
    
    try:
        # This is exactly how the booking service imports
        from scripts.build_ordercreate_rq import generate_order_create_rq
        print("✅ Import successful using 'from scripts.build_ordercreate_rq import generate_order_create_rq'")
        print(f"Function type: {type(generate_order_create_rq)}")
        print(f"Function module: {generate_order_create_rq.__module__}")
        print(f"Function file: {generate_order_create_rq.__code__.co_filename}")
        
        # Test if the function is callable
        if callable(generate_order_create_rq):
            print("✅ Function is callable")
        else:
            print("❌ Function is not callable")
            
        return generate_order_create_rq
        
    except ImportError as e:
        print(f"❌ ImportError: {e}")
        return None
    except Exception as e:
        print(f"❌ Other error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_alternative_import():
    """Test alternative import methods."""
    
    print("\n=== Testing Alternative Import Methods ===")
    
    # Method 1: Direct import
    try:
        from build_ordercreate_rq import generate_order_create_rq
        print("✅ Direct import successful")
        return generate_order_create_rq
    except Exception as e:
        print(f"❌ Direct import failed: {e}")
    
    # Method 2: Import with sys.path manipulation
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("build_ordercreate_rq", "scripts/build_ordercreate_rq.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        func = getattr(module, 'generate_order_create_rq')
        print("✅ Importlib import successful")
        return func
    except Exception as e:
        print(f"❌ Importlib import failed: {e}")
    
    return None

def main():
    print("Current working directory:", os.getcwd())
    print("Python path:", sys.path)
    print("Scripts directory exists:", os.path.exists('scripts'))
    print("build_ordercreate_rq.py exists:", os.path.exists('scripts/build_ordercreate_rq.py'))
    
    # Test the main import method
    func1 = test_import()
    
    # Test alternative methods
    func2 = test_alternative_import()
    
    if func1:
        print("\n✅ Main import method works - booking service should be able to import")
    elif func2:
        print("\n⚠️ Main import failed but alternative works - there might be a path issue")
    else:
        print("\n❌ All import methods failed - there's a serious import issue")

if __name__ == "__main__":
    main()
