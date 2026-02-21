import { api } from './api'
import { BrowserConfig, Voice, Language, VoiceStyle, LLMProvider, LLMModel } from '@/types/config'

// Backend Schema Interface — mirrors ConfigUpdate in config_schemas.py
// One source of truth for the PATCH /agents/{uuid} payload.
interface BackendConfigUpdate {
    // LLM — canonical keys (always llm_provider / llm_model, never 'provider'/'model')
    llm_provider?: string
    llm_model?: string
    max_tokens?: number
    temperature?: number
    system_prompt?: string
    first_message?: string
    // Extended LLM
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
    // Voice
    voice_name?: string
    voice_style?: string
    voice_speed?: number
    voice_pitch?: number
    voice_volume?: number
    voiceStyleDegree?: number
    voiceBgSound?: string
    voiceBgUrl?: string
    // STT
    sttProvider?: string
    sttModel?: string
    sttLang?: string
    sttKeywords?: string
    interruption_threshold?: number
    vadSensitivity?: number
    silence_timeout_ms?: number
    // Tools
    tools_config?: Record<string, unknown>
}

export const configService = {
    /**
     * PATCH /api/agents/{uuid}
     * Maps BrowserConfig fields to the canonical BackendConfigUpdate payload.
     * agentUuid comes from Redux (agents.activeAgent.agent_uuid) — never hardcoded.
     */
    updateBrowserConfig: async (config: Partial<BrowserConfig>, agentId: string) => {
        if (!agentId) {
            console.error('[configService] updateBrowserConfig called without agentId. Aborting.')
            return
        }

        const payload: BackendConfigUpdate = {}

        // LLM
        if (config.provider !== undefined) payload.llm_provider = config.provider
        if (config.model !== undefined) payload.llm_model = config.model
        if (config.tokens !== undefined) payload.max_tokens = config.tokens
        if (config.temp !== undefined) payload.temperature = config.temp
        if (config.prompt !== undefined) payload.system_prompt = config.prompt
        if (config.msg !== undefined) payload.first_message = config.msg

        // Extended LLM
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

        // Voice
        if (config.voiceId !== undefined) payload.voice_name = config.voiceId
        if (config.voiceStyle !== undefined) payload.voice_style = config.voiceStyle
        if (config.voiceSpeed !== undefined) payload.voice_speed = config.voiceSpeed
        if (config.voicePitch !== undefined) payload.voice_pitch = config.voicePitch
        if (config.voiceVolume !== undefined) payload.voice_volume = config.voiceVolume
        if (config.voiceStyleDegree !== undefined) payload.voiceStyleDegree = config.voiceStyleDegree
        if (config.voiceBgSound !== undefined) payload.voiceBgSound = config.voiceBgSound
        if (config.voiceBgUrl !== undefined) payload.voiceBgUrl = config.voiceBgUrl

        // STT
        if (config.sttSilenceTimeout !== undefined) payload.silence_timeout_ms = config.sttSilenceTimeout
        if (config.sttProvider !== undefined) payload.sttProvider = config.sttProvider
        if (config.sttModel !== undefined) payload.sttModel = config.sttModel
        if (config.sttLang !== undefined) payload.sttLang = config.sttLang
        if (config.sttKeywords !== undefined) payload.sttKeywords = config.sttKeywords
        if (config.interruption_threshold !== undefined) payload.interruption_threshold = config.interruption_threshold
        if (config.vad_threshold !== undefined) payload.vadSensitivity = config.vad_threshold

        // Tools — only sent if any tool field is present
        if (config.toolsSchema !== undefined
            || config.toolServerUrl !== undefined
            || config.clientToolsEnabled !== undefined
            || config.asyncTools !== undefined) {

            let parsedTools: unknown[] = []
            try {
                if (config.toolsSchema) parsedTools = JSON.parse(config.toolsSchema)
            } catch (e) {
                console.warn('[configService] Failed to parse toolsSchema:', e)
            }

            payload.tools_config = {
                tools: parsedTools,
                tool_server_url: config.toolServerUrl,
                client_tools_enabled: config.clientToolsEnabled,
                async_execution: config.asyncTools,
                tool_timeout_ms: config.toolTimeoutMs,
                error_message: config.toolErrorMsg,
            }
        }

        return api.patch(`/agents/${agentId}`, payload)
    },

    // ── Catalogs ──────────────────────────────────────────────────────────────

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
        const params: Record<string, string> = { provider }
        if (language) params.language = language
        const response = await api.get<{ voices: Voice[] }>('/config/options/tts/voices', { params })
        return response.voices || []
    },

    getStyles: async (provider: string = 'azure', voiceId: string): Promise<VoiceStyle[]> => {
        if (!voiceId) return []
        const response = await api.get<{ styles: string[] }>('/config/options/tts/styles', { params: { provider, voice_id: voiceId } })
        // Backend returns string[], frontend expects { id, label }
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
        return api.post('/config/options/tts/preview', params, { responseType: 'blob' })
    },
}
