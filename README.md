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
- Node.js (for frontend)
- Python 3.8+ (for backend)
- eBay Developer Account (for API access)

### Installation
1. Clone the repository
2. Set up the frontend (see `frontend/README.md`)
3. Set up the backend (see `backend/README.md`)
4. Configure environment variables

## 📋 Development Status

This project is managed with Taskmaster. Current tasks and progress can be viewed with:
```bash
task-master list
```

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