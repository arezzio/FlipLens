import axios from 'axios';
import { apiService } from '../api';
import { searchCache, savedItemsCache } from '../../utils/offlineCache';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock the cache
jest.mock('../../utils/offlineCache', () => ({
  searchCache: {
    set: jest.fn(),
    get: jest.fn(),
    has: jest.fn()
  },
  savedItemsCache: {
    set: jest.fn(),
    get: jest.fn(),
    has: jest.fn()
  }
}));

describe('API Service Error Handling', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset axios mock
    mockedAxios.create.mockReturnValue(mockedAxios);
  });

  describe('searchItems', () => {
    it('should handle network errors and return cached data', async () => {
      // Mock network error
      mockedAxios.post.mockRejectedValue({
        code: 'ECONNABORTED',
        message: 'Network Error',
        response: undefined
      });

      // Mock cached data
      const cachedData = {
        results: [{ title: 'Cached Item', itemId: '123', price: '100' }],
        total: 1,
        query: 'test',
        limit: 20,
        status: 'success'
      };
      (searchCache.get as jest.Mock).mockReturnValue(cachedData);

      const result = await apiService.searchItems('test', 20);

      expect(result).toEqual({
        ...cachedData,
        query: 'test',
        status: 'success',
        _cached: true
      });
      expect(searchCache.get).toHaveBeenCalledWith('search_test_20');
    });

    it('should handle timeout errors and return cached data', async () => {
      // Mock timeout error
      mockedAxios.post.mockRejectedValue({
        code: 'ECONNABORTED',
        message: 'timeout of 15000ms exceeded',
        response: undefined
      });

      const cachedData = {
        results: [{ title: 'Cached Item', itemId: '123', price: '100' }],
        total: 1,
        query: 'test',
        limit: 20,
        status: 'success'
      };
      (searchCache.get as jest.Mock).mockReturnValue(cachedData);

      const result = await apiService.searchItems('test', 20);

      expect(result._cached).toBe(true);
    });

    it('should throw error when no cached data available', async () => {
      // Mock network error
      mockedAxios.post.mockRejectedValue({
        code: 'ECONNABORTED',
        message: 'Network Error',
        response: undefined
      });

      // No cached data
      (searchCache.get as jest.Mock).mockReturnValue(null);

      await expect(apiService.searchItems('test', 20)).rejects.toThrow();
    });

    it('should cache successful responses', async () => {
      const mockResponse = {
        data: {
          results: [{ title: 'Test Item', itemId: '123', price: '100' }],
          total: 1,
          query: 'test',
          limit: 20,
          status: 'success'
        }
      };

      mockedAxios.post.mockResolvedValue(mockResponse);

      await apiService.searchItems('test', 20);

      expect(searchCache.set).toHaveBeenCalledWith(
        'search_test_20',
        mockResponse.data
      );
    });
  });

  describe('getSavedItems', () => {
    it('should handle network errors and return cached data', async () => {
      // Mock network error
      mockedAxios.get.mockRejectedValue({
        code: 'ECONNABORTED',
        message: 'Network Error',
        response: undefined
      });

      // Mock cached data
      const cachedData = {
        items: [{ id: '123', title: 'Cached Item', price: '100' }],
        total: 1,
        status: 'success'
      };
      (savedItemsCache.get as jest.Mock).mockReturnValue(cachedData);

      const result = await apiService.getSavedItems();

      expect(result).toEqual({
        ...cachedData,
        status: 'success',
        _cached: true
      });
    });

    it('should cache successful responses', async () => {
      const mockResponse = {
        data: {
          items: [{ id: '123', title: 'Test Item', price: '100' }],
          total: 1,
          status: 'success'
        }
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      await apiService.getSavedItems();

      expect(savedItemsCache.set).toHaveBeenCalledWith(
        'saved_items_all',
        mockResponse.data
      );
    });
  });

  describe('error categorization', () => {
    it('should categorize network errors correctly', async () => {
      mockedAxios.post.mockRejectedValue({
        code: 'ECONNABORTED',
        message: 'Network Error',
        response: undefined
      });

      (searchCache.get as jest.Mock).mockReturnValue(null);

      try {
        await apiService.searchItems('test', 20);
      } catch (error: any) {
        expect(error.code).toBe('NETWORK_ERROR');
        expect(error.retryable).toBe(true);
      }
    });

    it('should categorize timeout errors correctly', async () => {
      mockedAxios.post.mockRejectedValue({
        code: 'ECONNABORTED',
        message: 'timeout of 15000ms exceeded',
        response: undefined
      });

      (searchCache.get as jest.Mock).mockReturnValue(null);

      try {
        await apiService.searchItems('test', 20);
      } catch (error: any) {
        expect(error.code).toBe('TIMEOUT_ERROR');
        expect(error.retryable).toBe(true);
      }
    });

    it('should categorize server errors correctly', async () => {
      mockedAxios.post.mockRejectedValue({
        response: {
          status: 500,
          data: { message: 'Internal Server Error' }
        }
      });

      (searchCache.get as jest.Mock).mockReturnValue(null);

      try {
        await apiService.searchItems('test', 20);
      } catch (error: any) {
        expect(error.code).toBe('SERVER_ERROR');
        expect(error.retryable).toBe(true);
      }
    });

    it('should categorize validation errors correctly', async () => {
      mockedAxios.post.mockRejectedValue({
        response: {
          status: 400,
          data: { message: 'Invalid request' }
        }
      });

      (searchCache.get as jest.Mock).mockReturnValue(null);

      try {
        await apiService.searchItems('test', 20);
      } catch (error: any) {
        expect(error.code).toBe('VALIDATION_ERROR');
        expect(error.retryable).toBe(false);
      }
    });

    it('should categorize rate limit errors correctly', async () => {
      mockedAxios.post.mockRejectedValue({
        response: {
          status: 429,
          headers: { 'retry-after': '60' },
          data: { message: 'Too many requests' }
        }
      });

      (searchCache.get as jest.Mock).mockReturnValue(null);

      try {
        await apiService.searchItems('test', 20);
      } catch (error: any) {
        expect(error.code).toBe('RATE_LIMIT_ERROR');
        expect(error.retryable).toBe(true);
        expect(error.retryAfter).toBe(60);
      }
    });
  });

  describe('retry logic', () => {
    it('should retry failed requests with exponential backoff', async () => {
      // Mock multiple failures then success
      mockedAxios.post
        .mockRejectedValueOnce({
          code: 'ECONNABORTED',
          message: 'Network Error',
          response: undefined
        })
        .mockRejectedValueOnce({
          code: 'ECONNABORTED',
          message: 'Network Error',
          response: undefined
        })
        .mockResolvedValueOnce({
          data: {
            results: [{ title: 'Success Item', itemId: '123', price: '100' }],
            total: 1,
            query: 'test',
            limit: 20,
            status: 'success'
          }
        });

      (searchCache.get as jest.Mock).mockReturnValue(null);

      const result = await apiService.searchItems('test', 20);

      expect(mockedAxios.post).toHaveBeenCalledTimes(3);
      expect(result.status).toBe('success');
    });

    it('should not retry non-retryable errors', async () => {
      mockedAxios.post.mockRejectedValue({
        response: {
          status: 400,
          data: { message: 'Invalid request' }
        }
      });

      (searchCache.get as jest.Mock).mockReturnValue(null);

      try {
        await apiService.searchItems('test', 20);
      } catch (error: any) {
        expect(error.code).toBe('VALIDATION_ERROR');
        expect(mockedAxios.post).toHaveBeenCalledTimes(1); // No retries
      }
    });
  });
}); 