export interface AnalyticsData {
    id: string;
    date: string;
    value: number;
    category?: string;
    segment?: string;
    [key: string]: any;
}

export interface AnalyticsFilter {
    dateRange?: {
        start: Date;
        end: Date;
    };
    category?: string;
    segment?: string;
    minValue?: number;
    maxValue?: number;
}

export interface AnalyticsMetric {
    name: string;
    value: number | string;
    trend?: number;
    status?: 'success' | 'warning' | 'error';
}

export type ExportFormat = 'csv' | 'xlsx' | 'pdf' | 'json';
