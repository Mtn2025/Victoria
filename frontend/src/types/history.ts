export interface TranscriptLine {
    role: string
    content: string
    timestamp: string | null
}

export interface HistoryCall {
    id: string
    start_time: string
    end_time: string | null
    client_type: 'browser' | 'twilio' | 'telnyx' | 'unknown'
    status?: string
    duration_seconds?: number
    extracted_data?: Record<string, any>
}

export interface CallDetail {
    call: HistoryCall
    transcripts: TranscriptLine[]
}

export interface HistoryResponse {
    calls: HistoryCall[]
    total: number
    page: number
}

export interface HistoryBackendCall {
    id: string
    start_time: string
    end_time?: string | null
    client_type: 'browser' | 'twilio' | 'telnyx' | 'unknown'
    status?: string
    duration?: number
    extracted_data?: Record<string, any>
}

export interface HistoryBackendResponse {
    calls: HistoryBackendCall[]
    total: number
    page: number
}
