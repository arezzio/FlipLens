# FlipLens Backend

Flask API backend for the FlipLens application.

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
Create a `.env` file in the backend directory with:
```
FLASK_ENV=development
EBAY_API_KEY=your_ebay_api_key_here
```

3. Run the development server:
```bash
python app.py
```

The API will be available at `http://localhost:5000`

## API Endpoints

- `GET /` - API status
- `GET /api/health` - Health check
- `POST /api/search` - Search eBay for items (to be implemented)
- `GET /api/saved-items` - Get saved items (to be implemented)
- `POST /api/saved-items` - Save an item (to be implemented) 