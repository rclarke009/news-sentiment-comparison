import React, { useState, useEffect } from 'react';
import { apiService, ModelComparisonResponse } from '../services/api';

const ModelComparisonCard: React.FC = () => {
  const [data, setData] = useState<ModelComparisonResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadComparison();
  }, [days]);

  const loadComparison = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.getModelComparison(days);
      setData(response);
    } catch (err: any) {
      if (err?.response?.status !== 404) {
        console.error('Error loading model comparison:', err);
        setError(err?.response?.data?.detail || 'Failed to load model comparison');
      } else {
        setError('No comparison data available');
      }
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse">Loading model comparison...</div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Model Comparison</h2>
        <p className="text-gray-600">{error || 'No data available'}</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-900">Model Comparison</h2>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="px-3 py-1 border border-gray-300 rounded text-sm"
        >
          <option value={7}>Last 7 days</option>
          <option value={14}>Last 14 days</option>
          <option value={30}>Last 30 days</option>
          <option value={60}>Last 60 days</option>
        </select>
      </div>

      {/* Overall Statistics */}
      <div className="grid md:grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-50 p-4 rounded-lg">
          <p className="text-xs text-gray-600 mb-1">Agreement Rate</p>
          <p className="text-2xl font-bold text-blue-700">{data.agreement_rate.toFixed(1)}%</p>
          <p className="text-xs text-gray-500 mt-1">Models agree on positive/negative</p>
        </div>
        <div className="bg-green-50 p-4 rounded-lg">
          <p className="text-xs text-gray-600 mb-1">Avg Difference</p>
          <p className="text-2xl font-bold text-green-700">{data.avg_score_difference.toFixed(2)}</p>
          <p className="text-xs text-gray-500 mt-1">Average score difference</p>
        </div>
        <div className="bg-purple-50 p-4 rounded-lg">
          <p className="text-xs text-gray-600 mb-1">Correlation</p>
          <p className="text-2xl font-bold text-purple-700">{data.correlation.toFixed(3)}</p>
          <p className="text-xs text-gray-500 mt-1">Score correlation</p>
        </div>
        <div className="bg-gray-50 p-4 rounded-lg">
          <p className="text-xs text-gray-600 mb-1">Total Headlines</p>
          <p className="text-2xl font-bold text-gray-700">{data.total_headlines}</p>
          <p className="text-xs text-gray-500 mt-1">Analyzed</p>
        </div>
      </div>

      {/* Side-by-Side Comparison */}
      <div className="grid md:grid-cols-2 gap-6 mb-6">
        {/* Conservative Stats */}
        <div className="border border-red-200 rounded-lg p-4 bg-red-50">
          <h3 className="text-lg font-semibold text-red-700 mb-3">Conservative</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Count:</span>
              <span className="font-semibold">{data.conservative_stats.count}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Correlation:</span>
              <span className="font-semibold">{data.conservative_stats.correlation.toFixed(3)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Avg LLM:</span>
              <span className="font-semibold text-red-600">{data.conservative_stats.avg_llm.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Avg Local:</span>
              <span className="font-semibold text-red-400">{data.conservative_stats.avg_local.toFixed(2)}</span>
            </div>
            <div className="flex justify-between pt-2 border-t border-red-200">
              <span className="text-sm font-semibold text-gray-700">Difference:</span>
              <span className="font-semibold">
                {(data.conservative_stats.avg_llm - data.conservative_stats.avg_local).toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        {/* Liberal Stats */}
        <div className="border border-blue-200 rounded-lg p-4 bg-blue-50">
          <h3 className="text-lg font-semibold text-blue-700 mb-3">Liberal</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Count:</span>
              <span className="font-semibold">{data.liberal_stats.count}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Correlation:</span>
              <span className="font-semibold">{data.liberal_stats.correlation.toFixed(3)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Avg LLM:</span>
              <span className="font-semibold text-blue-600">{data.liberal_stats.avg_llm.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Avg Local:</span>
              <span className="font-semibold text-blue-400">{data.liberal_stats.avg_local.toFixed(2)}</span>
            </div>
            <div className="flex justify-between pt-2 border-t border-blue-200">
              <span className="text-sm font-semibold text-gray-700">Difference:</span>
              <span className="font-semibold">
                {(data.liberal_stats.avg_llm - data.liberal_stats.avg_local).toFixed(2)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Divergence Examples */}
      {data.divergence_examples && data.divergence_examples.length > 0 && (
        <div className="mt-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Notable Divergences</h3>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {data.divergence_examples.map((example, idx) => (
              <div
                key={idx}
                className="bg-gray-50 p-3 rounded border-l-4 border-yellow-400"
              >
                <div className="flex justify-between items-start mb-1">
                  <p className="text-sm font-semibold text-gray-900 line-clamp-2 flex-1">
                    {example.title}
                  </p>
                  <span className="text-xs text-gray-500 ml-2">
                    {example.source} ({example.political_side})
                  </span>
                </div>
                <div className="flex justify-between text-xs text-gray-600 mt-2">
                  <span>LLM: {example.llm_score.toFixed(2)}</span>
                  <span>Local: {example.local_score.toFixed(2)} ({example.local_label}, {example.local_confidence.toFixed(2)})</span>
                  <span className="font-semibold text-gray-800">
                    Diff: {example.difference.toFixed(2)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelComparisonCard;
