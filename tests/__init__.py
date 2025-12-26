"""
Test suite for Student Risk Assessment Application.

Tests cover:
- Route handlers and API endpoints
- Data validation
- Model predictions
- PDF generation
- Firebase operations
- Error handling
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
