import { useState, useEffect } from 'react';
import { apiService, DailyComparison } from '../services/api';

export const useDailyData = (date: string) => {
  const [data, setData] = useState<DailyComparison | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await apiService.getDate(date);
        setData(result);
      } catch (err: any) {
        setError(err.message || 'Failed to load data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [date]);

  return { data, loading, error };
};
