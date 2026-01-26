import React from 'react';
import { DailyComparison as DailyComparisonType } from '../services/api';

interface DailyComparisonProps {
  comparison: DailyComparisonType;
}

const DailyComparison: React.FC<DailyComparisonProps> = ({ comparison }) => {
  const { conservative, liberal } = comparison;

  // #region agent log
  (() => {
    fetch('http://127.0.0.1:7245/ingest/e9826b1a-2dde-4f1c-88b3-12213b89f14e', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'DailyComparison.tsx:render', message: 'props received', data: { cAvg: conservative?.avg_uplift, cTotal: conservative?.total_headlines, lAvg: liberal?.avg_uplift, lTotal: liberal?.total_headlines }, timestamp: Date.now(), sessionId: 'debug-session', hypothesisId: 'H1' }) }).catch(() => {});
  })();
  // #endregion

  const ScoreBar = ({ score, side }: { score: number; side: 'conservative' | 'liberal' }) => {
    const percentage = ((score + 5) / 10) * 100; // Convert -5 to +5 scale to 0-100%
    const color = side === 'conservative' ? 'bg-red-500' : 'bg-blue-500';
    
    return (
      <div className="w-full bg-gray-200 rounded-full h-8 relative">
        <div
          className={`${color} h-8 rounded-full flex items-center justify-center text-white font-semibold transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        >
          {score > 0 && <span>{score.toFixed(2)}</span>}
        </div>
        {score <= 0 && (
          <span className="absolute inset-0 flex items-center justify-center text-gray-700 font-semibold">
            {score.toFixed(2)}
          </span>
        )}
      </div>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-bold mb-6 text-gray-900">
        Daily Comparison - {comparison.date}
      </h2>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Conservative Side */}
        <div className="border-r md:border-r md:border-b-0 border-b border-gray-200 pr-6 pb-6 md:pb-0">
          <h3 className="text-lg font-semibold text-red-600 mb-4">Conservative</h3>
          
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm text-gray-600">Average Uplift</span>
                <span className="font-semibold">{conservative.avg_uplift.toFixed(2)}</span>
              </div>
              <ScoreBar score={conservative.avg_uplift} side="conservative" />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 p-3 rounded">
                <p className="text-xs text-gray-600">Positive %</p>
                <p className="text-lg font-bold">{conservative.positive_percentage.toFixed(1)}%</p>
              </div>
              <div className="bg-gray-50 p-3 rounded">
                <p className="text-xs text-gray-600">Total Headlines</p>
                <p className="text-lg font-bold">{conservative.total_headlines}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Liberal Side */}
        <div className="pl-0 md:pl-6">
          <h3 className="text-lg font-semibold text-blue-600 mb-4">Liberal</h3>
          
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm text-gray-600">Average Uplift</span>
                <span className="font-semibold">{liberal.avg_uplift.toFixed(2)}</span>
              </div>
              <ScoreBar score={liberal.avg_uplift} side="liberal" />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 p-3 rounded">
                <p className="text-xs text-gray-600">Positive %</p>
                <p className="text-lg font-bold">{liberal.positive_percentage.toFixed(1)}%</p>
              </div>
              <div className="bg-gray-50 p-3 rounded">
                <p className="text-xs text-gray-600">Total Headlines</p>
                <p className="text-lg font-bold">{liberal.total_headlines}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DailyComparison;
