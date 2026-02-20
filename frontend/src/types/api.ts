export interface ApiResponse<T> {
    success: boolean;
    data?: T;
    error?: string;
    meta?: {
        page: number;
        limit: number;
        total: number;
    };
}

export interface ServiceInternalError {
    message: string;
    code?: string;
}
