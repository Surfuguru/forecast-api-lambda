"""
Pytest configuration and fixtures
"""

import sys
import os

# Add the lambdas directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambdas'))
