import { apiClient } from '@/lib/api/client';
import type {
  Report,
  ReportTemplate,
  CreateReportDTO,
  UpdateReportDTO,
  ReportSchedule,
} from '@/types/reports';

export const reportsService = {
  async getAll(): Promise<Report[]> {
    // Connect to FastAPI backend: GET /api/v1/reports
    return apiClient.get<Report[]>('/api/v1/reports');
  },

  async getById(id: string): Promise<Report> {
    // Connect to FastAPI backend: GET /api/v1/reports/{id}
    return apiClient.get<Report>(`/api/v1/reports/${id}`);
  },

  async create(report: CreateReportDTO): Promise<Report> {
    // Connect to FastAPI backend: POST /api/v1/reports
    return apiClient.post<Report>('/api/v1/reports', report);
  },

  async update(id: string, report: UpdateReportDTO): Promise<Report> {
    // Connect to FastAPI backend: PUT /api/v1/reports/{id}
    return apiClient.put<Report>(`/api/v1/reports/${id}`, report);
  },

  async delete(id: string): Promise<void> {
    // Connect to FastAPI backend: DELETE /api/v1/reports/{id}
    return apiClient.delete(`/api/v1/reports/${id}`);
  },

  async getTemplates(): Promise<ReportTemplate[]> {
    // Connect to FastAPI backend: GET /api/v1/reports/templates
    // TODO: Backend endpoint not implemented yet
    return apiClient.get<ReportTemplate[]>('/api/v1/reports/templates');
  },

  async generatePDF(id: string): Promise<Blob> {
    // Connect to FastAPI backend: POST /api/v1/reports/{id}/generate-pdf
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/api/v1/reports/${id}/generate-pdf`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
    return response.blob();
  },

  async schedule(
    id: string,
    schedule: Omit<ReportSchedule, 'id' | 'reportId'>
  ): Promise<ReportSchedule> {
    // Connect to FastAPI backend: POST /api/v1/reports/{id}/schedule
    // TODO: Backend endpoint not implemented yet
    return apiClient.post<ReportSchedule>(`/api/v1/reports/${id}/schedule`, schedule);
  },
};
