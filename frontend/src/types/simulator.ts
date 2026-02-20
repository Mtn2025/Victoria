export interface SimulatorTranscript {
    role: 'user' | 'assistant' | 'system'
    text: string
    timestamp: string
}

export interface SimulatorMetrics {
    llm_latency: string | null
    tts_latency: string | null
}

export type VisualizerMode = 'wave' | 'bars' | 'orb'

export interface SimulatorState {
    status: 'ready' | 'connecting' | 'connected'
    transcripts: SimulatorTranscript[]
    metrics: SimulatorMetrics
    vadLevel: number
    isAgentSpeaking: boolean
}

// WebSocket Message Types
export interface WSMessage {
    type?: string
    event?: string
    data?: any
    media?: { payload: string, track: string }
    config?: any
    text?: string
    role?: 'user' | 'assistant' | 'system'
}
