import React from 'react';
import { useOfflineDetection } from '../hooks/useOfflineDetection';

interface OfflineIndicatorProps {
  className?: string;
}

export const OfflineIndicator: React.FC<OfflineIndicatorProps> = ({ className = '' }) => {
  const { isOffline, lastOnlineTime, connectionType } = useOfflineDetection();

  if (!isOffline) {
    return null;
  }

  const formatLastOnline = (timestamp: number | null) => {
    if (!timestamp) return 'Unknown';
    
    const now = Date.now();
    const diff = now - timestamp;
    const minutes = Math.floor(diff / (1000 * 60));
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m ago`;
    }
    return `${minutes}m ago`;
  };

  const getConnectionIcon = () => {
    switch (connectionType) {
      case 'wifi':
        return '📶';
      case 'cellular':
        return '📱';
      case 'none':
        return '❌';
      default:
        return '❓';
    }
  };

  return (
    <div className={`fixed top-4 left-1/2 transform -translate-x-1/2 z-50 ${className}`}>
      <div className="bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg flex items-center space-x-2 text-sm font-medium">
        <span className="text-lg">{getConnectionIcon()}</span>
        <span>You're offline</span>
        {lastOnlineTime && (
          <span className="text-red-100 text-xs">
            (Last online: {formatLastOnline(lastOnlineTime)})
          </span>
        )}
      </div>
    </div>
  );
};

export const OfflineBanner: React.FC<{ className?: string }> = ({ className = '' }) => {
  const { isOffline } = useOfflineDetection();

  if (!isOffline) {
    return null;
  }

  return (
    <div className={`bg-yellow-50 border-l-4 border-yellow-400 p-4 ${className}`}>
      <div className="flex">
        <div className="flex-shrink-0">
          <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        </div>
        <div className="ml-3">
          <p className="text-sm text-yellow-700">
            <strong>Offline Mode:</strong> You're currently offline. Some features may be limited.
          </p>
        </div>
      </div>
    </div>
  );
}; 