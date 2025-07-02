import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

interface PortfolioItem {
  id: number;
  item_name: string;
  brand?: string;
  model?: string;
  condition: string;
  purchase_price: number;
  purchase_date: string;
  current_market_price?: number;
  fliplens_rating?: number;
  rating_factors?: Record<string, number>;
  status: 'owned' | 'listed' | 'sold';
  profit_loss?: number;
  profit_percentage?: number;
  listing_price?: number;
  sale_price?: number;
  notes?: string;
  tags?: string[];
}

interface PortfolioSummary {
  total_items: number;
  owned_items: number;
  listed_items: number;
  sold_items: number;
  total_investment: number;
  current_value: number;
  total_profit_loss: number;
  profit_percentage: number;
}

interface PortfolioData {
  items: PortfolioItem[];
  summary: PortfolioSummary;
  pagination: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

const Portfolio: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [showAddModal, setShowAddModal] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      fetchPortfolio();
    }
  }, [isAuthenticated, currentPage, statusFilter, sortBy, sortOrder]);

  const fetchPortfolio = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: currentPage.toString(),
        per_page: '20',
        sort_by: sortBy,
        sort_order: sortOrder,
      });

      if (statusFilter) {
        params.append('status', statusFilter);
      }

      const response = await apiService.get(`/portfolio?${params}`);
      setPortfolioData(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch portfolio');
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(price);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getStatusBadge = (status: string) => {
    const statusStyles = {
      owned: 'bg-blue-100 text-blue-800',
      listed: 'bg-yellow-100 text-yellow-800',
      sold: 'bg-green-100 text-green-800',
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusStyles[status as keyof typeof statusStyles]}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  const getRatingColor = (rating: number) => {
    if (rating >= 8) return 'text-green-600';
    if (rating >= 6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getRatingStars = (rating: number) => {
    const stars = Math.round(rating / 2); // Convert 0-10 scale to 0-5 stars
    return '★'.repeat(stars) + '☆'.repeat(5 - stars);
  };

  if (!isAuthenticated) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Portfolio</h1>
          <p className="text-gray-600">Please sign in to view your portfolio.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading portfolio...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">My Portfolio</h1>
        <p className="text-gray-600">
          Track your owned items, their market value, and profit potential
        </p>
      </div>

      {/* Portfolio Summary */}
      {portfolioData?.summary && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Portfolio Summary</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {portfolioData.summary.total_items}
              </div>
              <div className="text-sm text-gray-500">Total Items</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {portfolioData.summary.owned_items}
              </div>
              <div className="text-sm text-gray-500">Owned</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">
                {portfolioData.summary.listed_items}
              </div>
              <div className="text-sm text-gray-500">Listed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {portfolioData.summary.sold_items}
              </div>
              <div className="text-sm text-gray-500">Sold</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">
                {formatPrice(portfolioData.summary.total_investment)}
              </div>
              <div className="text-sm text-gray-500">Investment</div>
            </div>
            <div className="text-center">
              <div className={`text-2xl font-bold ${portfolioData.summary.total_profit_loss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatPrice(portfolioData.summary.total_profit_loss)}
              </div>
              <div className="text-sm text-gray-500">
                P&L ({portfolioData.summary.profit_percentage.toFixed(1)}%)
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters and Controls */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-4">
            <div>
              <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                id="status"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Items</option>
                <option value="owned">Owned</option>
                <option value="listed">Listed</option>
                <option value="sold">Sold</option>
              </select>
            </div>

            <div>
              <label htmlFor="sortBy" className="block text-sm font-medium text-gray-700 mb-1">
                Sort By
              </label>
              <select
                id="sortBy"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="created_at">Date Added</option>
                <option value="purchase_date">Purchase Date</option>
                <option value="purchase_price">Purchase Price</option>
                <option value="current_market_price">Market Price</option>
                <option value="fliplens_rating">FlipLens Rating</option>
              </select>
            </div>

            <div>
              <label htmlFor="sortOrder" className="block text-sm font-medium text-gray-700 mb-1">
                Order
              </label>
              <select
                id="sortOrder"
                value={sortOrder}
                onChange={(e) => setSortOrder(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="desc">Descending</option>
                <option value="asc">Ascending</option>
              </select>
            </div>
          </div>

          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Add Item
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Portfolio Items */}
      {portfolioData?.items && portfolioData.items.length > 0 ? (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Item
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Purchase
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Market Value
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    FlipLens Rating
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    P&L
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {portfolioData.items.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {item.item_name}
                        </div>
                        {item.brand && (
                          <div className="text-sm text-gray-500">
                            {item.brand} {item.model && `- ${item.model}`}
                          </div>
                        )}
                        <div className="text-xs text-gray-400">
                          {item.condition} • {formatDate(item.purchase_date)}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatPrice(item.purchase_price)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {item.current_market_price ? formatPrice(item.current_market_price) : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {item.fliplens_rating ? (
                        <div className="text-center">
                          <div className={`text-lg font-bold ${getRatingColor(item.fliplens_rating)}`}>
                            {item.fliplens_rating.toFixed(1)}
                          </div>
                          <div className="text-xs text-gray-500">
                            {getRatingStars(item.fliplens_rating)}
                          </div>
                        </div>
                      ) : (
                        <span className="text-gray-400">N/A</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {item.profit_loss !== undefined ? (
                        <div className="text-center">
                          <div className={`text-sm font-medium ${item.profit_loss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {formatPrice(item.profit_loss)}
                          </div>
                          {item.profit_percentage !== undefined && (
                            <div className={`text-xs ${item.profit_percentage >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                              {item.profit_percentage.toFixed(1)}%
                            </div>
                          )}
                        </div>
                      ) : (
                        <span className="text-gray-400">N/A</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(item.status)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {portfolioData.pagination && portfolioData.pagination.pages > 1 && (
            <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
              <div className="flex-1 flex justify-between sm:hidden">
                <button
                  onClick={() => setCurrentPage(currentPage - 1)}
                  disabled={!portfolioData.pagination.has_prev}
                  className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setCurrentPage(currentPage + 1)}
                  disabled={!portfolioData.pagination.has_next}
                  className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  Next
                </button>
              </div>
              <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm text-gray-700">
                    Showing page {portfolioData.pagination.page} of {portfolioData.pagination.pages}
                  </p>
                </div>
                <div>
                  <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                    <button
                      onClick={() => setCurrentPage(currentPage - 1)}
                      disabled={!portfolioData.pagination.has_prev}
                      className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => setCurrentPage(currentPage + 1)}
                      disabled={!portfolioData.pagination.has_next}
                      className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                    >
                      Next
                    </button>
                  </nav>
                </div>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No portfolio items</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by adding your first item to track.
          </p>
          <div className="mt-6">
            <button
              onClick={() => setShowAddModal(true)}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              Add Your First Item
            </button>
          </div>
        </div>
      )}

      {/* Add Item Modal Placeholder */}
      {showAddModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3 text-center">
              <h3 className="text-lg font-medium text-gray-900">Add Portfolio Item</h3>
              <div className="mt-2 px-7 py-3">
                <p className="text-sm text-gray-500">
                  Add item form would go here. This requires additional form components.
                </p>
              </div>
              <div className="items-center px-4 py-3">
                <button
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 bg-gray-500 text-white text-base font-medium rounded-md shadow-sm hover:bg-gray-600"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Portfolio;
