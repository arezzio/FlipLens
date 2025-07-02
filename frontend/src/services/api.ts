import axios, { AxiosResponse, AxiosError } from 'axios';
import { 
  SearchResponse, 
  SavedItemsResponse, 
  SavedItem, 
  ApiError,
  NetworkError,
  TimeoutError,
  ServerError,
  ValidationError,
  AuthenticationError,
  RateLimitError,
  RetryConfig
} from '../types/api';
import { searchCache, savedItemsCache } from '../utils/offlineCache';
import { config } from '../utils/config';

// Use configuration utility for API URL
const API_BASE_URL = config.apiUrl;

// Retry configuration
const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  retryDelay: 1000,
  backoffMultiplier: 2,
  maxRetryDelay: 10000
};

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000, // Increased timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('fliplens_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Enhanced error categorization
const categorizeError = (error: AxiosError): ApiError => {
  const timestamp = new Date().toISOString();
  
  if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
    return {
      error: 'TimeoutError',
      message: 'Request timed out. Please check your connection and try again.',
      status: 'error',
      code: 'TIMEOUT_ERROR',
      retryable: true,
      timestamp
    } as TimeoutError;
  }

  if (!error.response) {
    // Network error
    return {
      error: 'NetworkError',
      message: 'Unable to connect to server. Please check your internet connection.',
      status: 'error',
      code: 'NETWORK_ERROR',
      retryable: true,
      timestamp
    } as NetworkError;
  }

  const { status, data } = error.response;
  
  // Type guard for error response data
  const errorData = data as { message?: string; details?: string } | undefined;
  
  switch (status) {
    case 400:
      return {
        error: 'ValidationError',
        message: errorData?.message || 'Invalid request. Please check your input and try again.',
        status: 'error',
        code: 'VALIDATION_ERROR',
        retryable: false,
        details: errorData?.details,
        timestamp
      } as ValidationError;
    
    case 401:
      return {
        error: 'AuthenticationError',
        message: 'Authentication required. Please log in and try again.',
        status: 'error',
        code: 'AUTH_ERROR',
        retryable: false,
        timestamp
      } as AuthenticationError;
    
    case 429:
      return {
        error: 'RateLimitError',
        message: 'Too many requests. Please wait a moment and try again.',
        status: 'error',
        code: 'RATE_LIMIT_ERROR',
        retryable: true,
        retryAfter: parseInt(error.response.headers['retry-after'] || '60'),
        timestamp
      } as RateLimitError;
    
    case 500:
    case 502:
    case 503:
    case 504:
      return {
        error: 'ServerError',
        message: 'Server error occurred. Please try again later.',
        status: 'error',
        code: 'SERVER_ERROR',
        retryable: true,
        details: errorData?.details,
        timestamp
      } as ServerError;
    
    default:
      return {
        error: 'ServerError',
        message: errorData?.message || `Unexpected error (${status}). Please try again.`,
        status: 'error',
        code: 'SERVER_ERROR',
        retryable: status >= 500,
        details: errorData?.details,
        timestamp
      } as ServerError;
  }
};

// Retry logic with exponential backoff
const retryRequest = async <T>(
  requestFn: () => Promise<T>,
  retryConfig: RetryConfig = DEFAULT_RETRY_CONFIG
): Promise<T> => {
  let lastError: ApiError | null = null;
  
  for (let attempt = 0; attempt <= retryConfig.maxRetries; attempt++) {
    try {
      return await requestFn();
    } catch (error) {
      const apiError = categorizeError(error as AxiosError);
      lastError = apiError;
      
      // Don't retry if error is not retryable or we've reached max retries
      if (!apiError.retryable || attempt === retryConfig.maxRetries) {
        throw apiError;
      }
      
      // Calculate delay with exponential backoff
      const delay = Math.min(
        retryConfig.retryDelay * Math.pow(retryConfig.backoffMultiplier, attempt),
        retryConfig.maxRetryDelay
      );
      
      // Special handling for rate limit errors
      if (apiError.code === 'RATE_LIMIT_ERROR') {
        const rateLimitError = apiError as RateLimitError;
        const retryAfter = rateLimitError.retryAfter || 60;
        console.warn(`Rate limited. Retrying after ${retryAfter} seconds...`);
        await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
      } else {
        console.warn(`Request failed (attempt ${attempt + 1}/${retryConfig.maxRetries + 1}). Retrying in ${delay}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  
  // This should never be reached, but TypeScript requires it
  throw new Error(lastError?.message || 'Request failed after all retries');
};

// Response interceptor to handle common errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const apiError = categorizeError(error);
    console.error('API Error:', apiError);
    return Promise.reject(apiError);
  }
);

// Generic HTTP methods
const makeRequest = async (method: string, url: string, data?: any, config?: any) => {
  return retryRequest(async () => {
    switch (method.toUpperCase()) {
      case 'GET':
        return await apiClient.get(url, config);
      case 'POST':
        return await apiClient.post(url, data, config);
      case 'PUT':
        return await apiClient.put(url, data, config);
      case 'DELETE':
        return await apiClient.delete(url, { ...config, data });
      default:
        throw new Error(`Unsupported HTTP method: ${method}`);
    }
  });
};

export const apiService = {
  // Generic HTTP methods
  get: async (url: string, config?: any) => {
    return makeRequest('GET', url, null, config);
  },

  post: async (url: string, data?: any, config?: any) => {
    return makeRequest('POST', url, data, config);
  },

  put: async (url: string, data?: any, config?: any) => {
    return makeRequest('PUT', url, data, config);
  },

  delete: async (url: string, data?: any, config?: any) => {
    return makeRequest('DELETE', url, data, config);
  },

  // Search endpoints
  searchItems: async (query: string, limit: number = 20): Promise<SearchResponse> => {
    const cacheKey = `search_${query}_${limit}`;
    
    try {
      const response: AxiosResponse<SearchResponse> = await retryRequest(async () => {
        const result = await apiClient.post('/search', {
          query,
          limit
        });
        
        // Cache successful responses
        searchCache.set(cacheKey, result.data);
        return result;
      });
      
      return response.data;
    } catch (error) {
      const apiError = error as ApiError;
      
      // If it's a network error, try to serve from cache
      if (apiError.code === 'NETWORK_ERROR' || apiError.code === 'TIMEOUT_ERROR') {
        const cachedData = searchCache.get(cacheKey);
        if (cachedData) {
          console.log('Serving search results from cache due to network error');
          return {
            ...cachedData,
            query,
            status: 'success' as const,
            _cached: true
          };
        }
      }
      
      throw apiError;
    }
  },

  searchItemsGet: async (query: string, limit: number = 20): Promise<SearchResponse> => {
    const cacheKey = `search_get_${query}_${limit}`;
    
    try {
      const response: AxiosResponse<SearchResponse> = await retryRequest(async () => {
        const result = await apiClient.get('/search', {
          params: { q: query, limit }
        });
        
        // Cache successful responses
        searchCache.set(cacheKey, result.data);
        return result;
      });
      
      return response.data;
    } catch (error) {
      const apiError = error as ApiError;
      
      // If it's a network error, try to serve from cache
      if (apiError.code === 'NETWORK_ERROR' || apiError.code === 'TIMEOUT_ERROR') {
        const cachedData = searchCache.get(cacheKey);
        if (cachedData) {
          console.log('Serving search results from cache due to network error');
          return {
            ...cachedData,
            query,
            status: 'success' as const,
            _cached: true
          };
        }
      }
      
      throw apiError;
    }
  },

  // Saved items endpoints
  getSavedItems: async (): Promise<SavedItemsResponse> => {
    const cacheKey = 'saved_items_all';
    
    try {
      const response: AxiosResponse<SavedItemsResponse> = await retryRequest(async () => {
        const result = await apiClient.get('/saved-items');
        
        // Cache successful responses
        savedItemsCache.set(cacheKey, result.data);
        return result;
      });
      
      return response.data;
    } catch (error) {
      const apiError = error as ApiError;
      
      // If it's a network error, try to serve from cache
      if (apiError.code === 'NETWORK_ERROR' || apiError.code === 'TIMEOUT_ERROR') {
        const cachedData = savedItemsCache.get(cacheKey);
        if (cachedData) {
          console.log('Serving saved items from cache due to network error');
          return {
            ...cachedData,
            status: 'success' as const,
            _cached: true
          };
        }
      }
      
      throw apiError;
    }
  },

  saveItem: async (itemData: {
    item_id: string;
    title: string;
    price: string;
    currency?: string;
    image_url?: string;
    item_url?: string;
    condition?: string;
    location?: string;
    notes?: string;
  }): Promise<{ message: string; item: SavedItem; status: string }> => {
    return retryRequest(async () => {
      const response = await apiClient.post('/saved-items', itemData);
      return response.data;
    });
  },

  getSavedItem: async (itemId: string): Promise<{ item: SavedItem; status: string }> => {
    return retryRequest(async () => {
      const response = await apiClient.get(`/saved-items/${itemId}`);
      return response.data;
    });
  },

  updateSavedItem: async (itemId: string, updates: Partial<SavedItem>): Promise<{ message: string; item: SavedItem; status: string }> => {
    return retryRequest(async () => {
      const response = await apiClient.put(`/saved-items/${itemId}`, updates);
      return response.data;
    });
  },

  deleteSavedItem: async (itemId: string): Promise<{ message: string; deleted_item: SavedItem; status: string }> => {
    return retryRequest(async () => {
      const response = await apiClient.delete(`/saved-items/${itemId}`);
      return response.data;
    });
  },

  // Health check
  healthCheck: async (): Promise<{ status: string; service: string; version: string }> => {
    return retryRequest(async () => {
      const response = await apiClient.get('/health');
      return response.data;
    });
  },

  // Utility functions
  isRetryableError: (error: ApiError): boolean => {
    return error.retryable || false;
  },

  getRetryDelay: (error: ApiError): number => {
    if (error.code === 'RATE_LIMIT_ERROR') {
      const rateLimitError = error as RateLimitError;
      return (rateLimitError.retryAfter || 60) * 1000;
    }
    return DEFAULT_RETRY_CONFIG.retryDelay;
  },

  // Authentication endpoints
  login: async (email: string, password: string): Promise<any> => {
    return retryRequest(async () => {
      const response = await apiClient.post('/auth/login', {
        email,
        password
      });
      return response.data;
    });
  },

  register: async (userData: {
    email: string;
    username: string;
    password: string;
    first_name?: string;
    last_name?: string;
  }): Promise<any> => {
    return retryRequest(async () => {
      const response = await apiClient.post('/auth/register', userData);
      return response.data;
    });
  },

  getCurrentUser: async (): Promise<any> => {
    return retryRequest(async () => {
      const response = await apiClient.get('/auth/me');
      return response.data;
    });
  },

  logout: async (): Promise<any> => {
    return retryRequest(async () => {
      const response = await apiClient.post('/auth/logout');
      return response.data;
    });
  },

  refreshToken: async (): Promise<any> => {
    return retryRequest(async () => {
      const response = await apiClient.post('/auth/refresh');
      return response.data;
    });
  },

  getHealth: async (): Promise<{ status: string; service: string; version: string }> => {
    return retryRequest(async () => {
      const response = await apiClient.get('/health');
      return response.data;
    });
  },
};