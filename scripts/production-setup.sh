#!/bin/bash

# FlipLens Production Setup Script
# This script sets up FlipLens for production deployment

set -e  # Exit on any error

echo "🚀 FlipLens Production Setup Starting..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   exit 1
fi

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

print_status "Project root: $PROJECT_ROOT"

# Check if we're in the right directory
if [[ ! -f "$PROJECT_ROOT/package.json" ]] || [[ ! -d "$PROJECT_ROOT/backend" ]] || [[ ! -d "$PROJECT_ROOT/frontend" ]]; then
    print_error "This doesn't appear to be the FlipLens project root directory"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
print_status "Checking prerequisites..."

# Check Node.js
if command_exists node; then
    NODE_VERSION=$(node --version)
    print_success "Node.js found: $NODE_VERSION"
else
    print_error "Node.js is not installed. Please install Node.js 16+ first."
    exit 1
fi

# Check Python
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version)
    print_success "Python found: $PYTHON_VERSION"
else
    print_error "Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check pip
if command_exists pip3; then
    print_success "pip3 found"
else
    print_error "pip3 is not installed. Please install pip3 first."
    exit 1
fi

# Setup backend
print_status "Setting up backend..."

cd "$PROJECT_ROOT/backend"

# Create virtual environment if it doesn't exist
if [[ ! -d "venv" ]]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install backend dependencies
print_status "Installing backend dependencies..."
pip install -r requirements.txt
print_success "Backend dependencies installed"

# Check if .env file exists
if [[ ! -f ".env" ]]; then
    print_warning ".env file not found. Creating from example..."
    if [[ -f ".env.example" ]]; then
        cp .env.example .env
        print_warning "Please edit .env file with your production values before starting the application"
    else
        print_error ".env.example file not found"
        exit 1
    fi
else
    print_success ".env file found"
fi

# Initialize database
print_status "Initializing database..."
python -c "
try:
    from models.database import init_db
    from __init__ import create_app
    app = create_app()
    with app.app_context():
        init_db(app)
    print('Database initialized successfully')
except Exception as e:
    print(f'Database initialization failed: {e}')
    exit(1)
"
print_success "Database initialized"

# Test backend
print_status "Testing backend..."
python -c "
try:
    from __init__ import create_app
    app = create_app()
    print('Backend configuration test passed')
except Exception as e:
    print(f'Backend test failed: {e}')
    exit(1)
"
print_success "Backend test passed"

# Deactivate virtual environment
deactivate

# Setup frontend
print_status "Setting up frontend..."

cd "$PROJECT_ROOT/frontend"

# Install frontend dependencies
print_status "Installing frontend dependencies..."
npm install
print_success "Frontend dependencies installed"

# Check if .env file exists for frontend
if [[ ! -f ".env.production" ]]; then
    print_warning ".env.production file not found for frontend. Creating basic version..."
    cat > .env.production << EOF
REACT_APP_API_BASE_URL=http://localhost:5000/api
REACT_APP_ENVIRONMENT=production
EOF
    print_warning "Please edit frontend/.env.production with your production API URL"
else
    print_success "Frontend .env.production file found"
fi

# Build frontend for production
print_status "Building frontend for production..."
npm run build
print_success "Frontend built successfully"

# Create PM2 ecosystem file
print_status "Creating PM2 ecosystem configuration..."

cd "$PROJECT_ROOT"

cat > ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: 'fliplens-backend',
    script: 'app.py',
    interpreter: './venv/bin/python',
    cwd: '$PROJECT_ROOT/backend',
    env: {
      FLASK_ENV: 'production'
    },
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    error_file: './logs/err.log',
    out_file: './logs/out.log',
    log_file: './logs/combined.log',
    time: true
  }]
};
EOF

print_success "PM2 ecosystem configuration created"

# Create logs directory
mkdir -p logs

# Create nginx configuration template
print_status "Creating Nginx configuration template..."

cat > nginx.conf.template << 'EOF'
server {
    listen 80;
    server_name YOUR_DOMAIN_HERE;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name YOUR_DOMAIN_HERE;

    # SSL Configuration (update paths as needed)
    ssl_certificate /etc/letsencrypt/live/YOUR_DOMAIN_HERE/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/YOUR_DOMAIN_HERE/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # Frontend (React App)
    location / {
        root PROJECT_ROOT_HERE/frontend/build;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:5000;
        access_log off;
    }
}
EOF

# Replace placeholders in nginx template
sed -i "s|PROJECT_ROOT_HERE|$PROJECT_ROOT|g" nginx.conf.template

print_success "Nginx configuration template created"

# Create startup script
print_status "Creating startup script..."

cat > start-production.sh << EOF
#!/bin/bash

# FlipLens Production Startup Script

echo "Starting FlipLens in production mode..."

# Check if PM2 is installed
if ! command -v pm2 &> /dev/null; then
    echo "PM2 is not installed. Installing globally..."
    npm install -g pm2
fi

# Start backend with PM2
echo "Starting backend..."
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

echo "FlipLens backend started successfully!"
echo ""
echo "To check status: pm2 status"
echo "To view logs: pm2 logs fliplens-backend"
echo "To stop: pm2 stop fliplens-backend"
echo ""
echo "Don't forget to:"
echo "1. Configure your web server (nginx) with the provided template"
echo "2. Set up SSL certificates"
echo "3. Update your DNS records"
echo "4. Test the application thoroughly"
EOF

chmod +x start-production.sh

print_success "Startup script created"

# Create test script
print_status "Creating test script..."

cat > test-production.sh << EOF
#!/bin/bash

echo "Testing FlipLens production setup..."

# Test backend health
echo "Testing backend health..."
curl -f http://localhost:5000/api/health || {
    echo "Backend health check failed"
    exit 1
}

echo "Backend is healthy!"

# Run comprehensive tests
if [[ -f "test_complete_functionality.py" ]]; then
    echo "Running comprehensive functionality tests..."
    python3 test_complete_functionality.py
else
    echo "Comprehensive test script not found, skipping..."
fi

echo "Production setup test completed!"
EOF

chmod +x test-production.sh

print_success "Test script created"

# Final summary
print_status "Production setup completed successfully!"
echo ""
print_success "✅ Backend virtual environment created and dependencies installed"
print_success "✅ Database initialized"
print_success "✅ Frontend built for production"
print_success "✅ PM2 ecosystem configuration created"
print_success "✅ Nginx configuration template created"
print_success "✅ Startup and test scripts created"
echo ""
print_warning "⚠️  IMPORTANT: Before starting the application:"
echo "   1. Edit backend/.env with your production values (eBay API keys, database, etc.)"
echo "   2. Edit frontend/.env.production with your production API URL"
echo "   3. Configure your web server using nginx.conf.template"
echo "   4. Set up SSL certificates"
echo "   5. Update DNS records to point to your server"
echo ""
print_status "To start the application: ./start-production.sh"
print_status "To test the application: ./test-production.sh"
echo ""
print_success "🎉 FlipLens is ready for production deployment!"
