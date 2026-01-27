import React from 'react';
import { DailyComparison as DailyComparisonType } from '../services/api';

interface DailyComparisonProps {
  comparison: DailyComparisonType;
}

const DailyComparison: React.FC<DailyComparisonProps> = ({ comparison }) => {
  const { conservative, liberal } = comparison;


  const ScoreBar = ({ 
    score, 
    side, 
    isLocal = false 
  }: { 
    score: number; 
    side: 'conservative' | 'liberal';
    isLocal?: boolean;
  }) => {
    const percentage = ((score + 5) / 10) * 100; // Convert -5 to +5 scale to 0-100%
    
    // Determine color classes based on side and model type
    let colorClass: string;
    if (isLocal) {
      // Local model: lighter colors with dashed border
      colorClass = side === 'conservative' 
        ? 'bg-red-300 border-2 border-red-500 border-dashed' 
        : 'bg-blue-300 border-2 border-blue-500 border-dashed';
    } else {
      // LLM model: solid colors
      colorClass = side === 'conservative' ? 'bg-red-500' : 'bg-blue-500';
    }
    
    const textColor = isLocal ? 'text-gray-700' : 'text-white';
    
    return (
      <div className="w-full bg-gray-200 rounded-full h-8 relative">
        <div
          className={`${colorClass} h-8 rounded-full flex items-center justify-center ${textColor} font-semibold transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        >
          {score > 0 && <span className="text-xs">{score.toFixed(2)}</span>}
        </div>
        {score <= 0 && (
          <span className="absolute inset-0 flex items-center justify-center text-gray-700 font-semibold text-xs">
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
            {/* LLM Model Score */}
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-xs font-semibold text-gray-700">LLM Model</span>
                <span className="text-xs font-semibold">{conservative.avg_uplift.toFixed(2)}</span>
              </div>
              <ScoreBar score={conservative.avg_uplift} side="conservative" isLocal={false} />
            </div>

            {/* Local Model Score */}
            {conservative.avg_local_sentiment !== undefined && conservative.avg_local_sentiment !== null && (
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-xs font-semibold text-gray-700">Local Model</span>
                  <span className="text-xs font-semibold">{conservative.avg_local_sentiment.toFixed(2)}</span>
                </div>
                <ScoreBar score={conservative.avg_local_sentiment} side="conservative" isLocal={true} />
                {conservative.avg_uplift !== undefined && (
                  <div className="text-xs text-gray-500 mt-1">
                    Difference: {(conservative.avg_uplift - conservative.avg_local_sentiment).toFixed(2)}
                  </div>
                )}
              </div>
            )}

            <div className="grid grid-cols-2 gap-4 mt-4">
              <div className="bg-gray-50 p-3 rounded">
                <p className="text-xs text-gray-600">LLM Positive %</p>
                <p className="text-lg font-bold">{conservative.positive_percentage.toFixed(1)}%</p>
                {conservative.local_positive_percentage !== undefined && (
                  <p className="text-xs text-gray-500 mt-1">
                    Local: {conservative.local_positive_percentage.toFixed(1)}%
                  </p>
                )}
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
            {/* LLM Model Score */}
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-xs font-semibold text-gray-700">LLM Model</span>
                <span className="text-xs font-semibold">{liberal.avg_uplift.toFixed(2)}</span>
              </div>
              <ScoreBar score={liberal.avg_uplift} side="liberal" isLocal={false} />
            </div>

            {/* Local Model Score */}
            {liberal.avg_local_sentiment !== undefined && liberal.avg_local_sentiment !== null && (
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-xs font-semibold text-gray-700">Local Model</span>
                  <span className="text-xs font-semibold">{liberal.avg_local_sentiment.toFixed(2)}</span>
                </div>
                <ScoreBar score={liberal.avg_local_sentiment} side="liberal" isLocal={true} />
                {liberal.avg_uplift !== undefined && (
                  <div className="text-xs text-gray-500 mt-1">
                    Difference: {(liberal.avg_uplift - liberal.avg_local_sentiment).toFixed(2)}
                  </div>
                )}
              </div>
            )}

            <div className="grid grid-cols-2 gap-4 mt-4">
              <div className="bg-gray-50 p-3 rounded">
                <p className="text-xs text-gray-600">LLM Positive %</p>
                <p className="text-lg font-bold">{liberal.positive_percentage.toFixed(1)}%</p>
                {liberal.local_positive_percentage !== undefined && (
                  <p className="text-xs text-gray-500 mt-1">
                    Local: {liberal.local_positive_percentage.toFixed(1)}%
                  </p>
                )}
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
