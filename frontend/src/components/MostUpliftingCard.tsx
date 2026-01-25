import React from 'react';
import { MostUpliftingStory } from '../services/api';

interface MostUpliftingCardProps {
  side: 'conservative' | 'liberal';
  story: MostUpliftingStory | null;
}

const MostUpliftingCard: React.FC<MostUpliftingCardProps> = ({ side, story }) => {
  const colorClass = side === 'conservative' ? 'border-red-500 bg-red-50' : 'border-blue-500 bg-blue-50';
  const titleColor = side === 'conservative' ? 'text-red-700' : 'text-blue-700';
  const badgeColor = side === 'conservative' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800';

  if (!story) {
    return (
      <div className={`border-2 ${colorClass} rounded-lg p-6`}>
        <h3 className={`text-lg font-semibold ${titleColor} mb-2`}>
          Most Uplifting {side.charAt(0).toUpperCase() + side.slice(1)} Story
        </h3>
        <p className="text-gray-600">No uplifting story found for this date.</p>
      </div>
    );
  }

  return (
    <div className={`border-2 ${colorClass} rounded-lg p-6 hover:shadow-lg transition-shadow`}>
      <div className="flex items-start justify-between mb-3">
        <h3 className={`text-lg font-semibold ${titleColor}`}>
          Most Uplifting {side.charAt(0).toUpperCase() + side.slice(1)} Story
        </h3>
        <span className={`px-2 py-1 rounded text-xs font-semibold ${badgeColor}`}>
          {story.final_score.toFixed(1)}
        </span>
      </div>
      
      <h4 className="font-bold text-gray-900 mb-2 line-clamp-2">
        {story.title}
      </h4>
      
      {story.description && (
        <p className="text-sm text-gray-600 mb-3 line-clamp-3">
          {story.description}
        </p>
      )}
      
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>{story.source}</span>
        <a
          href={story.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline"
        >
          Read more →
        </a>
      </div>
    </div>
  );
};

export default MostUpliftingCard;
