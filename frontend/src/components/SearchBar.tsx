import React, { useState } from 'react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  isLoading?: boolean;
  placeholder?: string;
}

export const SearchBar: React.FC<SearchBarProps> = ({
  onSearch,
  isLoading = false,
  placeholder = "Search for items on eBay..."
}) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && query.trim()) {
      onSearch(query.trim());
    }
  };

  return (
    <div className="w-full max-w-sm sm:max-w-md lg:max-w-lg xl:max-w-xl 2xl:max-w-2xl mx-auto">
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={placeholder}
            disabled={isLoading}
            className="stockx-input text-base sm:text-lg lg:text-xl font-medium placeholder-neutral-400 disabled:opacity-50 disabled:cursor-not-allowed pr-24 lg:pr-28 pl-16 touch-target"
          />
          
          {/* Search Icon */}
          <div className="absolute inset-y-0 left-0 pl-4 lg:pl-6 flex items-center pointer-events-none">
            <svg
              className="h-5 w-5 sm:h-6 sm:w-6 lg:h-7 lg:w-7 text-neutral-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>

          {/* Search Button */}
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="absolute inset-y-0 right-0 px-4 sm:px-6 lg:px-8 flex items-center bg-stockx-500 text-white rounded-r-xl hover:bg-stockx-600 focus:outline-none focus:ring-2 focus:ring-stockx-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-semibold touch-target"
          >
            {isLoading ? (
              <svg
                className="animate-spin h-4 w-4 sm:h-5 sm:w-5 lg:h-6 lg:w-6 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
            ) : (
              <span className="font-semibold text-sm sm:text-base lg:text-lg">Search</span>
            )}
          </button>
        </div>
      </form>

      {/* Search Suggestions */}
      {query && !isLoading && (
        <div className="mt-3 lg:mt-4 text-sm lg:text-base text-neutral-600 animate-fade-in">
          <p className="font-medium">Press Enter to search for "{query}"</p>
        </div>
      )}

      {/* Popular Searches */}
      {!query && !isLoading && (
        <div className="mt-4 sm:mt-6 lg:mt-8 animate-fade-in">
          <p className="text-sm lg:text-base font-medium text-neutral-700 mb-3 lg:mb-4">Popular searches:</p>
          <div className="flex flex-wrap gap-2 lg:gap-3">
            {['iPhone', 'Nike Air Jordan', 'Supreme', 'Yeezy', 'PlayStation 5'].map((term) => (
              <button
                key={term}
                onClick={() => onSearch(term)}
                className="stockx-badge-neutral hover:bg-neutral-200 transition-colors duration-200 cursor-pointer touch-target text-xs sm:text-sm lg:text-base px-3 py-1 lg:px-4 lg:py-2"
              >
                {term}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}; 