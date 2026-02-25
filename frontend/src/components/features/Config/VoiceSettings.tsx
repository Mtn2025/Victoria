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

export const VoiceSettings = () => {
    const dispatch = useAppDispatch()
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

    useEffect(() => {
        if (browser.voiceProvider && activeAgent?.language) {
            dispatch(fetchVoices({ provider: browser.voiceProvider, language: activeAgent.language }))
        }
    }, [dispatch, browser.voiceProvider, activeAgent?.language])

    // Fetch Styles when Voice Changes
    useEffect(() => {
        if (browser.voiceProvider && browser.voiceId) {
            dispatch(fetchStyles({ provider: browser.voiceProvider, voiceId: browser.voiceId }))
        }
    }, [dispatch, browser.voiceProvider, browser.voiceId])

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
                            Configuración Base (Voz & Tono)
                        </span>
                    }
                >
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Fila 1 */}
                        <div>
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Proveedor TTS</label>
                            <Select
                                value={browser.voiceProvider}
                                onChange={(e) => update('voiceProvider', e.target.value)}
                                className="w-full"
                            >
                                {availableTTSProviders.length === 0 && <option value="azure" disabled>Cargando proveedores...</option>}
                                {availableTTSProviders.map(p => (
                                    <option key={p.id} value={p.id}>{p.name}</option>
                                ))}
                            </Select>
                        </div>

                        <div>
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Idioma Heredado</label>
                            <div className="w-full bg-slate-800/80 border border-slate-700/50 rounded-lg px-3 py-2 text-sm text-slate-400 cursor-not-allowed flex items-center gap-2">
                                <span className="text-[12px] bg-slate-700 px-1.5 py-0.5 rounded text-slate-300 border border-slate-600 font-mono flex items-baseline">
                                    {activeAgent?.language || 'es-MX'}
                                </span>
                                Automático
                            </div>
                            <p className="text-[10px] text-slate-500 mt-1.5 flex items-center gap-1">
                                <AlertCircle size={10} className="text-blue-400" />
                                El Agente dicta el idioma general.
                            </p>
                        </div>

                        {/* Fila 2 */}
                        <div>
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Género</label>
                            <Select
                                value={browser.voiceGender}
                                onChange={(e) => update('voiceGender', e.target.value)}
                                disabled={isLoadingOptions || availableVoices.length === 0}
                                className="w-full"
                            >
                                <option value="female">Femenino</option>
                                <option value="male">Masculino</option>
                                {otherVoices.length > 0 && <option value="other">Otros / Sin Categoria</option>}
                            </Select>
                        </div>

                        <div>
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Voz</label>
                            <Select
                                value={browser.voiceId}
                                onChange={(e) => update('voiceId', e.target.value)}
                                disabled={isLoadingOptions || availableVoices.length === 0}
                                className="w-full"
                            >
                                <option value="" disabled>Seleccionar Voz...</option>
                                {availableVoices.length === 0 && <option disabled>Cargando voces...</option>}

                                {filteredVoices.map(v => (
                                    <option key={v.id} value={v.id}>{v.name}</option>
                                ))}
                            </Select>
                        </div>

                        {/* Fila 3 (Estilo Emocional, condicional a si hay estilos) */}
                        {availableStyles.filter(s => s && s.id && s.id.trim() !== '' && s.id !== 'default').length > 0 && (
                            <div className="animate-in fade-in duration-300">
                                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Estilo Emocional</label>
                                <Select
                                    value={browser.voiceStyle}
                                    onChange={(e) => update('voiceStyle', e.target.value)}
                                    className="w-full"
                                >
                                    <option value="">(Default)</option>
                                    {availableStyles.filter(s => s && s.id && s.id.trim() !== '').map(s => (
                                        <option key={s.id} value={s.id}>{s.label}</option>
                                    ))}
                                </Select>
                            </div>
                        )}
                    </div>

                    {/* Sliders Section (Velocidad, Pitch, Volumen) */}
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

                        {/* Volume */}
                        <div>
                            <label className="flex justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                                <span>Volumen</span>
                                <span className="text-emerald-400">{browser.voiceVolume}</span>
                            </label>
                            <input
                                type="range"
                                min="0"
                                max="100"
                                step="1"
                                value={browser.voiceVolume}
                                onChange={(e) => update('voiceVolume', parseInt(e.target.value))}
                                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                            />
                        </div>
                    </div>

                    {/* Style Degree (Conditionally rendered in full width if styles apply) */}
                    {browser.voiceStyle && browser.voiceStyle !== 'default' && browser.voiceStyle !== '' && (
                        <div className="pt-4 border-t border-white/5">
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
                </Accordion>

                {/* HUMANIZACIÓN */}
                <Accordion
                    isOpen={openSection === 'humanization'}
                    onToggle={() => setOpenSection(openSection === 'humanization' ? null : 'humanization')}
                    className="border-pink-500/30 mt-4"
                    headerClassName="hover:bg-pink-900/20"
                    title={
                        <span className="text-sm font-bold text-pink-400 uppercase tracking-wider flex items-center gap-2">
                            <span className="text-lg">🗣️</span> Humanización
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
                                <span className="text-sm font-medium text-white">Inyección de "Muletillas"</span>
                                <span className="text-xs text-slate-400">Agrega "eh...", "hmm..." de forma natural</span>
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
                                <span className="text-sm font-medium text-white">Escucha Activa</span>
                                <span className="text-xs text-slate-400">Dice "ajá", "sí" mientras escuchas</span>
                            </div>
                        </label>
                    </div>
                </Accordion>

                {/* NORMALIZACIÓN DE TEXTO */}
                <div className="pt-4">
                    <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Normalización de Texto</label>
                    <Select
                        value={browser.textNormalizationRule}
                        onChange={(e) => update('textNormalizationRule', e.target.value)}
                        className="w-full"
                    >
                        <option value="default">🤖 Automático (Default)</option>
                        <option value="numbers_to_words">🔢 Convertir Números a Palabras</option>
                        <option value="remove_emojis">🚫 Ignorar Emojis</option>
                        <option value="spell_out">🔤 Deletrear Acrónimos</option>
                    </Select>
                </div>

                {/* AJUSTES TÉCNICOS */}
                <Accordion
                    isOpen={openSection === 'technical'}
                    onToggle={() => setOpenSection(openSection === 'technical' ? null : 'technical')}
                    className="border-slate-500/30 mt-4"
                    headerClassName="hover:bg-slate-800/50"
                    title={
                        <span className="text-sm font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                            <span>⚙️</span> Ajustes Técnicos
                        </span>
                    }
                >
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Latencia / Calidad</label>
                            <Select
                                value={browser.ttsLatencyOptimization || '0'}
                                onChange={(e) => update('ttsLatencyOptimization', parseInt(e.target.value))}
                                className="w-full"
                            >
                                <option value="0">⭐ Calidad Máxima (Default)</option>
                                <option value="1">⚡ Optimizado para Latencia Mínima</option>
                                <option value="2">⚡ Ultra Rápido (Menos Expresividad)</option>
                            </Select>
                            <p className="text-[10px] text-slate-500 mt-1">Afecta calidad de audio vs velocidad de respuesta.</p>
                        </div>

                        <div>
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Formato de Salida</label>
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
                                Ajustes Precisos (ElevenLabs)
                            </span>
                        }
                    >
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pb-2">
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
                    </Accordion>
                )}
            </div>
        </div>
    )
}
