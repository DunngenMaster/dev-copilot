import React from "react"

export default function ResultCard({ data }) {
  if (!data) return null
  const { score, bottlenecks = [], sop_preview = "", report_url = "#", cache_status, partial, semantic_enabled, postman_mode, similarity } = data
  return (
    <div className="max-w-5xl mx-auto mt-8 bg-gray-800 bg-opacity-50 backdrop-blur-xl border border-gray-700 rounded-2xl shadow-2xl p-8">
      <div className="flex items-center justify-between mb-6 pb-4 border-b border-gray-700">
        <div className="text-5xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">Score: {score ?? "-"}</div>
        <div className="flex items-center gap-2 flex-wrap justify-end">
          {cache_status && (
            <span className={`px-3 py-1.5 rounded-full text-xs font-bold backdrop-blur-sm ${
              cache_status === "HIT" 
                ? "bg-green-500 bg-opacity-20 text-green-300 border border-green-500 border-opacity-50 shadow-lg shadow-green-500/20" 
                : cache_status === "MISS"
                ? "bg-yellow-500 bg-opacity-20 text-yellow-300 border border-yellow-500 border-opacity-50 shadow-lg shadow-yellow-500/20"
                : "bg-red-500 bg-opacity-20 text-red-300 border border-red-500 border-opacity-50 shadow-lg shadow-red-500/20"
            }`}>
              {cache_status}{similarity ? ` • ${similarity.toFixed?.(2)}` : ""}
            </span>
          )}
          {postman_mode && (
            <span className="px-3 py-1.5 rounded-full text-xs font-bold bg-blue-500 bg-opacity-20 text-blue-300 border border-blue-500 border-opacity-50 backdrop-blur-sm shadow-lg shadow-blue-500/20">
              {postman_mode}
            </span>
          )}
          <span className="px-3 py-1.5 rounded-full text-xs font-bold bg-purple-500 bg-opacity-20 text-purple-300 border border-purple-500 border-opacity-50 backdrop-blur-sm shadow-lg shadow-purple-500/20">
            {semantic_enabled ? "semantic:on" : "semantic:off"}
          </span>
          {partial && (
            <span className="px-3 py-1.5 rounded-full text-xs font-bold bg-red-500 bg-opacity-20 text-red-300 border border-red-500 border-opacity-50 backdrop-blur-sm shadow-lg shadow-red-500/20">
              partial
            </span>
          )}
        </div>
      </div>
      
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-transparent bg-gradient-to-r from-pink-400 to-red-400 bg-clip-text mb-4">Bottlenecks</h2>
        {bottlenecks && bottlenecks.length > 0 ? (
          <ul className="space-y-3">
            {bottlenecks.map((b, i) => (
              <li key={i} className="flex items-start group">
                <span className="text-red-400 mr-3 mt-1 text-lg group-hover:scale-125 transition-transform">•</span>
                <span className="text-gray-300 leading-relaxed text-base">{b}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-500 italic">No bottlenecks detected</p>
        )}
      </div>
      
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-transparent bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text mb-4">SOP Preview</h2>
        <div className="border border-gray-700 rounded-xl p-5 bg-gray-900 bg-opacity-50 h-96 overflow-auto backdrop-blur-sm shadow-inner">
          <pre className="whitespace-pre-wrap text-sm text-gray-300 font-mono leading-relaxed">
            {sop_preview || "—"}
          </pre>
        </div>
      </div>
      
      <div className="flex items-center gap-3 mb-6 flex-wrap">
        <a 
          href={report_url !== "#" ? report_url : undefined} 
          target="_blank" 
          rel="noreferrer" 
          className={`px-6 py-3 rounded-lg font-semibold text-sm transition-all ${
            report_url !== "#"
              ? "bg-gradient-to-r from-emerald-600 to-teal-600 text-white hover:from-emerald-700 hover:to-teal-700 shadow-lg hover:shadow-xl transform hover:scale-[1.02] active:scale-[0.98]"
              : "bg-gray-700 text-gray-500 cursor-not-allowed"
          }`}
          onClick={(e) => report_url === "#" && e.preventDefault()}
        >
          Open Full Report
        </a>
        <button 
          onClick={() => window.location.reload()} 
          className="px-6 py-3 rounded-lg border-2 border-gray-600 text-gray-300 font-semibold text-sm hover:bg-gray-700 hover:border-gray-500 transition-all transform hover:scale-[1.02] active:scale-[0.98]"
        >
          Re-run Analysis
        </button>
      </div>
      
      <details className="mt-6 group">
        <summary className="cursor-pointer text-sm text-gray-400 hover:text-gray-200 font-medium flex items-center gap-2">
          <span className="transform group-open:rotate-90 transition-transform">▶</span>
          View Technical Details
        </summary>
        <pre className="mt-3 text-xs bg-gray-900 bg-opacity-80 text-gray-300 p-4 rounded-lg overflow-auto max-h-96 border border-gray-700 backdrop-blur-sm">
          {JSON.stringify(data, null, 2)}
        </pre>
      </details>
    </div>
  )
}
