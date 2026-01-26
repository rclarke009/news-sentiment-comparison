/**
 * API client for news sentiment comparison API
 */

import axios from 'axios';

// Use relative URL to leverage Vite proxy, or absolute URL if VITE_API_URL is set
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface DailyComparison {
  date: string;
  conservative: SideStats;
  liberal: SideStats;
  created_at: string;
  updated_at: string;
}

export interface SideStats {
  avg_uplift: number;
  positive_percentage: number;
  total_headlines: number;
  most_uplifting: MostUpliftingStory | null;
  score_distribution: Record<string, number>;
}

export interface MostUpliftingStory {
  title: string;
  description: string | null;
  url: string;
  source: string;
  uplift_score: number;
  final_score: number;
  published_at: string;
}

export interface HistoryResponse {
  comparisons: DailyComparison[];
  days: number;
}

export interface StatsResponse {
  total_days: number;
  conservative_avg: number;
  liberal_avg: number;
  conservative_positive_pct: number;
  liberal_positive_pct: number;
}

export interface SourcesResponse {
  conservative: string[];
  liberal: string[];
}

export const apiService = {
  /**
   * Get today's comparison
   */
  getToday: async (): Promise<DailyComparison> => {
    const response = await api.get<DailyComparison>('/today');
    return response.data;
  },

  /**
   * Get comparison for a specific date
   */
  getDate: async (date: string): Promise<DailyComparison> => {
    // #region agent log
    fetch('http://127.0.0.1:7245/ingest/e9826b1a-2dde-4f1c-88b3-12213b89f14e',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'api.ts:73',message:'getDate API request',data:{date, url:`${API_BASE_URL}/date/${date}`, baseUrl:API_BASE_URL},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A,B,C'})}).catch(()=>{});
    // #endregion
    const response = await api.get<DailyComparison>(`/date/${date}`);
    // #region agent log
    fetch('http://127.0.0.1:7245/ingest/e9826b1a-2dde-4f1c-88b3-12213b89f14e',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'api.ts:75',message:'getDate API response',data:{status:response.status, receivedDate:response.data?.date},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
    // #endregion
    return response.data;
  },

  /**
   * Get historical comparisons
   */
  getHistory: async (days: number = 7): Promise<HistoryResponse> => {
    // #region agent log
    fetch('http://127.0.0.1:7245/ingest/e9826b1a-2dde-4f1c-88b3-12213b89f14e',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'api.ts:81',message:'getHistory API request',data:{days, url:`${API_BASE_URL}/history`},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
    // #endregion
    const response = await api.get<HistoryResponse>('/history', {
      params: { days },
    });
    // #region agent log
    fetch('http://127.0.0.1:7245/ingest/e9826b1a-2dde-4f1c-88b3-12213b89f14e',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'api.ts:85',message:'getHistory API response',data:{status:response.status, comparisonsCount:response.data?.comparisons?.length},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
    // #endregion
    return response.data;
  },

  /**
   * Get most uplifting story
   */
  getMostUplifting: async (
    side: 'conservative' | 'liberal',
    date?: string
  ): Promise<MostUpliftingStory> => {
    const response = await api.get<MostUpliftingStory>('/most-uplifting', {
      params: { side, date },
    });
    return response.data;
  },

  /**
   * Get aggregate statistics
   */
  getStats: async (days: number = 30): Promise<StatsResponse> => {
    const response = await api.get<StatsResponse>('/stats', {
      params: { days },
    });
    return response.data;
  },

  /**
   * Get configured news sources (display names)
   */
  getSources: async (): Promise<SourcesResponse> => {
    const response = await api.get<SourcesResponse>('/sources');
    return response.data;
  },

  /**
   * Health check
   */
  healthCheck: async (): Promise<{ status: string; timestamp: string }> => {
    const response = await api.get('/health');
    return response.data;
  },
};
