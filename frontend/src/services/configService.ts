import { api } from './api'
import { BrowserConfig, TwilioConfig, TelnyxConfig, Voice, Language, VoiceStyle, LLMProvider, LLMModel } from '@/types/config'

// Backend Schema Interface (Partial)
interface BackendConfigUpdate {
    agent_id: string
    llm_provider?: string
    llm_model?: string
    max_tokens?: number
    temperature?: number
    system_prompt?: string
    first_message?: string
    voice_name?: string
    voice_style?: string
    voice_speed?: number
    voice_pitch?: number
    voice_volume?: number
    silence_timeout_ms?: number
    // Allow other fields if backend supports them dynamically
    [key: string]: any
}

export const configService = {
    // Config Management

    // Helper to map BrowserConfig to Backend ConfigUpdate
    updateBrowserConfig: async (config: Partial<BrowserConfig>) => {
        const payload: BackendConfigUpdate = {
            agent_id: 'Victoria', // Hardcoded for now, or match current active agent
        }

        // Map Fields
        if (config.provider) payload.llm_provider = config.provider
        if (config.model) payload.llm_model = config.model
        if (config.tokens) payload.max_tokens = config.tokens
        if (config.temp) payload.temperature = config.temp
        if (config.msg) payload.system_prompt = config.msg // Assuming msg is system prompt
        // if (config.prompt) ... ?

        if (config.voiceId) payload.voice_name = config.voiceId
        if (config.voiceStyle) payload.voice_style = config.voiceStyle
        if (config.voiceSpeed) payload.voice_speed = config.voiceSpeed
        if (config.voicePitch) payload.voice_pitch = config.voicePitch
        if (config.voiceVolume) payload.voice_volume = config.voiceVolume

        if (config.sttSilenceTimeout !== undefined) payload.silence_timeout_ms = config.sttSilenceTimeout
        if (config.idleMessage !== undefined) payload.first_message = config.idleMessage // Rough mapping

        // INT-05: Map Tools Config
        // We aggregate all tool-related settings into the 'tools_config' dictionary
        // expected by the backend.
        if (config.toolsSchema !== undefined || config.toolServerUrl !== undefined || config.clientToolsEnabled !== undefined || config.asyncTools !== undefined) {
            let parsedTools = []
            try {
                if (config.toolsSchema) {
                    parsedTools = JSON.parse(config.toolsSchema)
                }
            } catch (e) {
                console.warn("Failed to parse toolsSchema for backend update", e)
            }

            payload.tools_config = {
                tools: parsedTools,
                tool_server_url: config.toolServerUrl,
                client_tools_enabled: config.clientToolsEnabled,
                async_execution: config.asyncTools,
                tool_timeout_ms: config.toolTimeoutMs,
                error_message: config.toolErrorMsg
            }
        }

        const response = await api.patch('/config/', payload)
        return response
    },

    updateTwilioConfig: async (config: Partial<TwilioConfig>) => {
        // Twilio config is infrastructure specific, might not map to "Agent" entity directly
        // Backend ConfigUpdate seems focused on "Agent Behavior" (LLM/Voice)
        // For now, we mimic the old behavior but maybe warn or just send what we can.
        // If Backend doesn't support infra config via this endpoint, we might fail.
        // But Phase F goal is to fix "Method Not Allowed".
        const payload: BackendConfigUpdate = {
            agent_id: 'Victoria',
            ...config // Naive spread, backend will ignore unknown fields if Pydantic set to ignore?
            // Actually Pydantic default is ignore extra.
        }
        return api.patch('/config/', payload)
    },

    updateTelnyxConfig: async (config: Partial<TelnyxConfig>) => {
        const payload: BackendConfigUpdate = {
            agent_id: 'Victoria',
            ...config
        }
        return api.patch('/config/', payload)
    },

    // Options / Catalogs
    getLLMProviders: async (): Promise<LLMProvider[]> => {
        const response = await api.get<{ providers: LLMProvider[] }>('/config/options/llm/providers')
        return response.providers || []
    },

    getLLMModels: async (provider: string): Promise<LLMModel[]> => {
        if (!provider) return []
        const response = await api.get<{ models: LLMModel[] }>('/config/options/llm/models', { params: { provider } })
        return response.models || []
    },

    getLanguages: async (provider: string = 'azure'): Promise<Language[]> => {
        const response = await api.get<{ languages: Language[] }>('/config/options/tts/languages', { params: { provider } })
        return response.languages || []
    },

    getVoices: async (provider: string = 'azure', language?: string): Promise<Voice[]> => {
        const params: any = { provider }
        if (language) params.language = language
        const response = await api.get<{ voices: Voice[] }>('/config/options/tts/voices', { params })
        return response.voices || []
    },

    getStyles: async (provider: string = 'azure', voiceId: string): Promise<VoiceStyle[]> => {
        if (!voiceId) return []
        const response = await api.get<{ styles: string[] }>('/config/options/tts/styles', { params: { provider, voice_id: voiceId } })
        // Legacy backend returns strings, frontend expects objects
        return response.styles.map(s => ({ id: s, label: s }))
    },

    previewVoice: async (params: {
        voice_name: string
        voice_speed: number
        voice_pitch: number
        voice_volume: number
        voice_style?: string
        voice_style_degree?: number
        provider: string
    }) => {
        const response = await api.post('/config/options/tts/preview', params, { responseType: 'blob' })
        return response
    }
}
