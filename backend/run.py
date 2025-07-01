#!/usr/bin/env python3
"""
Simple script to run the Flask application
"""
import os
from app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting FlipLens API server on port {port}")
    app.run(debug=True, host='0.0.0.0', port=port) 