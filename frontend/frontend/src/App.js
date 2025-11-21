import { useState } from 'react';
import LogPanel from './components/LogPanel';

function App() {
  const [formData, setFormData] = useState({
    repo: '',
    team: '',
    window_days: 14
  });
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  const [requestStatus, setRequestStatus] = useState(null);
  const [cacheStatus, setCacheStatus] = useState(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'window_days' ? parseInt(value) || 14 : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResponse(null);
    setRequestStatus('loading');
    setCacheStatus(null);

    try {
      const res = await fetch('http://localhost:8000/analyze-workflow', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }

      const data = await res.json();
      setResponse(data);
      setRequestStatus('success');
      setCacheStatus(data.cache_status || null);
    } catch (err) {
      setError(err.message);
      setRequestStatus('error');
      setCacheStatus(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-8">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            Workflow agent
          </h1>
          <p className="text-lg text-gray-500">
            (coming soon)
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Repository
              </label>
              <input
                type="text"
                name="repo"
                value={formData.repo}
                onChange={handleInputChange}
                placeholder="owner/repository"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Team
              </label>
              <input
                type="text"
                name="team"
                value={formData.team}
                onChange={handleInputChange}
                placeholder="platform"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Window Days
              </label>
              <input
                type="number"
                name="window_days"
                value={formData.window_days}
                onChange={handleInputChange}
                min="1"
                max="90"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Analyzing...' : 'Analyze'}
            </button>
          </form>

          {/* Loading State */}
          {loading && (
            <div className="mt-4 p-4 bg-blue-50 rounded-md">
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                <span className="text-blue-700">Analyzing workflow...</span>
              </div>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="mt-4 p-4 bg-red-50 rounded-md">
              <div className="flex">
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">
                    Error
                  </h3>
                  <div className="mt-2 text-sm text-red-700">
                    {error}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Response Panel */}
          {response && (
            <div className="mt-4">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Response</h3>
              <pre className="bg-gray-100 rounded-md p-4 overflow-auto text-sm font-mono text-gray-800 max-h-96">
                {JSON.stringify(response, null, 2)}
              </pre>
            </div>
          )}

          {/* Log Panel */}
          {(requestStatus || cacheStatus) && (
            <div className="mt-4">
              <LogPanel 
                lastRequest={requestStatus} 
                cacheStatus={cacheStatus} 
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
