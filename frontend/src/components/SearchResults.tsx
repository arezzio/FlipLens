import React, { useState } from 'react';
import { SearchResult } from '../types/api';

interface SearchResultsProps {
  items: SearchResult[];
  onSaveItem: (item: SearchResult) => void;
  savedItems: Set<string>;
  isLoading?: boolean;
  isCached?: boolean;
}

export const SearchResults: React.FC<SearchResultsProps> = ({
  items,
  onSaveItem,
  savedItems,
  isLoading = false,
  isCached = false
}) => {
  const [imageErrors, setImageErrors] = useState<Set<string>>(new Set());
  const [savingItems, setSavingItems] = useState<Set<string>>(new Set());

  // Image optimization helper
  const getOptimizedImageUrl = (originalUrl: string, width: number = 400) => {
    if (!originalUrl || originalUrl.includes('placeholder')) {
      return '/placeholder-image.jpg';
    }
    
    // For eBay images, we can optimize by adding size parameters
    // This is a basic optimization - in production you'd use a CDN or image service
    try {
      const url = new URL(originalUrl);
      if (url.hostname.includes('ebay')) {
        // eBay images can be optimized by adding size parameters
        url.searchParams.set('s', `${width}x${width}`);
        return url.toString();
      }
    } catch (e) {
      // If URL parsing fails, return original
      return originalUrl;
    }
    
    return originalUrl;
  };

  // Intersection Observer for lazy loading
  const imageRef = React.useRef<HTMLImageElement>(null);
  
  React.useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const img = entry.target as HTMLImageElement;
            if (img.dataset.src) {
              img.src = img.dataset.src;
              img.removeAttribute('data-src');
              observer.unobserve(img);
            }
          }
        });
      },
      {
        rootMargin: '50px 0px',
        threshold: 0.1
      }
    );

    const images = document.querySelectorAll('img[data-src]');
    images.forEach((img) => observer.observe(img));

    return () => observer.disconnect();
  }, [items]);

  // Handle image loading errors
  const handleImageError = (itemId: string, fallbackUrl: string) => {
    setImageErrors(prev => new Set(prev).add(itemId));
    return fallbackUrl;
  };

  // Handle save item with loading state
  const handleSaveItem = async (item: SearchResult) => {
    setSavingItems(prev => new Set(prev).add(item.itemId));
    
    try {
      await onSaveItem(item);
    } catch (error) {
      console.error('Failed to save item:', error);
      // Error will be handled by parent component
    } finally {
      setSavingItems(prev => {
        const newSet = new Set(prev);
        newSet.delete(item.itemId);
        return newSet;
      });
    }
  };

  if (isLoading) {
    return (
      <div className="w-full">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-4 sm:gap-6 lg:gap-8">
          {[...Array(10)].map((_, index) => (
            <div key={index} className="stockx-card animate-pulse">
              <div className="loading-skeleton aspect-square rounded-lg mb-4 lg:mb-6"></div>
              <div className="space-y-3 lg:space-y-4">
                <div className="loading-skeleton h-4 w-3/4"></div>
                <div className="loading-skeleton h-4 w-1/2"></div>
                <div className="loading-skeleton h-6 w-1/3"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="w-full text-center py-12 sm:py-16 lg:py-20">
        <div className="max-w-md lg:max-w-lg mx-auto">
          <svg
            className="mx-auto h-16 w-16 sm:h-20 sm:w-20 lg:h-24 lg:w-24 text-neutral-300 mb-4 lg:mb-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <h3 className="text-lg sm:text-xl lg:text-2xl xl:text-3xl font-semibold text-neutral-900 mb-2 lg:mb-3">
            No items found
          </h3>
          <p className="text-neutral-600 text-sm sm:text-base lg:text-lg">
            Try adjusting your search terms or browse our popular categories
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full">
      {/* Results Header */}
      <div className="mb-6 sm:mb-8 lg:mb-12">
        <div className="flex items-center justify-between mb-2 lg:mb-3">
          <h2 className="text-xl sm:text-2xl lg:text-3xl xl:text-4xl font-bold text-neutral-900">
            Search Results
          </h2>
          {isCached && (
            <div className="flex items-center space-x-2 px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-medium">
              <span>📦</span>
              <span>Cached</span>
            </div>
          )}
        </div>
        <p className="text-neutral-600 text-sm sm:text-base lg:text-lg">
          Found {items.length} item{items.length !== 1 ? 's' : ''}
          {isCached && (
            <span className="text-yellow-600 ml-2">
              (showing cached results)
            </span>
          )}
        </p>
      </div>

      {/* Results Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-4 sm:gap-6 lg:gap-8">
        {items.map((item) => {
          const isSaved = savedItems.has(item.itemId);
          const isSaving = savingItems.has(item.itemId);
          const hasImageError = imageErrors.has(item.itemId);
          
          const price = parseFloat(item.price || '0');
          const formattedPrice = new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: item.currency || 'USD',
          }).format(price);

          // Optimize image URL based on screen size
          const imageUrl = getOptimizedImageUrl(item.galleryURL || '', 400);
          const placeholderUrl = '/placeholder-image.jpg';
          const finalImageUrl = hasImageError ? placeholderUrl : imageUrl;

          return (
            <div key={item.itemId} className="stockx-card group hover:shadow-stockx-lg transition-all duration-300">
              {/* Image Container */}
              <div className="image-responsive mb-4 sm:mb-6 lg:mb-8">
                <img
                  ref={imageRef}
                  data-src={finalImageUrl}
                  src={placeholderUrl}
                  alt={item.title || 'Product image'}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  loading="lazy"
                  decoding="async"
                  onError={(e) => {
                    const target = e.target as HTMLImageElement;
                    handleImageError(item.itemId, placeholderUrl);
                    target.src = placeholderUrl;
                  }}
                  onLoad={(e) => {
                    const target = e.target as HTMLImageElement;
                    target.classList.add('loaded');
                  }}
                />
                
                {/* Save Button with Loading State */}
                <button
                  onClick={() => handleSaveItem(item)}
                  disabled={isSaving}
                  className={`absolute top-3 right-3 p-2 lg:p-3 rounded-full transition-all duration-200 touch-target ${
                    isSaving
                      ? 'bg-neutral-400 text-white shadow-stockx-md cursor-not-allowed'
                      : isSaved
                      ? 'bg-stockx-500 text-white shadow-stockx-md'
                      : 'bg-white/90 text-neutral-600 hover:bg-stockx-500 hover:text-white shadow-stockx'
                  }`}
                  aria-label={isSaved ? 'Remove from saved items' : 'Save item'}
                >
                  {isSaving ? (
                    <svg className="animate-spin h-4 w-4 sm:h-5 sm:w-5 lg:h-6 lg:w-6" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                  ) : (
                    <svg
                      className={`h-4 w-4 sm:h-5 sm:w-5 lg:h-6 lg:w-6 ${isSaved ? 'fill-current' : 'stroke-current fill-none'}`}
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={isSaved ? 0 : 2}
                        d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                      />
                    </svg>
                  )}
                </button>

                {/* Condition Badge */}
                {item.condition && (
                  <div className="absolute top-3 left-3">
                    <span className="stockx-badge-premium text-xs sm:text-sm lg:text-base font-semibold px-2 py-1 lg:px-3 lg:py-1.5">
                      {item.condition}
                    </span>
                  </div>
                )}

                {/* Confidence Badge */}
                {typeof item.confidence === 'number' && (
                  <div className={`absolute ${item.condition ? 'top-12' : 'top-3'} left-3`}>
                    <span
                      className={`text-xs sm:text-sm lg:text-base font-semibold px-2 py-1 lg:px-3 lg:py-1.5 rounded-full shadow-sm
                        ${item.confidence >= 0.8 ? 'bg-green-100 text-green-800' : item.confidence >= 0.5 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}`}
                      aria-label={`Confidence: ${Math.round(item.confidence * 100)}%`}
                    >
                      Confidence: {Math.round(item.confidence * 100)}%
                    </span>
                  </div>
                )}

                {/* Image Error Indicator */}
                {hasImageError && (
                  <div className="absolute bottom-3 left-3">
                    <span className="bg-neutral-800/75 text-white text-xs px-2 py-1 rounded-full">
                      Image unavailable
                    </span>
                  </div>
                )}
              </div>

              {/* Content */}
              <div className="space-y-3 sm:space-y-4 lg:space-y-5 p-4 sm:p-6 lg:p-8">
                {/* Title */}
                <h3 className="font-semibold text-neutral-900 line-clamp-2 text-sm sm:text-base lg:text-lg leading-tight">
                  {item.title}
                </h3>

                {/* Price */}
                <div className="flex items-center justify-between">
                  <div className="flex items-baseline space-x-2 lg:space-x-3">
                    <span className="text-xl sm:text-2xl lg:text-3xl xl:text-4xl font-bold text-neutral-900">
                      {formattedPrice}
                    </span>
                  </div>
                  
                  {/* Location Badge */}
                  {item.location && (
                    <span className="stockx-badge-neutral text-xs sm:text-sm lg:text-base font-semibold px-2 py-1 lg:px-3 lg:py-1.5">
                      {item.location}
                    </span>
                  )}
                </div>

                {/* View Details Button */}
                <button
                  onClick={() => window.open(item.viewItemURL, '_blank')}
                  className="w-full stockx-button-secondary text-sm sm:text-base lg:text-lg touch-target py-3 lg:py-4"
                >
                  View on eBay
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Load More Button (if needed) */}
      {items.length >= 10 && (
        <div className="mt-8 sm:mt-12 lg:mt-16 text-center">
          <button className="stockx-button-primary text-sm sm:text-base lg:text-lg touch-target px-8 lg:px-12 py-3 lg:py-4">
            Load More Results
          </button>
        </div>
      )}
    </div>
  );
}; 