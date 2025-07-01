import { config } from './config';

interface CachedItem {
  data: any;
  timestamp: number;
  expiresAt: number;
}

interface CacheConfig {
  maxAge: number; // milliseconds
  maxItems: number;
}

const DEFAULT_CONFIG: CacheConfig = {
  maxAge: config.cacheExpiryHours * 60 * 60 * 1000, // Use config for cache expiry
  maxItems: Math.floor(config.maxCacheSizeMB * 1024 * 1024 / 1000) // Rough estimate: 1KB per item
};

class OfflineCache {
  private config: CacheConfig;
  private storageKey: string;

  constructor(storageKey: string = 'fliplens_cache', config?: Partial<CacheConfig>) {
    this.storageKey = storageKey;
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  private getStorage(): Storage {
    return localStorage;
  }

  private getCache(): Record<string, CachedItem> {
    try {
      const cached = this.getStorage().getItem(this.storageKey);
      return cached ? JSON.parse(cached) : {};
    } catch (error) {
      console.warn('Failed to read cache from storage:', error);
      return {};
    }
  }

  private setCache(cache: Record<string, CachedItem>): void {
    try {
      this.getStorage().setItem(this.storageKey, JSON.stringify(cache));
    } catch (error) {
      console.warn('Failed to write cache to storage:', error);
    }
  }

  private cleanup(): void {
    const cache = this.getCache();
    const now = Date.now();
    const keys = Object.keys(cache);
    
    // Remove expired items
    keys.forEach(key => {
      if (cache[key].expiresAt < now) {
        delete cache[key];
      }
    });

    // Remove oldest items if over limit
    if (keys.length > this.config.maxItems) {
      const sortedKeys = keys.sort((a, b) => cache[a].timestamp - cache[b].timestamp);
      const keysToRemove = sortedKeys.slice(0, keys.length - this.config.maxItems);
      keysToRemove.forEach(key => delete cache[key]);
    }

    this.setCache(cache);
  }

  set(key: string, data: any, maxAge?: number): void {
    // Only cache if offline cache is enabled
    if (!config.enableOfflineCache) {
      return;
    }

    const now = Date.now();
    const age = maxAge || this.config.maxAge;
    
    const cache = this.getCache();
    cache[key] = {
      data,
      timestamp: now,
      expiresAt: now + age
    };

    this.setCache(cache);
    this.cleanup();
  }

  get(key: string): any | null {
    // Only serve from cache if offline cache is enabled
    if (!config.enableOfflineCache) {
      return null;
    }

    const cache = this.getCache();
    const item = cache[key];
    
    if (!item) {
      return null;
    }

    if (item.expiresAt < Date.now()) {
      delete cache[key];
      this.setCache(cache);
      return null;
    }

    return item.data;
  }

  has(key: string): boolean {
    return this.get(key) !== null;
  }

  remove(key: string): void {
    const cache = this.getCache();
    delete cache[key];
    this.setCache(cache);
  }

  clear(): void {
    this.getStorage().removeItem(this.storageKey);
  }

  getKeys(): string[] {
    return Object.keys(this.getCache());
  }

  getSize(): number {
    return Object.keys(this.getCache()).length;
  }
}

// Create cache instances for different data types
export const searchCache = new OfflineCache('fliplens_search_cache', {
  maxAge: 30 * 60 * 1000, // 30 minutes for search results
  maxItems: 50
});

export const savedItemsCache = new OfflineCache('fliplens_saved_items_cache', {
  maxAge: 24 * 60 * 60 * 1000, // 24 hours for saved items
  maxItems: 200
});

export default OfflineCache; 