import { useEffect, useState } from 'react'
import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { updateBrowserConfig, fetchLanguages, fetchVoices, fetchStyles } from '@/store/slices/configSlice'
import { Select } from '@/components/ui/Select'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { BrowserConfig } from '@/types/config'
import { Play, AlertCircle, Volume2 } from 'lucide-react'
import { configService } from '@/services/configService'

export const VoiceSettings = () => {
    const dispatch = useAppDispatch()
    const { browser, availableLanguages, availableVoices, availableStyles, isLoadingOptions } = useAppSelector(state => state.config)
    const [previewLoading, setPreviewLoading] = useState(false)

    // Initial Load - Fetch Languages for current Provider
    useEffect(() => {
        if (browser.voiceProvider) {
            dispatch(fetchLanguages(browser.voiceProvider))
        }
    }, [dispatch, browser.voiceProvider])

    // Fetch Voices when Provider or Language Changes
    useEffect(() => {
        if (browser.voiceProvider && browser.voiceLang) {
            dispatch(fetchVoices({ provider: browser.voiceProvider, language: browser.voiceLang }))
        }
    }, [dispatch, browser.voiceProvider, browser.voiceLang])

    // Fetch Styles when Voice Changes
    useEffect(() => {
        if (browser.voiceProvider && browser.voiceId) {
            dispatch(fetchStyles({ provider: browser.voiceProvider, voiceId: browser.voiceId }))
        }
    }, [dispatch, browser.voiceProvider, browser.voiceId])

    const update = (key: keyof BrowserConfig, value: any) => {
        // Cascade Rules for Voice Configuration
        if (key === 'voiceProvider') {
            dispatch(updateBrowserConfig({ voiceProvider: value, voiceLang: '', voiceId: '', voiceStyle: '' }))
        } else if (key === 'voiceLang') {
            dispatch(updateBrowserConfig({ voiceLang: value, voiceId: '', voiceStyle: '' }))
        } else if (key === 'voiceId') {
            dispatch(updateBrowserConfig({ voiceId: value, voiceStyle: '' }))
        } else {
            dispatch(updateBrowserConfig({ [key]: value }))
        }
    }

    // Computed grouping by Gender
    const femaleVoices = availableVoices.filter(v => v.gender === 'female' || v.gender === 'Mujer' || v.gender === 'Female')
    const maleVoices = availableVoices.filter(v => v.gender === 'male' || v.gender === 'Hombre' || v.gender === 'Male')

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
        <div className="space-y-6 animate-fade-in-up">
            {/* Header / Intro */}
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-white flex items-center gap-2">
                    <Volume2 className="w-5 h-5 text-blue-400" />
                    Configuración de Voz (TTS)
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
                    Probar Voz
                </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Provider & Language */}
                <div className="space-y-4">
                    <Select
                        value={browser.voiceProvider}
                        onChange={(e) => update('voiceProvider', e.target.value)}
                        className="w-full"
                    >
                        <option value="azure">Azure Open AI / Speech</option>
                        <option value="elevenlabs">ElevenLabs</option>
                        <option value="openai">OpenAI TTS</option>
                    </Select>

                    <div>
                        <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Idioma</label>
                        <Select
                            value={browser.voiceLang}
                            onChange={(e) => update('voiceLang', e.target.value)}
                            disabled={isLoadingOptions}
                        >
                            {availableLanguages.map(l => (
                                <option key={l.id} value={l.id}>{l.name}</option>
                            ))}
                        </Select>
                    </div>
                </div>

                {/* Voice Selection */}
                <div className="space-y-4">
                    <div>
                        <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Voz</label>
                        <Select
                            value={browser.voiceId}
                            onChange={(e) => update('voiceId', e.target.value)}
                            disabled={isLoadingOptions || availableVoices.length === 0}
                        >
                            <option value="" disabled>Seleccionar Voz...</option>
                            {availableVoices.length === 0 && <option disabled>Cargando voces...</option>}

                            {femaleVoices.length > 0 && (
                                <optgroup label="Femenino">
                                    {femaleVoices.map(v => (
                                        <option key={v.id} value={v.id}>{v.name}</option>
                                    ))}
                                </optgroup>
                            )}

                            {maleVoices.length > 0 && (
                                <optgroup label="Masculino">
                                    {maleVoices.map(v => (
                                        <option key={v.id} value={v.id}>{v.name}</option>
                                    ))}
                                </optgroup>
                            )}

                            {/* Uncategorized (e.g. ElevenLabs fallback) */}
                            {availableVoices.filter(v => v.gender !== 'female' && v.gender !== 'male' && v.gender !== 'Mujer' && v.gender !== 'Hombre' && v.gender !== 'Female' && v.gender !== 'Male').map(v => (
                                <option key={v.id} value={v.id}>{v.name}</option>
                            ))}
                        </Select>
                    </div>

                    {/* Style Selection (Conditional) */}
                    {availableStyles.length > 0 && (
                        <div>
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Estilo Emocional</label>
                            <Select
                                value={browser.voiceStyle}
                                onChange={(e) => update('voiceStyle', e.target.value)}
                            >
                                <option value="">(Default)</option>
                                {availableStyles.map(s => (
                                    <option key={s.id} value={s.id}>{s.label}</option>
                                ))}
                            </Select>
                        </div>
                    )}
                </div>
            </div>

            {/* Sliders Section */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4 border-t border-white/5">
                {/* Speed */}
                <div>
                    <label className="flex justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                        <span>Velocidad</span>
                        <span className="text-blue-400">{browser.voiceSpeed}x</span>
                    </label>
                    <input
                        type="range"
                        min="0.5"
                        max="2.0"
                        step="0.1"
                        value={browser.voiceSpeed}
                        onChange={(e) => update('voiceSpeed', parseFloat(e.target.value))}
                        className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                    />
                </div>

                {/* Pitch */}
                <div>
                    <label className="flex justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                        <span>Tono (Pitch)</span>
                        <span className="text-purple-400">{browser.voicePitch}st</span>
                    </label>
                    <input
                        type="range"
                        min="-12"
                        max="12"
                        step="1"
                        value={browser.voicePitch}
                        onChange={(e) => update('voicePitch', parseInt(e.target.value))}
                        className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-500"
                    />
                </div>

                {/* Style Degree */}
                {browser.voiceStyle && (
                    <div>
                        <label className="flex justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                            <span>Intensidad Estilo</span>
                            <span className="text-pink-400">{browser.voiceStyleDegree}</span>
                        </label>
                        <input
                            type="range"
                            min="0.1"
                            max="2.0"
                            step="0.1"
                            value={browser.voiceStyleDegree}
                            onChange={(e) => update('voiceStyleDegree', parseFloat(e.target.value))}
                            className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-pink-500"
                        />
                    </div>
                )}
            </div>

            {/* Background Sound */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-white/5">
                <div>
                    <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Sonido de Fondo</label>
                    <Select
                        value={browser.voiceBgSound}
                        onChange={(e) => update('voiceBgSound', e.target.value)}
                    >
                        <option value="none">🔇 Silencio</option>
                        <option value="office">🏢 Oficina</option>
                        <option value="cafe">☕ Cafetería</option>
                        <option value="callcenter">📞 Call Center</option>
                        <option value="custom">🔗 URL Personalizada</option>
                    </Select>
                </div>
                {browser.voiceBgSound === 'custom' && (
                    <div>
                        <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">URL Audio</label>
                        <Input
                            value={browser.voiceBgUrl}
                            onChange={(e) => update('voiceBgUrl', e.target.value)}
                            placeholder="https://example.com/audio.mp3"
                        />
                    </div>
                )}
            </div>

            {/* Disclaimer */}
            <div className="flex items-start gap-2 p-3 bg-blue-900/20 border border-blue-500/20 rounded-lg text-xs text-blue-200">
                <AlertCircle className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
                <p>
                    Los cambios se aplican automáticamente a la sesión del simulador. Asegúrate de que el idioma de voz coincida con el idioma de transcripción para evitar alucinaciones.
                </p>
            </div>

            <div className="border-t border-white/5 my-4" />

            {/* ELEVENLABS ADVANCED */}
            {browser.voiceProvider === 'elevenlabs' && (
                <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2">
                    <h3 className="text-sm font-bold text-green-400 uppercase tracking-wider flex items-center gap-2">
                        🧪 ElevenLabs Avanzado
                    </h3>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <label className="flex justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider">
                                <span>Estabilidad</span>
                                <span className="text-green-400">{browser.voiceStability}</span>
                            </label>
                            <input
                                type="range"
                                aria-label="Estabilidad"
                                min="0" max="1" step="0.05"
                                value={browser.voiceStability}
                                onChange={(e) => update('voiceStability', parseFloat(e.target.value))}
                                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-green-500"
                            />
                            <p className="text-[10px] text-slate-500">Más bajo = Más emotivo/varía.</p>
                        </div>

                        <div className="space-y-2">
                            <label className="flex justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider">
                                <span>Similitud / Claridad</span>
                                <span className="text-green-400">{browser.voiceSimilarityBoost}</span>
                            </label>
                            <input
                                type="range"
                                min="0" max="1" step="0.05"
                                value={browser.voiceSimilarityBoost}
                                onChange={(e) => update('voiceSimilarityBoost', parseFloat(e.target.value))}
                                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-green-500"
                            />
                            <p className="text-[10px] text-slate-500">Más alto = Más fiel a la voz original.</p>
                        </div>

                        <div className="space-y-2">
                            <label className="flex justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider">
                                <span>Exageración Estilo</span>
                                <span className="text-green-400">{browser.voiceStyleExaggeration}</span>
                            </label>
                            <input
                                type="range"
                                min="0" max="1" step="0.05"
                                value={browser.voiceStyleExaggeration}
                                onChange={(e) => update('voiceStyleExaggeration', parseFloat(e.target.value))}
                                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-green-500"
                            />
                        </div>

                        <div className="space-y-2 flex flex-col justify-center">
                            <label className="flex items-center space-x-2 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={browser.voiceSpeakerBoost}
                                    onChange={(e) => update('voiceSpeakerBoost', e.target.checked)}
                                    className="w-4 h-4 rounded bg-slate-700 border-slate-600 text-green-500"
                                />
                                <span className="text-xs text-slate-300">Boost Speaker (Mejor Calidad)</span>
                            </label>
                            <label className="flex items-center space-x-2 cursor-pointer mt-2">
                                <input
                                    type="checkbox"
                                    checked={browser.voiceMultilingual}
                                    onChange={(e) => update('voiceMultilingual', e.target.checked)}
                                    className="w-4 h-4 rounded bg-slate-700 border-slate-600 text-green-500"
                                />
                                <span className="text-xs text-slate-300">Modo Multilingüe (v2)</span>
                            </label>
                        </div>
                    </div>
                </div>
            )}

            <div className="border-t border-white/5 my-4" />

            {/* HUMANIZATION */}
            <div className="space-y-4">
                <h3 className="text-sm font-bold text-pink-400 uppercase tracking-wider flex items-center gap-2">
                    🗣️ Humanización
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <label className="flex items-center space-x-3 cursor-pointer p-3 bg-slate-800/50 rounded-lg border border-slate-700 hover:border-pink-500/50 transition-colors">
                        <input
                            type="checkbox"
                            checked={browser.voiceFillerInjection}
                            onChange={(e) => update('voiceFillerInjection', e.target.checked)}
                            className="w-4 h-4 rounded bg-slate-700 border-slate-600 text-pink-500"
                        />
                        <div className="flex flex-col">
                            <span className="text-xs font-semibold text-slate-200">Inyección de "Muletillas"</span>
                            <span className="text-[10px] text-slate-500">Agrega "eh...", "hmm..." natural</span>
                        </div>
                    </label>

                    <label className="flex items-center space-x-3 cursor-pointer p-3 bg-slate-800/50 rounded-lg border border-slate-700 hover:border-pink-500/50 transition-colors">
                        <input
                            type="checkbox"
                            checked={browser.voiceBackchanneling}
                            onChange={(e) => update('voiceBackchanneling', e.target.checked)}
                            className="w-4 h-4 rounded bg-slate-700 border-slate-600 text-pink-500"
                        />
                        <div className="flex flex-col">
                            <span className="text-xs font-semibold text-slate-200">Escucha Activa</span>
                            <span className="text-[10px] text-slate-500">Dice "ajá", "sí" mientras escuchas</span>
                        </div>
                    </label>
                </div>

                <div>
                    <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Normalización de Texto</label>
                    <Select
                        value={browser.textNormalizationRule}
                        onChange={(e) => update('textNormalizationRule', e.target.value)}
                    >
                        <option value="auto">🤖 Automático (Default)</option>
                        <option value="verbal">🗣️ Verbalizado ("123" -&gt; "ciento veintitrés")</option>
                    </Select>
                </div>
            </div>

            <div className="border-t border-white/5 my-4" />

            {/* TECH SETTINGS */}
            <div className="space-y-4">
                <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
                    ⚙️ Ajustes Técnicos
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Latencia / Calidad</label>
                        <Select
                            value={browser.ttsLatencyOptimization}
                            onChange={(e) => update('ttsLatencyOptimization', parseInt(e.target.value))}
                        >
                            <option value="0">⭐ Calidad Máxima (Default)</option>
                            <option value="1">🚀 Latencia Baja (Normal)</option>
                            <option value="2">⚡ Latencia Ultra Baja</option>
                            <option value="3">🔥 Modo Turbo (Menor Calidad)</option>
                        </Select>
                    </div>
                    <div>
                        <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Formato de Salida</label>
                        <Select
                            value={browser.ttsOutputFormat}
                            onChange={(e) => update('ttsOutputFormat', e.target.value)}
                        >
                            <option value="pcm_16000">PCM 16kHz (WAV)</option>
                            <option value="pcm_8000">PCM 8kHz (Teléfono)</option>
                            <option value="mp3_44100_128">MP3 44.1kHz 128kbps</option>
                            <option value="ulaw_8000">Mu-Law 8kHz (Telephony)</option>
                        </Select>
                    </div>
                </div>
            </div>
        </div>
    )
}
