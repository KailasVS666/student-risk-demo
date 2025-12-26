"""
Unit tests for data validation functions.

Tests:
- Student data validation
- Input sanitization
- Range checking
- Type conversion
"""

import pytest
from app.routes import validate_student_data


class TestStudentDataValidation:
    """Tests for validate_student_data function."""
    
    def test_valid_student_data(self, sample_student_data):
        """
        Test validation accepts valid student data.
        
        Expectations:
        - Function returns True
        """
        result = validate_student_data(sample_student_data)
        assert result is True
    
    def test_missing_required_field(self, sample_student_data):
        """
        Test validation rejects missing required fields.
        
        Expectations:
        - ValueError raised with "Missing required fields" message
        """
        invalid_data = sample_student_data.copy()
        del invalid_data['G1']
        
        with pytest.raises(ValueError) as exc_info:
            validate_student_data(invalid_data)
        
        assert 'Missing required fields' in str(exc_info.value)
    
    def test_empty_required_field(self, sample_student_data):
        """
        Test validation rejects empty required fields.
        
        Expectations:
        - ValueError raised with "cannot be empty" message
        """
        invalid_data = sample_student_data.copy()
        invalid_data['school'] = ''
        
        with pytest.raises(ValueError) as exc_info:
            validate_student_data(invalid_data)
        
        assert 'cannot be empty' in str(exc_info.value)
    
    def test_age_below_minimum(self, sample_student_data):
        """
        Test validation rejects age below minimum (15).
        
        Expectations:
        - ValueError raised with age range message
        """
        invalid_data = sample_student_data.copy()
        invalid_data['age'] = '14'
        
        with pytest.raises(ValueError) as exc_info:
            validate_student_data(invalid_data)
        
        assert 'Age must be between' in str(exc_info.value)
    
    def test_age_above_maximum(self, sample_student_data):
        """
        Test validation rejects age above maximum (30).
        
        Expectations:
        - ValueError raised with age range message
        """
        invalid_data = sample_student_data.copy()
        invalid_data['age'] = '31'
        
        with pytest.raises(ValueError) as exc_info:
            validate_student_data(invalid_data)
        
        assert 'Age must be between' in str(exc_info.value)
    
    def test_grade_negative(self, sample_student_data):
        """
        Test validation rejects negative grades.
        
        Expectations:
        - ValueError raised
        """
        invalid_data = sample_student_data.copy()
        invalid_data['G1'] = '-1'
        
        with pytest.raises(ValueError):
            validate_student_data(invalid_data)
    
    def test_grade_above_maximum(self, sample_student_data):
        """
        Test validation rejects grades above 20.
        
        Expectations:
        - ValueError raised
        """
        invalid_data = sample_student_data.copy()
        invalid_data['G2'] = '21'
        
        with pytest.raises(ValueError) as exc_info:
            validate_student_data(invalid_data)
        
        assert 'Grades must be between' in str(exc_info.value)
    
    def test_non_numeric_age(self, sample_student_data):
        """
        Test validation rejects non-numeric age.
        
        Expectations:
        - ValueError raised with "Invalid numeric values" message
        """
        invalid_data = sample_student_data.copy()
        invalid_data['age'] = 'seventeen'
        
        with pytest.raises(ValueError) as exc_info:
            validate_student_data(invalid_data)
        
        assert 'Invalid numeric values' in str(exc_info.value)
    
    def test_non_numeric_grade(self, sample_student_data):
        """
        Test validation rejects non-numeric grades.
        
        Expectations:
        - ValueError raised
        """
        invalid_data = sample_student_data.copy()
        invalid_data['G1'] = 'excellent'
        
        with pytest.raises(ValueError):
            validate_student_data(invalid_data)
    
    def test_string_field_too_long(self, sample_student_data):
        """
        Test validation rejects overly long string fields.
        
        Expectations:
        - ValueError raised with "exceeds maximum length" message
        """
        invalid_data = sample_student_data.copy()
        invalid_data['school'] = 'A' * 101
        
        with pytest.raises(ValueError) as exc_info:
            validate_student_data(invalid_data)
        
        assert 'exceeds maximum length' in str(exc_info.value)
    
    def test_string_field_invalid_characters(self, sample_student_data):
        """
        Test validation rejects string fields with invalid characters.
        
        Expectations:
        - ValueError raised with "invalid characters" message
        """
        invalid_data = sample_student_data.copy()
        invalid_data['sex'] = 'F@#'
        
        with pytest.raises(ValueError) as exc_info:
            validate_student_data(invalid_data)
        
        assert 'invalid characters' in str(exc_info.value)
    
    def test_custom_prompt_length_limit(self, sample_student_data):
        """
        Test custom prompt field has 500 character limit.
        
        Expectations:
        - ValueError raised for prompts > 500 chars
        """
        invalid_data = sample_student_data.copy()
        invalid_data['customPrompt'] = 'A' * 501
        
        with pytest.raises(ValueError) as exc_info:
            validate_student_data(invalid_data)
        
        assert 'Custom prompt exceeds maximum length' in str(exc_info.value)
    
    def test_valid_custom_prompt(self, sample_student_data):
        """
        Test custom prompt within valid length is accepted.
        
        Expectations:
        - Function returns True
        """
        valid_data = sample_student_data.copy()
        valid_data['customPrompt'] = 'Please provide advice in bullet points'
        
        result = validate_student_data(valid_data)
        assert result is True
    
    def test_edge_case_age_minimum(self, sample_student_data):
        """
        Test edge case: age = 15 (minimum valid).
        
        Expectations:
        - Function returns True
        """
        valid_data = sample_student_data.copy()
        valid_data['age'] = '15'
        
        result = validate_student_data(valid_data)
        assert result is True
    
    def test_edge_case_age_maximum(self, sample_student_data):
        """
        Test edge case: age = 30 (maximum valid).
        
        Expectations:
        - Function returns True
        """
        valid_data = sample_student_data.copy()
        valid_data['age'] = '30'
        
        result = validate_student_data(valid_data)
        assert result is True
    
    def test_edge_case_grade_zero(self, sample_student_data):
        """
        Test edge case: grade = 0 (minimum valid).
        
        Expectations:
        - Function returns True
        """
        valid_data = sample_student_data.copy()
        valid_data['G1'] = '0'
        
        result = validate_student_data(valid_data)
        assert result is True
    
    def test_edge_case_grade_twenty(self, sample_student_data):
        """
        Test edge case: grade = 20 (maximum valid).
        
        Expectations:
        - Function returns True
        """
        valid_data = sample_student_data.copy()
        valid_data['G2'] = '20'
        
        result = validate_student_data(valid_data)
        assert result is True
