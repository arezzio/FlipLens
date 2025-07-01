# FlipLens

A web application that helps thrift resellers rapidly evaluate the resale potential of clothing items by retrieving market data from eBay, calculating net profits, and displaying data confidence indicators.

## 🎯 Purpose

FlipLens helps thrift resellers make data-driven purchasing decisions by:
- Searching for clothing items by keyword
- Fetching market data from eBay
- Calculating estimated net profit after platform fees
- Providing data confidence indicators
- Enabling users to save profitable items for later review

## 🏗️ Architecture

- **Frontend**: React.js with Tailwind CSS
- **Backend**: Python Flask API
- **Database**: SQLite (for saved items)
- **APIs**: eBay Finding API

## 📁 Project Structure

```
FlipLens/
├── frontend/          # React frontend application
├── backend/           # Flask backend API
├── docs/             # Documentation
├── .taskmaster/      # Taskmaster project management
└── README.md         # This file
```

## 🚀 Getting Started

### Prerequisites
- Node.js 16+ (for frontend)
- Python 3.8+ (for backend)
- eBay Developer Account (for API access)
- PostgreSQL or SQLite (for database)

### Quick Setup (Development)
```bash
# Clone the repository
git clone https://github.com/your-username/FlipLens.git
cd FlipLens

# Install all dependencies
npm run install:all

# Set up environment variables
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit the .env files with your eBay API keys and configuration

# Start development servers
npm run dev
```

### Production Setup
For production deployment, use the automated setup script:

```bash
# Make the setup script executable
chmod +x scripts/production-setup.sh

# Run the production setup
./scripts/production-setup.sh
```

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed production deployment instructions.

## ✨ Features

### Core Functionality
- **🔍 Advanced Search**: Search eBay with intelligent filtering and sorting
- **💰 Profit Calculator**: Automatic profit estimation with platform fees
- **📊 Market Analysis**: Confidence scores and market position indicators
- **💾 Save Items**: Personal collection with notes and tags
- **👤 User Authentication**: Secure registration and login system
- **📱 Responsive Design**: Works perfectly on mobile and desktop

### Business Intelligence
- **Market Position Analysis**: Compare prices against market averages
- **Confidence Scoring**: Data reliability indicators for better decisions
- **Profit Margins**: Calculate estimated profits after all fees
- **Search History**: Track your research and popular queries

### Technical Features
- **Real-time Data**: Live eBay API integration
- **Secure Backend**: JWT authentication with rate limiting
- **Database Persistence**: PostgreSQL/SQLite with full CRUD operations
- **Production Ready**: Complete deployment configuration
- **Comprehensive Testing**: Automated test suite for all functionality

## 📋 Development Status

✅ **Completed Features:**
- User authentication system
- eBay API integration with profit calculations
- Database models and persistence
- Frontend with modern React/TypeScript
- Production deployment configuration
- Comprehensive testing suite

🚀 **Ready for Production!**

## 📝 License

ISC 

## Security

FlipLens is designed with security best practices for both backend and frontend:

- **API Keys & Secrets:**
  - All sensitive API keys (e.g., eBay credentials) are stored in backend environment variables and never exposed to the frontend or client code.
  - Backend uses `.env` files (see `backend/.env.example`) and validates required keys at startup.
  - Frontend uses only public, non-sensitive environment variables with the `REACT_APP_` prefix (see `frontend/.env.example`).
  - No secrets or private keys are ever present in frontend code or build artifacts.

- **Validation & Fail-Fast:**
  - Both backend and frontend validate required environment variables at startup.
  - The frontend fails to start in development if any required variable is missing or invalid.
  - Backend validates and sanitizes all user input, and enforces security headers.

- **Documentation:**
  - See [SECURITY.md](SECURITY.md) for comprehensive security documentation and best practices.
  - See [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md) for a comprehensive guide to secure environment variable setup.
  - Frontend and backend READMEs include security best practices for their respective environments.

- **Never commit real `.env` files or secrets to version control.** 