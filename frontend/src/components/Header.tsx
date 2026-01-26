import React from 'react';

interface HeaderProps {
  selectedDate: string;
  onDateChange: (date: string) => void;
}

const Header: React.FC<HeaderProps> = ({ selectedDate, onDateChange }) => {
  return (
    <header className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              News Sentiment Comparison
            </h1>
            <p className="text-sm text-gray-600 mt-1">
              Comparing uplift scores between conservative and liberal news sources
            </p>
          </div>
          <div>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => {
                const newDate = e.target.value;
                console.log("MYDEBUG → Date picker changed:", newDate, "from", selectedDate);
                onDateChange(newDate);
              }}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
