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
  avg_local_sentiment?: number;
  local_positive_percentage?: number;
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

export interface ModelComparisonResponse {
  total_headlines: number;
  agreement_rate: number;
  avg_score_difference: number;
  correlation: number;
  divergence_examples: Array<{
    title: string;
    source: string;
    political_side: string;
    llm_score: number;
    local_score: number;
    local_label: string;
    local_confidence: number;
    difference: number;
  }>;
  conservative_stats: {
    count: number;
    correlation: number;
    avg_llm: number;
    avg_local: number;
  };
  liberal_stats: {
    count: number;
    correlation: number;
    avg_llm: number;
    avg_local: number;
  };
}

export const apiService = {
  /**
   * Get today's comparison
   */
  getToday: async (): Promise<DailyComparison> => {
    // #region agent log
    fetch('http://127.0.0.1:7245/ingest/e9826b1a-2dde-4f1c-88b3-12213b89f14e',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'api.ts:getToday',message:'api_getToday_entry',data:{baseURL:API_BASE_URL,url:'/today'},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'H6_H10'})}).catch(()=>{});
    // #endregion
    try {
      const response = await api.get<DailyComparison>('/today');
      // #region agent log
      fetch('http://127.0.0.1:7245/ingest/e9826b1a-2dde-4f1c-88b3-12213b89f14e',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'api.ts:getToday',message:'api_getToday_success',data:{status:response.status,date:response.data.date},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'H7'})}).catch(()=>{});
      // #endregion
      return response.data;
    } catch (err: any) {
      // #region agent log
      fetch('http://127.0.0.1:7245/ingest/e9826b1a-2dde-4f1c-88b3-12213b89f14e',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'api.ts:getToday',message:'api_getToday_error',data:{status:err?.response?.status,message:err?.message,code:err?.code},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'H6_H7_H9'})}).catch(()=>{});
      // #endregion
      throw err;
    }
  },

  /**
   * Get comparison for a specific date
   */
  getDate: async (date: string): Promise<DailyComparison> => {
    const response = await api.get<DailyComparison>(`/date/${date}`);
    return response.data;
  },

  /**
   * Get historical comparisons
   */
  getHistory: async (days: number = 7): Promise<HistoryResponse> => {
    const response = await api.get<HistoryResponse>('/history', {
      params: { days },
    });
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

  /**
   * Get model comparison statistics
   */
  getModelComparison: async (
    days: number = 30,
    source?: 'conservative' | 'liberal'
  ): Promise<ModelComparisonResponse> => {
    const response = await api.get<ModelComparisonResponse>('/model-comparison', {
      params: { days, source },
    });
    return response.data;
  },
};
