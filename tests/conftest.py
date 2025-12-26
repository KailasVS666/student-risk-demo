"""
Pytest configuration and fixtures for the test suite.
"""

import pytest
import os
import json
from dotenv import load_dotenv
from app import create_app

# Load test environment variables
load_dotenv('.env.test')
load_dotenv()  # Fallback to regular .env


@pytest.fixture
def app():
    """
    Create and configure a test Flask application.
    
    Returns:
        Flask app configured for testing
    """
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for test requests
    
    return app


@pytest.fixture
def client(app):
    """
    Create a Flask test client.
    
    Args:
        app: Flask app fixture
        
    Returns:
        Flask test client
    """
    return app.test_client()


@pytest.fixture
def runner(app):
    """
    Create a Flask test CLI runner.
    
    Args:
        app: Flask app fixture
        
    Returns:
        Flask CLI test runner
    """
    return app.test_cli_runner()


@pytest.fixture
def sample_student_data():
    """
    Provide valid sample student assessment data for testing.
    
    Returns:
        dict: Valid student data
    """
    return {
        'age': '18',
        'sex': 'F',
        'school': 'GP',
        'address': 'U',
        'famsize': 'LE3',
        'Pstatus': 'T',
        'Medu': '4',
        'Fedu': '3',
        'Mjob': 'other',
        'Fjob': 'other',
        'reason': 'course',
        'guardian': 'mother',
        'traveltime': '2',
        'studytime': '2',
        'failures': '0',
        'schoolsup': 'yes',
        'famsup': 'yes',
        'paid': 'no',
        'activities': 'yes',
        'nursery': 'yes',
        'higher': 'yes',
        'internet': 'yes',
        'romantic': 'no',
        'famrel': '4',
        'freetime': '3',
        'goout': '4',
        'Dalc': '1',
        'Walc': '1',
        'health': '3',
        'absences': '6',
        'G1': '10',
        'G2': '12',
        'average_grade': '11.0',
        'grade_change': '2.0'
    }


@pytest.fixture
def sample_pdf_data():
    """
    Provide sample data for PDF generation testing.
    
    Returns:
        dict: Valid PDF generation data
    """
    return {
        'predicted_grade': '12',
        'risk_category': 'low',
        'confidence': 0.85,
        'risk_descriptor': 'On track, but minor improvements can maximize potential.',
        'mentoring_advice': '### Priority Actions\nFocus on consistent engagement',
        'shap_values': [
            {'feature': 'G2', 'importance': 0.85},
            {'feature': 'Failures', 'importance': -0.65}
        ]
    }


@pytest.fixture
def invalid_student_data():
    """
    Provide invalid student data for negative testing.
    
    Returns:
        dict: Invalid student data
    """
    return {
        'age': 'invalid',  # Should be numeric
        'sex': 'F',
        # Missing required fields
        'G1': '-5',  # Out of valid range
    }
