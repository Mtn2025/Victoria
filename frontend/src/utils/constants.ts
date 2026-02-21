// WS_BASE_URL is the only URL that needs to be absolute (WebSocket requires ws:// or wss://).
// All HTTP calls use relative paths (/api/...) via api.ts — no base URL needed.
export const WS_BASE_URL = window.__ENV__?.VITE_WS_URL ?? import.meta.env.VITE_WS_URL;

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
