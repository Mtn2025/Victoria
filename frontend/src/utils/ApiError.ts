export class ApiError extends Error {
    constructor(
        public message: string,
        public status?: number,
        public statusText?: string,
        public data?: any
    ) {
        super(message);
        this.name = 'ApiError';
    }
}
