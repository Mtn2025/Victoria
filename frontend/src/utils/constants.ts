// WebSocket URL derived from window.location — same host as the app, no env vars needed.
// Protocol: wss:// in production (https), ws:// in local dev (http).
// Path must match audio_stream.py router: /ws/media-stream
const _wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
export const WS_BASE_URL = `${_wsProtocol}//${window.location.host}/ws/media-stream`

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
