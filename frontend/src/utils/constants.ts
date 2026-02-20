export const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';
export const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

export const CALL_STATUS = {
    PENDING: 'pending',
    IN_PROGRESS: 'in-progress',
    COMPLETED: 'completed',
    FAILED: 'failed',
    NO_ANSWER: 'no-answer',
} as const;

export const PROVIDERS = {
    TWILIO: 'twilio',
    TELNYX: 'telnyx',
    SIMULATOR: 'simulator',
} as const;
