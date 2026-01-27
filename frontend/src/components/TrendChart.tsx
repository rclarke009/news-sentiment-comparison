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
        conservativeLLM: comp.conservative.avg_uplift,
        liberalLLM: comp.liberal.avg_uplift,
        conservativeLocal: comp.conservative.avg_local_sentiment ?? null,
        liberalLocal: comp.liberal.avg_local_sentiment ?? null,
      }));


      setData(chartData.reverse()); // Show oldest to newest
    } catch (error: any) {
      // Don't log 404s as errors - they're expected when there's no data
      if (error?.response?.status !== 404) {
        console.error('Error loading history:', error);
      }
      // Set empty data on error (including 404)
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
      
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          {/* LLM Model Lines - Solid */}
          <Line
            type="monotone"
            dataKey="conservativeLLM"
            stroke="#dc2626"
            strokeWidth={2}
            name="Conservative (LLM)"
            dot={{ r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="liberalLLM"
            stroke="#2563eb"
            strokeWidth={2}
            name="Liberal (LLM)"
            dot={{ r: 4 }}
          />
          {/* Local Model Lines - Dashed */}
          <Line
            type="monotone"
            dataKey="conservativeLocal"
            stroke="#f87171"
            strokeWidth={2}
            strokeDasharray="5 5"
            name="Conservative (Local)"
            dot={{ r: 3 }}
            connectNulls={false}
          />
          <Line
            type="monotone"
            dataKey="liberalLocal"
            stroke="#60a5fa"
            strokeWidth={2}
            strokeDasharray="5 5"
            name="Liberal (Local)"
            dot={{ r: 3 }}
            connectNulls={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default TrendChart;
