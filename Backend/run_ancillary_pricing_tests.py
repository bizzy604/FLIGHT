"""
Quick test runner for ancillary pricing sequential flow.

Run this script to execute all tests for the new ancillary pricing implementation.
"""

import sys
import subprocess
from pathlib import Path

def print_banner(text):
    """Print a formatted banner."""
    border = "=" * 80
    print(f"\n{border}")
    print(f"  {text}")
    print(f"{border}\n")

def run_tests():
    """Run all ancillary pricing tests."""
    print_banner("ANCILLARY PRICING SEQUENTIAL FLOW - TEST SUITE")
    
    # Get the Backend directory
    backend_dir = Path(__file__).parent
    
    # Test files
    unit_tests = backend_dir / "test_ancillary_pricing_sequential.py"
    integration_tests = backend_dir / "test_ancillary_pricing_routes_integration.py"
    
    print("📋 Test Plan:")
    print("  1. Unit Tests - Request builders and detection logic")
    print("  2. Integration Tests - API endpoints and sequential flow")
    print()
    
    # Check if test files exist
    if not unit_tests.exists():
        print(f"❌ Unit test file not found: {unit_tests}")
        return False
    
    if not integration_tests.exists():
        print(f"❌ Integration test file not found: {integration_tests}")
        return False
    
    # Run unit tests
    print_banner("RUNNING UNIT TESTS")
    print(f"File: {unit_tests.name}")
    print()
    
    unit_result = subprocess.run(
        [sys.executable, "-m", "pytest", str(unit_tests), "-v", "-s"],
        cwd=backend_dir
    )
    
    if unit_result.returncode != 0:
        print("\n❌ Unit tests FAILED")
        return False
    
    print("\n✅ Unit tests PASSED")
    
    # Run integration tests
    print_banner("RUNNING INTEGRATION TESTS")
    print(f"File: {integration_tests.name}")
    print()
    
    integration_result = subprocess.run(
        [sys.executable, "-m", "pytest", str(integration_tests), "-v", "-s"],
        cwd=backend_dir
    )
    
    if integration_result.returncode != 0:
        print("\n❌ Integration tests FAILED")
        return False
    
    print("\n✅ Integration tests PASSED")
    
    # Summary
    print_banner("TEST SUMMARY")
    print("✅ All tests PASSED!")
    print()
    print("Next steps:")
    print("  1. Review test output above")
    print("  2. Check API logs for sequential pricing calls")
    print("  3. Test with real API endpoints")
    print("  4. Verify OrderCreate with ancillaries works")
    print()
    
    return True

def run_specific_test(test_path):
    """Run a specific test or test class."""
    backend_dir = Path(__file__).parent
    
    print_banner(f"RUNNING SPECIFIC TEST: {test_path}")
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", test_path, "-v", "-s"],
        cwd=backend_dir
    )
    
    return result.returncode == 0

def run_with_coverage():
    """Run tests with coverage report."""
    backend_dir = Path(__file__).parent
    
    print_banner("RUNNING TESTS WITH COVERAGE")
    
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            "test_ancillary_pricing_sequential.py",
            "test_ancillary_pricing_routes_integration.py",
            "--cov=scripts.build_flightprice_ancillary_rq",
            "--cov=routes.ancillary_pricing_routes",
            "--cov-report=html",
            "--cov-report=term",
            "-v"
        ],
        cwd=backend_dir
    )
    
    if result.returncode == 0:
        print("\n✅ Coverage report generated: htmlcov/index.html")
    
    return result.returncode == 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run ancillary pricing tests")
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run tests with coverage report"
    )
    parser.add_argument(
        "--test",
        type=str,
        help="Run a specific test (e.g., test_ancillary_pricing_sequential.py::TestClass::test_method)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.test:
            success = run_specific_test(args.test)
        elif args.coverage:
            success = run_with_coverage()
        else:
            success = run_tests()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error running tests: {e}")
        sys.exit(1)
