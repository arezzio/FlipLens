#!/bin/bash

# FlipLens Development Script
echo "🚀 Starting FlipLens development environment..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js"
    exit 1
fi

# Install backend dependencies if not already installed
echo "📦 Installing backend dependencies..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Install frontend dependencies if not already installed
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Start both servers
echo "🌐 Starting servers..."
echo "Frontend will be available at: http://localhost:3000"
echo "Backend will be available at: http://localhost:5000"
echo ""

# Start backend in background
cd backend
source venv/bin/activate
python app.py &
BACKEND_PID=$!
cd ..

# Start frontend
cd frontend
npm start

# Cleanup on exit
trap "kill $BACKEND_PID" EXIT 