# Contributing to Webhook Dispatcher

Thank you for your interest in contributing to the Secure B2B Webhook Dispatcher! This document provides guidelines and information for contributors.

## 🚀 Quick Start

1. **Fork and clone the repository**
```bash
git fork https://github.com/melaven/webhook-dispatcher
git clone https://github.com/yourusername/webhook-dispatcher.git
cd webhook-dispatcher
```

2. **Set up development environment**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Run tests to ensure everything works**
```bash
pytest -v
# Expected: 43 passed, 4 skipped, 0 failed
```

## 🔧 Development Workflow

### Creating a Feature Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### Code Standards
- **Python**: Follow PEP 8 style guide
- **Type hints**: Required for all functions
- **Docstrings**: Use Google-style docstrings
- **Testing**: Write tests for new features

### Pre-commit Checks
```bash
# Format code
black app/ tests/
isort app/ tests/

# Run linting
flake8 app/ tests/

# Run tests
pytest -v

# Security tests must pass
pytest tests/test_security.py -v
```

## 🧪 Testing Guidelines

### Test Categories
1. **Unit Tests**: Individual function testing
2. **Integration Tests**: End-to-end scenarios
3. **Security Tests**: Authentication and validation
4. **Performance Tests**: Load and stress testing

### Writing Tests
```python
# Example test structure
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_webhook_endpoint():
    """Test webhook processing with valid data."""
    response = client.post(
        "/api/v1/webhook/incoming",
        headers={"X-API-Key": "test-key"},
        json={"event_type": "lead.created", ...}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
```

### Security Test Requirements
- All security tests must pass before merging
- Test replay protection mechanisms
- Validate input sanitization
- Verify authentication flows

## 🔐 Security Considerations

### Sensitive Data Handling
- **Never commit** real API keys or secrets
- Use `.env.example` for configuration templates
- Mask sensitive data in logs
- Follow the principle of least privilege

### Security Review Checklist
- [ ] No hardcoded secrets or credentials
- [ ] Input validation implemented
- [ ] Authentication mechanisms tested
- [ ] Rate limiting considerations
- [ ] SQL injection prevention
- [ ] XSS prevention measures

## 📊 Feature Development

### Adding New Event Types
1. **Define Pydantic schema** in `app/schemas.py`
2. **Add validation logic** in webhook processor
3. **Write comprehensive tests**
4. **Update API documentation**

### PDF Report Features
1. **Modify HTML template** in `templates/`
2. **Update ReportBuilder class** logic
3. **Test with sample Excel files**
4. **Validate output formatting**

### API Endpoints
1. **Follow FastAPI best practices**
2. **Include proper error handling**
3. **Add authentication where required**
4. **Document with OpenAPI schemas**

## 🐳 Docker Development

### Local Testing
```bash
# Build and test locally
docker compose up -d --build

# Check container health
docker ps

# View logs
docker compose logs api
```

### Docker Best Practices
- Use multi-stage builds for optimization
- Implement proper health checks
- Handle graceful shutdowns
- Minimize image size

## 📚 Documentation

### Required Documentation Updates
- Update README.md for new features
- Add docstrings to all functions
- Update API documentation
- Include usage examples

### Documentation Style
- Use clear, concise language
- Include code examples
- Provide practical use cases
- Follow existing formatting

## 🚀 Deployment Guidelines

### Environment Configuration
- Test in development environment first
- Validate production configurations
- Ensure security settings are appropriate
- Test backup and recovery procedures

### Release Process
1. **Feature branch** → **Development testing**
2. **Pull request** → **Code review**
3. **Staging deployment** → **Integration testing**
4. **Production release** → **Monitoring**

## 🐛 Bug Reports

### Issue Template
```markdown
**Bug Description**: Clear description of the issue

**Environment**:
- OS: [e.g., Ubuntu 20.04]
- Python: [e.g., 3.11.0]
- Docker: [e.g., 24.0.0]

**Steps to Reproduce**:
1. Step one
2. Step two
3. Expected vs actual behavior

**Error Logs**:
```
[Include relevant error messages]
```

**Additional Context**:
[Any additional information]
```

### Security Issues
**Do not open public issues for security vulnerabilities.**
Contact: [security@yourcompany.com]

## 💡 Feature Requests

### Enhancement Template
```markdown
**Feature Description**: What functionality should be added?

**Use Case**: Why is this feature needed?

**Proposed Solution**: How should it work?

**Alternative Solutions**: Any alternative approaches considered?

**Additional Context**: Screenshots, mockups, etc.
```

## 🏆 Recognition

### Contributors
We appreciate all contributions and will:
- Add you to the contributors list
- Recognize significant contributions in release notes
- Provide feedback and mentorship for new contributors

### Contribution Types
- 🐛 Bug fixes
- ✨ New features  
- 📚 Documentation improvements
- 🧪 Test coverage enhancements
- 🔐 Security improvements
- 🚀 Performance optimizations

## 📞 Getting Help

### Resources
- **Documentation**: [README.md](README.md)
- **API Docs**: http://localhost:8000/docs
- **Discussion**: GitHub Discussions
- **Issues**: GitHub Issues

### Communication Guidelines
- Be respectful and inclusive
- Provide clear, detailed information
- Help others when possible
- Follow the code of conduct

---

**Thank you for contributing to making webhook processing more secure and reliable for the B2B community!** 🚀