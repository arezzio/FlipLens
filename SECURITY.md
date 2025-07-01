# Security Documentation

## Overview

FlipLens implements comprehensive security measures across both backend and frontend to protect user data, API keys, and prevent common web vulnerabilities.

## Backend Security

### API Key Management
- **Secure Storage**: All API keys are stored in environment variables, never in code
- **Enhanced Validation**: API keys are validated for format and strength on startup
- **Secure Logging**: API keys are masked in logs (e.g., `ArezzioR-****`)
- **Error Handling**: Missing or invalid API keys trigger clear error messages without exposing sensitive data

### Input Validation & Sanitization
- **Request Validation**: All incoming requests are validated for structure and content
- **SQL Injection Prevention**: Input sanitization removes dangerous characters
- **XSS Protection**: HTML escaping and character filtering
- **Rate Limiting**: Configurable rate limiting to prevent abuse

### Security Middleware
- **Security Headers**: Comprehensive security headers including CSP, X-Frame-Options, etc.
- **Request Monitoring**: Suspicious request patterns are logged
- **Error Handling**: Production errors don't expose internal details
- **CORS Configuration**: Proper CORS setup with configurable origins

### Configuration Security
```python
# Example secure configuration
class Config:
    @classmethod
    def get_api_key(cls, key_name: str, required: bool = True) -> Optional[str]:
        """Safely get API key with validation and secure logging"""
        # Implementation includes format validation and secure logging
```

## Frontend Security

### Content Security Policy (CSP)
- **XSS Protection**: Strict CSP prevents inline scripts and unsafe content
- **Resource Control**: Only allows resources from trusted sources
- **Frame Protection**: Prevents clickjacking attacks

### Error Handling
- **Global Error Boundary**: Catches unhandled errors and displays user-friendly messages
- **No Stack Traces**: Production errors don't expose internal details
- **Graceful Degradation**: App continues to function even with component errors

### Secure API Usage
- **No Secrets in Code**: No API keys or secrets in frontend code
- **Service Layer**: All API calls go through a centralized service layer
- **Error Display**: Safe error messages without exposing sensitive information

### Input Validation
- **Client-Side Validation**: Form inputs are validated before submission
- **Sanitization**: User inputs are sanitized to prevent injection attacks

## Environment Variables

### Backend (.env)
```bash
# Required
EBAY_API_KEY=your-ebay-api-key-here
SECRET_KEY=your-secret-key-here

# Optional
FLASK_ENV=development
EBAY_USE_SANDBOX=true
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600
```

### Frontend
- No sensitive environment variables in frontend
- Only public configuration values are exposed
- API endpoints are configured via service layer

## Security Testing

### Backend Tests
- **API Key Validation**: Tests for proper API key handling and validation
- **Input Sanitization**: Tests for XSS and injection prevention
- **Security Headers**: Tests for proper security header implementation
- **Error Handling**: Tests for secure error responses

### Frontend Tests
- **No Secrets**: Tests ensure no secrets are exposed in configuration
- **Error Boundaries**: Tests for proper error handling
- **Input Validation**: Tests for client-side validation

Run tests:
```bash
# Backend security tests
cd backend
python test_security_enhanced.py

# Frontend security tests
cd frontend
npm test
```

## Best Practices for Contributors

### Code Security
1. **Never commit secrets**: API keys, passwords, or tokens should never be in code
2. **Use environment variables**: All configuration should use environment variables
3. **Validate inputs**: Always validate and sanitize user inputs
4. **Handle errors securely**: Don't expose internal details in error messages
5. **Use HTTPS**: Always use HTTPS for API calls in production

### API Key Management
1. **Rotate regularly**: Change API keys periodically
2. **Use least privilege**: Only grant necessary permissions
3. **Monitor usage**: Watch for unusual API usage patterns
4. **Secure storage**: Use secure methods to store API keys

### Development Security
1. **Use .env.example**: Always provide example environment files
2. **Test security features**: Include security tests in your changes
3. **Review dependencies**: Check for vulnerable packages
4. **Follow security patterns**: Use established security patterns in the codebase

## Security Monitoring

### Logging
- **Security Events**: All security-related events are logged
- **Suspicious Activity**: Unusual patterns are flagged
- **Error Tracking**: Errors are logged without exposing sensitive data

### Monitoring
- **API Usage**: Monitor for unusual API usage patterns
- **Error Rates**: Track error rates and patterns
- **Performance**: Monitor for performance degradation

## Reporting Security Issues

If you discover a security vulnerability:

1. **Do not create a public issue**: Security issues should be reported privately
2. **Contact maintainers**: Reach out to the project maintainers directly
3. **Provide details**: Include steps to reproduce and potential impact
4. **Allow time for fix**: Give maintainers time to address the issue

## Security Checklist

Before deploying to production:

- [ ] All API keys are in environment variables
- [ ] No secrets are in code or configuration files
- [ ] Security headers are properly configured
- [ ] Input validation is implemented
- [ ] Error handling is secure
- [ ] HTTPS is enforced
- [ ] Dependencies are up to date
- [ ] Security tests pass
- [ ] Rate limiting is configured
- [ ] CORS is properly configured

## Updates

This security documentation is updated as new security features are implemented. Always review this document when making security-related changes. 