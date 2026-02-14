import { User } from './user';

export interface Report {
    id: string;
    title: string;
    description?: string;
    content: any; // TipTap JSON
    status: string;
    author_id: string;
    created_at: string;
    updated_at: string;
    author?: User;
}

export interface ReportTemplate {
    id: string;
    name: string;
    description: string;
    content: any;
}

export interface CreateReportDTO {
    title: string;
    description?: string;
    content: any;
    status?: string;
}

export interface UpdateReportDTO {
    title?: string;
    description?: string;
    content?: any;
    status?: string;
}

export interface ReportSchedule {
    id: string;
    reportId: string;
    cron: string;
    recipients: string[];
    lastRun?: string;
    nextRun?: string;
}
