import { renderHook, act } from '@testing-library/react';
import { useOfflineDetection } from '../useOfflineDetection';

// Mock navigator.onLine
const mockNavigatorOnLine = (value: boolean) => {
  Object.defineProperty(navigator, 'onLine', {
    value,
    writable: true,
    configurable: true
  });
};

// Mock navigator.connection
const mockNavigatorConnection = (connectionInfo: any) => {
  Object.defineProperty(navigator, 'connection', {
    value: connectionInfo,
    writable: true,
    configurable: true
  });
};

describe('useOfflineDetection', () => {
  beforeEach(() => {
    // Reset mocks
    mockNavigatorOnLine(true);
    mockNavigatorConnection(null);
    
    // Clear event listeners
    window.removeEventListener('online', () => {});
    window.removeEventListener('offline', () => {});
  });

  afterEach(() => {
    // Clean up
    jest.clearAllMocks();
  });

  it('should initialize with online status when navigator.onLine is true', () => {
    mockNavigatorOnLine(true);
    
    const { result } = renderHook(() => useOfflineDetection());
    
    expect(result.current.isOffline).toBe(false);
    expect(result.current.lastOnlineTime).toBeTruthy();
    expect(result.current.lastOfflineTime).toBeNull();
  });

  it('should initialize with offline status when navigator.onLine is false', () => {
    mockNavigatorOnLine(false);
    
    const { result } = renderHook(() => useOfflineDetection());
    
    expect(result.current.isOffline).toBe(true);
    expect(result.current.lastOnlineTime).toBeNull();
    expect(result.current.lastOfflineTime).toBeTruthy();
  });

  it('should detect connection type when navigator.connection is available', () => {
    mockNavigatorConnection({
      effectiveType: '4g',
      type: 'cellular'
    });
    
    const { result } = renderHook(() => useOfflineDetection());
    
    expect(result.current.connectionType).toBe('cellular');
  });

  it('should detect WiFi connection type', () => {
    mockNavigatorConnection({
      effectiveType: '4g',
      type: 'wifi'
    });
    
    const { result } = renderHook(() => useOfflineDetection());
    
    expect(result.current.connectionType).toBe('wifi');
  });

  it('should default to unknown when connection API is not available', () => {
    mockNavigatorConnection(null);
    
    const { result } = renderHook(() => useOfflineDetection());
    
    expect(result.current.connectionType).toBe('unknown');
  });

  it('should update state when going offline', () => {
    mockNavigatorOnLine(true);
    
    const { result } = renderHook(() => useOfflineDetection());
    
    expect(result.current.isOffline).toBe(false);
    
    act(() => {
      // Simulate going offline
      mockNavigatorOnLine(false);
      window.dispatchEvent(new Event('offline'));
    });
    
    expect(result.current.isOffline).toBe(true);
    expect(result.current.lastOfflineTime).toBeTruthy();
  });

  it('should update state when going online', () => {
    mockNavigatorOnLine(false);
    
    const { result } = renderHook(() => useOfflineDetection());
    
    expect(result.current.isOffline).toBe(true);
    
    act(() => {
      // Simulate going online
      mockNavigatorOnLine(true);
      window.dispatchEvent(new Event('online'));
    });
    
    expect(result.current.isOffline).toBe(false);
    expect(result.current.lastOnlineTime).toBeTruthy();
  });

  it('should handle connection changes', () => {
    mockNavigatorConnection({
      effectiveType: '4g',
      type: 'cellular'
    });
    
    const { result } = renderHook(() => useOfflineDetection());
    
    expect(result.current.connectionType).toBe('cellular');
    
    act(() => {
      // Simulate connection change
      mockNavigatorConnection({
        effectiveType: '4g',
        type: 'wifi'
      });
      
      // Trigger connection change event
      if ('connection' in navigator) {
        const connection = (navigator as any).connection;
        connection.dispatchEvent(new Event('change'));
      }
    });
    
    expect(result.current.connectionType).toBe('wifi');
  });

  it('should maintain timestamps correctly', () => {
    mockNavigatorOnLine(true);
    
    const { result } = renderHook(() => useOfflineDetection());
    
    const initialOnlineTime = result.current.lastOnlineTime;
    
    act(() => {
      // Go offline
      mockNavigatorOnLine(false);
      window.dispatchEvent(new Event('offline'));
    });
    
    expect(result.current.lastOnlineTime).toBe(initialOnlineTime);
    expect(result.current.lastOfflineTime).toBeTruthy();
    
    act(() => {
      // Go online again
      mockNavigatorOnLine(true);
      window.dispatchEvent(new Event('online'));
    });
    
    expect(result.current.lastOnlineTime).toBeGreaterThan(initialOnlineTime!);
    expect(result.current.lastOfflineTime).toBeTruthy(); // Should still have the offline time
  });

  it('should handle multiple online/offline transitions', () => {
    mockNavigatorOnLine(true);
    
    const { result } = renderHook(() => useOfflineDetection());
    
    expect(result.current.isOffline).toBe(false);
    
    // Multiple transitions
    act(() => {
      mockNavigatorOnLine(false);
      window.dispatchEvent(new Event('offline'));
    });
    
    expect(result.current.isOffline).toBe(true);
    
    act(() => {
      mockNavigatorOnLine(true);
      window.dispatchEvent(new Event('online'));
    });
    
    expect(result.current.isOffline).toBe(false);
    
    act(() => {
      mockNavigatorOnLine(false);
      window.dispatchEvent(new Event('offline'));
    });
    
    expect(result.current.isOffline).toBe(true);
  });
}); 