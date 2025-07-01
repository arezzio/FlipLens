import React, { ReactNode } from 'react';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  errorInfo?: string;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(_: Error): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log error to console or external service
    // eslint-disable-next-line no-console
    console.error('Uncaught error:', error, errorInfo);
    this.setState({ errorInfo: errorInfo.componentStack || undefined });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-red-50 text-red-800 p-8">
          <h1 className="text-2xl font-bold mb-2">Something went wrong</h1>
          <p className="mb-4">An unexpected error occurred. Please refresh the page or try again later.</p>
          {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
            <pre className="bg-red-100 p-2 rounded text-xs overflow-x-auto max-w-xl">{this.state.errorInfo}</pre>
          )}
        </div>
      );
    }
    return this.props.children;
  }
} 