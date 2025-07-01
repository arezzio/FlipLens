import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ErrorDisplay } from '../ErrorDisplay';
import { ErrorState } from '../../types/api';

// Mock the error handler hook
jest.mock('../../hooks/useErrorHandler', () => ({
  useErrorHandler: () => ({
    errorState: {
      hasError: false,
      error: null,
      retryCount: 0,
      lastRetryTime: null,
      isRetrying: false
    },
    setError: jest.fn(),
    clearError: jest.fn(),
    retry: jest.fn()
  })
}));

describe('ErrorDisplay', () => {
  const mockOnRetry = jest.fn();
  const mockOnDismiss = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should not render when there is no error', () => {
    const errorState: ErrorState = {
      hasError: false,
      error: null,
      retryCount: 0,
      lastRetryTime: null,
      isRetrying: false
    };

    render(
      <ErrorDisplay
        errorState={errorState}
        onRetry={mockOnRetry}
        onDismiss={mockOnDismiss}
      />
    );

    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('should render network error correctly', () => {
    const errorState: ErrorState = {
      hasError: true,
      error: {
        error: 'NetworkError',
        message: 'Unable to connect to server. Please check your internet connection.',
        status: 'error',
        code: 'NETWORK_ERROR',
        retryable: true,
        timestamp: '2024-01-01T00:00:00Z'
      },
      retryCount: 0,
      lastRetryTime: null,
      isRetrying: false
    };

    render(
      <ErrorDisplay
        errorState={errorState}
        onRetry={mockOnRetry}
        onDismiss={mockOnDismiss}
      />
    );

    expect(screen.getByText('Connection Error')).toBeInTheDocument();
    expect(screen.getByText('Unable to connect to server. Please check your internet connection.')).toBeInTheDocument();
    expect(screen.getByText('Try Again')).toBeInTheDocument();
    expect(screen.getByText('Dismiss')).toBeInTheDocument();
  });

  it('should render timeout error correctly', () => {
    const errorState: ErrorState = {
      hasError: true,
      error: {
        error: 'TimeoutError',
        message: 'Request timed out. Please check your connection and try again.',
        status: 'error',
        code: 'TIMEOUT_ERROR',
        retryable: true,
        timestamp: '2024-01-01T00:00:00Z'
      },
      retryCount: 1,
      lastRetryTime: Date.now(),
      isRetrying: false
    };

    render(
      <ErrorDisplay
        errorState={errorState}
        onRetry={mockOnRetry}
        onDismiss={mockOnDismiss}
      />
    );

    expect(screen.getByText('Request Timeout')).toBeInTheDocument();
    expect(screen.getByText('Request timed out. Please check your connection and try again.')).toBeInTheDocument();
    expect(screen.getByText('Retry attempt 1 of 3')).toBeInTheDocument();
  });

  it('should render server error correctly', () => {
    const errorState: ErrorState = {
      hasError: true,
      error: {
        error: 'ServerError',
        message: 'Server error occurred. Please try again later.',
        status: 'error',
        code: 'SERVER_ERROR',
        retryable: true,
        timestamp: '2024-01-01T00:00:00Z'
      },
      retryCount: 2,
      lastRetryTime: Date.now(),
      isRetrying: false
    };

    render(
      <ErrorDisplay
        errorState={errorState}
        onRetry={mockOnRetry}
        onDismiss={mockOnDismiss}
      />
    );

    expect(screen.getByText('Error')).toBeInTheDocument();
    expect(screen.getByText('Server error occurred. Please try again later.')).toBeInTheDocument();
    expect(screen.getByText('Retry attempt 2 of 3')).toBeInTheDocument();
  });

  it('should render validation error correctly', () => {
    const errorState: ErrorState = {
      hasError: true,
      error: {
        error: 'ValidationError',
        message: 'Invalid request. Please check your input and try again.',
        status: 'error',
        code: 'VALIDATION_ERROR',
        retryable: false,
        timestamp: '2024-01-01T00:00:00Z'
      },
      retryCount: 0,
      lastRetryTime: null,
      isRetrying: false
    };

    render(
      <ErrorDisplay
        errorState={errorState}
        onRetry={mockOnRetry}
        onDismiss={mockOnDismiss}
      />
    );

    expect(screen.getByText('Invalid Input')).toBeInTheDocument();
    expect(screen.getByText('Invalid request. Please check your input and try again.')).toBeInTheDocument();
    expect(screen.queryByText('Try Again')).not.toBeInTheDocument();
  });

  it('should render rate limit error correctly', () => {
    const errorState: ErrorState = {
      hasError: true,
      error: {
        error: 'RateLimitError',
        message: 'Too many requests. Please wait a moment and try again.',
        status: 'error',
        code: 'RATE_LIMIT_ERROR',
        retryable: true,
        retryAfter: 60,
        timestamp: '2024-01-01T00:00:00Z'
      } as any, // Type assertion for test
      retryCount: 0,
      lastRetryTime: null,
      isRetrying: false
    };

    render(
      <ErrorDisplay
        errorState={errorState}
        onRetry={mockOnRetry}
        onDismiss={mockOnDismiss}
      />
    );

    expect(screen.getByText('Rate Limited')).toBeInTheDocument();
    expect(screen.getByText('Too many requests. Please wait a moment and try again.')).toBeInTheDocument();
    expect(screen.getByText('Try Again')).toBeInTheDocument();
  });

  it('should show retrying state correctly', () => {
    const errorState: ErrorState = {
      hasError: true,
      error: {
        error: 'NetworkError',
        message: 'Unable to connect to server.',
        status: 'error',
        code: 'NETWORK_ERROR',
        retryable: true,
        timestamp: '2024-01-01T00:00:00Z'
      },
      retryCount: 1,
      lastRetryTime: Date.now(),
      isRetrying: true
    };

    render(
      <ErrorDisplay
        errorState={errorState}
        onRetry={mockOnRetry}
        onDismiss={mockOnDismiss}
      />
    );

    expect(screen.getByText('Retrying...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /retrying/i })).toBeDisabled();
  });

  it('should call onRetry when retry button is clicked', () => {
    const errorState: ErrorState = {
      hasError: true,
      error: {
        error: 'NetworkError',
        message: 'Unable to connect to server.',
        status: 'error',
        code: 'NETWORK_ERROR',
        retryable: true,
        timestamp: '2024-01-01T00:00:00Z'
      },
      retryCount: 0,
      lastRetryTime: null,
      isRetrying: false
    };

    render(
      <ErrorDisplay
        errorState={errorState}
        onRetry={mockOnRetry}
        onDismiss={mockOnDismiss}
      />
    );

    fireEvent.click(screen.getByText('Try Again'));
    expect(mockOnRetry).toHaveBeenCalledTimes(1);
  });

  it('should call onDismiss when dismiss button is clicked', () => {
    const errorState: ErrorState = {
      hasError: true,
      error: {
        error: 'NetworkError',
        message: 'Unable to connect to server.',
        status: 'error',
        code: 'NETWORK_ERROR',
        retryable: true,
        timestamp: '2024-01-01T00:00:00Z'
      },
      retryCount: 0,
      lastRetryTime: null,
      isRetrying: false
    };

    render(
      <ErrorDisplay
        errorState={errorState}
        onRetry={mockOnRetry}
        onDismiss={mockOnDismiss}
      />
    );

    fireEvent.click(screen.getByText('Dismiss'));
    expect(mockOnDismiss).toHaveBeenCalledTimes(1);
  });

  it('should not show retry button for non-retryable errors', () => {
    const errorState: ErrorState = {
      hasError: true,
      error: {
        error: 'ValidationError',
        message: 'Invalid request.',
        status: 'error',
        code: 'VALIDATION_ERROR',
        retryable: false,
        timestamp: '2024-01-01T00:00:00Z'
      },
      retryCount: 0,
      lastRetryTime: null,
      isRetrying: false
    };

    render(
      <ErrorDisplay
        errorState={errorState}
        onRetry={mockOnRetry}
        onDismiss={mockOnDismiss}
      />
    );

    expect(screen.queryByText('Try Again')).not.toBeInTheDocument();
    expect(screen.getByText('Dismiss')).toBeInTheDocument();
  });

  it('should show max retries reached message', () => {
    const errorState: ErrorState = {
      hasError: true,
      error: {
        error: 'NetworkError',
        message: 'Unable to connect to server.',
        status: 'error',
        code: 'NETWORK_ERROR',
        retryable: true,
        timestamp: '2024-01-01T00:00:00Z'
      },
      retryCount: 3,
      lastRetryTime: Date.now(),
      isRetrying: false
    };

    render(
      <ErrorDisplay
        errorState={errorState}
        onRetry={mockOnRetry}
        onDismiss={mockOnDismiss}
      />
    );

    expect(screen.getByText('Retry attempt 3 of 3')).toBeInTheDocument();
    expect(screen.queryByText('Try Again')).not.toBeInTheDocument();
  });
}); 