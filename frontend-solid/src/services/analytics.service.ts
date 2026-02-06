/**
 * Analytics Service
 * Serviço para comunicação com API de analytics
 */

import { apiClient } from '@/lib/api/client';
import type {
  AnalyticsData,
  AnalyticsFilter,
  AnalyticsMetric,
  ExportFormat,
} from '@/types/analytics';

export const analyticsService = {
  async getData(filters?: AnalyticsFilter): Promise<AnalyticsData[]> {
    // Connect to FastAPI backend: GET /api/v1/analytics/data
    const params = new URLSearchParams();
    if (filters?.dateRange) {
      params.append('date_start', filters.dateRange.start.toISOString());
      params.append('date_end', filters.dateRange.end.toISOString());
    }
    if (filters?.category) params.append('category', filters.category);
    if (filters?.segment) params.append('segment', filters.segment);
    if (filters?.minValue !== undefined) params.append('min_value', filters.minValue.toString());
    if (filters?.maxValue !== undefined) params.append('max_value', filters.maxValue.toString());

    return apiClient.get<AnalyticsData[]>(`/api/v1/analytics/data?${params.toString()}`);
  },

  async getMetrics(): Promise<AnalyticsMetric[]> {
    // Connect to FastAPI backend: GET /api/v1/analytics/metrics
    return apiClient.get<AnalyticsMetric[]>('/api/v1/analytics/metrics');
  },

  async exportData(format: ExportFormat, filters?: AnalyticsFilter): Promise<Blob> {
    // Connect to FastAPI backend: POST /api/v1/analytics/export
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/analytics/export`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ format, filters }),
    });
    return response.blob();
  },

  async runCustomQuery(query: string): Promise<any> {
    // Connect to FastAPI backend: POST /api/v1/analytics/query
    return apiClient.post('/api/v1/analytics/query', { query });
  },
};
