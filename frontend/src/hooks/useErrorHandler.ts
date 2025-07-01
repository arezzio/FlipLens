import { useState, useCallback } from 'react';
import { ApiError, ErrorState } from '../types/api';

export const useErrorHandler = () => {
  const [errorState, setErrorState] = useState<ErrorState>({
    hasError: false,
    error: null,
    retryCount: 0,
    lastRetryTime: null,
    isRetrying: false
  });

  const setError = useCallback((error: ApiError) => {
    setErrorState({
      hasError: true,
      error,
      retryCount: 0,
      lastRetryTime: null,
      isRetrying: false
    });
  }, []);

  const clearError = useCallback(() => {
    setErrorState({
      hasError: false,
      error: null,
      retryCount: 0,
      lastRetryTime: null,
      isRetrying: false
    });
  }, []);

  const retry = useCallback(async (retryFn: () => Promise<void>) => {
    if (!errorState.error?.retryable || errorState.retryCount >= 3) {
      return;
    }

    setErrorState(prev => ({
      ...prev,
      isRetrying: true,
      retryCount: prev.retryCount + 1,
      lastRetryTime: Date.now()
    }));

    try {
      await retryFn();
      clearError();
    } catch (error) {
      setErrorState(prev => ({
        ...prev,
        isRetrying: false,
        error: error as ApiError
      }));
    }
  }, [errorState.error, errorState.retryCount, clearError]);

  const handleAsyncError = useCallback(async <T>(
    asyncFn: () => Promise<T>,
    onSuccess?: (result: T) => void,
    onError?: (error: ApiError) => void
  ): Promise<T | null> => {
    try {
      clearError();
      const result = await asyncFn();
      if (onSuccess) {
        onSuccess(result);
      }
      return result;
    } catch (error) {
      const apiError = error as ApiError;
      setError(apiError);
      if (onError) {
        onError(apiError);
      }
      return null;
    }
  }, [clearError, setError]);

  return {
    errorState,
    setError,
    clearError,
    retry,
    handleAsyncError
  };
}; 