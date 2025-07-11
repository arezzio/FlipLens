import requests
from flask import current_app
import os
import logging
import time
from typing import Dict, Any, Optional, List

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

            # Check if using test keys and return mock data
            if self._is_using_test_keys():
                return self._get_mock_search_results(sanitized_query, validated_limit)

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
                
                # Enhance results with profit calculations and confidence scores
                enhanced_results = self._enhance_results_with_analysis(results)

                return {
                    'results': enhanced_results,
                    'total': len(enhanced_results),
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

    def _enhance_results_with_analysis(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance search results with profit calculations and market analysis"""
        try:
            if not results:
                return results

            enhanced_results = []

            # Calculate market statistics for the entire result set
            prices = []
            for item in results:
                try:
                    price = float(item.get('price', 0))
                    if price > 0:
                        prices.append(price)
                except (ValueError, TypeError):
                    continue

            if not prices:
                return results

            # Market statistics
            avg_price = sum(prices) / len(prices)
            min_price = min(prices)
            max_price = max(prices)

            # Enhance each item
            for item in results:
                enhanced_item = item.copy()

                try:
                    # Calculate profit estimates
                    profit_data = self._calculate_profit_estimates(item, avg_price, min_price, max_price)
                    enhanced_item.update(profit_data)

                    # Update confidence score with market data
                    enhanced_item['confidence'] = self._calculate_enhanced_confidence(
                        item, len(results), avg_price
                    )

                except Exception as e:
                    logger.warning(f"Error enhancing item {item.get('itemId', 'unknown')}: {str(e)}")

                enhanced_results.append(enhanced_item)

            return enhanced_results

        except Exception as e:
            logger.error(f"Error enhancing results: {str(e)}")
            return results

    def _calculate_profit_estimates(self, item: Dict[str, Any], avg_price: float, min_price: float, max_price: float) -> Dict[str, Any]:
        """Calculate profit estimates for an item"""
        try:
            current_price = float(item.get('price', 0))
            if current_price <= 0:
                return {
                    'estimated_profit': 0,
                    'profit_margin': 0,
                    'market_position': 'unknown'
                }

            # Platform fees (eBay + PayPal typical fees)
            ebay_fee_rate = 0.10  # 10% eBay final value fee
            paypal_fee_rate = 0.029  # 2.9% PayPal fee
            shipping_cost = 10.0  # Estimated shipping cost

            # Calculate total fees
            total_fee_rate = ebay_fee_rate + paypal_fee_rate
            platform_fees = current_price * total_fee_rate
            total_costs = platform_fees + shipping_cost

            # Estimate purchase price (assume buying at 30-50% of market value)
            purchase_price_low = current_price * 0.3
            purchase_price_high = current_price * 0.5

            # Calculate profit estimates
            profit_low = current_price - total_costs - purchase_price_high
            profit_high = current_price - total_costs - purchase_price_low
            estimated_profit = (profit_low + profit_high) / 2

            # Calculate profit margin
            profit_margin = (estimated_profit / current_price) * 100 if current_price > 0 else 0

            # Determine market position
            if current_price <= min_price * 1.1:
                market_position = 'low'
            elif current_price >= max_price * 0.9:
                market_position = 'high'
            elif abs(current_price - avg_price) / avg_price <= 0.2:
                market_position = 'average'
            else:
                market_position = 'moderate'

            return {
                'estimated_profit': round(estimated_profit, 2),
                'profit_margin': round(profit_margin, 1),
                'market_position': market_position,
                'platform_fees': round(platform_fees, 2),
                'estimated_purchase_price': round((purchase_price_low + purchase_price_high) / 2, 2)
            }

        except Exception as e:
            logger.warning(f"Error calculating profit estimates: {str(e)}")
            return {
                'estimated_profit': 0,
                'profit_margin': 0,
                'market_position': 'unknown'
            }

    def _calculate_enhanced_confidence(self, item: Dict[str, Any], total_results: int, avg_price: float) -> float:
        """Calculate enhanced confidence score with market data"""
        try:
            base_confidence = item.get('confidence', 0.5)

            # Factors that increase confidence
            confidence_factors = []

            # Market data availability
            if total_results >= 10:
                confidence_factors.append(0.1)  # Good market data
            elif total_results >= 5:
                confidence_factors.append(0.05)  # Moderate market data

            # Price reasonableness
            try:
                price = float(item.get('price', 0))
                if price > 0 and avg_price > 0:
                    price_ratio = price / avg_price
                    if 0.5 <= price_ratio <= 2.0:  # Price within reasonable range
                        confidence_factors.append(0.1)
            except (ValueError, TypeError):
                pass

            # Item condition
            condition = item.get('condition', '').lower()
            if condition in ['new', 'new with tags', 'new without tags']:
                confidence_factors.append(0.1)
            elif condition in ['excellent', 'very good', 'good']:
                confidence_factors.append(0.05)

            # Location (US items generally more reliable)
            location = item.get('location', '').lower()
            if 'united states' in location or 'usa' in location or 'us' in location:
                confidence_factors.append(0.05)

            # Calculate final confidence
            enhanced_confidence = base_confidence + sum(confidence_factors)

            # Cap at 1.0
            return min(enhanced_confidence, 1.0)

        except Exception as e:
            logger.warning(f"Error calculating enhanced confidence: {str(e)}")
            return item.get('confidence', 0.5)

    def _is_using_test_keys(self) -> bool:
        """Check if we're using test API keys"""
        try:
            return (
                self.app_id.startswith('test-') or
                self.app_id == 'test-api-key' or
                self.app_id == 'test-app-id'
            )
        except:
            return True  # Assume test keys if we can't determine

    def _get_mock_search_results(self, query: str, limit: int) -> Dict[str, Any]:
        """Return mock search results for testing"""
        logger.info(f"Returning mock search results for query: '{query}'")

        # Generate mock items based on query
        mock_items = []
        for i in range(min(limit, 5)):  # Return up to 5 mock items
            item = {
                'title': f'{query} - Mock Item {i+1}',
                'itemId': f'mock-{i+1}-{hash(query) % 10000}',
                'viewItemURL': f'https://ebay.com/item/mock-{i+1}',
                'galleryURL': 'https://via.placeholder.com/150x150?text=Mock+Item',
                'price': round(50 + (i * 25) + (hash(query) % 100), 2),
                'currency': 'USD',
                'location': 'United States',
                'condition': ['New', 'Used', 'Excellent', 'Good'][i % 4],
                'confidence': 0.8 + (i * 0.05),
                'estimated_profit': round(20 + (i * 10), 2),
                'profit_margin': round(25 + (i * 5), 1),
                'market_position': ['low', 'average', 'moderate', 'high'][i % 4],
                'platform_fees': round(8 + (i * 2), 2),
                'estimated_purchase_price': round(30 + (i * 15), 2)
            }
            mock_items.append(item)

        return {
            'results': mock_items,
            'total': len(mock_items),
            'query': query,
            'limit': limit,
            'mock_data': True,
            'message': 'Mock data returned - configure production eBay API keys for real results'
        }