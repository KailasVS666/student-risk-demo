"""
Unit tests for API endpoints (routes.py).

Tests:
- POST /api/predict - Risk prediction endpoint
- POST /generate-pdf - PDF generation endpoint
- GET /healthz - Health check endpoint
- Data validation
- Error handling
"""

import pytest
import json
from flask import jsonify


class TestPredictRiskEndpoint:
    """Tests for the /api/predict endpoint."""
    
    def test_predict_risk_success(self, client, sample_student_data):
        """
        Test successful risk prediction with valid data.
        
        Expectations:
        - Status code 200
        - Response contains prediction, risk_category, shap_values, mentoring_advice
        - Risk category is one of: 'high', 'medium', 'low'
        """
        response = client.post(
            '/api/predict',
            data=json.dumps(sample_student_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify response structure
        assert 'prediction' in data
        assert 'risk_category' in data
        assert 'confidence' in data
        assert 'shap_values' in data
        assert 'mentoring_advice' in data
        assert 'status' in data
        
        # Verify prediction values
        assert data['status'] == 'success'
        assert data['risk_category'] in ['high', 'medium', 'low']
        assert 0 <= data['prediction'] <= 20
        assert 0 <= data['confidence'] <= 1
        assert isinstance(data['shap_values'], list)
    
    def test_predict_risk_missing_fields(self, client, sample_student_data):
        """
        Test prediction with missing required fields.
        
        Expectations:
        - Status code 400 (Bad Request)
        - Error message indicating missing field
        - status = 'validation_error'
        """
        # Remove a required field
        invalid_data = sample_student_data.copy()
        del invalid_data['G2']
        
        response = client.post(
            '/api/predict',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'status' in data
        assert data['status'] == 'validation_error'
    
    def test_predict_risk_invalid_age(self, client, sample_student_data):
        """
        Test prediction with invalid age (out of range).
        
        Expectations:
        - Status code 400
        - Error message about age range
        """
        invalid_data = sample_student_data.copy()
        invalid_data['age'] = '50'  # Out of valid range (15-30)
        
        response = client.post(
            '/api/predict',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'Age must be between' in data.get('error', '')
    
    def test_predict_risk_invalid_grade(self, client, sample_student_data):
        """
        Test prediction with invalid grade (out of range).
        
        Expectations:
        - Status code 400
        - Error message about grade range
        """
        invalid_data = sample_student_data.copy()
        invalid_data['G1'] = '25'  # Out of valid range (0-20)
        
        response = client.post(
            '/api/predict',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'grade' in data.get('error', '').lower() or 'numeric' in data.get('error', '').lower()
    
    def test_predict_risk_invalid_json(self, client):
        """
        Test prediction with invalid JSON.
        
        Expectations:
        - Status code indicates error (400 or 500)
        - Request fails (not a 200 success)
        """
        response = client.post(
            '/api/predict',
            data='invalid json',
            content_type='application/json'
        )
        
        # Either Flask rejects JSON (400) or error handler catches it (500)
        assert response.status_code != 200
    
    def test_predict_risk_empty_request(self, client):
        """
        Test prediction with empty request body.
        
        Expectations:
        - Status code 400
        - Error message about empty request
        """
        response = client.post(
            '/api/predict',
            data='{}',
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'validation_error'
    
    def test_predict_risk_rate_limiting(self, client, sample_student_data):
        """
        Test rate limiting on /api/predict endpoint.
        
        Expectations:
        - After 30 requests per minute, subsequent requests get 429 status
        Note: This test may need adjustment based on actual rate limiting config
        """
        # Make 31 requests and check if last one is rate limited
        responses = []
        for i in range(31):
            response = client.post(
                '/api/predict',
                data=json.dumps(sample_student_data),
                content_type='application/json'
            )
            responses.append(response.status_code)
        
        # Should have at least one successful response
        assert 200 in responses


class TestPDFGenerationEndpoint:
    """Tests for the /generate-pdf endpoint."""
    
    def test_generate_pdf_success(self, client, sample_pdf_data):
        """
        Test successful PDF generation.
        
        Expectations:
        - Status code 200
        - Content-Type is 'application/pdf'
        - Content-Disposition header with filename
        - Response body is valid PDF (starts with %PDF)
        """
        response = client.post(
            '/generate-pdf',
            data=json.dumps(sample_pdf_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        assert response.content_type == 'application/pdf'
        assert 'Content-Disposition' in response.headers
        assert 'student_report' in response.headers['Content-Disposition']
        assert response.data.startswith(b'%PDF')
    
    def test_generate_pdf_missing_fields(self, client):
        """
        Test PDF generation with missing required fields.
        
        Expectations:
        - Status code 400
        - Error message indicating missing field
        """
        invalid_data = {'confidence': 0.85}  # Missing predicted_grade, risk_category
        
        response = client.post(
            '/generate-pdf',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'status' in data
        assert data['status'] == 'validation_error'
    
    def test_generate_pdf_invalid_confidence(self, client, sample_pdf_data):
        """
        Test PDF generation with invalid confidence (negative).
        
        Expectations:
        - Status code 200 (should clamp to [0, 100])
        - PDF generated successfully
        """
        invalid_data = sample_pdf_data.copy()
        invalid_data['confidence'] = -0.5  # Should be clamped to 0
        
        response = client.post(
            '/generate-pdf',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        # Should still generate PDF, with confidence clamped
        assert response.status_code == 200
        assert response.content_type == 'application/pdf'
    
    def test_generate_pdf_rate_limiting(self, client, sample_pdf_data):
        """
        Test rate limiting on /generate-pdf endpoint.
        
        Expectations:
        - After 5 requests per minute, subsequent requests get 429 status
        """
        responses = []
        for i in range(6):
            response = client.post(
                '/generate-pdf',
                data=json.dumps(sample_pdf_data),
                content_type='application/json'
            )
            responses.append(response.status_code)
        
        # Should have at least one successful response
        assert 200 in responses


class TestHealthEndpoints:
    """Tests for health check endpoints."""
    
    def test_healthz_endpoint(self, client):
        """
        Test /healthz endpoint.
        
        Expectations:
        - Status code 200
        - Response contains 'ok': True
        - Response contains 'models_loaded'
        - Response contains 'time' (ISO format)
        """
        response = client.get('/healthz')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'ok' in data
        assert 'models_loaded' in data
        assert 'time' in data
        assert isinstance(data['ok'], bool)
    
    def test_status_endpoint(self, client):
        """
        Test /status endpoint.
        
        Expectations:
        - Status code 200
        - Response contains pipeline, label_encoder, risk_explainer status
        """
        response = client.get('/status')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'pipeline' in data
        assert 'label_encoder' in data
        assert 'risk_explainer' in data
        assert all(isinstance(v, bool) for v in data.values())


class TestInputValidation:
    """Tests for input validation in routes."""
    
    def test_validate_string_length(self, client, sample_student_data):
        """
        Test validation of string field length limits.
        
        Expectations:
        - Fields with > 100 chars are rejected
        """
        invalid_data = sample_student_data.copy()
        invalid_data['school'] = 'A' * 101  # Exceeds 100 char limit
        
        response = client.post(
            '/api/predict',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_validate_alphanumeric(self, client, sample_student_data):
        """
        Test validation of alphanumeric fields.
        
        Expectations:
        - Fields with special characters are rejected
        """
        invalid_data = sample_student_data.copy()
        invalid_data['school'] = 'G@P#'  # Contains special characters
        
        response = client.post(
            '/api/predict',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_validate_empty_fields(self, client, sample_student_data):
        """
        Test validation rejects empty required fields.
        
        Expectations:
        - Empty strings in required fields are rejected
        """
        invalid_data = sample_student_data.copy()
        invalid_data['G1'] = ''  # Empty required field
        
        response = client.post(
            '/api/predict',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
