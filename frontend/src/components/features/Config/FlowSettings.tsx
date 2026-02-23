import { useState } from 'react'
import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { updateBrowserConfig } from '@/store/slices/configSlice'
import { BrowserConfig } from '@/types/config'
import { Disc, Clock, Voicemail } from 'lucide-react'
import { Input } from '@/components/ui/Input'
import { Accordion } from '@/components/ui/Accordion'

export const FlowSettings = () => {
    const dispatch = useAppDispatch()
    const { browser } = useAppSelector(state => state.config)

    // Controlamos qué sección está abierta por defecto
    const [openSection, setOpenSection] = useState<string | null>('barge')

    const update = <K extends keyof BrowserConfig>(key: K, value: BrowserConfig[K]) => {
        dispatch(updateBrowserConfig({ [key]: value }))
    }

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10">

            {/* 1. Interrupciones (Barge-in) */}
            <Accordion
                isOpen={openSection === 'barge'}
                onToggle={() => setOpenSection(openSection === 'barge' ? null : 'barge')}
                className="border-rose-500/30"
                headerClassName="hover:bg-rose-900/20"
                title={
                    <div className="flex items-center gap-2">
                        <Disc className="w-4 h-4 text-rose-400" />
                        <span className="text-sm font-bold text-rose-400 tracking-wider">
                            INTERRUPCIONES (BARGE-IN)
                        </span>
                    </div>
                }
            >
                <div className="space-y-6">
                    <div className="flex items-center justify-between bg-slate-800/50 p-3 rounded-lg border border-slate-700">
                        <div>
                            <span className="text-xs font-bold text-slate-300 block">Permitir Interrupciones</span>
                            <span className="text-[10px] text-slate-500">Deja que el usuario detenga a la IA hablando por encima de ella.</span>
                        </div>
                        <input
                            type="checkbox"
                            aria-label="Barge-in Logic"
                            checked={browser.bargeInEnabled}
                            onChange={(e) => update('bargeInEnabled', e.target.checked)}
                            className="toggle-checkbox"
                        />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="bg-slate-900/30 p-4 rounded-xl border border-slate-800">
                            <div className="flex justify-between mb-2">
                                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Sensibilidad del Micrófono</label>
                                <span className="text-xs font-mono text-rose-400">
                                    {browser.interruptionSensitivity} ({browser.interruptionSensitivity > 0.8 ? 'Alta' : 'Baja'})
                                </span>
                            </div>
                            <input
                                type="range"
                                aria-label="Interruption Sensitivity"
                                min="0" max="1" step="0.1"
                                value={browser.interruptionSensitivity}
                                onChange={(e) => update('interruptionSensitivity', parseFloat(e.target.value))}
                                className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-rose-500"
                            />
                            <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                                <span>Difícil de Interrumpir</span>
                                <span>Sensible (Fácil)</span>
                            </div>
                        </div>

                        <div className="bg-slate-900/30 p-4 rounded-xl border border-slate-800">
                            <div className="flex justify-between mb-2">
                                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Frases de Detención Fuerte</label>
                                <span className="text-[10px] text-slate-500">Array JSON</span>
                            </div>
                            <Input
                                aria-label="Interruption Phrases"
                                value={browser.interruptionPhrases}
                                onChange={(e) => update('interruptionPhrases', e.target.value)}
                                placeholder='["para", "espera", "escúchame"]'
                            />
                            <p className="text-[10px] text-slate-500 mt-1">Palabras exactas que cortarán a la IA inmediatamente.</p>
                        </div>
                    </div>
                </div>
            </Accordion>

            {/* 2. Detección de Buzón (AMD) */}
            <Accordion
                isOpen={openSection === 'amd'}
                onToggle={() => setOpenSection(openSection === 'amd' ? null : 'amd')}
                className="border-amber-500/30"
                headerClassName="hover:bg-amber-900/20"
                title={
                    <div className="flex items-center gap-2">
                        <Voicemail className="w-4 h-4 text-amber-400" />
                        <span className="text-sm font-bold text-amber-400 tracking-wider">
                            DETECCIÓN DE BUZÓN (AMD)
                        </span>
                    </div>
                }
            >
                <div className="space-y-6">
                    <div className="flex items-center justify-between bg-slate-800/50 p-3 rounded-lg border border-slate-700">
                        <div>
                            <span className="text-xs font-bold text-slate-300 block">Identificar Máquinas (Voicemail)</span>
                            <span className="text-[10px] text-slate-500">Detecta si contestó una grabadora, deja el mensaje y cuelga.</span>
                        </div>
                        <input
                            type="checkbox"
                            aria-label="Voicemail Detection"
                            checked={browser.voicemailDetectionEnabled}
                            onChange={(e) => update('voicemailDetectionEnabled', e.target.checked)}
                            className="toggle-checkbox"
                        />
                    </div>

                    <div className="space-y-4">
                        <div>
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Mensaje Fijo para el Buzón</label>
                            <textarea
                                aria-label="Voicemail Message"
                                value={browser.voicemailMessage}
                                onChange={(e) => update('voicemailMessage', e.target.value)}
                                className="w-full h-20 bg-[#0B1121] text-xs text-slate-300 p-3 border border-amber-900/30 rounded-lg focus:outline-none focus:border-amber-500 resize-none custom-scrollbar"
                                placeholder="Hola, te llamaba de Ubrokers para..."
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Precisión AMD</label>
                                <Input
                                    type="number"
                                    aria-label="AMD Sensitivity"
                                    step="0.1" min="0" max="1"
                                    value={browser.machineDetectionSensitivity}
                                    onChange={(e) => update('machineDetectionSensitivity', parseFloat(e.target.value))}
                                />
                            </div>
                            <div>
                                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Acción Resolutiva</label>
                                <select
                                    className="w-full bg-[#0B1121] py-2 px-3 rounded-lg text-xs text-slate-300 border border-slate-700/50 focus:outline-none focus:border-amber-500"
                                    value={browser.amdAction}
                                    onChange={(e) => update('amdAction', e.target.value)}
                                >
                                    <option value="hangup">Cuelgue Inmediato</option>
                                    <option value="leave_message">Dejar Mensaje y Colgar</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
            </Accordion>

            {/* 3. Ritmo y Naturalidad (Pacing) */}
            <Accordion
                isOpen={openSection === 'pacing'}
                onToggle={() => setOpenSection(openSection === 'pacing' ? null : 'pacing')}
                className="border-emerald-500/30"
                headerClassName="hover:bg-emerald-900/20"
                title={
                    <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-emerald-400" />
                        <span className="text-sm font-bold text-emerald-400 tracking-wider">
                            RITMO Y NATURALIDAD (PACING)
                        </span>
                    </div>
                }
            >
                <div className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                        {/* Latencia Artificial */}
                        <div className="bg-slate-900/30 p-4 rounded-xl border border-slate-800">
                            <div className="flex justify-between mb-2">
                                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Latencia Artificial Inyectada</label>
                                <span className="text-xs font-mono text-emerald-400">{browser.responseDelaySeconds}s</span>
                            </div>
                            <input
                                type="range"
                                aria-label="Response Delay"
                                min="0" max="3" step="0.1"
                                value={browser.responseDelaySeconds}
                                onChange={(e) => update('responseDelaySeconds', parseFloat(e.target.value))}
                                className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                            />
                            <p className="text-[10px] text-slate-500 mt-2">Fuerza a la IA a "pensar" unos segundos antes de escupir la respuesta.</p>
                        </div>

                        {/* Toggles Rápidos */}
                        <div className="space-y-3 bg-slate-900/30 p-4 rounded-xl border border-slate-800">
                            <div className="flex items-center justify-between">
                                <div>
                                    <span className="text-xs font-bold text-slate-300 block">Respiros Orgánicos (Hyphenation)</span>
                                    <span className="text-[10px] text-slate-500">Inyecta comas dinámicas en el stream (TTS).</span>
                                </div>
                                <input
                                    type="checkbox"
                                    aria-label="Hyphenation Enabled"
                                    checked={browser.hyphenationEnabled}
                                    onChange={(e) => update('hyphenationEnabled', e.target.checked)}
                                    className="toggle-checkbox"
                                />
                            </div>
                        </div>

                        {/* Despedida */}
                        <div className="col-span-1 md:col-span-2 bg-slate-900/30 p-4 rounded-xl border border-slate-800">
                            <div className="flex justify-between mb-2">
                                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Cuelgue Automático por Intención</label>
                                <span className="text-[10px] text-slate-500">Array JSON</span>
                            </div>
                            <Input
                                aria-label="End Call Phrases"
                                value={browser.endCallPhrases}
                                onChange={(e) => update('endCallPhrases', e.target.value)}
                                placeholder='["gracias", "adiós", "hasta luego"]'
                            />
                            <p className="text-[10px] text-slate-500 mt-1">Si la IA produce o escucha estas frases de despedida, finalizará la llamada solita.</p>
                        </div>

                    </div>
                </div>
            </Accordion>
        </div>
    )
}
