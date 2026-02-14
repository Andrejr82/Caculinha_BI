export interface User {
    id: string;
    username: string;
    email: string;
    role: string;
    is_active: boolean;
    allowed_segments: string[];
    created_at?: string;
    updated_at?: string;
    last_login?: string;
}
