#!/usr/bin/env python3
"""
Test file to verify Python functionality in Cursor
"""

def test_imports():
    """Test basic imports work"""
    import sys
    import os
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    return True

def test_functions_framework():
    """Test that our dependencies work"""
    try:
        import functions_framework
        print("✓ functions-framework imported successfully")
        return True
    except ImportError as e:
        print(f"✗ functions-framework import failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Python environment in Cursor...")
    print("-" * 40)

    test_imports()
    print()

    success = test_functions_framework()

    print("-" * 40)
    if success:
        print("✓ All tests passed! Python is working correctly in Cursor.")
    else:
        print("✗ Some tests failed. Check the errors above.")
