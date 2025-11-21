import React from 'react';

const LogPanel = ({ lastRequest, cacheStatus }) => {
  if (!lastRequest && !cacheStatus) {
    return null;
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'success':
        return 'text-green-600 bg-green-50';
      case 'error':
        return 'text-red-600 bg-red-50';
      case 'loading':
        return 'text-blue-600 bg-blue-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getCacheStatusColor = (status) => {
    switch (status) {
      case 'HIT':
        return 'text-green-700 bg-green-100';
      case 'MISS':
        return 'text-orange-700 bg-orange-100';
      default:
        return 'text-gray-700 bg-gray-100';
    }
  };

  return (
    <div className="border border-gray-300 rounded-md p-3 bg-gray-50 text-sm">
      <div className="font-medium text-gray-700 mb-2">Request Log</div>
      
      <div className="space-y-1">
        {lastRequest && (
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Status:</span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(lastRequest)}`}>
              {lastRequest.toUpperCase()}
            </span>
          </div>
        )}
        
        {cacheStatus && (
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Cache:</span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCacheStatusColor(cacheStatus)}`}>
              {cacheStatus}
            </span>
          </div>
        )}
        
        <div className="flex items-center justify-between text-xs text-gray-500 pt-1">
          <span>Last updated:</span>
          <span>{new Date().toLocaleTimeString()}</span>
        </div>
      </div>
    </div>
  );
};

export default LogPanel;