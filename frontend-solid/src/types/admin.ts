import { User } from './user';

export interface AdminStats {
    totalUsers: number;
    activeUsers: number;
    totalQueries: number;
    systemHealth: string;
}

export type { User };

export interface CreateUserDTO {
    username: string;
    email: string;
    password?: string;
    role: string;
    allowed_segments?: string[];
}

export interface UpdateUserDTO {
    username?: string;
    email?: string;
    password?: string;
    role?: string;
    is_active?: boolean;
    allowed_segments?: string[];
}

export interface AuditLog {
    id: string;
    user_id: string;
    user_name: string;
    action: string;
    resource: string;
    details: string;
    ip_address: string;
    timestamp: string;
    status: string;
}

export interface SystemSettings {
    [key: string]: any;
}
