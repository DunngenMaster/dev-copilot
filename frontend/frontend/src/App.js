import { useState } from 'react';
import ResultCard from './components/ResultCard';
import Dashboard from './components/Dashboard';

function App() {
  const [activeTab, setActiveTab] = useState('analyze'); // 'analyze' or 'dashboard'
  const [repo, setRepo] = useState('owner/repository');
  const [team, setTeam] = useState('platform');
  const [windowDays, setWindowDays] = useState(14);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [response, setResponse] = useState(null);

  const onSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await fetch('http://localhost:8000/analyze-workflow', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo, team, window_days: Number(windowDays) })
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResponse(data);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-slate-900 to-gray-800 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-6xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent mb-4">Workflow Agent</h1>
          <p className="text-gray-400 text-lg">AI-powered workflow analysis</p>
        </div>

        {/* Tab Navigation */}
        <div className="flex justify-center mb-8 gap-4">
          <button
            onClick={() => setActiveTab('analyze')}
            className={`px-8 py-3 rounded-lg font-semibold transition-all ${
              activeTab === 'analyze'
                ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg'
                : 'bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700'
            }`}
          >
            🔍 Analyze
          </button>
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`px-8 py-3 rounded-lg font-semibold transition-all ${
              activeTab === 'dashboard'
                ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg'
                : 'bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700'
            }`}
          >
            📊 Dashboard
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'analyze' ? (
          <>
            <div className="bg-gray-800 bg-opacity-50 backdrop-blur-xl border border-gray-700 rounded-2xl shadow-2xl p-8 mb-8">
              <form onSubmit={onSubmit} className="grid grid-cols-1 gap-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-300 mb-2">
                    Repository
                  </label>
                  <input 
                    className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all" 
                    placeholder="owner/repository"
                    value={repo} 
                    onChange={e=>setRepo(e.target.value)}
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-semibold text-gray-300 mb-2">
                    Team
                  </label>
                  <input 
                    className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all" 
                    placeholder="platform"
                    value={team} 
                    onChange={e=>setTeam(e.target.value)}
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-semibold text-gray-300 mb-2">
                    Window Days
                  </label>
                  <input 
                    type="number" 
                    className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all" 
                    min="1"
                    max="90"
                    value={windowDays} 
                    onChange={e=>setWindowDays(e.target.value)}
                    required
                  />
                </div>
                
                <button 
                  disabled={loading} 
                  className="mt-4 px-6 py-4 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold text-lg hover:from-blue-700 hover:to-purple-700 disabled:from-gray-600 disabled:to-gray-600 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl transform hover:scale-[1.02] active:scale-[0.98]"
                >
                  {loading ? (
                    <span className="flex items-center justify-center">
                      <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Analyzing...
                    </span>
                  ) : (
                    'Analyze Workflow'
                  )}
                </button>
              </form>
              
              {error && (
                <div className="mt-6 p-4 bg-red-900 bg-opacity-50 border border-red-700 rounded-lg backdrop-blur-sm">
                  <p className="text-red-200 text-sm font-medium">{error}</p>
                </div>
              )}
            </div>
            
            <ResultCard data={response}/>
          </>
        ) : (
          <Dashboard />
        )}
      </div>
    </div>
  );
}

export default App;
