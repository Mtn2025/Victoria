import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { ConfigState, BrowserConfig, TwilioConfig, TelnyxConfig } from '@/types/config'
import { configService } from '@/services/configService'
import { agentService } from '@/services/agentService'

// Async Thunks
export const fetchLanguages = createAsyncThunk(
    'config/fetchLanguages',
    async (provider: string = 'azure') => {
        return await configService.getLanguages(provider)
    }
)

export const fetchVoices = createAsyncThunk(
    'config/fetchVoices',
    async ({ provider, language }: { provider: string, language?: string }) => {
        return await configService.getVoices(provider, language)
    }
)

export const fetchStyles = createAsyncThunk(
    'config/fetchStyles',
    async ({ provider, voiceId }: { provider: string, voiceId: string }) => {
        return await configService.getStyles(provider, voiceId)
    }
)

export const fetchLLMProviders = createAsyncThunk(
    'config/fetchLLMProviders',
    async () => {
        return await configService.getLLMProviders()
    }
)

export const fetchLLMModels = createAsyncThunk(
    'config/fetchLLMModels',
    async (provider: string) => {
        return await configService.getLLMModels(provider)
    }
)

export const fetchTTSProviders = createAsyncThunk(
    'config/fetchTTSProviders',
    async () => {
        return await configService.getTTSProviders()
    }
)

export const saveAgentConfig = createAsyncThunk(
    'config/saveAgentConfig',
    async (config: Partial<BrowserConfig> & { connectivity_config?: any, agent_provider?: string }, { getState, rejectWithValue }) => {

        const state = getState() as { agents: { activeAgent: { agent_uuid: string } | null } }
        const agentUuid = state.agents.activeAgent?.agent_uuid
        if (!agentUuid) {
            console.error('[saveAgentConfig] No active agent in Redux state. Aborting PATCH.')
            return rejectWithValue('No active agent')
        }
        return await configService.updateBrowserConfig(config, agentUuid)
    }
)

// Agent config is ALWAYS fetched from GET /api/agents/active.
// No agentId or name parameter needed — the backend resolves active agent from DB.
export const fetchAgentConfig = createAsyncThunk(
    'config/fetchAgentConfig',
    async () => {
        return await agentService.getActiveAgent()
    }
)

const initialState: ConfigState = {
    browser: {
        provider: 'groq',
        model: 'llama3-8b-8192',
        temp: 0.5,
        tokens: 1024,
        msg: 'Hola, ¿cómo estás?',
        mode: 'markdown',
        prompt: 'Eres un asistente útil.',

        // Conversation Style
        responseLength: 'medium',
        conversationTone: 'neutral',
        conversationFormality: 'formal',
        conversationPacing: 'moderate',

        // Advanced AI
        contextWindow: 10,
        frequencyPenalty: 0.0,
        presencePenalty: 0.0,
        toolChoice: 'auto',
        dynamicVarsEnabled: false,
        dynamicVars: '{}',

        // Voice Defaults
        voiceProvider: 'azure',
        voiceLang: 'es-MX',
        voiceGender: 'female',
        voiceId: 'es-MX-DaliaNeural',
        voiceStyle: '',
        voiceSpeed: 1.0,
        voicePitch: 0,
        voiceVolume: 100,
        voiceStyleDegree: 1.0,
        voiceBgSound: 'none',
        voiceBgUrl: '',

        voiceStability: 0.5,
        voiceSimilarityBoost: 0.75,
        voiceStyleExaggeration: 0.0,
        voiceSpeakerBoost: true,
        voiceMultilingual: true,
        ttsLatencyOptimization: 0,
        ttsOutputFormat: 'pcm_16000',
        voiceFillerInjection: false,
        voiceBackchanneling: false,
        textNormalizationRule: 'auto',

        // STT Defaults
        sttProvider: 'azure',
        sttLang: 'es-MX',
        sttModel: 'nova-2',
        sttKeywords: '',
        interruption_threshold: 0,
        hallucination_blacklist: '',
        sttSilenceTimeout: 600,
        sttUtteranceEnd: 'default',
        vad_threshold: 0.5,
        interruptRMS: 0,

        sttPunctuation: true,
        sttSmartFormatting: true,
        sttProfanityFilter: false,
        sttDiarization: false,
        sttMultilingual: false,

        // Advanced / Quality
        noiseSuppressionLevel: 'balanced',
        audioCodec: 'PCMU',
        enableBackchannel: false,
        maxDuration: 600,
        maxRetries: 1,
        useSameInactivityMessage: true,
        idleMessage: '',
        endCallEnabled: false,
        endCallPhrases: '',
        endCallInstructions: '',

        // Campaigns / Integrations
        crmEnabled: false,
        webhookUrl: '',
        webhookSecret: '',

        // System / Governance
        concurrencyLimit: 1,
        spendLimitDaily: 10.00,
        environment: 'development',
        privacyMode: false,
        auditLogEnabled: false,

        // Analysis Defaults
        analysisPrompt: '',
        successRubric: '',
        sentimentAnalysis: false,
        costTrackingEnabled: false,
        extractionSchema: '{}',
        piiRedactionEnabled: false,
        logWebhookUrl: '',
        retentionDays: 30,

        // Flow Defaults
        bargeInEnabled: true,
        interruptionSensitivity: 0.5,
        interruptionPhrases: '[]',
        voicemailDetectionEnabled: false,
        voicemailMessage: '',
        machineDetectionSensitivity: 0.7,
        amdSensitivity: 0.5,
        amdAction: 'hangup',
        responseDelaySeconds: 0.5,
        hyphenationEnabled: false,

        // Tools
        toolsSchema: '[]',
        asyncTools: false,
        clientToolsEnabled: false,
        toolServerUrl: '',
        toolServerSecret: '',
        toolTimeoutMs: 10000,
        toolRetryCount: 1,
        toolErrorMsg: "Lo siento, hubo un error con la herramienta.",
        redactParams: '[]',
        transferWhitelist: '[]',
        stateInjectionEnabled: false
    },
    twilio: {
        twilioAccountSid: '',
        twilioAuthToken: '',
        twilioFromNumber: '',
        sipTrunkUriPhone: '',
        sipAuthUserPhone: '',
        sipAuthPassPhone: '',
        fallbackNumberPhone: '',
        geoRegionPhone: 'us-east-1',
        recordingChannelsPhone: 'mono',
        recordingEnabledPhone: false,
        hipaaEnabledPhone: false,
        dtmfListeningEnabledPhone: false
    } as TwilioConfig,
    telnyx: {
        telnyxApiKey: '',
        telnyxConnectionId: '',
        callerIdTelnyx: '',
        sipTrunkUriTelnyx: '',
        sipAuthUserTelnyx: '',
        sipAuthPassTelnyx: '',
        fallbackNumberTelnyx: '',
        geoRegionTelnyx: 'us-central',
        recordingChannelsTelnyx: 'dual',
        enableRecordingTelnyx: false,
        hipaaEnabledTelnyx: false,
        dtmfListeningEnabledTelnyx: false,
        amdConfig: 'disabled',
        interruptRMS: 1000,

        // Campaigns / Integrations
        crmEnabled: false,
        webhookUrl: '',
        webhookSecret: '',

        // System / Governance
        concurrencyLimit: 20,
        spendLimitDaily: 100.00,
        environment: 'production',
        privacyMode: false,
        auditLogEnabled: true,

        // Tools Defaults
        toolsSchema: '[]',
        asyncTools: false,
        clientToolsEnabled: false,
        toolServerUrl: '',
        toolServerSecret: '',
        toolTimeoutMs: 10000,
        toolRetryCount: 1,
        toolErrorMsg: "Lo siento, hubo un error con la herramienta.",
        redactParams: '[]',
        transferWhitelist: '[]',
        stateInjectionEnabled: false
    } as TelnyxConfig,

    // Catalogs
    availableLanguages: [],
    availableVoices: [],
    availableStyles: [],
    availableLLMProviders: [],
    availableLLMModels: [],
    availableTTSProviders: [],

    isLoadingOptions: false,
    saveStatus: 'idle',
    lastSaved: null
}

export const configSlice = createSlice({
    name: 'config',
    initialState,
    reducers: {
        updateBrowserConfig: (state, action: PayloadAction<Partial<BrowserConfig>>) => {
            state.browser = { ...state.browser, ...action.payload }
            if ('voiceId' in action.payload || 'voiceProvider' in action.payload || 'voiceGender' in action.payload) {
                // Si se actualizaron campos base en cascada, re-validamos.
                // Siempre que cambia de voz, limpiamos los estilos actuales
                // hasta que se hagan fetch de los nuevos.
                state.availableStyles = []
            }
        },
        updateTwilioConfigState: (state, action: PayloadAction<Partial<TwilioConfig>>) => {
            state.twilio = { ...state.twilio, ...action.payload }
        },
        updateTelnyxConfigState: (state, action: PayloadAction<Partial<TelnyxConfig>>) => {
            state.telnyx = { ...state.telnyx, ...action.payload }
        },
        setLoadingOptions: (state, action: PayloadAction<boolean>) => {
            state.isLoadingOptions = action.payload
        },
        setSaveStatus: (state, action: PayloadAction<'idle' | 'saving' | 'saved' | 'error'>) => {
            state.saveStatus = action.payload
        },
        setLastSaved: (state, action: PayloadAction<string>) => {
            state.lastSaved = action.payload
        }
    },
    extraReducers: (builder) => {
        // Languages
        builder.addCase(fetchLanguages.pending, (state) => {
            state.isLoadingOptions = true
        })
        builder.addCase(fetchLanguages.fulfilled, (state, action) => {
            state.availableLanguages = action.payload
            state.isLoadingOptions = false
        })
        builder.addCase(fetchLanguages.rejected, (state) => {
            state.isLoadingOptions = false
        })

        // Voices
        builder.addCase(fetchVoices.pending, (state) => {
            state.isLoadingOptions = true
        })
        builder.addCase(fetchVoices.fulfilled, (state, action) => {
            state.availableVoices = action.payload
            state.isLoadingOptions = false
        })
        builder.addCase(fetchVoices.rejected, (state) => {
            state.isLoadingOptions = false
        })

        // Styles
        builder.addCase(fetchStyles.pending, (state) => {
            state.availableStyles = []
        })
        builder.addCase(fetchStyles.fulfilled, (state, action) => {
            state.availableStyles = action.payload || []
        })
        builder.addCase(fetchStyles.rejected, (state) => {
            state.availableStyles = []
        })

        // LLM Providers
        builder.addCase(fetchLLMProviders.pending, (state) => {
            state.isLoadingOptions = true
        })
        builder.addCase(fetchLLMProviders.fulfilled, (state, action) => {
            state.availableLLMProviders = action.payload
            state.isLoadingOptions = false
        })
        builder.addCase(fetchLLMProviders.rejected, (state) => {
            state.isLoadingOptions = false
        })

        // LLM Models
        builder.addCase(fetchLLMModels.pending, (state) => {
            state.isLoadingOptions = true
        })
        builder.addCase(fetchLLMModels.fulfilled, (state, action) => {
            state.availableLLMModels = action.payload
            state.isLoadingOptions = false
        })
        builder.addCase(fetchLLMModels.rejected, (state) => {
            state.isLoadingOptions = false
        })

        // TTS Providers
        builder.addCase(fetchTTSProviders.pending, (state) => {
            state.isLoadingOptions = true
        })
        builder.addCase(fetchTTSProviders.fulfilled, (state, action) => {
            state.availableTTSProviders = action.payload as any
            state.isLoadingOptions = false
        })
        builder.addCase(fetchTTSProviders.rejected, (state) => {
            state.isLoadingOptions = false
        })

        // Save Agent Config (Browser + Connectivity JSON)
        builder.addCase(saveAgentConfig.pending, (state) => {
            state.saveStatus = 'saving'
        })
        builder.addCase(saveAgentConfig.fulfilled, (state) => {
            state.saveStatus = 'saved'
            state.lastSaved = new Date().toISOString()
        })
        builder.addCase(saveAgentConfig.rejected, (state) => {
            state.saveStatus = 'error'
        })

        // Fetch Agent Config (Hydration)
        builder.addCase(fetchAgentConfig.pending, (state) => {
            state.isLoadingOptions = true
        })
        builder.addCase(fetchAgentConfig.fulfilled, (state, action) => {
            state.isLoadingOptions = false
            const data = action.payload as any

            // Hydrate Browser Config from Server
            if (data.system_prompt) state.browser.prompt = data.system_prompt
            if (data.first_message) state.browser.msg = data.first_message
            if (data.silence_timeout_ms !== undefined) state.browser.sttSilenceTimeout = data.silence_timeout_ms

            if (data.voice) {
                if (data.voice.name) state.browser.voiceId = data.voice.name
                if (data.voice.gender) state.browser.voiceGender = data.voice.gender
                if (data.voice.style) state.browser.voiceStyle = data.voice.style
                if (data.voice.speed !== undefined) state.browser.voiceSpeed = data.voice.speed
                if (data.voice.pitch !== undefined) state.browser.voicePitch = data.voice.pitch
                if (data.voice.volume !== undefined) state.browser.voiceVolume = data.voice.volume
            }

            if (data.llm_config) {
                // Backend stores these as 'llm_provider' and 'llm_model' inside llm_config
                if (data.llm_config.llm_provider) state.browser.provider = data.llm_config.llm_provider
                if (data.llm_config.llm_model) state.browser.model = data.llm_config.llm_model
                if (data.llm_config.max_tokens !== undefined) state.browser.tokens = data.llm_config.max_tokens
                if (data.llm_config.temperature !== undefined) state.browser.temp = data.llm_config.temperature

                // Advanced LLM mapped fields (camelCase keys stored verbatim by backend)
                const copyFields = ['responseLength', 'conversationTone', 'conversationFormality',
                    'conversationPacing', 'contextWindow', 'frequencyPenalty',
                    'presencePenalty', 'toolChoice', 'dynamicVarsEnabled',
                    'dynamicVars', 'mode', 'hallucination_blacklist']
                copyFields.forEach(field => {
                    if (data.llm_config[field] !== undefined) {
                        (state.browser as any)[field] = data.llm_config[field]
                    }
                })

                if (data.llm_config.end_call_enabled !== undefined) state.browser.endCallEnabled = data.llm_config.end_call_enabled
                if (data.llm_config.end_call_phrases !== undefined) state.browser.endCallPhrases = (data.llm_config.end_call_phrases || []).join(', ')
                if (data.llm_config.end_call_instructions !== undefined) state.browser.endCallInstructions = data.llm_config.end_call_instructions
            }

            if (data.voice_config_json) {
                const vc = data.voice_config_json
                if (vc.voiceStyleDegree !== undefined) state.browser.voiceStyleDegree = vc.voiceStyleDegree
                if (vc.voiceBgSound !== undefined) state.browser.voiceBgSound = vc.voiceBgSound
                if (vc.voiceBgUrl !== undefined) state.browser.voiceBgUrl = vc.voiceBgUrl
            }

            if (data.stt_config) {
                const stt = data.stt_config
                if (stt.sttProvider !== undefined) state.browser.sttProvider = stt.sttProvider
                if (stt.sttModel !== undefined) state.browser.sttModel = stt.sttModel
                if (stt.sttLang !== undefined) state.browser.sttLang = stt.sttLang
                if (stt.sttKeywords !== undefined) state.browser.sttKeywords = stt.sttKeywords
                if (stt.interruption_threshold !== undefined) state.browser.interruption_threshold = stt.interruption_threshold
                if (stt.vadSensitivity !== undefined) state.browser.vad_threshold = stt.vadSensitivity
                if (stt.noise_suppression_level !== undefined) state.browser.noiseSuppressionLevel = stt.noise_suppression_level
                if (stt.audio_codec !== undefined) state.browser.audioCodec = stt.audio_codec
            }

            if (data.flow_config) {
                const flow = data.flow_config
                if (flow.barge_in_enabled !== undefined) state.browser.bargeInEnabled = flow.barge_in_enabled
                if (flow.barge_in_sensitivity !== undefined) state.browser.interruptionSensitivity = flow.barge_in_sensitivity
                if (flow.barge_in_phrases !== undefined) state.browser.interruptionPhrases = (flow.barge_in_phrases || []).join(', ')
                if (flow.amd_enabled !== undefined) state.browser.voicemailDetectionEnabled = flow.amd_enabled
                if (flow.amd_message !== undefined) state.browser.voicemailMessage = flow.amd_message
                if (flow.amd_sensitivity !== undefined) state.browser.amdSensitivity = flow.amd_sensitivity
                if (flow.amd_action !== undefined) state.browser.amdAction = flow.amd_action
                if (flow.pacing_response_delay_ms !== undefined) state.browser.responseDelaySeconds = flow.pacing_response_delay_ms / 1000
                if (flow.pacing_hyphenation !== undefined) state.browser.hyphenationEnabled = flow.pacing_hyphenation
                if (flow.pacing_end_call_phrases !== undefined) state.browser.endCallPhrases = (flow.pacing_end_call_phrases || []).join(', ')
                if (flow.enable_backchannel !== undefined) state.browser.enableBackchannel = flow.enable_backchannel
                if (flow.idle_message !== undefined) {
                    state.browser.idleMessage = flow.idle_message
                    state.browser.useSameInactivityMessage = !Array.isArray(flow.idle_message)
                }
            }

            if (data.analysis_config) {
                const analysis = data.analysis_config
                if (analysis.analysis_prompt !== undefined) state.browser.analysisPrompt = analysis.analysis_prompt
                if (analysis.success_rubric !== undefined) state.browser.successRubric = analysis.success_rubric
                if (analysis.sentiment_analysis !== undefined) state.browser.sentimentAnalysis = analysis.sentiment_analysis
                if (analysis.webhook_url !== undefined) state.browser.webhookUrl = analysis.webhook_url
                if (analysis.webhook_secret !== undefined) state.browser.webhookSecret = analysis.webhook_secret
                if (analysis.pii_redaction_enabled !== undefined) state.browser.piiRedactionEnabled = analysis.pii_redaction_enabled
                if (analysis.cost_tracking_enabled !== undefined) state.browser.costTrackingEnabled = analysis.cost_tracking_enabled
                if (analysis.retention_days !== undefined) state.browser.retentionDays = analysis.retention_days
                if (analysis.extraction_schema !== undefined) {
                    try {
                        state.browser.extractionSchema = typeof analysis.extraction_schema === 'string' ? analysis.extraction_schema : JSON.stringify(analysis.extraction_schema, null, 2)
                    } catch (e) {
                        state.browser.extractionSchema = String(analysis.extraction_schema)
                    }
                }
            }

            if ((data as any).system_config) {
                const sys = (data as any).system_config
                if (sys.concurrency_limit !== undefined) state.browser.concurrencyLimit = sys.concurrency_limit
                if (sys.spend_limit_daily !== undefined) state.browser.spendLimitDaily = sys.spend_limit_daily
                if (sys.environment !== undefined) state.browser.environment = sys.environment
                if (sys.privacy_mode !== undefined) state.browser.privacyMode = sys.privacy_mode
                if (sys.audit_log_enabled !== undefined) state.browser.auditLogEnabled = sys.audit_log_enabled
                if (sys.max_duration !== undefined) state.browser.maxDuration = sys.max_duration
                if (sys.max_retries !== undefined) state.browser.maxRetries = sys.max_retries
            }

            if (data.tools_config && data.tools_config.length > 0) {
                const tc = data.tools_config[0]
                if (tc.tools) state.browser.toolsSchema = JSON.stringify(tc.tools)
                if (tc.tool_server_url !== undefined) state.browser.toolServerUrl = tc.tool_server_url
                if (tc.client_tools_enabled !== undefined) state.browser.clientToolsEnabled = tc.client_tools_enabled
                if (tc.async_execution !== undefined) state.browser.asyncTools = tc.async_execution
                if (tc.tool_timeout_ms !== undefined) state.browser.toolTimeoutMs = tc.tool_timeout_ms
                if (tc.error_message !== undefined) state.browser.toolErrorMsg = tc.error_message
                if (tc.retry_count !== undefined) state.browser.toolRetryCount = tc.retry_count
                if (tc.redact_params !== undefined) state.browser.redactParams = tc.redact_params
                if (tc.transfer_whitelist !== undefined) state.browser.transferWhitelist = tc.transfer_whitelist
                if (tc.state_injection_enabled !== undefined) state.browser.stateInjectionEnabled = tc.state_injection_enabled
            }

            // Hydrate Connectivity Config (Twilio / Telnyx specific isolated fields)
            // Fix: Hydrate regardless of current active provider, otherwise inactive provider tabs look empty.
            if (data.connectivity_config) {
                const conn = data.connectivity_config
                if (data.provider === 'twilio') {
                    // --- TWILIO ---
                    if (conn.twilio_account_sid !== undefined) state.twilio.twilioAccountSid = conn.twilio_account_sid
                    else if (conn.twilioAccountSid !== undefined) state.twilio.twilioAccountSid = conn.twilioAccountSid

                    if (conn.twilio_auth_token !== undefined) state.twilio.twilioAuthToken = conn.twilio_auth_token
                    else if (conn.twilioAuthToken !== undefined) state.twilio.twilioAuthToken = conn.twilioAuthToken

                    if (conn.twilio_from_number !== undefined) state.twilio.twilioFromNumber = conn.twilio_from_number
                    else if (conn.twilioFromNumber !== undefined) state.twilio.twilioFromNumber = conn.twilioFromNumber

                    if (conn.sip_trunk_uri_phone !== undefined) state.twilio.sipTrunkUriPhone = conn.sip_trunk_uri_phone
                    else if (conn.sipTrunkUriPhone !== undefined) state.twilio.sipTrunkUriPhone = conn.sipTrunkUriPhone

                    if (conn.sip_auth_user_phone !== undefined) state.twilio.sipAuthUserPhone = conn.sip_auth_user_phone
                    else if (conn.sipAuthUserPhone !== undefined) state.twilio.sipAuthUserPhone = conn.sipAuthUserPhone

                    if (conn.sip_auth_pass_phone !== undefined) state.twilio.sipAuthPassPhone = conn.sip_auth_pass_phone
                    else if (conn.sipAuthPassPhone !== undefined) state.twilio.sipAuthPassPhone = conn.sipAuthPassPhone

                    if (conn.fallback_number_phone !== undefined) state.twilio.fallbackNumberPhone = conn.fallback_number_phone
                    else if (conn.fallbackNumberPhone !== undefined) state.twilio.fallbackNumberPhone = conn.fallbackNumberPhone

                    if (conn.geo_region_phone !== undefined) state.twilio.geoRegionPhone = conn.geo_region_phone
                    else if (conn.geoRegionPhone !== undefined) state.twilio.geoRegionPhone = conn.geoRegionPhone

                    if (conn.recording_channels_phone !== undefined) state.twilio.recordingChannelsPhone = conn.recording_channels_phone
                    else if (conn.recordingChannelsPhone !== undefined) state.twilio.recordingChannelsPhone = conn.recordingChannelsPhone

                    if (conn.recording_enabled_phone !== undefined) state.twilio.recordingEnabledPhone = conn.recording_enabled_phone
                    else if (conn.recordingEnabledPhone !== undefined) state.twilio.recordingEnabledPhone = conn.recordingEnabledPhone

                    if (conn.hipaa_enabled_phone !== undefined) state.twilio.hipaaEnabledPhone = conn.hipaa_enabled_phone
                    else if (conn.hipaaEnabledPhone !== undefined) state.twilio.hipaaEnabledPhone = conn.hipaaEnabledPhone

                    if (conn.dtmf_listening_enabled_phone !== undefined) state.twilio.dtmfListeningEnabledPhone = conn.dtmf_listening_enabled_phone
                    else if (conn.dtmfListeningEnabledPhone !== undefined) state.twilio.dtmfListeningEnabledPhone = conn.dtmfListeningEnabledPhone
                } else if (data.provider === 'telnyx') {
                    // Fix destructive auto-save: map snake_case from DB back to camelCase in Redux
                    if (conn.telnyx_api_key !== undefined) state.telnyx.telnyxApiKey = conn.telnyx_api_key
                    else if (conn.telnyxApiKey !== undefined) state.telnyx.telnyxApiKey = conn.telnyxApiKey

                    if (conn.telnyx_connection_id !== undefined) state.telnyx.telnyxConnectionId = conn.telnyx_connection_id
                    else if (conn.telnyxConnectionId !== undefined) state.telnyx.telnyxConnectionId = conn.telnyxConnectionId

                    if (conn.telnyx_phone_number !== undefined) state.telnyx.callerIdTelnyx = conn.telnyx_phone_number
                    else if (conn.callerIdTelnyx !== undefined) state.telnyx.callerIdTelnyx = conn.callerIdTelnyx

                    if (conn.sip_trunk_uri_telnyx !== undefined) state.telnyx.sipTrunkUriTelnyx = conn.sip_trunk_uri_telnyx
                    else if (conn.sipTrunkUriTelnyx !== undefined) state.telnyx.sipTrunkUriTelnyx = conn.sipTrunkUriTelnyx

                    if (conn.sip_auth_user_telnyx !== undefined) state.telnyx.sipAuthUserTelnyx = conn.sip_auth_user_telnyx
                    else if (conn.sipAuthUserTelnyx !== undefined) state.telnyx.sipAuthUserTelnyx = conn.sipAuthUserTelnyx

                    if (conn.sip_auth_pass_telnyx !== undefined) state.telnyx.sipAuthPassTelnyx = conn.sip_auth_pass_telnyx
                    else if (conn.sipAuthPassTelnyx !== undefined) state.telnyx.sipAuthPassTelnyx = conn.sipAuthPassTelnyx

                    if (conn.fallback_number_telnyx !== undefined) state.telnyx.fallbackNumberTelnyx = conn.fallback_number_telnyx
                    else if (conn.fallbackNumberTelnyx !== undefined) state.telnyx.fallbackNumberTelnyx = conn.fallbackNumberTelnyx

                    if (conn.geo_region_telnyx !== undefined) state.telnyx.geoRegionTelnyx = conn.geo_region_telnyx
                    else if (conn.geoRegionTelnyx !== undefined) state.telnyx.geoRegionTelnyx = conn.geoRegionTelnyx

                    if (conn.recording_channels_telnyx !== undefined) state.telnyx.recordingChannelsTelnyx = conn.recording_channels_telnyx
                    else if (conn.recordingChannelsTelnyx !== undefined) state.telnyx.recordingChannelsTelnyx = conn.recordingChannelsTelnyx

                    if (conn.enable_recording_telnyx !== undefined) state.telnyx.enableRecordingTelnyx = conn.enable_recording_telnyx
                    else if (conn.enableRecordingTelnyx !== undefined) state.telnyx.enableRecordingTelnyx = conn.enableRecordingTelnyx

                    if (conn.hipaa_enabled_telnyx !== undefined) state.telnyx.hipaaEnabledTelnyx = conn.hipaa_enabled_telnyx
                    else if (conn.hipaaEnabledTelnyx !== undefined) state.telnyx.hipaaEnabledTelnyx = conn.hipaaEnabledTelnyx

                    if (conn.dtmf_listening_enabled_telnyx !== undefined) state.telnyx.dtmfListeningEnabledTelnyx = conn.dtmf_listening_enabled_telnyx
                    else if (conn.dtmfListeningEnabledTelnyx !== undefined) state.telnyx.dtmfListeningEnabledTelnyx = conn.dtmfListeningEnabledTelnyx

                    if (conn.amdConfig !== undefined) state.telnyx.amdConfig = conn.amdConfig
                    if (conn.interruptRMS !== undefined) state.telnyx.interruptRMS = conn.interruptRMS
                }
            }
        })
        builder.addCase(fetchAgentConfig.rejected, (state) => {
            state.isLoadingOptions = false
        })
    }
})

export const { updateBrowserConfig, updateTwilioConfigState, updateTelnyxConfigState, setLoadingOptions, setSaveStatus, setLastSaved } = configSlice.actions
export default configSlice.reducer
