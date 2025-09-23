#!/usr/bin/env python3
"""
Test script to verify Python extension functionality
"""

def hello_world():
    """Simple test function"""
    print("Hello, World!")
    return "Python extension is working!"

if __name__ == "__main__":
    result = hello_world()
    print(f"Result: {result}")
