# FlipLens Backend

Flask API backend for the FlipLens application - a thrift resale scanner and ROI tracker.

## Features

- eBay Finding API integration for product search
- Saved items management with SQLite database
- Rate limiting and error handling
- CORS support for frontend integration
- Health monitoring endpoints

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
Create a `.env` file in the backend directory with:
```
FLASK_ENV=development
SECRET_KEY=your_secret_key_here
EBAY_API_KEY=your_ebay_api_key_here
EBAY_APP_ID=your_ebay_app_id_here
EBAY_CERT_ID=your_ebay_cert_id_here
EBAY_DEV_ID=your_ebay_dev_id_here
```

3. Run the development server:
```bash
python app.py
```

The API will be available at `http://localhost:5000`

## API Endpoints

### Health & Status
- `GET /` - API status and version information
- `GET /api/health` - Health check endpoint

### Search
- `POST /api/search` - Search eBay for items
  - **Request Body:**
    ```json
    {
      "query": "iPhone 13",
      "limit": 20
    }
    ```
  - **Response:**
    ```json
    {
      "results": [
        {
          "itemId": "123456789",
          "title": "iPhone 13 Pro Max",
          "price": "999.99",
          "currency": "USD",
          "galleryURL": "https://...",
          "viewItemURL": "https://...",
          "condition": "New",
          "location": "United States"
        }
      ]
    }
    ```

### Saved Items
- `GET /api/saved-items` - Get all saved items
  - **Response:**
    ```json
    {
      "items": [
        {
          "id": "123456789",
          "title": "iPhone 13 Pro Max",
          "price": "999.99",
          "currency": "USD",
          "image_url": "https://...",
          "item_url": "https://...",
          "condition": "New",
          "location": "United States",
          "saved_at": "2024-01-15T10:30:00Z",
          "notes": "Good deal for resale"
        }
      ]
    }
    ```

- `POST /api/saved-items` - Save an item
  - **Request Body:**
    ```json
    {
      "item_id": "123456789",
      "title": "iPhone 13 Pro Max",
      "price": "999.99",
      "currency": "USD",
      "image_url": "https://...",
      "item_url": "https://...",
      "condition": "New",
      "location": "United States",
      "notes": "Good deal for resale"
    }
    ```

- `PUT /api/saved-items/<item_id>` - Update saved item notes
  - **Request Body:**
    ```json
    {
      "notes": "Updated notes about this item"
    }
    ```

- `DELETE /api/saved-items/<item_id>` - Delete a saved item

## Error Handling

The API includes comprehensive error handling:

- **400 Bad Request** - Invalid request data
- **404 Not Found** - Resource not found
- **429 Too Many Requests** - Rate limit exceeded
- **500 Internal Server Error** - Server error

All errors return JSON responses with error details.

## Rate Limiting

The API implements rate limiting to prevent abuse:
- 100 requests per minute per IP address
- Rate limit headers included in responses

## Testing

Run the test suite:
```bash
pytest test_app.py -v
```

## Development

The backend uses:
- **Flask** - Web framework
- **Flask-CORS** - Cross-origin resource sharing
- **SQLite** - Database for saved items
- **python-dotenv** - Environment variable management
- **requests** - HTTP client for eBay API

## Architecture

```
backend/
├── app.py                 # Application entry point
├── __init__.py           # Flask app factory
├── routes/               # API route definitions
│   ├── search.py         # Search endpoints
│   ├── saved_items.py    # Saved items endpoints
│   └── health.py         # Health check endpoints
├── services/             # Business logic
│   └── ebay_service.py   # eBay API integration
├── utils/                # Utilities
│   ├── error_handlers.py # Error handling
│   └── rate_limiter.py   # Rate limiting
├── models/               # Data models
└── config/               # Configuration
``` 