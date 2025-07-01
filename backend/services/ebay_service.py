import requests
from flask import current_app
import os
import logging
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class EbayService:
    """Service class for eBay Finding API integration with enhanced security"""
    
    def __init__(self):
        # Validate API key configuration with enhanced security
        self.app_id = self._validate_api_key()
        
        # Use configuration for sandbox setting
        self.use_sandbox = current_app.config.get('EBAY_USE_SANDBOX', True)
        
        if self.use_sandbox:
            self.base_url = "https://svcs.sandbox.ebay.com/services/search/FindingService/v1"
            logger.info("Using eBay Sandbox API")
        else:
            self.base_url = "https://svcs.ebay.com/services/search/FindingService/v1"
            logger.info("Using eBay Production API")
        
        # Request timeout and retry configuration
        self.timeout = 15
        self.max_retries = 3
        self.retry_delay = 1
    
    def _validate_api_key(self) -> str:
        """Validate and return API key with enhanced security and error handling"""
        try:
            # Use the enhanced configuration method
            from config.settings import Config
            app_id = Config.get_api_key('EBAY_API_KEY')
            
            if not app_id:
                logger.error("eBay API key not configured")
                raise ValueError("EBAY_API_KEY not configured")
            
            # Additional security validation
            from utils.security import ApiKeySecurity, SecurityValidator
            
            # Validate format
            if not SecurityValidator.validate_api_key_format(app_id):
                logger.error("Invalid eBay API key format")
                raise ValueError("Invalid eBay API key format")
            
            # Validate strength
            is_strong, strength_msg = ApiKeySecurity.validate_api_key_strength(app_id)
            if not is_strong:
                logger.warning(f"eBay API key strength issue: {strength_msg}")
            
            # Log successful configuration (without exposing the key)
            masked_key = ApiKeySecurity.mask_api_key(app_id)
            logger.info(f"eBay API key configured successfully: {masked_key}")
            
            return app_id
            
        except ImportError:
            # Fallback to direct environment variable access
            app_id = current_app.config.get('EBAY_API_KEY') or current_app.config.get('EBAY_APP_ID')
            
            if not app_id:
                logger.error("eBay API key not configured")
                raise ValueError("EBAY_API_KEY or EBAY_APP_ID not configured")
            
            # Basic validation
            if not isinstance(app_id, str) or len(app_id) < 10:
                logger.error("Invalid eBay API key format")
                raise ValueError("Invalid eBay API key format")
            
            logger.info(f"eBay API key configured (length: {len(app_id)})")
            return app_id
    
    def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request with retry logic and enhanced security measures"""
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Making eBay API request (attempt {attempt + 1}/{self.max_retries})")
                
                # Enhanced request headers with security considerations
                headers = {
                    'User-Agent': 'FlipLens/1.0 (Secure)',
                    'Accept': 'application/json',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'close'  # Prevent connection reuse for sensitive requests
                }
                
                response = requests.get(
                    self.base_url,
                    params=params,
                    timeout=self.timeout,
                    headers=headers,
                    allow_redirects=False  # Prevent redirect attacks
                )
                
                # Log response status (without sensitive data)
                logger.debug(f"eBay API response status: {response.status_code}")
                
                # Handle different HTTP status codes with enhanced security
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    logger.error("eBay API authentication failed - check API key")
                    return {"error": "Authentication failed", "message": "Invalid API key"}
                elif response.status_code == 429:
                    logger.warning("eBay API rate limit exceeded")
                    return {"error": "Rate limit exceeded", "message": "Too many requests to eBay API"}
                elif response.status_code >= 500:
                    logger.error(f"eBay API server error: {response.status_code}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (2 ** attempt))
                        continue
                    return {"error": "eBay API server error", "message": "eBay service temporarily unavailable"}
                else:
                    logger.error(f"eBay API error: {response.status_code}")
                    return {"error": "eBay API error", "message": f"HTTP {response.status_code}"}
                
            except requests.exceptions.Timeout:
                logger.warning(f"eBay API timeout (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
                return {"error": "Timeout", "message": "eBay API request timed out"}
                
            except requests.exceptions.ConnectionError:
                logger.error(f"eBay API connection error (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
                return {"error": "Connection error", "message": "Unable to connect to eBay API"}
                
            except requests.exceptions.RequestException as e:
                logger.error(f"eBay API request error: {str(e)}")
                return {"error": "Request error", "message": str(e)}
                
            except Exception as e:
                logger.error(f"Unexpected error in eBay API request: {str(e)}")
                return {"error": "Unexpected error", "message": "An unexpected error occurred"}
        
        return {"error": "Max retries exceeded", "message": "Failed after maximum retry attempts"}
    
    def _sanitize_query(self, query: str) -> str:
        """Sanitize search query to prevent injection attacks"""
        if not isinstance(query, str):
            return ""
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '|', '`', '$', '(', ')', '{', '}']
        for char in dangerous_chars:
            query = query.replace(char, '')
        
        # Limit query length
        if len(query) > 100:
            query = query[:100]
        
        return query.strip()
    
    def _validate_limit(self, limit: Any) -> int:
        """Validate and sanitize limit parameter"""
        try:
            limit = int(limit)
            if limit < 1:
                return 1
            elif limit > 100:
                return 100
            return limit
        except (ValueError, TypeError):
            return 20
    
    def search_items(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """
        Search for items using eBay Finding API with enhanced security
        
        Args:
            query (str): Search query
            limit (int): Maximum number of results
            
        Returns:
            dict: Search results from eBay API or error information
        """
        try:
            # Validate and sanitize inputs
            if not query or not isinstance(query, str):
                logger.warning("Invalid query parameter")
                return {"error": "Invalid query", "message": "Query must be a non-empty string"}
            
            sanitized_query = self._sanitize_query(query)
            if not sanitized_query:
                logger.warning("Query sanitization resulted in empty string")
                return {"error": "Invalid query", "message": "Query contains invalid characters"}
            
            validated_limit = self._validate_limit(limit)
            
            logger.info(f"Searching eBay for: '{sanitized_query}' (limit: {validated_limit})")
            
            # Prepare API request parameters
            params = {
                'OPERATION-NAME': 'findItemsByKeywords',
                'SERVICE-VERSION': '1.0.0',
                'SECURITY-APPNAME': self.app_id,
                'RESPONSE-DATA-FORMAT': 'JSON',
                'REST-PAYLOAD': '',
                'keywords': sanitized_query,
                'paginationInput.entriesPerPage': validated_limit
            }
            
            # Make API request
            response_data = self._make_request(params)
            
            # Check for API errors
            if 'error' in response_data:
                logger.error(f"eBay API error: {response_data['error']}")
                return response_data
            
            # Parse and validate response
            try:
                # Extract items from response
                response = response_data.get('findItemsByKeywordsResponse', [{}])
                if not response:
                    logger.warning("Empty response from eBay API")
                    return {"results": [], "total": 0}
                
                search_result = response[0].get('searchResult', [{}])
                if not search_result:
                    logger.warning("No search results from eBay API")
                    return {"results": [], "total": 0}
                
                items = search_result[0].get('item', [])
                
                # Process and sanitize items
                results = []
                for item in items:
                    try:
                        processed_item = self._process_item(item)
                        if processed_item:
                            results.append(processed_item)
                    except Exception as e:
                        logger.warning(f"Error processing item: {str(e)}")
                        continue
                
                logger.info(f"Search completed successfully. Found {len(results)} items")
                
                return {
                    'results': results,
                    'total': len(results),
                    'query': sanitized_query,
                    'limit': validated_limit
                }
                
            except Exception as e:
                logger.error(f"Error parsing eBay API response: {str(e)}")
                return {"error": "Response parsing error", "message": "Failed to parse eBay API response"}
                
        except Exception as e:
            logger.error(f"Unexpected error in search_items: {str(e)}", exc_info=True)
            return {"error": "Unexpected error", "message": "An unexpected error occurred"}
    
    def _process_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process and sanitize a single eBay item, including confidence score"""
        try:
            # Extract and validate item data
            title = self._extract_safe_string(item.get('title', ['']))
            item_id = self._extract_safe_string(item.get('itemId', ['']))
            view_item_url = self._extract_safe_string(item.get('viewItemURL', ['']))
            gallery_url = self._extract_safe_string(item.get('galleryURL', ['']))
            
            # Extract price information
            selling_status = item.get('sellingStatus', [{}])
            current_price = selling_status[0].get('currentPrice', [{}]) if selling_status else [{}]
            price = self._extract_safe_string(current_price[0].get('__value__', '')) if current_price else ''
            currency = self._extract_safe_string(current_price[0].get('@currencyId', '')) if current_price else ''
            
            # Extract other fields
            location = self._extract_safe_string(item.get('location', ['']))
            condition = self._extract_safe_string(item.get('condition', [{}])[0].get('conditionDisplayName', ['']) if item.get('condition') else [''])
            
            # Validate required fields
            if not title or not item_id:
                return None

            # --- Confidence Score Calculation ---
            score = 0.0
            total = 6  # title, item_id, view_item_url, gallery_url, price+currency, location, condition
            present = 0
            if title: present += 1
            if item_id: present += 1
            if view_item_url: present += 1
            if gallery_url: present += 1
            if price and currency:
                try:
                    price_val = float(price)
                    if 1 <= price_val <= 10000:
                        present += 1
                except Exception:
                    pass
            if location: present += 1
            if condition: present += 1
            score = present / total
            # Clamp between 0 and 1
            score = max(0.0, min(1.0, score))
            # --- End Confidence Score ---

            return {
                'title': title,
                'itemId': item_id,
                'viewItemURL': view_item_url,
                'galleryURL': gallery_url,
                'price': price,
                'currency': currency,
                'location': location,
                'condition': condition,
                'confidence': round(score, 2),
            }
            
        except Exception as e:
            logger.warning(f"Error processing item data: {str(e)}")
            return None
    
    def _extract_safe_string(self, value: Any) -> str:
        """Extract and sanitize string value from eBay response"""
        if isinstance(value, list):
            value = value[0] if value else ''
        
        if not isinstance(value, str):
            return ''
        
        # Basic sanitization
        value = value.strip()
        if len(value) > 500:  # Limit length
            value = value[:500]
        
        return value 