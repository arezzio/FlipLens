# FlipLens Production Deployment Guide

## 🚀 Overview

This guide will help you deploy FlipLens to production with complete functionality including user authentication, database persistence, and eBay API integration.

## 📋 Prerequisites

### Required Accounts & Services
1. **eBay Developer Account** - [developer.ebay.com](https://developer.ebay.com)
2. **Domain Name** - For your production website
3. **SSL Certificate** - For HTTPS (Let's Encrypt recommended)
4. **Server/Hosting** - VPS, AWS EC2, DigitalOcean, etc.

### Required Software
- **Node.js** 16+ (for frontend)
- **Python** 3.8+ (for backend)
- **PostgreSQL** or **SQLite** (database)
- **Nginx** (web server/reverse proxy)
- **PM2** (process manager)

## 🔧 Backend Production Setup

### 1. Server Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install python3 python3-pip python3-venv nginx postgresql postgresql-contrib -y

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install PM2 globally
sudo npm install -g pm2
```

### 2. Database Setup (PostgreSQL)
```bash
# Create database and user
sudo -u postgres psql
CREATE DATABASE fliplens_production;
CREATE USER fliplens_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE fliplens_production TO fliplens_user;
\q
```

### 3. Backend Deployment
```bash
# Clone repository
git clone https://github.com/your-username/FlipLens.git
cd FlipLens/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create production environment file
cp .env.production.example .env
```

### 4. Configure Production Environment
Edit `/backend/.env` with your production values:

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-super-secure-secret-key-here
DEBUG=false

# eBay API Configuration (PRODUCTION KEYS)
EBAY_API_KEY=your-production-ebay-api-key
EBAY_APP_ID=your-production-ebay-app-id
EBAY_CERT_ID=your-production-ebay-cert-id
EBAY_DEV_ID=your-production-ebay-dev-id
EBAY_USE_SANDBOX=false

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_ACCESS_TOKEN_EXPIRES=86400

# Database Configuration
DATABASE_URL=postgresql://fliplens_user:your_secure_password@localhost/fliplens_production

# Security Configuration
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Server Configuration
PORT=5000
HOST=127.0.0.1
```

### 5. Initialize Database
```bash
# Run database migrations
python -c "from models.database import init_db; from __init__ import create_app; app = create_app(); init_db(app)"
```

### 6. Start Backend with PM2
```bash
# Create PM2 ecosystem file
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: 'fliplens-backend',
    script: 'app.py',
    interpreter: './venv/bin/python',
    cwd: '/path/to/FlipLens/backend',
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

# Start with PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

## 🎨 Frontend Production Setup

### 1. Build Frontend
```bash
cd ../frontend

# Install dependencies
npm install

# Create production environment file
cat > .env.production << EOF
REACT_APP_API_BASE_URL=https://yourdomain.com/api
REACT_APP_ENVIRONMENT=production
EOF

# Build for production
npm run build
```

### 2. Deploy Frontend Files
```bash
# Copy build files to web server directory
sudo cp -r build/* /var/www/html/
sudo chown -R www-data:www-data /var/www/html/
```

## 🌐 Nginx Configuration

### 1. Create Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/fliplens
```

Add the following configuration:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # Frontend (React App)
    location / {
        root /var/www/html;
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
```

### 2. Enable Site and Restart Nginx
```bash
sudo ln -s /etc/nginx/sites-available/fliplens /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🔒 SSL Certificate Setup

### Using Let's Encrypt (Recommended)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

## 🔑 eBay API Production Keys

### 1. Get Production Keys
1. Go to [eBay Developer Program](https://developer.ebay.com)
2. Create a new application for production
3. Get your production keys:
   - App ID (Client ID)
   - Cert ID (Client Secret)
   - Dev ID
4. Update your `.env` file with production keys
5. Set `EBAY_USE_SANDBOX=false`

### 2. Test eBay Integration
```bash
# Test API connection
curl -X POST https://yourdomain.com/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "iPhone", "limit": 5}'
```

## 🔍 Monitoring & Maintenance

### 1. Log Monitoring
```bash
# View backend logs
pm2 logs fliplens-backend

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 2. Health Checks
```bash
# Check backend health
curl https://yourdomain.com/api/health

# Check PM2 status
pm2 status

# Check Nginx status
sudo systemctl status nginx
```

### 3. Database Backup
```bash
# Create backup script
cat > /home/ubuntu/backup_db.sh << EOF
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h localhost -U fliplens_user fliplens_production > /home/ubuntu/backups/fliplens_backup_$DATE.sql
find /home/ubuntu/backups -name "fliplens_backup_*.sql" -mtime +7 -delete
EOF

chmod +x /home/ubuntu/backup_db.sh

# Add to crontab for daily backups
echo "0 2 * * * /home/ubuntu/backup_db.sh" | crontab -
```

## 🚨 Security Checklist

- [ ] Strong SECRET_KEY and JWT_SECRET_KEY
- [ ] HTTPS enabled with valid SSL certificate
- [ ] Database credentials secured
- [ ] CORS origins properly configured
- [ ] Rate limiting enabled
- [ ] Security headers configured
- [ ] Firewall configured (only ports 22, 80, 443 open)
- [ ] Regular security updates scheduled
- [ ] Database backups automated
- [ ] Monitoring and alerting set up

## 🎯 Performance Optimization

### 1. Frontend Optimization
- Gzip compression enabled in Nginx
- Static asset caching configured
- CDN setup (optional)

### 2. Backend Optimization
- Database connection pooling
- Redis caching (optional)
- API response caching

### 3. Database Optimization
- Regular VACUUM and ANALYZE
- Proper indexing
- Connection pooling

## 📞 Support

If you encounter issues during deployment:

1. Check logs: `pm2 logs` and `/var/log/nginx/error.log`
2. Verify environment variables are set correctly
3. Test eBay API connectivity
4. Ensure database connection is working
5. Check firewall and security group settings

## 🎉 Post-Deployment

After successful deployment:

1. Test all functionality:
   - User registration/login
   - Search functionality
   - Save/unsave items
   - Profile management

2. Monitor performance and logs

3. Set up automated backups

4. Configure monitoring and alerting

Your FlipLens application is now ready for production use! 🚀
