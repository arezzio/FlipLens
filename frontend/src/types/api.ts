export interface SearchResult {
  title: string;
  itemId: string;
  viewItemURL: string;
  galleryURL: string;
  price: string;
  currency: string;
  location: string;
  condition: string;
  confidence?: number;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
  limit: number;
  status: 'success' | 'error';
  _cached?: boolean;
}

export interface SavedItem {
  id: string;
  title: string;
  price: string;
  currency: string;
  image_url: string;
  item_url: string;
  condition: string;
  location: string;
  saved_at: string;
  notes: string;
  updated_at?: string;
}

export interface SavedItemsResponse {
  items: SavedItem[];
  total: number;
  status: 'success' | 'error';
  _cached?: boolean;
}

// Enhanced error types for better error handling
export interface ApiError {
  error: string;
  message: string;
  status: 'error';
  code?: string;
  details?: string;
  retryable?: boolean;
  timestamp?: string;
}

export interface NetworkError extends ApiError {
  error: 'NetworkError';
  retryable: true;
  code: 'NETWORK_ERROR';
}

export interface TimeoutError extends ApiError {
  error: 'TimeoutError';
  retryable: true;
  code: 'TIMEOUT_ERROR';
}

export interface ServerError extends ApiError {
  error: 'ServerError';
  retryable: true;
  code: 'SERVER_ERROR';
}

export interface ValidationError extends ApiError {
  error: 'ValidationError';
  retryable: false;
  code: 'VALIDATION_ERROR';
}

export interface AuthenticationError extends ApiError {
  error: 'AuthenticationError';
  retryable: false;
  code: 'AUTH_ERROR';
}

export interface RateLimitError extends ApiError {
  error: 'RateLimitError';
  retryable: true;
  code: 'RATE_LIMIT_ERROR';
  retryAfter?: number;
}

// Error state types for components
export interface ErrorState {
  hasError: boolean;
  error: ApiError | null;
  retryCount: number;
  lastRetryTime: number | null;
  isRetrying: boolean;
}

// Loading state types
export interface LoadingState {
  isLoading: boolean;
  loadingType: 'search' | 'save' | 'load' | 'delete' | null;
  progress?: number;
}

// Retry configuration
export interface RetryConfig {
  maxRetries: number;
  retryDelay: number;
  backoffMultiplier: number;
  maxRetryDelay: number;
} 