export interface Call {
    id: string;
    sid: string;
    from_number: string;
    to_number: string;
    status: 'pending' | 'in-progress' | 'completed' | 'failed' | 'no-answer';
    direction: 'inbound' | 'outbound';
    duration: number;
    cost?: number;
    recording_url?: string;
    transcript?: string; // or JSON
    started_at: string;
    ended_at?: string;
    provider: 'twilio' | 'telnyx' | 'browser' | 'simulator';
    client_type?: 'telnyx' | 'twilio' | 'browser' | 'simulator';
    transcription?: string;
    summary?: string;
    analysis?: any;
}

export interface CallFilter {
    status?: string;
    startDate?: string;
    endDate?: string;
    limit?: number;
    offset?: number;
    client_type?: string;
}
