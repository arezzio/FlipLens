import React, { useState } from 'react';
import './App.css';
import { SearchScreen } from './components/SearchScreen';
import { SavedItems } from './components/SavedItems';
import { ErrorBoundary } from './components/ErrorBoundary';
import { AuthModal } from './components/auth/AuthModal';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';

const AppContent: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');

  const handleAuthClick = (mode: 'login' | 'register') => {
    setAuthMode(mode);
    setAuthModalOpen(true);
  };

  return (
    <Router>
        {/* StockX-style Navigation Bar */}
        <nav className="sticky top-0 z-50 bg-white border-b border-neutral-200 flex items-center justify-between px-4 sm:px-8 lg:px-16 h-20">
          {/* Logo and Tagline */}
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="w-10 h-10 bg-stockx-500 rounded-lg flex items-center justify-center transition-transform group-hover:scale-105">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <div className="flex flex-col">
              <span className="text-xl font-bold text-neutral-900 tracking-tight">FlipLens</span>
              <span className="text-xs text-neutral-500 font-medium leading-tight">Find your next flip</span>
            </div>
          </Link>
          {/* Navigation Links */}
          <div className="flex-1 flex items-center justify-center space-x-8 xl:space-x-12">
            <Link to="/" className="text-base font-medium text-neutral-700 hover:text-stockx-500 transition-colors">Search</Link>
            <Link to="/saved" className="text-base font-medium text-neutral-700 hover:text-stockx-500 transition-colors">Saved Items</Link>
            {/* Placeholders for future features */}
            <button className="text-base font-medium text-neutral-400 hover:text-stockx-500 transition-colors cursor-not-allowed" disabled>Market</button>
            <button className="text-base font-medium text-neutral-400 hover:text-stockx-500 transition-colors cursor-not-allowed" disabled>Portfolio</button>
            <button className="text-base font-medium text-neutral-400 hover:text-stockx-500 transition-colors cursor-not-allowed" disabled>Alerts</button>
            <button className="text-base font-medium text-neutral-400 hover:text-stockx-500 transition-colors cursor-not-allowed" disabled>Profile</button>
            <button className="text-base font-medium text-neutral-400 hover:text-stockx-500 transition-colors cursor-not-allowed" disabled>Settings</button>
          </div>
          {/* Auth Buttons */}
          <div className="ml-4 flex items-center space-x-3">
            {isAuthenticated ? (
              <div className="flex items-center space-x-3">
                <span className="text-sm text-neutral-600">
                  Welcome, {user?.first_name || user?.username}!
                </span>
                <button
                  onClick={logout}
                  className="px-4 py-2 text-neutral-700 hover:text-stockx-500 font-medium transition-colors"
                >
                  Sign Out
                </button>
              </div>
            ) : (
              <>
                <button
                  onClick={() => handleAuthClick('login')}
                  className="px-4 py-2 text-neutral-700 hover:text-stockx-500 font-medium transition-colors"
                >
                  Sign In
                </button>
                <button
                  onClick={() => handleAuthClick('register')}
                  className="px-6 py-2 rounded-lg bg-stockx-500 text-white font-semibold text-base shadow-stockx-md hover:bg-stockx-600 transition-colors"
                >
                  Get Started
                </button>
              </>
            )}
          </div>
        </nav>
        {/* Main Content Area */}
        <div className="min-h-screen bg-neutral-50 safe-area-padding">
          <Routes>
            <Route path="/" element={<SearchScreen />} />
            <Route path="/saved" element={<SavedItems />} />
          </Routes>
        </div>

        {/* Auth Modal */}
        <AuthModal
          isOpen={authModalOpen}
          onClose={() => setAuthModalOpen(false)}
          initialMode={authMode}
        />
      </Router>
    );
};

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
