import React, { useState } from 'react';
import './App.css';
import { SearchScreen } from './components/SearchScreen';
import { SavedItems } from './components/SavedItems';
import { ErrorBoundary } from './components/ErrorBoundary';
import { AuthModal } from './components/auth/AuthModal';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import MarketTrends from './components/MarketTrends';
import Portfolio from './components/Portfolio';
import Alerts from './components/Alerts';
import Profile from './components/Profile';
import Settings from './components/Settings';
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
      <div className="bg-neutral-50 min-h-screen">
        {/* Navigation */}
        <nav className="bg-white shadow-sm border-b border-neutral-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              {/* Logo */}
              <div className="flex items-center">
                <Link to="/" className="flex items-center">
                  <div className="text-2xl font-bold text-blue-600">FlipLens</div>
                </Link>
              </div>

              {/* Navigation Links */}
              <div className="hidden md:block">
                <div className="ml-10 flex items-baseline space-x-4">
                  <Link
                    to="/"
                    className="text-neutral-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                  >
                    Search
                  </Link>
                  <Link
                    to="/saved"
                    className="text-neutral-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                  >
                    Saved Items
                  </Link>
                  <Link
                    to="/market-trends"
                    className="text-neutral-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                  >
                    Market Trends
                  </Link>
                  <Link
                    to="/portfolio"
                    className="text-neutral-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                  >
                    Portfolio
                  </Link>
                  <Link
                    to="/alerts"
                    className="text-neutral-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                  >
                    Alerts
                  </Link>
                  {isAuthenticated && (
                    <>
                      <Link
                        to="/profile"
                        className="text-neutral-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                      >
                        Profile
                      </Link>
                      <Link
                        to="/settings"
                        className="text-neutral-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                      >
                        Settings
                      </Link>
                    </>
                  )}
                </div>
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
                      className="px-4 py-2 text-neutral-700 hover:text-blue-600 font-medium transition-colors"
                    >
                      Sign Out
                    </button>
                  </div>
                ) : (
                  <>
                    <button
                      onClick={() => handleAuthClick('login')}
                      className="px-4 py-2 text-neutral-700 hover:text-blue-600 font-medium transition-colors"
                    >
                      Sign In
                    </button>
                    <button
                      onClick={() => handleAuthClick('register')}
                      className="px-6 py-2 rounded-lg bg-blue-600 text-white font-semibold text-base shadow-md hover:bg-blue-700 transition-colors"
                    >
                      Get Started
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <Routes>
            <Route path="/" element={<SearchScreen />} />
            <Route path="/saved" element={<SavedItems />} />
            <Route path="/market-trends" element={<MarketTrends />} />
            <Route path="/portfolio" element={<Portfolio />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
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
