import React, { useState, useEffect } from 'react';
import { SearchBar } from './SearchBar';
import { SearchResults } from './SearchResults';
import { ResponsiveTest } from './ResponsiveTest';
import { ErrorDisplay } from './ErrorDisplay';
import { OfflineIndicator, OfflineBanner } from './OfflineIndicator';
import { SearchResult, SavedItem } from '../types/api';
import { apiService } from '../services/api';
import { useErrorHandler } from '../hooks/useErrorHandler';
import { useOfflineDetection } from '../hooks/useOfflineDetection';

export const SearchScreen: React.FC = () => {
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [savedItems, setSavedItems] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [lastQuery, setLastQuery] = useState<string | null>(null);
  const [lastSaveItem, setLastSaveItem] = useState<SearchResult | null>(null);
  
  // Error handling
  const { errorState, setError, clearError, retry } = useErrorHandler();
  
  // Offline detection
  const { isOffline } = useOfflineDetection();

  // Load saved items on component mount
  useEffect(() => {
    const loadSavedItems = async () => {
      try {
        const response = await apiService.getSavedItems();
        if (response.status === 'success') {
          const savedIds = new Set(response.items.map((item: SavedItem) => item.id));
          setSavedItems(savedIds);
        }
      } catch (err) {
        console.error('Failed to load saved items:', err);
        // Don't show error for saved items loading - it's not critical
      }
    };

    loadSavedItems();
  }, []);

  const handleSearch = async (query: string) => {
    if (!query.trim()) return;

    setIsLoading(true);
    clearError();
    setHasSearched(true);
    setLastQuery(query);

    try {
      const response = await apiService.searchItems(query, 20);
      if (response.status === 'success') {
        setSearchResults(response.results);
      } else {
        setError({
          error: 'SearchError',
          message: 'Failed to search items. Please try again.',
          status: 'error',
          code: 'SEARCH_ERROR',
          retryable: true
        });
        setSearchResults([]);
      }
    } catch (err) {
      const apiError = err as any;
      setError(apiError);
      setSearchResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetrySearch = async () => {
    if (hasSearched && lastQuery) {
      await retry(async () => {
        setIsLoading(true);
        try {
          const response = await apiService.searchItems(lastQuery, 20);
          if (response.status === 'success') {
            setSearchResults(response.results);
          } else {
            setError({
              error: 'SearchError',
              message: 'Failed to search items. Please try again.',
              status: 'error',
              code: 'SEARCH_ERROR',
              retryable: true
            });
            setSearchResults([]);
          }
        } catch (err) {
          const apiError = err as any;
          setError(apiError);
          setSearchResults([]);
        } finally {
          setIsLoading(false);
        }
      });
    }
  };

  const handleSaveItem = async (item: SearchResult) => {
    setLastSaveItem(item);
    try {
      const response = await apiService.saveItem({
        item_id: item.itemId,
        title: item.title,
        price: item.price,
        currency: item.currency,
        image_url: item.galleryURL,
        item_url: item.viewItemURL,
        condition: item.condition,
        location: item.location,
        notes: ''
      });

      if (response.status === 'success') {
        // Update saved items set
        const newSavedItems = new Set(savedItems);
        if (newSavedItems.has(item.itemId)) {
          newSavedItems.delete(item.itemId);
        } else {
          newSavedItems.add(item.itemId);
        }
        setSavedItems(newSavedItems);
      } else {
        setError({
          error: 'SaveError',
          message: 'Failed to save item. Please try again.',
          status: 'error',
          code: 'SAVE_ERROR',
          retryable: true
        });
      }
    } catch (err) {
      const apiError = err as any;
      setError(apiError);
    }
  };

  const handleRetrySave = async () => {
    if (lastSaveItem) {
      await retry(async () => {
        await handleSaveItem(lastSaveItem);
      });
    }
  };

  return (
    <div className="min-h-screen bg-neutral-50 safe-area-padding">
      {/* Offline Indicator */}
      <OfflineIndicator />
      {/* Responsive Test Indicator */}
      <ResponsiveTest />
      {/* Main Content */}
      <main className="container-responsive py-6 sm:py-8 lg:py-12 xl:py-16">
        {/* Search Section */}
        <section className="mb-8 sm:mb-12 lg:mb-16 xl:mb-20">
          <div className="text-center mb-6 sm:mb-8 lg:mb-12">
            <h2 className="heading-responsive text-neutral-900 mb-3 sm:mb-4 lg:mb-6">
              Discover Your Next Investment
            </h2>
            <p className="text-responsive text-neutral-600 max-w-3xl mx-auto">
              Search millions of items on eBay to find the best deals and opportunities for flipping
            </p>
          </div>
          <SearchBar
            onSearch={handleSearch}
            isLoading={isLoading}
            placeholder="Search for items on eBay..."
          />
        </section>
        {/* Offline Banner */}
        <OfflineBanner className="mb-6" />
        {/* Enhanced Error Display */}
        <ErrorDisplay
          errorState={errorState}
          onRetry={errorState.error?.code === 'SAVE_ERROR' ? handleRetrySave : handleRetrySearch}
          onDismiss={clearError}
        />
        {/* Results Section */}
        {hasSearched && (
          <section className="animate-fade-in">
            <SearchResults
              items={searchResults}
              onSaveItem={handleSaveItem}
              savedItems={savedItems}
              isLoading={isLoading}
              isCached={searchResults.length > 0 && (searchResults as any)._cached}
            />
          </section>
        )}
        {/* Empty State */}
        {!hasSearched && !isLoading && (
          <section className="text-center py-12 sm:py-16 lg:py-20 xl:py-24">
            <div className="max-w-md lg:max-w-lg xl:max-w-xl mx-auto">
              <div className="w-20 h-20 sm:w-24 sm:h-24 lg:w-28 lg:h-28 xl:w-32 xl:h-32 mx-auto mb-6 sm:mb-8 lg:mb-10 bg-neutral-100 rounded-full flex items-center justify-center">
                <svg
                  className="w-10 h-10 sm:w-12 sm:h-12 lg:w-14 lg:h-14 xl:w-16 xl:h-16 text-neutral-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
              </div>
              <h3 className="text-lg sm:text-xl lg:text-2xl xl:text-3xl font-bold text-neutral-900 mb-3 sm:mb-4 lg:mb-6">
                Ready to Find Deals?
              </h3>
              <p className="text-sm sm:text-base lg:text-lg xl:text-xl text-neutral-600 mb-6 sm:mb-8 lg:mb-10">
                Start by searching for items you're interested in flipping. We'll help you find the best opportunities.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 lg:gap-6 justify-center">
                <button
                  onClick={() => handleSearch('iPhone')}
                  className="stockx-button-primary text-sm sm:text-base lg:text-lg touch-target px-6 lg:px-8 py-3 lg:py-4"
                >
                  Search iPhone
                </button>
                <button
                  onClick={() => handleSearch('Nike Air Jordan')}
                  className="stockx-button-secondary text-sm sm:text-base lg:text-lg touch-target px-6 lg:px-8 py-3 lg:py-4"
                >
                  Search Sneakers
                </button>
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}; 