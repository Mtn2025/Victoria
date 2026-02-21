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

export const saveBrowserConfig = createAsyncThunk(
    'config/saveBrowserConfig',
    async (config: Partial<BrowserConfig>, { getState, rejectWithValue }) => {
        const state = getState() as { agents: { activeAgent: { agent_uuid: string } | null } }
        const agentUuid = state.agents.activeAgent?.agent_uuid
        if (!agentUuid) {
            console.error('[saveBrowserConfig] No active agent in Redux state. Aborting PATCH.')
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
        idleMessage: '¿Hola? ¿Sigues ahí?',

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
        analysisPrompt: 'Resume la llamada en 3 puntos clave.',
        successRubric: '- Cliente aceptó agendar cita.\n- Cliente solicitó información adicional.',
        sentimentAnalysis: false,
        costTrackingEnabled: false,
        extractionSchema: '{\n  "customer_intent": "string"\n}',
        piiRedactionEnabled: false,
        logWebhookUrl: '',
        retentionDays: 30,

        // Flow Defaults
        bargeInEnabled: true,
        interruptionSensitivity: 0.5,
        interruptionPhrases: '["para", "espera", "escúchame"]',
        voicemailDetectionEnabled: true,
        voicemailMessage: 'Hola, llamaba de Ubrokers...',
        machineDetectionSensitivity: 0.7,
        responseDelaySeconds: 0.5,
        waitForGreeting: true,
        hyphenationEnabled: true,
        endCallPhrases: '["gracias", "adiós", "hasta luego"]',

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

    isLoadingOptions: false
}

export const configSlice = createSlice({
    name: 'config',
    initialState,
    reducers: {
        updateBrowserConfig: (state, action: PayloadAction<Partial<BrowserConfig>>) => {
            state.browser = { ...state.browser, ...action.payload }
        },
        updateTwilioConfigState: (state, action: PayloadAction<Partial<TwilioConfig>>) => {
            state.twilio = { ...state.twilio, ...action.payload }
        },
        updateTelnyxConfigState: (state, action: PayloadAction<Partial<TelnyxConfig>>) => {
            state.telnyx = { ...state.telnyx, ...action.payload }
        },
        setLoadingOptions: (state, action: PayloadAction<boolean>) => {
            state.isLoadingOptions = action.payload
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
        builder.addCase(fetchStyles.fulfilled, (state, action) => {
            state.availableStyles = action.payload
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

        // Save Browser Config
        builder.addCase(saveBrowserConfig.pending, (state) => {
            state.isLoadingOptions = true
        })
        builder.addCase(saveBrowserConfig.fulfilled, (state) => {
            state.isLoadingOptions = false
        })
        builder.addCase(saveBrowserConfig.rejected, (state) => {
            state.isLoadingOptions = false
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
                if (data.voice.style) state.browser.voiceStyle = data.voice.style
                if (data.voice.speed !== undefined) state.browser.voiceSpeed = data.voice.speed
                if (data.voice.pitch !== undefined) state.browser.voicePitch = data.voice.pitch
                if (data.voice.volume !== undefined) state.browser.voiceVolume = data.voice.volume
            }

            if (data.llm_config) {
                if (data.llm_config.provider) state.browser.provider = data.llm_config.provider
                if (data.llm_config.model) state.browser.model = data.llm_config.model
                if (data.llm_config.max_tokens !== undefined) state.browser.tokens = data.llm_config.max_tokens
                if (data.llm_config.temperature !== undefined) state.browser.temp = data.llm_config.temperature

                // Advanced LLM mapped fields
                const copyFields = ['responseLength', 'conversationTone', 'conversationFormality',
                    'conversationPacing', 'contextWindow', 'frequencyPenalty',
                    'presencePenalty', 'toolChoice', 'dynamicVarsEnabled',
                    'dynamicVars', 'mode', 'hallucination_blacklist']
                copyFields.forEach(field => {
                    if (data.llm_config[field] !== undefined) {
                        (state.browser as any)[field] = data.llm_config[field]
                    }
                })
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
            }

            if (data.tools_config && data.tools_config.length > 0) {
                const tc = data.tools_config[0]
                if (tc.tools) state.browser.toolsSchema = JSON.stringify(tc.tools)
                if (tc.tool_server_url !== undefined) state.browser.toolServerUrl = tc.tool_server_url
                if (tc.client_tools_enabled !== undefined) state.browser.clientToolsEnabled = tc.client_tools_enabled
                if (tc.async_execution !== undefined) state.browser.asyncTools = tc.async_execution
                if (tc.tool_timeout_ms !== undefined) state.browser.toolTimeoutMs = tc.tool_timeout_ms
                if (tc.error_message !== undefined) state.browser.toolErrorMsg = tc.error_message
            }
        })
        builder.addCase(fetchAgentConfig.rejected, (state) => {
            state.isLoadingOptions = false
        })
    }
})

export const { updateBrowserConfig, updateTwilioConfigState, updateTelnyxConfigState, setLoadingOptions } = configSlice.actions
export default configSlice.reducer
