// Domain Interfaces
export interface Voice {
    id: string
    name: string
    gender: string
    locale: string
    styles?: string[]
}

export interface Language {
    id: string
    name: string
}

export interface VoiceStyle {
    id: string
    label: string
}

export interface BrowserConfig {
    // LLM
    provider: string
    model: string
    temp: number
    tokens: number
    msg: string
    mode: 'markdown' | 'text'
    prompt: string

    // Conversation Style
    responseLength: string
    conversationTone: string
    conversationFormality: string
    conversationPacing: string

    // Advanced AI
    contextWindow: number
    frequencyPenalty: number
    presencePenalty: number
    toolChoice: string
    dynamicVarsEnabled: boolean
    dynamicVars: string

    // Voice / TTS
    voiceProvider: string
    voiceLang: string
    voiceId: string
    voiceStyle: string
    voiceSpeed: number
    voicePitch: number
    voiceVolume: number
    voiceStyleDegree: number
    voiceBgSound: string
    voiceBgUrl: string

    // Advanced TTS
    voiceStability: number
    voiceSimilarityBoost: number
    voiceStyleExaggeration: number
    voiceSpeakerBoost: boolean
    voiceMultilingual: boolean
    ttsLatencyOptimization: number
    ttsOutputFormat: string
    voiceFillerInjection: boolean
    voiceBackchanneling: boolean
    textNormalizationRule: string

    // STT / Transcriber
    sttProvider: string
    sttLang: string
    sttModel: string
    sttKeywords: string
    interruption_threshold: number
    hallucination_blacklist: string
    sttSilenceTimeout: number
    sttUtteranceEnd: 'default' | 'semantic'
    vad_threshold: number
    interruptRMS: number

    // STT Booleans
    sttPunctuation: boolean
    sttSmartFormatting: boolean
    sttProfanityFilter: boolean
    sttDiarization: boolean
    sttMultilingual: boolean

    // Advanced / Quality
    noiseSuppressionLevel: string // 'off' | 'balanced' | 'high'
    audioCodec: string // 'PCMU' | 'PCMA' | 'OPUS'
    enableBackchannel: boolean
    maxDuration: number
    maxRetries: number
    idleMessage: string

    // Campaigns / Integrations
    crmEnabled: boolean
    webhookUrl: string
    webhookSecret: string

    // System / Governance
    concurrencyLimit: number
    spendLimitDaily: number
    environment: 'development' | 'staging' | 'production'
    privacyMode: boolean
    auditLogEnabled: boolean

    // Analysis & Data
    analysisPrompt: string
    successRubric: string
    sentimentAnalysis: boolean
    costTrackingEnabled: boolean
    extractionSchema: string
    piiRedactionEnabled: boolean
    logWebhookUrl: string
    retentionDays: number

    // Flow & Orchestration
    bargeInEnabled: boolean
    interruptionSensitivity: number
    interruptionPhrases: string
    voicemailDetectionEnabled: boolean
    voicemailMessage: string
    machineDetectionSensitivity: number
    responseDelaySeconds: number
    waitForGreeting: boolean
    hyphenationEnabled: boolean
    endCallPhrases: string

    // Tools
    toolsSchema: string
    asyncTools: boolean
    clientToolsEnabled: boolean
    toolServerUrl: string
    toolServerSecret: string
    toolTimeoutMs: number
    toolRetryCount: number
    toolErrorMsg: string
    redactParams: string
    transferWhitelist: string
    stateInjectionEnabled: boolean
}

export interface TwilioConfig {
    // Credentials
    twilioAccountSid: string
    twilioAuthToken: string
    twilioFromNumber: string

    // SIP Trunking
    sipTrunkUriPhone: string
    sipAuthUserPhone: string
    sipAuthPassPhone: string
    fallbackNumberPhone: string
    geoRegionPhone: 'us-east-1' | 'us-west-1' | 'eu-west-1'

    // Recording
    recordingChannelsPhone: 'mono' | 'dual'
    recordingEnabledPhone: boolean

    // Compliance
    hipaaEnabledPhone: boolean
    dtmfListeningEnabledPhone: boolean

    // Campaigns / Integrations
    crmEnabled: boolean
    webhookUrl: string
    webhookSecret: string

    // System / Governance
    concurrencyLimit: number
    spendLimitDaily: number
    environment: 'development' | 'staging' | 'production'
    privacyMode: boolean
    auditLogEnabled: boolean


    // Tools
    toolsSchema: string
    asyncTools: boolean
    clientToolsEnabled: boolean
    toolServerUrl: string
    toolServerSecret: string
    toolTimeoutMs: number
    toolRetryCount: number
    toolErrorMsg: string
    redactParams: string
    transferWhitelist: string
    stateInjectionEnabled: boolean
}

export interface TelnyxConfig {
    // Credentials
    telnyxApiKey: string
    telnyxConnectionId: string
    callerIdTelnyx: string

    // SIP Trunking
    sipTrunkUriTelnyx: string
    sipAuthUserTelnyx: string
    sipAuthPassTelnyx: string
    fallbackNumberTelnyx: string
    geoRegionTelnyx: 'us-central' | 'us-east' | 'global'

    // Recording
    recordingChannelsTelnyx: 'mono' | 'dual'
    enableRecordingTelnyx: boolean

    // Compliance
    hipaaEnabledTelnyx: boolean
    dtmfListeningEnabledTelnyx: boolean

    // Advanced
    amdConfig: 'disabled' | 'detect' | 'detect_hangup' | 'detect_message_end'
    interruptRMS: number // Duplicate of BrowserConfig but used here too

    // Campaigns / Integrations
    crmEnabled: boolean
    webhookUrl: string
    webhookSecret: string

    // System / Governance
    concurrencyLimit: number
    spendLimitDaily: number
    environment: 'development' | 'staging' | 'production'
    privacyMode: boolean
    auditLogEnabled: boolean


    // Tools
    toolsSchema: string
    asyncTools: boolean
    clientToolsEnabled: boolean
    toolServerUrl: string
    toolServerSecret: string
    toolTimeoutMs: number
    toolRetryCount: number
    toolErrorMsg: string
    redactParams: string
    transferWhitelist: string
    stateInjectionEnabled: boolean
}

export interface ConfigState {
    browser: BrowserConfig
    twilio: TwilioConfig
    telnyx: TelnyxConfig

    // Catalogs
    availableLanguages: Language[]
    availableVoices: Voice[]
    availableStyles: VoiceStyle[]

    // UI State
    isLoadingOptions: boolean
}
