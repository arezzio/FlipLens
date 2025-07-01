/**
 * Tests for frontend configuration utility
 * Verifies secure environment variable handling and validation
 */

// Mock console methods
const originalConsole = { ...console };
const mockConsole = {
  warn: jest.fn(),
  error: jest.fn(),
  group: jest.fn(),
  groupEnd: jest.fn(),
  log: jest.fn(),
};

describe('Frontend Configuration Security', () => {
  beforeEach(() => {
    // Reset console mocks
    Object.assign(console, mockConsole);
    jest.clearAllMocks();
    
    // Reset environment variables
    delete process.env.REACT_APP_API_URL;
    delete process.env.REACT_APP_ENV;
    delete process.env.REACT_APP_VERSION;
    delete process.env.REACT_APP_ENABLE_OFFLINE_CACHE;
    delete process.env.REACT_APP_CACHE_EXPIRY_HOURS;
    delete process.env.REACT_APP_MAX_CACHE_SIZE_MB;
    delete process.env.REACT_APP_DEBUG;
    delete process.env.REACT_APP_LOG_LEVEL;
  });

  afterEach(() => {
    // Restore original console
    Object.assign(console, originalConsole);
    // Reset modules to clear cached config
    jest.resetModules();
  });

  describe('Environment Variable Security', () => {
    test('should only use REACT_APP_ prefixed variables', () => {
      // Set a non-REACT_APP_ variable (should be ignored)
      process.env.API_KEY = 'secret-key';
      process.env.REACT_APP_API_URL = 'http://localhost:5000/api';
      
      // Import config after setting environment variables
      const { config } = require('../config');
      
      // The config should not expose the secret API key
      expect(config.apiUrl).toBe('http://localhost:5000/api');
      expect((config as any).API_KEY).toBeUndefined();
    });

    test('should handle missing environment variables gracefully', () => {
      // Set production environment to avoid validation throwing
      process.env.REACT_APP_ENV = 'production';
      // No environment variables set
      const { validateConfig } = require('../config');
      const errors = validateConfig();
      // Should log warnings for missing variables
      expect(console.warn).toHaveBeenCalled();
      // Fallbacks are used, so errors should be empty
      expect(errors).toHaveLength(0);
    });

    test('should validate required configuration in development', () => {
      // Set development environment
      process.env.REACT_APP_ENV = 'development';
      process.env.REACT_APP_API_URL = '';
      process.env.REACT_APP_CACHE_EXPIRY_HOURS = '0';
      process.env.REACT_APP_MAX_CACHE_SIZE_MB = '-1';
      // Should throw error in development for invalid config
      const { validateConfig } = require('../config');
      expect(() => validateConfig()).toThrow(
        expect.stringContaining('Missing or invalid environment variables')
      );
      expect(() => validateConfig()).toThrow(
        expect.stringContaining('REACT_APP_API_URL is required')
      );
      expect(() => validateConfig()).toThrow(
        expect.stringContaining('REACT_APP_CACHE_EXPIRY_HOURS must be greater than 0')
      );
      expect(() => validateConfig()).toThrow(
        expect.stringContaining('REACT_APP_MAX_CACHE_SIZE_MB must be greater than 0')
      );
    });

    test('should not throw in production for missing variables', () => {
      // Set production environment
      process.env.REACT_APP_ENV = 'production';
      process.env.REACT_APP_API_URL = '';
      
      // Should not throw in production, just return errors
      const { validateConfig } = require('../config');
      const errors = validateConfig();
      expect(errors).toContain('REACT_APP_API_URL is required');
      expect(() => validateConfig()).not.toThrow();
    });
  });

  describe('Configuration Validation', () => {
    test('should validate API URL is present', () => {
      process.env.REACT_APP_ENV = 'production'; // Avoid validation throwing
      process.env.REACT_APP_API_URL = '';
      const { validateConfig } = require('../config');
      const errors = validateConfig();
      expect(errors).toContain('REACT_APP_API_URL is required');
    });

    test('should validate cache expiry is positive', () => {
      process.env.REACT_APP_ENV = 'production'; // Avoid validation throwing
      process.env.REACT_APP_CACHE_EXPIRY_HOURS = '0';
      const { validateConfig } = require('../config');
      const errors = validateConfig();
      expect(errors).toContain('REACT_APP_CACHE_EXPIRY_HOURS must be greater than 0');
    });

    test('should validate max cache size is positive', () => {
      process.env.REACT_APP_ENV = 'production'; // Avoid validation throwing
      process.env.REACT_APP_MAX_CACHE_SIZE_MB = '-1';
      const { validateConfig } = require('../config');
      const errors = validateConfig();
      expect(errors).toContain('REACT_APP_MAX_CACHE_SIZE_MB must be greater than 0');
    });

    test('should accept valid configuration', () => {
      process.env.REACT_APP_API_URL = 'http://localhost:5000/api';
      process.env.REACT_APP_CACHE_EXPIRY_HOURS = '24';
      process.env.REACT_APP_MAX_CACHE_SIZE_MB = '50';
      
      const { validateConfig } = require('../config');
      const errors = validateConfig();
      expect(errors).toHaveLength(0);
    });
  });

  describe('Configuration Values', () => {
    test('should use fallback values when environment variables are missing', () => {
      const { config } = require('../config');
      expect(config.apiUrl).toBe('http://localhost:5000/api');
      expect(config.environment).toBe('development');
      expect(config.version).toBe('1.0.0');
      expect(config.enableOfflineCache).toBe(true);
      expect(config.cacheExpiryHours).toBe(24);
      expect(config.maxCacheSizeMB).toBe(50);
      expect(config.debug).toBe(true);
      expect(config.logLevel).toBe('info');
    });

    test('should use environment variable values when provided', () => {
      process.env.REACT_APP_API_URL = 'https://api.example.com';
      process.env.REACT_APP_ENV = 'production';
      process.env.REACT_APP_VERSION = '2.0.0';
      process.env.REACT_APP_ENABLE_OFFLINE_CACHE = 'false';
      process.env.REACT_APP_CACHE_EXPIRY_HOURS = '48';
      process.env.REACT_APP_MAX_CACHE_SIZE_MB = '100';
      process.env.REACT_APP_DEBUG = 'false';
      process.env.REACT_APP_LOG_LEVEL = 'error';
      
      const { config } = require('../config');
      
      expect(config.apiUrl).toBe('https://api.example.com');
      expect(config.environment).toBe('production');
      expect(config.version).toBe('2.0.0');
      expect(config.enableOfflineCache).toBe(false);
      expect(config.cacheExpiryHours).toBe(48);
      expect(config.maxCacheSizeMB).toBe(100);
      expect(config.debug).toBe(false);
      expect(config.logLevel).toBe('error');
    });

    test('should handle boolean environment variables correctly', () => {
      process.env.REACT_APP_ENABLE_OFFLINE_CACHE = 'true';
      process.env.REACT_APP_DEBUG = 'false';
      
      const { config } = require('../config');
      
      expect(config.enableOfflineCache).toBe(true);
      expect(config.debug).toBe(false);
    });

    test('should handle numeric environment variables correctly', () => {
      process.env.REACT_APP_CACHE_EXPIRY_HOURS = '12';
      process.env.REACT_APP_MAX_CACHE_SIZE_MB = '75';
      
      const { config } = require('../config');
      
      expect(config.cacheExpiryHours).toBe(12);
      expect(config.maxCacheSizeMB).toBe(75);
    });

    test('should fallback to default for invalid numeric values', () => {
      process.env.REACT_APP_CACHE_EXPIRY_HOURS = 'invalid';
      process.env.REACT_APP_MAX_CACHE_SIZE_MB = 'not-a-number';
      
      const { config } = require('../config');
      
      expect(config.cacheExpiryHours).toBe(24); // fallback
      expect(config.maxCacheSizeMB).toBe(50); // fallback
    });
  });

  describe('Environment Detection', () => {
    test('should correctly detect development environment', () => {
      process.env.REACT_APP_ENV = 'development';
      
      const { config } = require('../config');
      
      expect(config.isDevelopment).toBe(true);
      expect(config.isProduction).toBe(false);
    });

    test('should correctly detect production environment', () => {
      process.env.REACT_APP_ENV = 'production';
      
      const { config } = require('../config');
      
      expect(config.isDevelopment).toBe(false);
      expect(config.isProduction).toBe(true);
    });
  });

  describe('Configuration Logging', () => {
    test('should log configuration in development mode', () => {
      process.env.REACT_APP_ENV = 'development';
      process.env.REACT_APP_DEBUG = 'true';
      
      const { logConfigStatus } = require('../config');
      logConfigStatus();
      
      expect(console.group).toHaveBeenCalledWith('📋 App Configuration');
      expect(console.log).toHaveBeenCalledWith('Environment:', 'development');
      expect(console.groupEnd).toHaveBeenCalled();
    });

    test('should not log configuration in production mode', () => {
      process.env.REACT_APP_ENV = 'production';
      process.env.REACT_APP_DEBUG = 'false';
      
      const { logConfigStatus } = require('../config');
      logConfigStatus();
      
      expect(console.group).not.toHaveBeenCalled();
      expect(console.log).not.toHaveBeenCalled();
    });
  });

  describe('Security Checks', () => {
    test('should not expose any secrets or API keys', () => {
      // Set some potential secrets (should be ignored)
      process.env.API_KEY = 'secret-api-key';
      process.env.EBAY_API_KEY = 'secret-ebay-key';
      process.env.DATABASE_PASSWORD = 'secret-password';
      
      const { config } = require('../config');
      
      // The config object should not contain any of these
      const configKeys = Object.keys(config);
      expect(configKeys).not.toContain('API_KEY');
      expect(configKeys).not.toContain('EBAY_API_KEY');
      expect(configKeys).not.toContain('DATABASE_PASSWORD');
      
      // Only REACT_APP_ prefixed variables should be accessible
      expect(configKeys).toEqual(
        expect.arrayContaining([
          'apiUrl',
          'environment',
          'version',
          'isDevelopment',
          'isProduction',
          'enableOfflineCache',
          'cacheExpiryHours',
          'maxCacheSizeMB',
          'sentryDsn',
          'gaTrackingId',
          'debug',
          'logLevel'
        ])
      );
    });

    test('should handle optional environment variables correctly', () => {
      // Set optional variables before requiring config
      process.env.REACT_APP_SENTRY_DSN = 'https://sentry.example.com/dsn';
      process.env.REACT_APP_GA_TRACKING_ID = 'GA-123456789';
      const { config } = require('../config');
      expect(config.sentryDsn).toBe('https://sentry.example.com/dsn');
      expect(config.gaTrackingId).toBe('GA-123456789');
    });
  });
}); 