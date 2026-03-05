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
    voice_provider?: string
    voice_name?: string
    voice_style?: string
    voice_speed?: number
    voice_pitch?: number
    voice_volume?: number
    voiceStyleDegree?: number
    voiceBgSound?: string
    voiceBgUrl?: string
    // ElevenLabs y Advanced TTS
    voiceStability?: number
    voiceSimilarityBoost?: number
    voiceStyleExaggeration?: number
    voiceSpeakerBoost?: boolean
    voiceMultilingual?: boolean
    voiceFillerInjection?: boolean
    voiceBackchanneling?: boolean
    textNormalizationRule?: string
    ttsLatencyOptimization?: number
    ttsOutputFormat?: string
    // STT
    sttProvider?: string
    sttModel?: string
    sttLang?: string
    sttKeywords?: string
    interruption_threshold?: number
    vadSensitivity?: number
    silence_timeout_ms?: number
    // Flow Config
    barge_in_enabled?: boolean
    barge_in_sensitivity?: number
    barge_in_phrases?: string[]
    amd_enabled?: boolean
    amd_sensitivity?: number
    amd_action?: string
    amd_message?: string
    pacing_response_delay_ms?: number
    pacing_hyphenation?: boolean
    pacing_end_call_phrases?: string[]
    // Tools
    tools_config?: Record<string, unknown>
    // Analysis
    analysis_prompt?: string
    success_rubric?: string
    extraction_schema?: any
    sentiment_analysis?: boolean
    webhook_url?: string
    webhook_secret?: string
    pii_redaction_enabled?: boolean
    cost_tracking_enabled?: boolean
    retention_days?: number
    crm_enabled?: boolean
    // System
    concurrency_limit?: number
    spend_limit_daily?: number
    environment?: string
    privacy_mode?: boolean
    audit_log_enabled?: boolean
    // Advanced
    noise_suppression_level?: string
    audio_codec?: string
    enable_backchannel?: boolean
    max_duration?: number
    max_retries?: number
    idle_message?: string | string[]
    end_call_enabled?: boolean
    end_call_phrases?: string[]
    end_call_instructions?: string
    // Connectivity
    connectivity_config?: Record<string, unknown>
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

        // Smart Hangup
        if (config.endCallEnabled !== undefined) payload.end_call_enabled = config.endCallEnabled
        if (config.endCallPhrases !== undefined) {
            payload.end_call_phrases = config.endCallPhrases
                .split(',')
                .map(s => s.trim())
                .filter(Boolean)
        }
        if (config.endCallInstructions !== undefined) payload.end_call_instructions = config.endCallInstructions

        // Voice
        if (config.voiceProvider !== undefined) payload.voice_provider = config.voiceProvider
        if (config.voiceId !== undefined) payload.voice_name = config.voiceId
        if (config.voiceStyle !== undefined) payload.voice_style = config.voiceStyle
        if (config.voiceSpeed !== undefined) payload.voice_speed = config.voiceSpeed
        if (config.voicePitch !== undefined) payload.voice_pitch = config.voicePitch
        if (config.voiceVolume !== undefined) payload.voice_volume = config.voiceVolume
        if (config.voiceStyleDegree !== undefined) payload.voiceStyleDegree = config.voiceStyleDegree
        if (config.voiceBgSound !== undefined) payload.voiceBgSound = config.voiceBgSound
        if (config.voiceBgUrl !== undefined) payload.voiceBgUrl = config.voiceBgUrl

        // Advanced TTS & Humanization
        if (config.voiceFillerInjection !== undefined) payload.voiceFillerInjection = config.voiceFillerInjection
        if (config.voiceBackchanneling !== undefined) payload.voiceBackchanneling = config.voiceBackchanneling
        if (config.textNormalizationRule !== undefined) payload.textNormalizationRule = config.textNormalizationRule
        if (config.ttsLatencyOptimization !== undefined) payload.ttsLatencyOptimization = config.ttsLatencyOptimization
        if (config.ttsOutputFormat !== undefined) payload.ttsOutputFormat = config.ttsOutputFormat

        // ElevenLabs specifics
        if (config.voiceStability !== undefined) payload.voiceStability = config.voiceStability
        if (config.voiceSimilarityBoost !== undefined) payload.voiceSimilarityBoost = config.voiceSimilarityBoost
        if (config.voiceStyleExaggeration !== undefined) payload.voiceStyleExaggeration = config.voiceStyleExaggeration
        if (config.voiceSpeakerBoost !== undefined) payload.voiceSpeakerBoost = config.voiceSpeakerBoost
        if (config.voiceMultilingual !== undefined) payload.voiceMultilingual = config.voiceMultilingual

        // STT
        if (config.sttSilenceTimeout !== undefined) payload.silence_timeout_ms = config.sttSilenceTimeout
        if (config.sttProvider !== undefined) payload.sttProvider = config.sttProvider
        if (config.sttModel !== undefined) payload.sttModel = config.sttModel
        if (config.sttLang !== undefined) payload.sttLang = config.sttLang
        if (config.sttKeywords !== undefined) payload.sttKeywords = config.sttKeywords
        if (config.interruption_threshold !== undefined) payload.interruption_threshold = config.interruption_threshold
        if (config.vad_threshold !== undefined) payload.vadSensitivity = config.vad_threshold
        if (config.noiseSuppressionLevel !== undefined) payload.noise_suppression_level = config.noiseSuppressionLevel
        if (config.audioCodec !== undefined) payload.audio_codec = config.audioCodec

        // Tools — only sent if any tool field is present
        if (config.toolsSchema !== undefined
            || config.toolServerUrl !== undefined
            || config.clientToolsEnabled !== undefined
            || config.asyncTools !== undefined
            || config.toolRetryCount !== undefined
            || config.redactParams !== undefined
            || config.transferWhitelist !== undefined
            || config.stateInjectionEnabled !== undefined) {

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
                retry_count: config.toolRetryCount,
                redact_params: config.redactParams,
                transfer_whitelist: config.transferWhitelist,
                state_injection_enabled: config.stateInjectionEnabled,
            }
        }

        // --- FLOW CONFIG (Barge-in, AMD, Pacing) ---
        if (config.bargeInEnabled !== undefined) payload.barge_in_enabled = config.bargeInEnabled
        if (config.interruptionSensitivity !== undefined) payload.barge_in_sensitivity = config.interruptionSensitivity
        if (config.voicemailDetectionEnabled !== undefined) payload.amd_enabled = config.voicemailDetectionEnabled
        if (config.voicemailMessage !== undefined) payload.amd_message = config.voicemailMessage
        if (config.amdSensitivity !== undefined) payload.amd_sensitivity = config.amdSensitivity
        if (config.amdAction !== undefined) payload.amd_action = config.amdAction
        if (config.responseDelaySeconds !== undefined) payload.pacing_response_delay_ms = Math.round(config.responseDelaySeconds * 1000)
        if (config.hyphenationEnabled !== undefined) payload.pacing_hyphenation = config.hyphenationEnabled

        // Convert comma-separated string back to array for the API
        if (config.interruptionPhrases !== undefined) {
            payload.barge_in_phrases = config.interruptionPhrases
                ? config.interruptionPhrases.split(',').map((p: string) => p.trim()).filter(Boolean)
                : []
        }
        if (config.endCallPhrases !== undefined) {
            payload.pacing_end_call_phrases = config.endCallPhrases
                ? config.endCallPhrases.split(',').map((p: string) => p.trim()).filter(Boolean)
                : []
        }
        if (config.enableBackchannel !== undefined) payload.enable_backchannel = config.enableBackchannel
        if (config.idleMessage !== undefined) {
            payload.idle_message = config.useSameInactivityMessage
                ? (Array.isArray(config.idleMessage) ? config.idleMessage[0] : config.idleMessage)
                : config.idleMessage
        }
        // --- ANALYSIS & INTEGRATIONS ---
        if (config.analysisPrompt !== undefined) payload.analysis_prompt = config.analysisPrompt
        if (config.successRubric !== undefined) payload.success_rubric = config.successRubric
        if (config.sentimentAnalysis !== undefined) payload.sentiment_analysis = config.sentimentAnalysis
        if (config.webhookUrl !== undefined) payload.webhook_url = config.webhookUrl
        if (config.webhookSecret !== undefined) payload.webhook_secret = config.webhookSecret
        if (config.piiRedactionEnabled !== undefined) payload.pii_redaction_enabled = config.piiRedactionEnabled
        if (config.costTrackingEnabled !== undefined) payload.cost_tracking_enabled = config.costTrackingEnabled
        if (config.retentionDays !== undefined) payload.retention_days = config.retentionDays
        if (config.crmEnabled !== undefined) payload.crm_enabled = config.crmEnabled

        // --- SYSTEM & GOVERNANCE ---
        if (config.concurrencyLimit !== undefined) payload.concurrency_limit = config.concurrencyLimit
        if (config.spendLimitDaily !== undefined) payload.spend_limit_daily = config.spendLimitDaily
        if (config.environment !== undefined) payload.environment = config.environment
        if (config.privacyMode !== undefined) payload.privacy_mode = config.privacyMode
        if (config.auditLogEnabled !== undefined) payload.audit_log_enabled = config.auditLogEnabled
        if (config.maxDuration !== undefined) payload.max_duration = config.maxDuration
        if (config.maxRetries !== undefined) payload.max_retries = config.maxRetries

        if (config.extractionSchema !== undefined) {
            try {
                payload.extraction_schema = config.extractionSchema ? JSON.parse(config.extractionSchema) : {}
            } catch (e) {
                console.warn('[configService] Failed to parse extractionSchema:', e)
                payload.extraction_schema = config.extractionSchema
            }
        }

        // --- CONNECTIVITY CONFIG (Telnyx / Twilio) ---
        if ((config as any).connectivity_config !== undefined) {
            const rawConn = (config as any).connectivity_config;
            const mappedConn: Record<string, any> = {};

            // Translate camelCase keys to snake_case dynamically for connectivity_config
            for (const key in rawConn) {
                if (Object.prototype.hasOwnProperty.call(rawConn, key)) {
                    // Manual overrides for specific nomenclature required by the backend
                    if (key === 'telnyxConnectionId') {
                        mappedConn['telnyx_connection_id'] = rawConn[key];
                    } else if (key === 'callerIdTelnyx') {
                        mappedConn['telnyx_phone_number'] = rawConn[key];
                    } else if (key === 'enableRecordingTelnyx') {
                        mappedConn['enable_recording_telnyx'] = rawConn[key];
                    } else if (key === 'recordingChannelsTelnyx') {
                        mappedConn['recording_channels_telnyx'] = rawConn[key];
                    } else {
                        // Generic camelCase to snake_case converter for other keys
                        const snakeKey = key.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
                        mappedConn[snakeKey] = rawConn[key];
                    }
                }
            }
            payload.connectivity_config = mappedConn;
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

    getTTSProviders: async (): Promise<{ id: string, name: string }[]> => {
        const response = await api.get<{ providers: { id: string, name: string }[] }>('/config/options/tts/providers')
        return response.providers || []
    },

    getSTTProviders: async (): Promise<{ id: string, name: string }[]> => {
        const response = await api.get<{ providers: { id: string, name: string }[] }>('/config/options/stt/providers')
        return response.providers || []
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
