/**
 * Frontend Configuration Utility
 * Handles environment variables and configuration settings securely
 */

interface AppConfig {
  // API Configuration
  apiUrl: string;
  
  // Environment Configuration
  environment: string;
  version: string;
  isDevelopment: boolean;
  isProduction: boolean;
  
  // Feature Flags
  enableOfflineCache: boolean;
  cacheExpiryHours: number;
  maxCacheSizeMB: number;
  
  // Error Reporting
  sentryDsn?: string;
  
  // Analytics
  gaTrackingId?: string;
  
  // Development Configuration
  debug: boolean;
  logLevel: string;
}

/**
 * Get environment variable with fallback
 * Only allows REACT_APP_ prefixed variables for security
 */
function getEnvVar(key: string, fallback: string = ''): string {
  const fullKey = `REACT_APP_${key}`;
  const value = process.env[fullKey];
  
  if (value === undefined) {
    console.warn(`Environment variable ${fullKey} not set, using fallback: ${fallback}`);
    return fallback;
  }
  
  return value;
}

/**
 * Get boolean environment variable
 */
function getBoolEnvVar(key: string, fallback: boolean = false): boolean {
  const value = getEnvVar(key, fallback.toString());
  return value.toLowerCase() === 'true';
}

/**
 * Get number environment variable
 */
function getNumberEnvVar(key: string, fallback: number): number {
  const value = getEnvVar(key, fallback.toString());
  const parsed = parseInt(value, 10);
  return isNaN(parsed) ? fallback : parsed;
}

/**
 * Application configuration object
 */
export const config: AppConfig = {
  // API Configuration
  apiUrl: getEnvVar('API_URL', 'http://localhost:5000/api'),
  
  // Environment Configuration
  environment: getEnvVar('ENV', 'development'),
  version: getEnvVar('VERSION', '1.0.0'),
  isDevelopment: getEnvVar('ENV', 'development') === 'development',
  isProduction: getEnvVar('ENV', 'development') === 'production',
  
  // Feature Flags
  enableOfflineCache: getBoolEnvVar('ENABLE_OFFLINE_CACHE', true),
  cacheExpiryHours: getNumberEnvVar('CACHE_EXPIRY_HOURS', 24),
  maxCacheSizeMB: getNumberEnvVar('MAX_CACHE_SIZE_MB', 50),
  
  // Error Reporting
  sentryDsn: getEnvVar('SENTRY_DSN', ''),
  
  // Analytics
  gaTrackingId: getEnvVar('GA_TRACKING_ID', ''),
  
  // Development Configuration
  debug: getBoolEnvVar('DEBUG', true),
  logLevel: getEnvVar('LOG_LEVEL', 'info'),
};

/**
 * Validate required configuration
 */
export function validateConfig(): string[] {
  const errors: string[] = [];
  
  // Validate API URL
  if (!config.apiUrl) {
    errors.push('REACT_APP_API_URL is required');
  }
  
  // Validate cache settings
  if (config.cacheExpiryHours <= 0) {
    errors.push('REACT_APP_CACHE_EXPIRY_HOURS must be greater than 0');
  }
  
  if (config.maxCacheSizeMB <= 0) {
    errors.push('REACT_APP_MAX_CACHE_SIZE_MB must be greater than 0');
  }
  
  // Throw in development if any required config is missing
  if (errors.length > 0 && config.isDevelopment) {
    throw new Error(
      `Missing or invalid environment variables:\n${errors.map(e => '- ' + e).join('\n')}`
    );
  }
  
  return errors;
}

/**
 * Log configuration status (only in development)
 */
export function logConfigStatus(): void {
  if (config.isDevelopment && config.debug) {
    console.group('📋 App Configuration');
    console.log('Environment:', config.environment);
    console.log('Version:', config.version);
    console.log('API URL:', config.apiUrl);
    console.log('Offline Cache:', config.enableOfflineCache ? 'Enabled' : 'Disabled');
    console.log('Cache Expiry:', `${config.cacheExpiryHours}h`);
    console.log('Max Cache Size:', `${config.maxCacheSizeMB}MB`);
    console.groupEnd();
  }
}

/**
 * Get configuration for specific environment
 */
export function getConfigForEnvironment(env: string): Partial<AppConfig> {
  switch (env) {
    case 'production':
      return {
        debug: false,
        logLevel: 'error',
        enableOfflineCache: true,
      };
    case 'development':
      return {
        debug: true,
        logLevel: 'info',
        enableOfflineCache: true,
      };
    case 'test':
      return {
        debug: false,
        logLevel: 'error',
        enableOfflineCache: false,
      };
    default:
      return {};
  }
}

// Initialize configuration logging
logConfigStatus();

// Validate config at module load
validateConfig();

export default config; 