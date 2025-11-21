import React, { useState, useEffect } from 'react';

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/dashboard/summary')
      .then(res => res.json())
      .then(data => {
        setSummary(data);
        setLoading(false);
      })
      .catch(err => console.error(err));
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 p-6">
      {/* Total Analyses Card */}
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-6 border border-gray-700 shadow-2xl">
        <h3 className="text-gray-400 text-sm font-medium mb-2">Total Analyses</h3>
        <p className="text-4xl font-bold text-white">{summary?.total_analyses || 0}</p>
        <p className="text-sm text-emerald-400 mt-2">↑ All time</p>
      </div>

      {/* Average Score Card */}
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-6 border border-gray-700 shadow-2xl">
        <h3 className="text-gray-400 text-sm font-medium mb-2">Avg Health Score</h3>
        <p className="text-4xl font-bold text-white">{summary?.avg_score || 0}</p>
        <div className="w-full bg-gray-700 rounded-full h-2 mt-4">
          <div 
            className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full"
            style={{ width: `${summary?.avg_score || 0}%` }}
          ></div>
        </div>
      </div>

      {/* Score Distribution Card */}
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-6 border border-gray-700 shadow-2xl col-span-2">
        <h3 className="text-gray-400 text-sm font-medium mb-4">Score Distribution</h3>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-emerald-400 flex items-center">
              <span className="w-3 h-3 bg-emerald-500 rounded-full mr-2"></span>
              Excellent (90+)
            </span>
            <span className="text-white font-semibold">
              {summary?.score_distribution?.excellent || 0}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-blue-400 flex items-center">
              <span className="w-3 h-3 bg-blue-500 rounded-full mr-2"></span>
              Good (70-89)
            </span>
            <span className="text-white font-semibold">
              {summary?.score_distribution?.good || 0}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-orange-400 flex items-center">
              <span className="w-3 h-3 bg-orange-500 rounded-full mr-2"></span>
              Needs Work (&lt;70)
            </span>
            <span className="text-white font-semibold">
              {summary?.score_distribution?.needs_improvement || 0}
            </span>
          </div>
        </div>
      </div>

      {/* Top Teams Card */}
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-6 border border-gray-700 shadow-2xl col-span-2">
        <h3 className="text-gray-400 text-sm font-medium mb-4">Top Teams</h3>
        <div className="space-y-2">
          {summary?.top_teams?.slice(0, 5).map((team, idx) => (
            <div key={idx} className="flex justify-between items-center py-2 border-b border-gray-700">
              <span className="text-white">{team.name || 'Unknown'}</span>
              <span className="bg-purple-900/50 text-purple-300 px-3 py-1 rounded-full text-sm">
                {team.count}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Top Repositories Card */}
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-6 border border-gray-700 shadow-2xl col-span-2">
        <h3 className="text-gray-400 text-sm font-medium mb-4">Top Repositories</h3>
        <div className="space-y-2">
          {summary?.top_repos?.slice(0, 5).map((repo, idx) => (
            <div key={idx} className="flex justify-between items-center py-2 border-b border-gray-700">
              <span className="text-white truncate">{repo.name || 'Unknown'}</span>
              <span className="bg-cyan-900/50 text-cyan-300 px-3 py-1 rounded-full text-sm">
                {repo.count}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
