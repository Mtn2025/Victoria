import { useEffect, useState } from 'react'
import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { updateBrowserConfig, fetchLanguages, fetchVoices, fetchStyles, fetchTTSProviders } from '@/store/slices/configSlice'
import { Select } from '@/components/ui/Select'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { BrowserConfig } from '@/types/config'
import { Accordion } from '@/components/ui/Accordion'
import { Play, AlertCircle, Volume2, Sparkles } from 'lucide-react'
import { configService } from '@/services/configService'
import { useTranslation } from '@/i18n/I18nContext'

export const VoiceSettings = () => {
    const dispatch = useAppDispatch()
    const { t } = useTranslation()
    const { browser, availableVoices, availableStyles, availableTTSProviders, isLoadingOptions } = useAppSelector(state => state.config)
    const [previewLoading, setPreviewLoading] = useState(false)
    const [openSection, setOpenSection] = useState<string | null>('core')

    // Initial Load - Fetch TTS Providers
    useEffect(() => {
        if (availableTTSProviders.length === 0) {
            dispatch(fetchTTSProviders())
        }
    }, [dispatch, availableTTSProviders.length])

    // Initial Load - Fetch Languages for current Provider
    useEffect(() => {
        if (browser.voiceProvider) {
            dispatch(fetchLanguages(browser.voiceProvider))
        }
    }, [dispatch, browser.voiceProvider])

    // Fetch Voices when Provider changes (Language is fixed to Agent's Base Language)
    const { activeAgent } = useAppSelector(state => state.agents)
    const isTelnyx = activeAgent?.provider === 'telnyx'

    useEffect(() => {
        if (browser.voiceProvider && activeAgent?.language) {
            dispatch(fetchVoices({ provider: browser.voiceProvider, language: activeAgent.language }))
        }
    }, [dispatch, browser.voiceProvider, activeAgent?.language])

    // Lock TTS format for Telnyx
    useEffect(() => {
        if (isTelnyx && browser.ttsOutputFormat !== 'pcm_8khz') {
            dispatch(updateBrowserConfig({ ttsOutputFormat: 'pcm_8khz' }))
        }
    }, [isTelnyx, browser.ttsOutputFormat, dispatch])

    // Fetch Styles when Voice Changes
    useEffect(() => {
        if (browser.voiceProvider && browser.voiceId) {
            dispatch(fetchStyles({ provider: browser.voiceProvider, voiceId: browser.voiceId }))
        }
    }, [dispatch, browser.voiceProvider, browser.voiceId])

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const update = (key: keyof BrowserConfig, value: any) => {
        // Cascade Rules for Voice Configuration
        if (key === 'voiceProvider') {
            dispatch(updateBrowserConfig({ voiceProvider: value, voiceId: '', voiceStyle: '' }))
        } else if (key === 'voiceGender') {
            dispatch(updateBrowserConfig({ voiceGender: value, voiceId: '', voiceStyle: '' }))
        } else if (key === 'voiceId') {
            dispatch(updateBrowserConfig({ voiceId: value, voiceStyle: '' }))
        } else {
            dispatch(updateBrowserConfig({ [key]: value }))
        }
    }

    // Computed grouping by Gender
    const femaleVoices = availableVoices.filter(v => v.gender === 'female' || v.gender === 'Mujer' || v.gender === 'Female')
    const maleVoices = availableVoices.filter(v => v.gender === 'male' || v.gender === 'Hombre' || v.gender === 'Male')
    const otherVoices = availableVoices.filter(v => v.gender !== 'female' && v.gender !== 'male' && v.gender !== 'Mujer' && v.gender !== 'Hombre' && v.gender !== 'Female' && v.gender !== 'Male')

    let filteredVoices = availableVoices
    if (browser.voiceGender === 'female') {
        filteredVoices = femaleVoices
    } else if (browser.voiceGender === 'male') {
        filteredVoices = maleVoices
    } else if (browser.voiceGender === 'other') {
        filteredVoices = otherVoices
    }

    const handlePreview = async () => {
        setPreviewLoading(true)
        try {
            const blob = await configService.previewVoice({
                voice_name: browser.voiceId,
                voice_speed: browser.voiceSpeed,
                voice_pitch: browser.voicePitch,
                voice_volume: browser.voiceVolume,
                voice_style: browser.voiceStyle,
                voice_style_degree: browser.voiceStyleDegree,
                provider: browser.voiceProvider
            })

            const url = URL.createObjectURL(blob as Blob)
            const audio = new Audio(url)
            audio.play()
            audio.onended = () => URL.revokeObjectURL(url)
        } catch (error) {
            console.error('Preview failed', error)
        } finally {
            setPreviewLoading(false)
        }
    }

    return (
        <div className="space-y-6 animate-fade-in-up pb-10">
            {/* Header / Intro */}
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-white flex items-center gap-2">
                    <Volume2 className="w-5 h-5 text-blue-400" />
                    {t('voice.title')}
                </h3>
                <Button
                    size="sm"
                    variant="outline"
                    onClick={handlePreview}
                    disabled={previewLoading || !browser.voiceId}
                    isLoading={previewLoading}
                    className="border-blue-500/30 text-blue-400 hover:bg-blue-500/10"
                >
                    <Play className="w-4 h-4 mr-2" />
                    {previewLoading ? t('voice.previewing') : t('voice.test_voice')}
                </Button>
            </div>

            {/* Main Content Areas inside Accordions */}
            <div className="space-y-3">
                {/* Core Config */}
                <Accordion
                    isOpen={openSection === 'core'}
                    onToggle={() => setOpenSection(openSection === 'core' ? null : 'core')}
                    className="border-blue-500/30"
                    headerClassName="hover:bg-blue-900/20"
                    title={
                        <span className="text-sm font-bold text-blue-400 uppercase tracking-wider flex items-center gap-2">
                            <Volume2 className="w-4 h-4" />
                            {t('voice.core_title')}
                        </span>
                    }
                >
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-2">
                        {/* Fila 1 */}
                        <div className="space-y-2">
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">{t('voice.provider_label')}</label>
                            <Select
                                value={browser.voiceProvider}
                                onChange={(e) => update('voiceProvider', e.target.value)}
                                className="w-full"
                            >
                                {availableTTSProviders.length === 0 && <option value="azure" disabled>{t('voice.provider_loading')}</option>}
                                {availableTTSProviders.map(p => (
                                    <option key={p.id} value={p.id}>{p.name}</option>
                                ))}
                            </Select>
                        </div>

                        <div className="space-y-2">
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">{t('voice.language_label')}</label>
                            <div className="w-full bg-slate-800/80 border border-slate-700/50 rounded-lg px-3 py-2 text-sm text-slate-400 cursor-not-allowed flex items-center gap-2">
                                <span className="text-[12px] bg-slate-700 px-1.5 py-0.5 rounded text-slate-300 border border-slate-600 font-mono flex items-baseline">
                                    {activeAgent?.language || 'es-MX'}
                                </span>
                                {t('voice.language_auto')}
                            </div>
                            <p className="text-[10px] text-slate-500 flex items-center gap-1">
                                <AlertCircle size={10} className="text-blue-400" />
                                {t('voice.language_desc')}
                            </p>
                        </div>

                        {/* Fila 2 */}
                        <div className="space-y-2">
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">{t('voice.gender_label')}</label>
                            <Select
                                value={browser.voiceGender}
                                onChange={(e) => update('voiceGender', e.target.value)}
                                disabled={isLoadingOptions || availableVoices.length === 0}
                                className="w-full"
                            >
                                <option value="female">{t('voice.gender_female')}</option>
                                <option value="male">{t('voice.gender_male')}</option>
                                {otherVoices.length > 0 && <option value="other">{t('voice.gender_other')}</option>}
                            </Select>
                        </div>

                        <div className="space-y-2">
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">{t('voice.voice_label')}</label>
                            <Select
                                value={browser.voiceId}
                                onChange={(e) => update('voiceId', e.target.value)}
                                disabled={isLoadingOptions || availableVoices.length === 0}
                                className="w-full"
                            >
                                <option value="" disabled>{t('voice.voice_placeholder')}</option>
                                {availableVoices.length === 0 && <option disabled>{t('voice.voice_loading')}</option>}

                                {filteredVoices.map(v => (
                                    <option key={v.id} value={v.id}>{v.name}</option>
                                ))}
                            </Select>
                        </div>

                        {/* Fila 3 (Estilo Emocional) */}
                        {availableStyles.filter(s => s && s.id && s.id.trim() !== '' && s.id !== 'default').length > 0 && (
                            <div className="space-y-2 animate-in fade-in duration-300">
                                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">{t('voice.style_label')}</label>
                                <Select
                                    value={browser.voiceStyle}
                                    onChange={(e) => update('voiceStyle', e.target.value)}
                                    className="w-full"
                                >
                                    <option value="">{t('voice.style_default')}</option>
                                    {availableStyles.filter(s => s && s.id && s.id.trim() !== '').map(s => (
                                        <option key={s.id} value={s.id}>{s.label}</option>
                                    ))}
                                </Select>
                            </div>
                        )}
                    </div>

                    {/* Sliders Area */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-white/5 pb-2">
                        {/* Speed */}
                        <div className="space-y-2">
                            <div className="flex justify-between items-center mb-1">
                                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{t('voice.speed_label')}</label>
                                <span className="text-sm font-bold text-blue-400">{browser.voiceSpeed}x</span>
                            </div>
                            <div className="flex items-center gap-3">
                                <span className="text-xs text-slate-500 font-mono">0.5</span>
                                <input
                                    type="range"
                                    min="0.5" max="2.0" step="0.1"
                                    value={browser.voiceSpeed}
                                    onChange={(e) => update('voiceSpeed', parseFloat(e.target.value))}
                                    className="flex-1 h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                                />
                                <span className="text-xs text-slate-500 font-mono">2.0</span>
                            </div>
                            <p className="text-[10px] text-slate-500">{t('voice.speed_desc')}</p>
                        </div>

                        {/* Pitch */}
                        <div className="space-y-2">
                            <div className="flex justify-between items-center mb-1">
                                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{t('voice.pitch_label')}</label>
                                <span className="text-sm font-bold text-purple-400">{browser.voicePitch}</span>
                            </div>
                            <div className="flex items-center gap-3">
                                <span className="text-xs text-slate-500 font-mono">-12</span>
                                <input
                                    type="range"
                                    min="-12" max="12" step="1"
                                    value={browser.voicePitch}
                                    onChange={(e) => update('voicePitch', parseInt(e.target.value))}
                                    className="flex-1 h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-500"
                                />
                                <span className="text-xs text-slate-500 font-mono">+12</span>
                            </div>
                            <p className="text-[10px] text-slate-500">{t('voice.pitch_desc')}</p>
                        </div>

                        {/* Volume */}
                        <div className="space-y-2">
                            <div className="flex justify-between items-center mb-1">
                                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{t('voice.volume_label')}</label>
                                <span className="text-sm font-bold text-emerald-400">{browser.voiceVolume}</span>
                            </div>
                            <div className="flex items-center gap-3">
                                <span className="text-xs text-slate-500 font-mono">0</span>
                                <input
                                    type="range"
                                    min="0" max="100" step="1"
                                    value={browser.voiceVolume}
                                    onChange={(e) => update('voiceVolume', parseInt(e.target.value))}
                                    className="flex-1 h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                                />
                                <span className="text-xs text-slate-500 font-mono">100</span>
                            </div>
                            <p className="text-[10px] text-slate-500">{t('voice.volume_desc')}</p>
                        </div>
                    </div>

                    {/* Style Degree (Conditionally rendered) */}
                    {browser.voiceStyle && browser.voiceStyle !== 'default' && browser.voiceStyle !== '' && (
                        <div className="pt-4 border-t border-white/5 space-y-2">
                            <div className="flex justify-between items-center mb-1">
                                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{t('voice.style_intensity_label')}</label>
                                <span className="text-sm font-bold text-pink-400">{browser.voiceStyleDegree}</span>
                            </div>
                            <div className="flex items-center gap-3">
                                <span className="text-xs text-slate-500 font-mono">0.1</span>
                                <input
                                    type="range"
                                    min="0.1" max="2.0" step="0.1"
                                    value={browser.voiceStyleDegree}
                                    onChange={(e) => update('voiceStyleDegree', parseFloat(e.target.value))}
                                    className="flex-1 h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-pink-500"
                                />
                                <span className="text-xs text-slate-500 font-mono">2.0</span>
                            </div>
                        </div>
                    )}

                    {/* Background Sound */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-white/5">
                        <div className="space-y-2">
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">{t('voice.bg_sound_label')}</label>
                            <Select
                                value={browser.voiceBgSound}
                                onChange={(e) => update('voiceBgSound', e.target.value)}
                            >
                                <option value="none">{t('voice.bg_none')}</option>
                                <option value="office">{t('voice.bg_office')}</option>
                                <option value="cafe">{t('voice.bg_cafe')}</option>
                                <option value="callcenter">{t('voice.bg_callcenter')}</option>
                                <option value="custom">{t('voice.bg_custom')}</option>
                            </Select>
                        </div>
                        {browser.voiceBgSound === 'custom' && (
                            <div className="space-y-2">
                                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">{t('voice.bg_url_label')}</label>
                                <Input
                                    value={browser.voiceBgUrl}
                                    onChange={(e) => update('voiceBgUrl', e.target.value)}
                                    placeholder={t('voice.bg_url_placeholder')}
                                />
                            </div>
                        )}
                    </div>
                </Accordion>

                {/* HUMANIZACIÓN */}
                <Accordion
                    isOpen={openSection === 'humanization'}
                    onToggle={() => setOpenSection(openSection === 'humanization' ? null : 'humanization')}
                    className="border-pink-500/30 mt-4"
                    headerClassName="hover:bg-pink-900/20"
                    title={
                        <span className="text-sm font-bold text-pink-400 uppercase tracking-wider flex items-center gap-2">
                            {t('voice.humanization_title')}
                        </span>
                    }
                >
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <label className={`relative flex items-start p-4 cursor-pointer rounded-lg border-2 transition-all duration-200 ${browser.voiceFillerInjection ? 'border-pink-500 bg-pink-500/10' : 'border-slate-700 bg-slate-800/50 hover:border-slate-600'}`}>
                            <div className="flex items-center h-5">
                                <input
                                    type="checkbox"
                                    className="w-4 h-4 rounded bg-slate-900 border-slate-600 text-pink-500 focus:ring-0 focus:ring-offset-0 disabled:opacity-50"
                                    checked={browser.voiceFillerInjection}
                                    onChange={(e) => update('voiceFillerInjection', e.target.checked)}
                                />
                            </div>
                            <div className="ml-3 flex flex-col">
                                <span className="text-sm font-medium text-white">{t('voice.filler_label')}</span>
                                <span className="text-[10px] text-slate-400 mt-1">{t('voice.filler_desc')}</span>
                            </div>
                        </label>

                        <label className={`relative flex items-start p-4 cursor-pointer rounded-lg border-2 transition-all duration-200 ${browser.voiceBackchanneling ? 'border-pink-500 bg-pink-500/10' : 'border-slate-700 bg-slate-800/50 hover:border-slate-600'}`}>
                            <div className="flex items-center h-5">
                                <input
                                    type="checkbox"
                                    className="w-4 h-4 rounded bg-slate-900 border-slate-600 text-pink-500 focus:ring-0 focus:ring-offset-0 disabled:opacity-50"
                                    checked={browser.voiceBackchanneling}
                                    onChange={(e) => update('voiceBackchanneling', e.target.checked)}
                                />
                            </div>
                            <div className="ml-3 flex flex-col">
                                <span className="text-sm font-medium text-white">{t('voice.active_listen_label')}</span>
                                <span className="text-[10px] text-slate-400 mt-1">{t('voice.active_listen_desc')}</span>
                            </div>
                        </label>
                    </div>
                </Accordion>

                {/* NORMALIZACIÓN DE TEXTO */}
                <Accordion
                    isOpen={openSection === 'normalization'}
                    onToggle={() => setOpenSection(openSection === 'normalization' ? null : 'normalization')}
                    className="border-indigo-500/30 mt-4"
                    headerClassName="hover:bg-indigo-900/20"
                    title={
                        <span className="text-sm font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-2">
                            {t('voice.normalization_title')}
                        </span>
                    }
                >
                    <div className="pt-2">
                        <Select
                            value={browser.textNormalizationRule || 'default'}
                            onChange={(e) => update('textNormalizationRule', e.target.value)}
                            className="w-full"
                        >
                            <option value="default">{t('voice.norm_default')}</option>
                            <option value="numbers_to_words">{t('voice.norm_numbers')}</option>
                            <option value="remove_emojis">{t('voice.norm_emojis')}</option>
                            <option value="spell_out">{t('voice.norm_spell')}</option>
                        </Select>
                        <p className="text-[10px] text-slate-500 mt-2">{t('voice.norm_desc')}</p>
                    </div>
                </Accordion>

                {/* AJUSTES TÉCNICOS */}
                <Accordion
                    isOpen={openSection === 'technical'}
                    onToggle={() => setOpenSection(openSection === 'technical' ? null : 'technical')}
                    className="border-slate-500/30 mt-4"
                    headerClassName="hover:bg-slate-800/50"
                    title={
                        <span className="text-sm font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                            {t('voice.tech_title')}
                        </span>
                    }
                >
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">{t('voice.latency_label')}</label>
                            <Select
                                value={browser.ttsLatencyOptimization || '0'}
                                onChange={(e) => update('ttsLatencyOptimization', parseInt(e.target.value))}
                                className="w-full"
                            >
                                <option value="0">{t('voice.latency_0')}</option>
                                <option value="1">{t('voice.latency_1')}</option>
                                <option value="2">{t('voice.latency_2')}</option>
                            </Select>
                            <p className="text-[10px] text-slate-500">{t('voice.latency_desc')}</p>
                        </div>

                        <div className="space-y-2">
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">{t('voice.format_label')}</label>
                            {isTelnyx ? (
                                <div>
                                    <div className="w-full bg-slate-800/80 border border-slate-700/50 rounded-lg px-3 py-2 text-sm text-slate-400 cursor-not-allowed">
                                        PCM 8kHz (Telefónico)
                                    </div>
                                    <p className="text-[10px] text-amber-500 mt-1 flex items-center gap-1">
                                        <AlertCircle size={10} />
                                        Fijo por estándar de red Telnyx
                                    </p>
                                </div>
                            ) : (
                                <Select
                                    value={browser.ttsOutputFormat || 'pcm_16khz'}
                                    onChange={(e) => update('ttsOutputFormat', e.target.value)}
                                    className="w-full"
                                >
                                    <option value="pcm_16khz">PCM 16kHz (WAV)</option>
                                    <option value="pcm_24khz">PCM 24kHz</option>
                                    <option value="pcm_8khz">PCM 8kHz (Telefónico)</option>
                                    <option value="mp3">MP3</option>
                                </Select>
                            )}
                        </div>
                    </div>
                </Accordion>

                {/* ELEVENLABS ADVANCED */}
                {browser.voiceProvider === 'elevenlabs' && availableTTSProviders.some(p => p.id === 'elevenlabs') && (
                    <Accordion
                        isOpen={openSection === 'elevenlabs'}
                        onToggle={() => setOpenSection(openSection === 'elevenlabs' ? null : 'elevenlabs')}
                        className="border-green-500/30"
                        headerClassName="hover:bg-green-900/20"
                        title={
                            <span className="text-sm font-bold text-green-400 uppercase tracking-wider flex items-center gap-2">
                                <Sparkles className="w-4 h-4" />
                                {t('voice.adv_title')}
                            </span>
                        }
                    >
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-2">
                            <div className="space-y-2">
                                <div className="flex justify-between items-center mb-1">
                                    <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{t('voice.stability_label')}</label>
                                    <span className="text-sm font-bold text-green-400">{browser.voiceStability}</span>
                                </div>
                                <div className="flex items-center gap-3">
                                    <span className="text-xs text-slate-500 font-mono">0.0</span>
                                    <input
                                        type="range"
                                        min="0" max="1" step="0.05"
                                        value={browser.voiceStability}
                                        onChange={(e) => update('voiceStability', parseFloat(e.target.value))}
                                        className="flex-1 h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-green-500"
                                    />
                                    <span className="text-xs text-slate-500 font-mono">1.0</span>
                                </div>
                                <p className="text-[10px] text-slate-500">{t('voice.stability_desc')}</p>
                            </div>

                            <div className="space-y-2">
                                <div className="flex justify-between items-center mb-1">
                                    <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{t('voice.similarity_label')}</label>
                                    <span className="text-sm font-bold text-green-400">{browser.voiceSimilarityBoost}</span>
                                </div>
                                <div className="flex items-center gap-3">
                                    <span className="text-xs text-slate-500 font-mono">0.0</span>
                                    <input
                                        type="range"
                                        min="0" max="1" step="0.05"
                                        value={browser.voiceSimilarityBoost}
                                        onChange={(e) => update('voiceSimilarityBoost', parseFloat(e.target.value))}
                                        className="flex-1 h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-green-500"
                                    />
                                    <span className="text-xs text-slate-500 font-mono">1.0</span>
                                </div>
                                <p className="text-[10px] text-slate-500">{t('voice.similarity_desc')}</p>
                            </div>

                            <div className="space-y-2">
                                <div className="flex justify-between items-center mb-1">
                                    <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{t('voice.exaggeration_label')}</label>
                                    <span className="text-sm font-bold text-green-400">{browser.voiceStyleExaggeration}</span>
                                </div>
                                <div className="flex items-center gap-3">
                                    <span className="text-xs text-slate-500 font-mono">0.0</span>
                                    <input
                                        type="range"
                                        min="0" max="1" step="0.05"
                                        value={browser.voiceStyleExaggeration}
                                        onChange={(e) => update('voiceStyleExaggeration', parseFloat(e.target.value))}
                                        className="flex-1 h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-green-500"
                                    />
                                    <span className="text-xs text-slate-500 font-mono">1.0</span>
                                </div>
                            </div>

                            <div className="space-y-2 flex flex-col justify-center">
                                <label className="flex items-center space-x-2 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={browser.voiceSpeakerBoost}
                                        onChange={(e) => update('voiceSpeakerBoost', e.target.checked)}
                                        className="w-4 h-4 rounded bg-slate-700 border-slate-600 text-green-500"
                                    />
                                    <span className="text-sm font-medium text-slate-300">{t('voice.speaker_boost_label')}</span>
                                </label>
                                <label className="flex items-center space-x-2 cursor-pointer mt-2">
                                    <input
                                        type="checkbox"
                                        checked={browser.voiceMultilingual}
                                        onChange={(e) => update('voiceMultilingual', e.target.checked)}
                                        className="w-4 h-4 rounded bg-slate-700 border-slate-600 text-green-500"
                                    />
                                    <span className="text-sm font-medium text-slate-300">{t('voice.multilingual_label')}</span>
                                </label>
                            </div>
                        </div>
                    </Accordion>
                )}
            </div>
        </div>
    )
}
