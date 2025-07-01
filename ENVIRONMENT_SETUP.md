# Environment Variables Setup Guide

This guide explains how to securely configure environment variables for the FlipLens application.

## Overview

FlipLens uses environment variables to store sensitive configuration like API keys and server settings. This ensures that sensitive data is not hardcoded in the source code and can be easily managed across different environments.

## Security Best Practices

### ✅ DO:
- Store all sensitive data in environment variables
- Use `.env` files for local development
- Keep `.env` files in `.gitignore`
- Use strong, unique API keys
- Rotate API keys regularly
- Use different keys for development and production

### ❌ DON'T:
- Commit API keys to version control
- Share API keys in public repositories
- Use the same keys across environments
- Hardcode sensitive data in source code
- Log API keys or sensitive data

## Backend Configuration

### Required Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# eBay API Configuration (Required)
EBAY_API_KEY=your-ebay-api-key-here
EBAY_APP_ID=your-ebay-app-id-here
EBAY_CERT_ID=your-ebay-cert-id-here
EBAY_DEV_ID=your-ebay-dev-id-here
EBAY_USE_SANDBOX=true

# Server Configuration
PORT=5000
HOST=0.0.0.0

# Security Configuration
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Optional Environment Variables

```bash
# Database Configuration (if needed in future)
DATABASE_URL=sqlite:///fliplens.db

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=fliplens.log
```

### eBay API Setup

1. **Get eBay API Keys:**
   - Go to [eBay Developer Program](https://developer.ebay.com/)
   - Create a new application
   - Get your API keys (App ID, Cert ID, Dev ID)

2. **Sandbox vs Production:**
   - Use `EBAY_USE_SANDBOX=true` for development
   - Use `EBAY_USE_SANDBOX=false` for production

## Frontend Configuration

### Required Environment Variables

Create a `.env` file in the `frontend/` directory:

```bash
# API Configuration
REACT_APP_API_URL=http://localhost:5000/api

# Environment Configuration
REACT_APP_ENV=development
REACT_APP_VERSION=1.0.0

# Feature Flags
REACT_APP_ENABLE_OFFLINE_CACHE=true
REACT_APP_CACHE_EXPIRY_HOURS=24
REACT_APP_MAX_CACHE_SIZE_MB=50

# Development Configuration
REACT_APP_DEBUG=true
REACT_APP_LOG_LEVEL=info
```

### Optional Environment Variables

```bash
# Error Reporting (if needed in future)
REACT_APP_SENTRY_DSN=your-sentry-dsn-here

# Analytics (if needed in future)
REACT_APP_GA_TRACKING_ID=your-ga-tracking-id-here
```

## Environment-Specific Configuration

### Development Environment

```bash
# Backend
FLASK_ENV=development
EBAY_USE_SANDBOX=true
DEBUG=true

# Frontend
REACT_APP_ENV=development
REACT_APP_DEBUG=true
REACT_APP_ENABLE_OFFLINE_CACHE=true
```

### Production Environment

```bash
# Backend
FLASK_ENV=production
EBAY_USE_SANDBOX=false
DEBUG=false
SECRET_KEY=your-strong-production-secret-key

# Frontend
REACT_APP_ENV=production
REACT_APP_DEBUG=false
REACT_APP_ENABLE_OFFLINE_CACHE=true
```

### Testing Environment

```bash
# Backend
FLASK_ENV=testing
EBAY_USE_SANDBOX=true
TESTING=true

# Frontend
REACT_APP_ENV=test
REACT_APP_DEBUG=false
REACT_APP_ENABLE_OFFLINE_CACHE=false
```

## Configuration Validation

### Backend Validation

The backend automatically validates required environment variables on startup:

```python
# Missing required variables will cause startup failure
if not EBAY_API_KEY:
    raise ValueError("EBAY_API_KEY is required")
```

### Frontend Validation

The frontend validates configuration on startup:

```typescript
// Configuration errors are logged to console
const errors = validateConfig();
if (errors.length > 0) {
    console.error('Configuration errors:', errors);
}
```

## Deployment Configuration

### Local Development

1. Copy `.env.example` to `.env` in both `backend/` and `frontend/` directories
2. Fill in your actual API keys and configuration
3. Start the development servers

### Production Deployment

1. **Environment Variables:**
   - Set environment variables on your hosting platform
   - Never commit `.env` files to production repositories

2. **Security:**
   - Use strong, unique SECRET_KEY
   - Enable HTTPS in production
   - Configure proper CORS origins
   - Use production eBay API keys

3. **Monitoring:**
   - Enable logging for debugging
   - Monitor API usage and errors
   - Set up error reporting (Sentry, etc.)

## Troubleshooting

### Common Issues

1. **API Key Not Working:**
   - Verify the key is correct
   - Check if you're using sandbox vs production
   - Ensure the key has proper permissions

2. **CORS Errors:**
   - Check CORS_ORIGINS configuration
   - Verify frontend URL is included

3. **Environment Variables Not Loading:**
   - Ensure `.env` files are in the correct directories
   - Check file permissions
   - Verify variable names match exactly

### Debug Commands

```bash
# Check backend configuration
cd backend
python -c "from config.settings import Config; print(Config.validate_required_keys())"

# Check frontend configuration
cd frontend
npm start  # Will show configuration in console
```

## Security Checklist

- [ ] All API keys stored in environment variables
- [ ] `.env` files added to `.gitignore`
- [ ] Different keys for development and production
- [ ] Strong SECRET_KEY for production
- [ ] CORS origins properly configured
- [ ] HTTPS enabled in production
- [ ] API keys rotated regularly
- [ ] No sensitive data in logs
- [ ] Error messages don't expose sensitive data

## Additional Resources

- [eBay Developer Program](https://developer.ebay.com/)
- [Flask Configuration](https://flask.palletsprojects.com/en/2.3.x/config/)
- [React Environment Variables](https://create-react-app.dev/docs/adding-custom-environment-variables/)
- [Security Best Practices](https://owasp.org/www-project-top-ten/)

## Frontend Environment Variable Security (React)

- **Never store secrets or private API keys in frontend `.env` files.**
  - Only use public, non-sensitive values (e.g., API URLs, feature flags).
  - All frontend environment variables must be prefixed with `REACT_APP_`.
- **API keys for third-party services (e.g., eBay) must only be used in the backend.**
- **If a required environment variable is missing or invalid, the app will fail to start in development.**
- **Review `frontend/.env.example` for the full list of supported variables.**
- **Never commit real `.env` files to version control.** 