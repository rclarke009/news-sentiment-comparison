import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { apiService, HistoryResponse } from '../services/api';

const TrendChart: React.FC = () => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(7);

  useEffect(() => {
    loadHistory();
  }, [days]);

  const loadHistory = async () => {
    try {
      setLoading(true);
      const response: HistoryResponse = await apiService.getHistory(days);

      const chartData = response.comparisons.map((comp) => ({
        date: comp.date,
        conservative: comp.conservative.avg_uplift,
        liberal: comp.liberal.avg_uplift,
      }));

      // #region agent log
      fetch('http://127.0.0.1:7245/ingest/e9826b1a-2dde-4f1c-88b3-12213b89f14e', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'TrendChart.tsx:loadHistory', message: 'history result', data: { days, count: response?.comparisons?.length ?? 0, chartDataLen: chartData?.length ?? 0 }, timestamp: Date.now(), sessionId: 'debug-session', hypothesisId: 'H3' }) }).catch(() => {});
      // #endregion

      setData(chartData.reverse()); // Show oldest to newest
    } catch (error: any) {
      // Don't log 404s as errors - they're expected when there's no data
      if (error?.response?.status !== 404) {
        console.error('Error loading history:', error);
      }
      // Set empty data on error (including 404)
      // #region agent log
      fetch('http://127.0.0.1:7245/ingest/e9826b1a-2dde-4f1c-88b3-12213b89f14e', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'TrendChart.tsx:loadHistory-catch', message: 'history fetch error', data: { days, status: error?.response?.status }, timestamp: Date.now(), sessionId: 'debug-session', hypothesisId: 'H3' }) }).catch(() => {});
      // #endregion
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse">Loading chart...</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">Trend Analysis</h2>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="px-3 py-1 border border-gray-300 rounded"
        >
          <option value={7}>Last 7 days</option>
          <option value={14}>Last 14 days</option>
          <option value={30}>Last 30 days</option>
        </select>
      </div>
      
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line
            type="monotone"
            dataKey="conservative"
            stroke="#dc2626"
            strokeWidth={2}
            name="Conservative"
          />
          <Line
            type="monotone"
            dataKey="liberal"
            stroke="#2563eb"
            strokeWidth={2}
            name="Liberal"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default TrendChart;
