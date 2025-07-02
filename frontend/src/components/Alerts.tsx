import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

interface PriceAlert {
  id: number;
  item_identifier: string;
  platform?: string;
  condition?: string;
  alert_type: 'price_drop' | 'price_increase' | 'threshold';
  threshold_price?: number;
  percentage_change?: number;
  is_active: boolean;
  notification_method: string;
  baseline_price?: number;
  last_checked_price?: number;
  last_triggered?: string;
  trigger_count: number;
  notes?: string;
  created_at: string;
  updated_at: string;
}

interface AlertStats {
  total_alerts: number;
  active_alerts: number;
  triggered_alerts: number;
  inactive_alerts: number;
}

interface AlertsData {
  alerts: PriceAlert[];
  stats: AlertStats;
  pagination: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

const Alerts: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [alertsData, setAlertsData] = useState<AlertsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [activeFilter, setActiveFilter] = useState<boolean | null>(null);
  const [alertTypeFilter, setAlertTypeFilter] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      fetchAlerts();
    }
  }, [isAuthenticated, currentPage, activeFilter, alertTypeFilter]);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: currentPage.toString(),
        per_page: '20',
      });

      if (activeFilter !== null) {
        params.append('is_active', activeFilter.toString());
      }

      if (alertTypeFilter) {
        params.append('alert_type', alertTypeFilter);
      }

      const response = await apiService.get(`/alerts?${params}`);
      setAlertsData(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch alerts');
    } finally {
      setLoading(false);
    }
  };

  const toggleAlert = async (alertId: number) => {
    try {
      await apiService.post(`/alerts/${alertId}/toggle`);
      fetchAlerts(); // Refresh the list
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to toggle alert');
    }
  };

  const deleteAlert = async (alertId: number) => {
    if (!window.confirm('Are you sure you want to delete this alert?')) {
      return;
    }

    try {
      await apiService.delete(`/alerts/${alertId}`);
      fetchAlerts(); // Refresh the list
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to delete alert');
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

  const getAlertTypeLabel = (type: string) => {
    const labels = {
      price_drop: 'Price Drop',
      price_increase: 'Price Increase',
      threshold: 'Price Threshold',
    };
    return labels[type as keyof typeof labels] || type;
  };

  const getAlertTypeColor = (type: string) => {
    const colors = {
      price_drop: 'bg-red-100 text-red-800',
      price_increase: 'bg-green-100 text-green-800',
      threshold: 'bg-blue-100 text-blue-800',
    };
    return colors[type as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  const getAlertDescription = (alert: PriceAlert) => {
    switch (alert.alert_type) {
      case 'threshold':
        return `Alert when price drops to ${alert.threshold_price ? formatPrice(alert.threshold_price) : 'N/A'}`;
      case 'price_drop':
        return `Alert when price drops by ${alert.percentage_change}%`;
      case 'price_increase':
        return `Alert when price increases by ${alert.percentage_change}%`;
      default:
        return 'Unknown alert type';
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Price Alerts</h1>
          <p className="text-gray-600">Please sign in to view your price alerts.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading alerts...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Price Alerts</h1>
        <p className="text-gray-600">
          Get notified when items reach your target prices or change by specific percentages
        </p>
      </div>

      {/* Alert Statistics */}
      {alertsData?.stats && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Alert Statistics</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {alertsData.stats.total_alerts}
              </div>
              <div className="text-sm text-gray-500">Total Alerts</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {alertsData.stats.active_alerts}
              </div>
              <div className="text-sm text-gray-500">Active</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">
                {alertsData.stats.triggered_alerts}
              </div>
              <div className="text-sm text-gray-500">Triggered</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-600">
                {alertsData.stats.inactive_alerts}
              </div>
              <div className="text-sm text-gray-500">Inactive</div>
            </div>
          </div>
        </div>
      )}

      {/* Filters and Controls */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-4">
            <div>
              <label htmlFor="activeFilter" className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                id="activeFilter"
                value={activeFilter === null ? '' : activeFilter.toString()}
                onChange={(e) => setActiveFilter(e.target.value === '' ? null : e.target.value === 'true')}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Alerts</option>
                <option value="true">Active</option>
                <option value="false">Inactive</option>
              </select>
            </div>

            <div>
              <label htmlFor="alertType" className="block text-sm font-medium text-gray-700 mb-1">
                Alert Type
              </label>
              <select
                id="alertType"
                value={alertTypeFilter}
                onChange={(e) => setAlertTypeFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Types</option>
                <option value="threshold">Price Threshold</option>
                <option value="price_drop">Price Drop</option>
                <option value="price_increase">Price Increase</option>
              </select>
            </div>
          </div>

          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Create Alert
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Alerts List */}
      {alertsData?.alerts && alertsData.alerts.length > 0 ? (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="divide-y divide-gray-200">
            {alertsData.alerts.map((alert) => (
              <div key={alert.id} className="p-6 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-medium text-gray-900">
                        {alert.item_identifier}
                      </h3>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getAlertTypeColor(alert.alert_type)}`}>
                        {getAlertTypeLabel(alert.alert_type)}
                      </span>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${alert.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                        {alert.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>

                    <p className="text-sm text-gray-600 mb-2">
                      {getAlertDescription(alert)}
                    </p>

                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      {alert.platform && (
                        <span>Platform: {alert.platform}</span>
                      )}
                      {alert.condition && (
                        <span>Condition: {alert.condition}</span>
                      )}
                      <span>Created: {formatDate(alert.created_at)}</span>
                      {alert.trigger_count > 0 && (
                        <span>Triggered: {alert.trigger_count} times</span>
                      )}
                    </div>

                    {alert.last_triggered && (
                      <div className="mt-2 text-sm text-yellow-600">
                        Last triggered: {formatDate(alert.last_triggered)}
                      </div>
                    )}

                    {alert.notes && (
                      <div className="mt-2 text-sm text-gray-600">
                        Notes: {alert.notes}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => toggleAlert(alert.id)}
                      className={`px-3 py-1 rounded-md text-sm font-medium ${
                        alert.is_active
                          ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200'
                          : 'bg-green-100 text-green-800 hover:bg-green-200'
                      }`}
                    >
                      {alert.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                    <button
                      onClick={() => deleteAlert(alert.id)}
                      className="px-3 py-1 bg-red-100 text-red-800 rounded-md text-sm font-medium hover:bg-red-200"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {alertsData.pagination && alertsData.pagination.pages > 1 && (
            <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
              <div className="flex-1 flex justify-between sm:hidden">
                <button
                  onClick={() => setCurrentPage(currentPage - 1)}
                  disabled={!alertsData.pagination.has_prev}
                  className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setCurrentPage(currentPage + 1)}
                  disabled={!alertsData.pagination.has_next}
                  className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  Next
                </button>
              </div>
              <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm text-gray-700">
                    Showing page {alertsData.pagination.page} of {alertsData.pagination.pages}
                  </p>
                </div>
                <div>
                  <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                    <button
                      onClick={() => setCurrentPage(currentPage - 1)}
                      disabled={!alertsData.pagination.has_prev}
                      className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => setCurrentPage(currentPage + 1)}
                      disabled={!alertsData.pagination.has_next}
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
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5v-5zM9 7H4l5-5v5zm6 10V7a1 1 0 00-1-1H5a1 1 0 00-1 1v10a1 1 0 001 1h9a1 1 0 001-1z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No price alerts</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by creating your first price alert.
          </p>
          <div className="mt-6">
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              Create Your First Alert
            </button>
          </div>
        </div>
      )}

      {/* Create Alert Modal Placeholder */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3 text-center">
              <h3 className="text-lg font-medium text-gray-900">Create Price Alert</h3>
              <div className="mt-2 px-7 py-3">
                <p className="text-sm text-gray-500">
                  Create alert form would go here. This requires additional form components.
                </p>
              </div>
              <div className="items-center px-4 py-3">
                <button
                  onClick={() => setShowCreateModal(false)}
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

export default Alerts;
