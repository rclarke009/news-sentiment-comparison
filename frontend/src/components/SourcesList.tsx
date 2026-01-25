import React, { useState, useEffect } from 'react';
import { apiService, SourcesResponse } from '../services/api';

const SourcesList: React.FC = () => {
  const [sources, setSources] = useState<SourcesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSources = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiService.getSources();
      setSources(data);
    } catch (err: unknown) {
      setError('Could not load sources');
      console.error('Error loading sources:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSources();
  }, []);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold mb-4 text-gray-900">Sources</h2>
        <p className="text-gray-600">Loading sources…</p>
      </div>
    );
  }

  if (error && !sources) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold mb-4 text-gray-900">Sources</h2>
        <p className="text-red-600 mb-3">{error}</p>
        <button
          type="button"
          onClick={fetchSources}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!sources) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-bold mb-6 text-gray-900">Sources</h2>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="border-r md:border-r md:border-b-0 border-b border-gray-200 pr-6 pb-6 md:pb-0">
          <h3 className="text-lg font-semibold text-red-600 mb-4">Conservative</h3>
          <ul className="space-y-1 text-gray-700">
            {sources.conservative.map((name) => (
              <li key={name}>{name}</li>
            ))}
          </ul>
        </div>

        <div className="pl-0 md:pl-6">
          <h3 className="text-lg font-semibold text-blue-600 mb-4">Liberal</h3>
          <ul className="space-y-1 text-gray-700">
            {sources.liberal.map((name) => (
              <li key={name}>{name}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default SourcesList;
