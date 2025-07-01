import React, { useEffect, useState } from 'react';
import { SavedItem } from '../types/api';
import { apiService } from '../services/api';

export const SavedItems: React.FC = () => {
  const [items, setItems] = useState<SavedItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [removing, setRemoving] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchSavedItems = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiService.getSavedItems();
      if (response.status === 'success') {
        setItems(response.items);
      } else {
        setError('Failed to load saved items.');
      }
    } catch (e) {
      setError('Failed to load saved items.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSavedItems();
  }, []);

  const handleRemove = async (item: SavedItem) => {
    setRemoving(item.id);
    setError(null);
    try {
      const response = await apiService.deleteSavedItem(item.id);
      if (response.status === 'success') {
        setItems((prev) => prev.filter((i) => i.id !== item.id));
      } else {
        setError('Failed to remove item.');
      }
    } catch (e) {
      setError('Failed to remove item.');
    } finally {
      setRemoving(null);
    }
  };

  if (isLoading) {
    return (
      <div className="w-full text-center py-16">
        <div className="loading-skeleton h-8 w-1/2 mx-auto mb-6"></div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="stockx-card animate-pulse">
              <div className="loading-skeleton aspect-square rounded-lg mb-4"></div>
              <div className="space-y-3">
                <div className="loading-skeleton h-4 w-3/4"></div>
                <div className="loading-skeleton h-4 w-1/2"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="w-full text-center py-20">
        <h2 className="text-2xl font-bold mb-4">No Saved Items</h2>
        <p className="text-neutral-600">You haven't saved any items yet. Start searching and save your favorites!</p>
      </div>
    );
  }

  return (
    <div className="w-full">
      <h2 className="text-2xl font-bold mb-8 text-center">Saved Items</h2>
      {error && <div className="text-red-600 text-center mb-4">{error}</div>}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-4 sm:gap-6 lg:gap-8">
        {items.map((item) => (
          <div key={item.id} className="stockx-card group hover:shadow-stockx-lg transition-all duration-300 relative">
            <div className="image-responsive mb-4">
              <img
                src={item.image_url || '/placeholder-image.jpg'}
                alt={item.title || 'Product image'}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                loading="lazy"
                decoding="async"
              />
              <button
                onClick={() => handleRemove(item)}
                disabled={removing === item.id}
                className={`absolute top-3 right-3 p-2 rounded-full bg-red-100 text-red-700 hover:bg-red-200 transition-all duration-200 touch-target shadow-stockx-md ${removing === item.id ? 'opacity-50 cursor-not-allowed' : ''}`}
                aria-label="Remove from saved items"
              >
                {removing === item.id ? (
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                ) : (
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                )}
              </button>
            </div>
            <div className="space-y-3 p-4">
              <h3 className="font-semibold text-neutral-900 line-clamp-2 text-sm sm:text-base lg:text-lg leading-tight">
                {item.title}
              </h3>
              <div className="flex items-center justify-between">
                <span className="text-xl font-bold text-neutral-900">
                  {new Intl.NumberFormat('en-US', { style: 'currency', currency: item.currency || 'USD' }).format(parseFloat(item.price || '0'))}
                </span>
                {item.location && (
                  <span className="stockx-badge-neutral text-xs font-semibold px-2 py-1">
                    {item.location}
                  </span>
                )}
              </div>
              <button
                onClick={() => window.open(item.item_url, '_blank')}
                className="w-full stockx-button-secondary text-sm touch-target py-2 mt-2"
              >
                View on eBay
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}; 