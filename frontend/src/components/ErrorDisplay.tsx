import React from 'react';
import { ApiError, ErrorState } from '../types/api';

interface ErrorDisplayProps {
  errorState: ErrorState;
  onRetry?: () => void;
  onDismiss?: () => void;
  className?: string;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  errorState,
  onRetry,
  onDismiss,
  className = ''
}) => {
  if (!errorState.hasError || !errorState.error) {
    return null;
  }

  const { error, retryCount, isRetrying } = errorState;
  
  // Get error-specific styling and icon
  const getErrorConfig = (error: ApiError) => {
    switch (error.code) {
      case 'NETWORK_ERROR':
        return {
          icon: (
            <svg className="w-5 h-5 sm:w-6 sm:h-6 lg:w-7 lg:h-7 text-red-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192L5.636 18.364M12 2.25a9.75 9.75 0 100 19.5 9.75 9.75 0 000-19.5z" />
            </svg>
          ),
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          textColor: 'text-red-900',
          messageColor: 'text-red-700',
          title: 'Connection Error'
        };
      
      case 'TIMEOUT_ERROR':
        return {
          icon: (
            <svg className="w-5 h-5 sm:w-6 sm:h-6 lg:w-7 lg:h-7 text-orange-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          ),
          bgColor: 'bg-orange-50',
          borderColor: 'border-orange-200',
          textColor: 'text-orange-900',
          messageColor: 'text-orange-700',
          title: 'Request Timeout'
        };
      
      case 'RATE_LIMIT_ERROR':
        return {
          icon: (
            <svg className="w-5 h-5 sm:w-6 sm:h-6 lg:w-7 lg:h-7 text-yellow-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          ),
          bgColor: 'bg-yellow-50',
          borderColor: 'border-yellow-200',
          textColor: 'text-yellow-900',
          messageColor: 'text-yellow-700',
          title: 'Rate Limited'
        };
      
      case 'VALIDATION_ERROR':
        return {
          icon: (
            <svg className="w-5 h-5 sm:w-6 sm:h-6 lg:w-7 lg:h-7 text-blue-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          ),
          bgColor: 'bg-blue-50',
          borderColor: 'border-blue-200',
          textColor: 'text-blue-900',
          messageColor: 'text-blue-700',
          title: 'Invalid Input'
        };
      
      case 'AUTH_ERROR':
        return {
          icon: (
            <svg className="w-5 h-5 sm:w-6 sm:h-6 lg:w-7 lg:h-7 text-purple-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          ),
          bgColor: 'bg-purple-50',
          borderColor: 'border-purple-200',
          textColor: 'text-purple-900',
          messageColor: 'text-purple-700',
          title: 'Authentication Required'
        };
      
      default:
        return {
          icon: (
            <svg className="w-5 h-5 sm:w-6 sm:h-6 lg:w-7 lg:h-7 text-red-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          ),
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          textColor: 'text-red-900',
          messageColor: 'text-red-700',
          title: 'Error'
        };
    }
  };

  const errorConfig = getErrorConfig(error);
  const canRetry = error.retryable && onRetry && retryCount < 3;

  return (
    <div className={`mb-6 sm:mb-8 lg:mb-12 animate-fade-in ${className}`}>
      <div className={`${errorConfig.bgColor} border ${errorConfig.borderColor} rounded-xl p-4 sm:p-6 lg:p-8`}>
        <div className="flex items-start space-x-3 lg:space-x-4">
          {errorConfig.icon}
          
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className={`text-sm sm:text-base lg:text-lg font-semibold ${errorConfig.textColor} mb-1 lg:mb-2`}>
                  {errorConfig.title}
                </h3>
                <p className={`text-sm sm:text-base lg:text-lg ${errorConfig.messageColor} mb-3 lg:mb-4`}>
                  {error.message}
                </p>
                
                {/* Error details if available */}
                {error.details && (
                  <div className="mb-3 lg:mb-4">
                    <details className="text-xs sm:text-sm text-neutral-600">
                      <summary className="cursor-pointer hover:text-neutral-800 transition-colors duration-200">
                        Technical Details
                      </summary>
                      <pre className="mt-2 p-2 bg-neutral-100 rounded text-xs overflow-x-auto">
                        {error.details}
                      </pre>
                    </details>
                  </div>
                )}
                
                {/* Retry count indicator */}
                {retryCount > 0 && (
                  <p className="text-xs sm:text-sm text-neutral-500 mb-3 lg:mb-4">
                    Retry attempt {retryCount} of 3
                  </p>
                )}
                
                {/* Action buttons */}
                <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 lg:gap-4">
                  {canRetry && (
                    <button
                      onClick={onRetry}
                      disabled={isRetrying}
                      className={`stockx-button-primary text-sm sm:text-base lg:text-lg touch-target px-4 lg:px-6 py-2 lg:py-3 ${
                        isRetrying ? 'opacity-50 cursor-not-allowed' : ''
                      }`}
                    >
                      {isRetrying ? (
                        <div className="flex items-center space-x-2">
                          <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                          </svg>
                          <span>Retrying...</span>
                        </div>
                      ) : (
                        'Try Again'
                      )}
                    </button>
                  )}
                  
                  {onDismiss && (
                    <button
                      onClick={onDismiss}
                      className="stockx-button-secondary text-sm sm:text-base lg:text-lg touch-target px-4 lg:px-6 py-2 lg:py-3"
                    >
                      Dismiss
                    </button>
                  )}
                </div>
              </div>
              
              {/* Close button */}
              {onDismiss && (
                <button
                  onClick={onDismiss}
                  className="ml-4 p-1 rounded-lg hover:bg-neutral-100 transition-colors duration-200 touch-target"
                  aria-label="Dismiss error"
                >
                  <svg className="w-5 h-5 text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}; 