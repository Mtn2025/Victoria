import { api } from './api'
import { BrowserConfig, TwilioConfig, TelnyxConfig, Voice, Language, VoiceStyle, LLMProvider, LLMModel } from '@/types/config'

// Backend Schema Interface (Partial)
interface BackendConfigUpdate {
    // Not sent in body for new /agents/{uuid}/ endpoint — kept optional for legacy compat
    agent_id?: string
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
    // Additional JSON Fields (LLM, Voice, STT)
    responseLength?: string
    conversationTone?: string
    conversationFormality?: string
    conversationPacing?: string
    contextWindow?: number
    frequencyPenalty?: number
    presencePenalty?: number
    toolChoice?: string
    dynamicVarsEnabled?: boolean
    dynamicVars?: string
    mode?: string
    hallucination_blacklist?: string

    voiceStyleDegree?: number
    voiceBgSound?: string
    voiceBgUrl?: string

    sttProvider?: string
    sttModel?: string
    sttLang?: string
    sttKeywords?: string
    interruption_threshold?: number
    vadSensitivity?: number

    // Allow other fields if backend supports them dynamically
    [key: string]: any
}

export const configService = {
    // Helper to PATCH agent config fields — agentUuid comes from Redux (agents.activeAgent.agent_uuid)
    // Never hardcoded. Never null.
    updateBrowserConfig: async (config: Partial<BrowserConfig>, agentId: string) => {
        if (!agentId) {
            console.error('[configService] updateBrowserConfig called without agentId. Aborting PATCH.')
            return
        }
        // UUID is in the URL — no need to repeat it in the body
        const payload: BackendConfigUpdate = {}

        // Map Fields
        if (config.provider) payload.llm_provider = config.provider
        if (config.model) payload.llm_model = config.model
        if (config.tokens) payload.max_tokens = config.tokens
        if (config.temp) payload.temperature = config.temp

        // Fix INT-05/Bug: Correct Mapping of System Prompt & First Message
        if (config.prompt !== undefined) payload.system_prompt = config.prompt
        if (config.msg !== undefined) payload.first_message = config.msg

        // Block 3: Additional LLM Settings
        if (config.responseLength !== undefined) payload.responseLength = config.responseLength
        if (config.conversationTone !== undefined) payload.conversationTone = config.conversationTone
        if (config.conversationFormality !== undefined) payload.conversationFormality = config.conversationFormality
        if (config.conversationPacing !== undefined) payload.conversationPacing = config.conversationPacing
        if (config.contextWindow !== undefined) payload.contextWindow = config.contextWindow
        if (config.frequencyPenalty !== undefined) payload.frequencyPenalty = config.frequencyPenalty
        if (config.presencePenalty !== undefined) payload.presencePenalty = config.presencePenalty
        if (config.toolChoice !== undefined) payload.toolChoice = config.toolChoice
        if (config.dynamicVarsEnabled !== undefined) payload.dynamicVarsEnabled = config.dynamicVarsEnabled
        if (config.dynamicVars !== undefined) payload.dynamicVars = config.dynamicVars
        if (config.mode !== undefined) payload.mode = config.mode
        if (config.hallucination_blacklist !== undefined) payload.hallucination_blacklist = config.hallucination_blacklist

        if (config.voiceId) payload.voice_name = config.voiceId
        if (config.voiceStyle) payload.voice_style = config.voiceStyle
        if (config.voiceSpeed) payload.voice_speed = config.voiceSpeed
        if (config.voicePitch !== undefined) payload.voice_pitch = config.voicePitch // Also fix to allow 0
        if (config.voiceVolume !== undefined) payload.voice_volume = config.voiceVolume

        if (config.voiceStyleDegree !== undefined) payload.voiceStyleDegree = config.voiceStyleDegree
        if (config.voiceBgSound !== undefined) payload.voiceBgSound = config.voiceBgSound
        if (config.voiceBgUrl !== undefined) payload.voiceBgUrl = config.voiceBgUrl

        if (config.sttSilenceTimeout !== undefined) payload.silence_timeout_ms = config.sttSilenceTimeout

        // Block 3: Additional STT Settings
        if (config.sttProvider !== undefined) payload.sttProvider = config.sttProvider
        if (config.sttModel !== undefined) payload.sttModel = config.sttModel
        if (config.sttLang !== undefined) payload.sttLang = config.sttLang
        if (config.sttKeywords !== undefined) payload.sttKeywords = config.sttKeywords
        if (config.interruption_threshold !== undefined) payload.interruption_threshold = config.interruption_threshold
        if (config.vad_threshold !== undefined) payload.vadSensitivity = config.vad_threshold // Map var names if different

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

        const response = await api.patch(`/agents/${agentId}`, payload)
        return response
    },

    updateTwilioConfig: async (config: Partial<TwilioConfig>, agentId: string) => {
        if (!agentId) {
            console.error('[configService] updateTwilioConfig called without agentId. Aborting PATCH.')
            return
        }
        const payload: BackendConfigUpdate = { ...config }
        return api.patch(`/agents/${agentId}`, payload)
    },

    updateTelnyxConfig: async (config: Partial<TelnyxConfig>, agentId: string) => {
        if (!agentId) {
            console.error('[configService] updateTelnyxConfig called without agentId. Aborting PATCH.')
            return
        }
        const payload: BackendConfigUpdate = { ...config }
        return api.patch(`/agents/${agentId}`, payload)
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
