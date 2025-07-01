import { useState, useEffect, useCallback } from 'react';

export interface OfflineState {
  isOffline: boolean;
  lastOnlineTime: number | null;
  lastOfflineTime: number | null;
  connectionType: 'wifi' | 'cellular' | 'none' | 'unknown';
}

export const useOfflineDetection = () => {
  const [offlineState, setOfflineState] = useState<OfflineState>({
    isOffline: !navigator.onLine,
    lastOnlineTime: navigator.onLine ? Date.now() : null,
    lastOfflineTime: navigator.onLine ? null : Date.now(),
    connectionType: 'unknown'
  });

  const updateConnectionType = useCallback(() => {
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      if (connection) {
        setOfflineState(prev => ({
          ...prev,
          connectionType: connection.effectiveType === '4g' || connection.effectiveType === '3g' 
            ? 'cellular' 
            : connection.type || 'unknown'
        }));
      }
    }
  }, []);

  const handleOnline = useCallback(() => {
    setOfflineState(prev => ({
      ...prev,
      isOffline: false,
      lastOnlineTime: Date.now(),
      lastOfflineTime: prev.lastOfflineTime
    }));
    updateConnectionType();
  }, [updateConnectionType]);

  const handleOffline = useCallback(() => {
    setOfflineState(prev => ({
      ...prev,
      isOffline: true,
      lastOnlineTime: prev.lastOnlineTime,
      lastOfflineTime: Date.now()
    }));
  }, []);

  const handleConnectionChange = useCallback(() => {
    updateConnectionType();
  }, [updateConnectionType]);

  useEffect(() => {
    // Set initial connection type
    updateConnectionType();

    // Add event listeners
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      if (connection) {
        connection.addEventListener('change', handleConnectionChange);
      }
    }

    // Cleanup
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      
      if ('connection' in navigator) {
        const connection = (navigator as any).connection;
        if (connection) {
          connection.removeEventListener('change', handleConnectionChange);
        }
      }
    };
  }, [handleOnline, handleOffline, handleConnectionChange, updateConnectionType]);

  return offlineState;
}; 