import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { updateBrowserConfig } from '@/store/slices/configSlice'
import { Select } from '@/components/ui/Select'
import { BrowserConfig } from '@/types/config'
import { Ear, Radio } from 'lucide-react'

export const TranscriberSettings = () => {
    const dispatch = useAppDispatch()
    // Use browser config and availableLanguages from store
    const { browser, availableLanguages } = useAppSelector(state => state.config)

    const update = (key: keyof BrowserConfig, value: any) => {
        dispatch(updateBrowserConfig({ [key]: value }))
    }

    return (
        <div className="space-y-6 animate-fade-in-up">
            {/* Header */}
            <h3 className="text-lg font-medium text-white flex items-center gap-2">
                <Ear className="w-5 h-5 text-emerald-400" />
                Configuración de Transcripción (STT)
            </h3>

            {/* Provider & Model */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                    <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Proveedor STT</label>
                    <Select
                        aria-label="Proveedor STT"
                        value={browser.sttProvider}
                        onChange={(e) => update('sttProvider', e.target.value)}
                    >
                        <option value="azure">Azure Speech</option>
                        <option value="deepgram">Deepgram</option>
                        <option value="groq">Groq Whisper</option>
                    </Select>
                </div>

                <div className="space-y-4">
                    <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Modelo</label>
                    <Select
                        aria-label="Modelo"
                        value={browser.sttModel}
                        onChange={(e) => update('sttModel', e.target.value)}
                    >
                        <option value="nova-2">Nova-2 (Fastest)</option>
                        <option value="enhanced">Enhanced (Azure)</option>
                        <option value="whisper-large">Whisper Large</option>
                    </Select>
                </div>
            </div>

            {/* Language & Keywords */}
            <div className="space-y-4">
                <div>
                    <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Idioma</label>
                    <Select
                        value={browser.sttLang}
                        onChange={(e) => update('sttLang', e.target.value)}
                    >
                        {availableLanguages.map(l => (
                            <option key={l.id} value={l.id}>{l.name}</option>
                        ))}
                    </Select>
                </div>

                <div>
                    <div className="flex justify-between mb-2">
                        <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">Keywords Boosting</label>
                        <span className="text-[10px] text-slate-500">CSV: "Marca, 2.0", "Producto, 1.5"</span>
                    </div>
                    <textarea
                        value={browser.sttKeywords}
                        onChange={(e) => update('sttKeywords', e.target.value)}
                        rows={2}
                        className="flex w-full rounded-lg border border-white/10 bg-slate-900/60 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                        placeholder='[{"word": "Ubrokers", "boost": 2.0}]'
                    />
                </div>
            </div>

            {/* Interruption Control */}
            <div className="p-4 rounded-lg border border-slate-700 bg-slate-800/50 space-y-4">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4 block flex items-center gap-2">
                    <Radio className="w-4 h-4" />
                    Control de Interrupciones
                </label>

                {/* Threshold */}
                <div>
                    <div className="flex justify-between mb-1">
                        <span className="text-sm text-slate-300">Umbral de Palabras</span>
                        <span className="text-emerald-400 font-mono">{browser.interruption_threshold}</span>
                    </div>
                    <input
                        type="range"
                        min="0" max="10" step="1"
                        value={browser.interruption_threshold}
                        onChange={(e) => update('interruption_threshold', parseInt(e.target.value))}
                        className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                    />
                    <p className="text-[10px] text-slate-500 mt-1">Palabras requeridas para detener al bot.</p>
                </div>

                {/* Blacklist */}
                <div>
                    <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Blacklist Alucinaciones</label>
                    <textarea
                        value={browser.hallucination_blacklist}
                        onChange={(e) => update('hallucination_blacklist', e.target.value)}
                        rows={1}
                        className="flex w-full rounded-lg border border-white/10 bg-slate-900/60 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                        placeholder="Pero.,,Y...,Mm.,Oye.,Ah."
                    />
                </div>

                {/* Silence Timeout */}
                <div className="pt-4 border-t border-slate-700/50">
                    <div className="flex justify-between mb-1">
                        <span className="text-sm text-slate-300">Endpointing (Silencio Final)</span>
                        <span className="text-emerald-400 font-mono">{browser.sttSilenceTimeout} ms</span>
                    </div>
                    <input
                        type="range"
                        min="200" max="2000" step="100"
                        value={browser.sttSilenceTimeout}
                        onChange={(e) => update('sttSilenceTimeout', parseInt(e.target.value))}
                        className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                    />
                </div>

                <div className="pt-4 border-t border-slate-700/50">
                    <div className="flex items-center justify-between mb-4">
                        <div>
                            <span className="text-sm font-bold text-emerald-400 block">Interrupción Inteligente</span>
                            <span className="text-[10px] text-slate-500">Usa IA para evitar cortes cuando el usuario duda.</span>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                            <input
                                type="checkbox"
                                aria-label="Interrupción Inteligente"
                                checked={browser.sttUtteranceEnd === 'semantic'}
                                onChange={(e) => update('sttUtteranceEnd', e.target.checked ? 'semantic' : 'default')}
                                className="sr-only peer"
                            />
                            <div className="w-9 h-5 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-500"></div>
                        </label>
                    </div>

                    <div className="flex justify-between mb-1">
                        <span className="text-sm text-slate-300">Sensibilidad VAD (Silero)</span>
                        <span className="text-emerald-400 font-mono">{browser.vad_threshold}</span>
                    </div>
                    <input
                        type="range"
                        aria-label="Sensibilidad VAD"
                        min="0.1" max="0.9" step="0.05"
                        value={browser.vad_threshold}
                        onChange={(e) => update('vad_threshold', parseFloat(e.target.value))}
                        className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                    />
                    <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                        <span>0.1 (Muy Sensible)</span>
                        <span>0.9 (Estricto)</span>
                    </div>
                </div>

                {/* Telnyx Specific */}
                <div className="pt-4 border-t border-slate-700/50">
                    <div className="flex justify-between mb-1">
                        <span className="text-sm text-slate-300">Sensibilidad Telnyx (RMS)</span>
                        <span className="text-emerald-400 font-mono">{browser.interruptRMS}</span>
                    </div>
                    <input
                        type="range"
                        aria-label="Sensibilidad RMS"
                        min="0" max="10000" step="100"
                        value={browser.interruptRMS}
                        onChange={(e) => update('interruptRMS', parseInt(e.target.value))}
                        className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                    />
                </div>
            </div>

            {/* Booleans */}
            <div className="space-y-4 pt-4 border-t border-slate-700">
                <h3 className="text-sm font-bold text-emerald-400 uppercase tracking-wider mb-3">
                    🧠 Inteligencia de Transcripción
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {[
                        { id: 'sttPunctuation', label: 'Puntuación Auto' },
                        { id: 'sttSmartFormatting', label: 'Smart Formatting' },
                        { id: 'sttProfanityFilter', label: 'Filtro Groserías' },
                        { id: 'sttDiarization', label: 'Diarización (A/B)' },
                        { id: 'sttMultilingual', label: 'Multi-Lenguaje' }
                    ].map(item => (
                        <label key={item.id} className="flex items-center justify-between cursor-pointer p-3 rounded-lg border border-white/5 bg-slate-900/30 hover:bg-slate-900/50 transition-colors">
                            <span className="text-sm text-slate-300">{item.label}</span>
                            <input
                                type="checkbox"
                                checked={!!browser[item.id as keyof BrowserConfig]}
                                onChange={(e) => update(item.id as keyof BrowserConfig, e.target.checked)}
                                className="w-4 h-4 rounded border-slate-600 text-emerald-500 focus:ring-emerald-500 focus:ring-offset-slate-900 bg-slate-800"
                            />
                        </label>
                    ))}
                </div>
            </div>
        </div>
    )
}
