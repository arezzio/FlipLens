import OfflineCache from '../offlineCache';

// Mock localStorage
const localStorageMock = (() => {
  let store: { [key: string]: string } = {};
  return {
    getItem: jest.fn((key: string) => store[key] || null),
    setItem: jest.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: jest.fn((key: string) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true
});

describe('OfflineCache', () => {
  let cache: OfflineCache;

  beforeEach(() => {
    localStorageMock.clear();
    jest.clearAllMocks();
    cache = new OfflineCache('test_cache', {
      maxAge: 1000, // 1 second for testing
      maxItems: 3
    });
  });

  describe('set and get', () => {
    it('should set and get data correctly', () => {
      const testData = { test: 'data' };
      cache.set('test_key', testData);
      
      const result = cache.get('test_key');
      expect(result).toEqual(testData);
    });

    it('should return null for non-existent keys', () => {
      const result = cache.get('non_existent');
      expect(result).toBeNull();
    });

    it('should handle expired data', async () => {
      const testData = { test: 'data' };
      cache.set('test_key', testData, 10); // 10ms expiration
      
      // Wait for expiration
      await new Promise(resolve => setTimeout(resolve, 20));
      
      const result = cache.get('test_key');
      expect(result).toBeNull();
    });

    it('should use default maxAge when not specified', () => {
      const testData = { test: 'data' };
      cache.set('test_key', testData);
      
      const result = cache.get('test_key');
      expect(result).toEqual(testData);
    });
  });

  describe('has', () => {
    it('should return true for existing keys', () => {
      cache.set('test_key', { test: 'data' });
      expect(cache.has('test_key')).toBe(true);
    });

    it('should return false for non-existing keys', () => {
      expect(cache.has('non_existent')).toBe(false);
    });

    it('should return false for expired keys', async () => {
      cache.set('test_key', { test: 'data' }, 10); // 10ms expiration
      
      // Wait for expiration
      await new Promise(resolve => setTimeout(resolve, 20));
      
      expect(cache.has('test_key')).toBe(false);
    });
  });

  describe('remove', () => {
    it('should remove existing keys', () => {
      cache.set('test_key', { test: 'data' });
      expect(cache.has('test_key')).toBe(true);
      
      cache.remove('test_key');
      expect(cache.has('test_key')).toBe(false);
    });

    it('should handle removing non-existing keys gracefully', () => {
      expect(() => cache.remove('non_existent')).not.toThrow();
    });
  });

  describe('clear', () => {
    it('should clear all cached data', () => {
      cache.set('key1', { data: '1' });
      cache.set('key2', { data: '2' });
      
      expect(cache.getSize()).toBe(2);
      
      cache.clear();
      expect(cache.getSize()).toBe(0);
    });
  });

  describe('getKeys', () => {
    it('should return all cache keys', () => {
      cache.set('key1', { data: '1' });
      cache.set('key2', { data: '2' });
      
      const keys = cache.getKeys();
      expect(keys).toContain('key1');
      expect(keys).toContain('key2');
      expect(keys.length).toBe(2);
    });

    it('should not include expired keys', async () => {
      cache.set('key1', { data: '1' }, 10); // 10ms expiration
      cache.set('key2', { data: '2' }); // No expiration
      
      // Wait for expiration
      await new Promise(resolve => setTimeout(resolve, 20));
      
      const keys = cache.getKeys();
      expect(keys).toContain('key2');
      expect(keys).not.toContain('key1');
      expect(keys.length).toBe(1);
    });
  });

  describe('getSize', () => {
    it('should return correct cache size', () => {
      expect(cache.getSize()).toBe(0);
      
      cache.set('key1', { data: '1' });
      expect(cache.getSize()).toBe(1);
      
      cache.set('key2', { data: '2' });
      expect(cache.getSize()).toBe(2);
    });

    it('should not count expired items', async () => {
      cache.set('key1', { data: '1' }, 10); // 10ms expiration
      cache.set('key2', { data: '2' }); // No expiration
      
      expect(cache.getSize()).toBe(2);
      
      // Wait for expiration
      await new Promise(resolve => setTimeout(resolve, 20));
      
      expect(cache.getSize()).toBe(1);
    });
  });

  describe('cleanup', () => {
    it('should remove expired items automatically', async () => {
      cache.set('key1', { data: '1' }, 10); // 10ms expiration
      cache.set('key2', { data: '2' }); // No expiration
      
      expect(cache.getSize()).toBe(2);
      
      // Wait for expiration
      await new Promise(resolve => setTimeout(resolve, 20));
      
      // Trigger cleanup by setting a new item
      cache.set('key3', { data: '3' });
      
      expect(cache.getSize()).toBe(2); // key2 and key3, key1 should be removed
      expect(cache.has('key1')).toBe(false);
      expect(cache.has('key2')).toBe(true);
      expect(cache.has('key3')).toBe(true);
    });

    it('should respect maxItems limit', () => {
      // Create cache with maxItems: 3
      const limitedCache = new OfflineCache('limited_cache', {
        maxAge: 1000,
        maxItems: 3
      });
      
      limitedCache.set('key1', { data: '1' });
      limitedCache.set('key2', { data: '2' });
      limitedCache.set('key3', { data: '3' });
      limitedCache.set('key4', { data: '4' }); // This should trigger cleanup
      
      expect(limitedCache.getSize()).toBe(3);
      
      // The oldest item (key1) should be removed
      expect(limitedCache.has('key1')).toBe(false);
      expect(limitedCache.has('key2')).toBe(true);
      expect(limitedCache.has('key3')).toBe(true);
      expect(limitedCache.has('key4')).toBe(true);
    });
  });

  describe('error handling', () => {
    it('should handle localStorage errors gracefully', () => {
      // Mock localStorage to throw error
      const originalSetItem = localStorageMock.setItem;
      localStorageMock.setItem = jest.fn().mockImplementation(() => {
        throw new Error('Storage error');
      });
      
      expect(() => cache.set('test_key', { data: 'test' })).not.toThrow();
      
      // Restore original function
      localStorageMock.setItem = originalSetItem;
    });

    it('should handle JSON parsing errors gracefully', () => {
      // Mock localStorage to return invalid JSON
      localStorageMock.getItem = jest.fn().mockReturnValue('invalid json');
      
      expect(() => cache.get('test_key')).not.toThrow();
      expect(cache.get('test_key')).toBeNull();
    });
  });

  describe('predefined cache instances', () => {
    it('should have searchCache with correct configuration', () => {
      const { searchCache } = require('../offlineCache');
      
      // Test that searchCache is properly configured
      searchCache.set('test_key', { data: 'test' });
      expect(searchCache.get('test_key')).toEqual({ data: 'test' });
    });

    it('should have savedItemsCache with correct configuration', () => {
      const { savedItemsCache } = require('../offlineCache');
      
      // Test that savedItemsCache is properly configured
      savedItemsCache.set('test_key', { data: 'test' });
      expect(savedItemsCache.get('test_key')).toEqual({ data: 'test' });
    });
  });
}); 