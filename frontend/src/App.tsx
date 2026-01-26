import { useState, useEffect, useRef } from 'react';
import { format } from 'date-fns';
import { apiService, DailyComparison } from './services/api';
import DailyComparisonView from './components/DailyComparison';
import Header from './components/Header';
import MostUpliftingCard from './components/MostUpliftingCard';
import SourcesList from './components/SourcesList';
import TrendChart from './components/TrendChart';

function App() {
  const [comparison, setComparison] = useState<DailyComparison | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Start with null - we'll load local "today" or most recent on mount
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [noDataAvailable, setNoDataAvailable] = useState(false);
  const [fallbackMessage, setFallbackMessage] = useState<string | null>(null);

  const skipNextSelectedDateEffect = useRef(false);

  // On initial load: prefer user's local "today", then fall back to most recent
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        setLoading(true);
        setError(null);
        setFallbackMessage(null);
        const localToday = format(new Date(), 'yyyy-MM-dd');
        try {
          const data = await apiService.getDate(localToday);
          setComparison(data);
          skipNextSelectedDateEffect.current = true;
          setSelectedDate(data.date);
        } catch (err: any) {
          if (err?.response?.status === 404) {
            try {
              const history = await apiService.getHistory(30);
              if (history.comparisons && history.comparisons.length > 0) {
                const mostRecent = history.comparisons[0];
                setComparison(mostRecent);
                setFallbackMessage(`Showing latest available: ${mostRecent.date}`);
                skipNextSelectedDateEffect.current = true;
                setSelectedDate(mostRecent.date);
              } else {
                setNoDataAvailable(true);
              }
            } catch (historyErr: any) {
              setNoDataAvailable(true);
            }
          } else {
            setNoDataAvailable(true);
            setError(err?.response?.data?.detail || err?.message || 'Failed to load data');
          }
        }
      } catch (err: any) {
        setNoDataAvailable(true);
        setError(err?.response?.data?.detail || err?.message || 'Failed to load data');
      } finally {
        setLoading(false);
      }
    };
    loadInitialData();
  }, []);

  // When selectedDate changes (user picks a date manually), load that date
  useEffect(() => {
    if (skipNextSelectedDateEffect.current) {
      skipNextSelectedDateEffect.current = false;
      return; // Skip; this change came from loadInitialData
    }
    if (selectedDate) {
      setFallbackMessage(null); // User explicitly picked a date; clear fallback hint
      loadComparison();
    }
  }, [selectedDate]);

  const loadComparison = async (tryFallback = true) => {
    if (!selectedDate) return; // Don't load if no date selected
    
    try {
      setLoading(true);
      setError(null);
      setNoDataAvailable(false);
      console.log("MYDEBUG → Requesting date:", selectedDate);
      const data = await apiService.getDate(selectedDate);
      console.log("MYDEBUG → Received data:", data?.date, "hasData:", !!data);
      setComparison(data);
    } catch (err: any) {
      console.log("MYDEBUG → API call failed:", {
        status: err?.response?.status,
        detail: err?.response?.data?.detail,
        requestedDate: selectedDate,
        url: err?.config?.url
      });
      // If 404 and we haven't tried fallback yet, try to get most recent date
      if (err?.response?.status === 404 && tryFallback) {
        try {
          const history = await apiService.getHistory(30);
          if (history.comparisons && history.comparisons.length > 0) {
            // Use the most recent available date
            const mostRecent = history.comparisons[0];
            console.log("MYDEBUG → Fallback found data for:", mostRecent.date, "updating selectedDate");
            setComparison(mostRecent);
            setSelectedDate(mostRecent.date); // Update selectedDate to match the found data
            setError(null); // Clear error since we found data
            return;
          }
        } catch (historyErr: any) {
          // History also failed (likely also 404 - no data), continue to show "no data" message
          // Don't log this as an error since it's expected when there's no data
        }
      }
      
      // No data available at all - this is expected when the collector hasn't run yet
      if (err?.response?.status === 404) {
        setNoDataAvailable(true);
        // Don't log 404s as errors - they're expected when there's no data
      } else {
        // Only log non-404 errors (network issues, server errors, etc.)
        const errorMessage = err?.response?.data?.detail || err?.message || 'Failed to load comparison';
        setError(errorMessage);
        console.error('Error loading comparison:', err);
      }
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Show helpful message if no data exists at all
  if (noDataAvailable && !comparison) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header selectedDate={selectedDate} onDateChange={setSelectedDate} />
        <main className="container mx-auto px-4 py-8">
          <div className="max-w-2xl mx-auto mt-12">
            <div className="bg-white rounded-lg shadow-md p-8 text-center">
              <div className="text-6xl mb-4">📊</div>
              <h2 className="text-2xl font-bold text-gray-800 mb-4">No Data Available Yet</h2>
              <p className="text-gray-600 mb-6">
                It looks like this is your first time running the application. You need to collect some news data first.
              </p>
              <div className="bg-gray-50 rounded-lg p-6 text-left">
                <h3 className="font-semibold text-gray-800 mb-3">No data has been collected yet</h3>
                <p className="text-gray-700 mb-3">
                  The news collector runs automatically on a schedule. If this is a new deployment, 
                  data will appear after the first scheduled collection runs.
                </p>
                <p className="text-sm text-gray-600">
                  For local development, you can run: <code className="bg-gray-200 px-2 py-1 rounded text-xs">python scripts/run_collector.py</code>
                </p>
              </div>
              <button
                onClick={() => loadComparison(false)}
                className="mt-6 px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Check Again
              </button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Show error with retry option
  if (error && !comparison) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header selectedDate={selectedDate} onDateChange={setSelectedDate} />
        <main className="container mx-auto px-4 py-8">
          <div className="max-w-2xl mx-auto mt-12">
            <div className="bg-white rounded-lg shadow-md p-8 text-center">
              <p className="text-red-600 mb-4">{error}</p>
              <button
                onClick={() => loadComparison(false)}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Retry
              </button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (!comparison) {
    console.log("MYDEBUG → No comparison to render, selectedDate:", selectedDate);
    return null;
  }

  console.log("MYDEBUG → Rendering comparison for date:", comparison.date, "selectedDate:", selectedDate);

  return (
    <div className="min-h-screen bg-gray-50">
      <Header selectedDate={selectedDate} onDateChange={setSelectedDate} />
      
      {fallbackMessage && (
        <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mx-4 mt-4">
          <div className="flex">
            <div className="ml-3">
              <p className="text-sm text-blue-700">{fallbackMessage}</p>
            </div>
          </div>
        </div>
      )}
      {error && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mx-4 mt-4">
          <div className="flex">
            <div className="ml-3">
              <p className="text-sm text-yellow-700">{error}</p>
            </div>
          </div>
        </div>
      )}
      
      <main className="container mx-auto px-4 py-8">
        {/* Most Uplifting Stories */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <MostUpliftingCard
            side="conservative"
            story={comparison.conservative.most_uplifting}
          />
          <MostUpliftingCard
            side="liberal"
            story={comparison.liberal.most_uplifting}
          />
        </div>

        {/* Daily Comparison */}
        <DailyComparisonView comparison={comparison} />

        {/* Trend Chart */}
        <div className="mt-8">
          <TrendChart />
        </div>

        {/* Sources */}
        <div className="mt-8">
          <SourcesList />
        </div>
      </main>
    </div>
  );
}

export default App;
