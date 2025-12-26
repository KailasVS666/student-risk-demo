# Test Suite for Student Risk Assessment Application

## Overview

Comprehensive test suite covering API endpoints, data validation, error handling, and security features. Tests ensure reliability and correctness of the student risk prediction system.

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py             # Pytest fixtures and configuration
├── test_routes.py          # API endpoint tests
├── test_validation.py      # Data validation tests
└── README.md              # This file
```

## Test Categories

### 1. **API Route Tests** (`test_routes.py`)
- ✅ Predict Risk Endpoint (`POST /api/predict`)
  - Valid data prediction
  - Missing field validation
  - Invalid age/grade handling
  - Invalid JSON handling
  - Empty request handling
  - Rate limiting verification

- ✅ PDF Generation Endpoint (`POST /generate-pdf`)
  - Successful PDF generation
  - Missing field validation
  - Invalid confidence handling
  - Rate limiting verification

- ✅ Health Check Endpoints
  - `/healthz` endpoint
  - `/status` endpoint

- ✅ Input Validation
  - String length limits (100 chars for school/sex, 500 for customPrompt)
  - Alphanumeric validation
  - Empty field rejection

### 2. **Data Validation Tests** (`test_validation.py`)
- ✅ Required Field Validation
- ✅ Age Range Validation (15-30)
- ✅ Grade Range Validation (0-20)
- ✅ Numeric Type Validation
- ✅ String Field Validation (length, characters)
- ✅ Edge Case Testing
- ✅ Custom Prompt Validation

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test File
```bash
pytest tests/test_routes.py
pytest tests/test_validation.py
```

### Run Specific Test Class
```bash
pytest tests/test_routes.py::TestPredictRiskEndpoint
pytest tests/test_validation.py::TestStudentDataValidation
```

### Run Specific Test
```bash
pytest tests/test_routes.py::TestPredictRiskEndpoint::test_predict_risk_success
```

### Run with Verbose Output
```bash
pytest -v
```

### Run with Coverage Report
```bash
pytest --cov=app --cov-report=html
# View report: htmlcov/index.html
```

### Run with Markers
```bash
pytest -m unit
pytest -m integration
pytest -m routes
pytest -m validation
```

## Test Fixtures

### `app`
Creates a test Flask application with:
- Testing mode enabled
- CSRF protection disabled (for API tests)
- Proper configuration

### `client`
Flask test client for making HTTP requests

### `runner`
Flask CLI test runner for command-line operations

### `sample_student_data`
Valid student assessment data for positive tests:
```python
{
    'age': '18',
    'sex': 'F',
    'school': 'GP',
    'G1': '10',
    'G2': '12',
    # ... additional required fields
}
```

### `sample_pdf_data`
Valid PDF generation data:
```python
{
    'predicted_grade': '12',
    'risk_category': 'low',
    'confidence': 0.85,
    'shap_values': [...]
}
```

### `invalid_student_data`
Invalid data for negative testing

## Coverage Goals

| Module | Coverage | Status |
|--------|----------|--------|
| `routes.py` | > 85% | ✅ |
| `routes.validate_student_data()` | 100% | ✅ |
| `routes.predict_risk()` | 85% | ✅ |
| `routes.generate_pdf()` | 85% | ✅ |

## Test Examples

### Example 1: Test Prediction Endpoint
```python
def test_predict_risk_success(client, sample_student_data):
    response = client.post(
        '/api/predict',
        data=json.dumps(sample_student_data),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    assert response.get_json()['status'] == 'success'
```

### Example 2: Test Validation
```python
def test_age_below_minimum(sample_student_data):
    invalid_data = sample_student_data.copy()
    invalid_data['age'] = '14'
    
    with pytest.raises(ValueError) as exc_info:
        validate_student_data(invalid_data)
    
    assert 'Age must be between' in str(exc_info.value)
```

## Dependencies

```
pytest==7.4.0
pytest-cov==4.1.0      # For coverage reports
pytest-timeout==2.1.0  # For test timeouts
```

Install with:
```bash
pip install pytest pytest-cov pytest-timeout
```

## Common Issues

### Issue: Tests fail with "No module named 'app'"
**Solution**: Run tests from project root directory
```bash
cd /path/to/student-risk-demo
pytest tests/
```

### Issue: CSRF token errors in tests
**Solution**: CSRF is disabled in test configuration (conftest.py)
```python
app.config['WTF_CSRF_ENABLED'] = False
```

### Issue: Model files not found
**Solution**: Ensure model files exist in project root:
- `early_warning_model_pipeline_tuned.joblib`
- `student_risk_classifier_tuned.joblib`
- `label_encoder.joblib`

## Best Practices

1. **Isolation**: Each test is independent
2. **Fixtures**: Use provided fixtures for consistency
3. **Assertions**: Clear, specific assertions
4. **Documentation**: Docstrings explain test purpose
5. **Error Messages**: ValueError messages are descriptive for debugging
6. **Edge Cases**: Tests cover boundary values

## Contributing

When adding new tests:

1. Follow naming convention: `test_<function>_<scenario>`
2. Add docstring explaining what is tested and expected
3. Use fixtures for common data
4. Group related tests in classes
5. Add appropriate markers (`@pytest.mark.unit`, etc.)
6. Update this README with new test categories

## Performance

- Total test suite runtime: < 30 seconds
- Individual test runtime: < 5 seconds (excluding slow tests)
- Typical coverage: 85%+ of critical code paths

## CI/CD Integration

Run tests in CI/CD pipeline:
```bash
# Full test suite with coverage
pytest tests/ --cov=app --cov-report=xml

# Exit with error if coverage below threshold
pytest tests/ --cov=app --cov-fail-under=80
```

## Future Enhancements

- [ ] Integration tests with real Firebase
- [ ] Performance benchmarks
- [ ] Gemini API mocking and testing
- [ ] PDF content validation tests
- [ ] Security testing (XSS, SQL injection prevention)
- [ ] Load testing for rate limiting
