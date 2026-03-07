import { useState } from 'react'
import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { updateBrowserConfig } from '@/store/slices/configSlice'
import { BrowserConfig } from '@/types/config'
import { Disc, Clock, Voicemail, AlertCircle, Hash, Cpu } from 'lucide-react'
import { Input } from '@/components/ui/Input'
import { Accordion } from '@/components/ui/Accordion'

export const FlowSettings = () => {
    const dispatch = useAppDispatch()
    const { browser } = useAppSelector(state => state.config)
    const { activeAgent } = useAppSelector(state => state.agents)
    const isTelnyx = activeAgent?.provider === 'telnyx'

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
            {isTelnyx ? (
                <Accordion
                    isOpen={openSection === 'amd'}
                    onToggle={() => setOpenSection(openSection === 'amd' ? null : 'amd')}
                    className="border-amber-500/30"
                    headerClassName="hover:bg-amber-900/20"
                    title={
                        <div className="flex items-center gap-2">
                            <Voicemail className="w-4 h-4 text-amber-400" />
                            <span className="text-sm font-bold text-amber-400 tracking-wider">
                                AMD / RUIDO (TELNYX)
                            </span>
                        </div>
                    }
                >
                    <div className="space-y-3">
                        {/* Info: AMD configurado en Connectivity */}
                        <div className="p-3 bg-amber-500/10 rounded-lg border border-amber-500/30">
                            <div className="flex items-start gap-2">
                                <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                                <div>
                                    <h4 className="text-xs font-bold text-amber-400 mb-1">AMD gestionado en Conectividad</h4>
                                    <p className="text-[10px] text-amber-500/80">
                                        La detección de buzón (AMD) se configura en
                                        <strong className="text-amber-300 mx-1">Conectividad → Features &amp; Call Options → AMD Config</strong>.
                                        Ofrece 4 modos nativos de Telnyx: detect, detect_hangup, detect_message_end.
                                    </p>
                                </div>
                            </div>
                        </div>
                        {/* Info: Noise Suppression automático */}
                        <div className="flex items-center justify-between bg-emerald-900/20 p-3 rounded-lg border border-emerald-700/50">
                            <div>
                                <span className="text-xs font-bold text-emerald-400 block">Supresión de Ruido Automática</span>
                                <span className="text-[10px] text-slate-500">Activa siempre en Telnyx gracias al motor nativo de red. Sin configuración adicional.</span>
                            </div>
                            <span className="text-[10px] font-bold text-emerald-400 bg-emerald-900/40 px-2 py-1 rounded">ACTIVO</span>
                        </div>
                    </div>
                </Accordion>
            ) : (
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
                                        value={browser.amdSensitivity}
                                        onChange={(e) => update('amdSensitivity', parseFloat(e.target.value))}
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
            )}

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

            {/* 4. DTMF + Voice AI Gather (solo Telnyx) */}
            {isTelnyx && (
                <Accordion
                    isOpen={openSection === 'dtmf'}
                    onToggle={() => setOpenSection(openSection === 'dtmf' ? null : 'dtmf')}
                    className="border-violet-500/30"
                    headerClassName="hover:bg-violet-900/20"
                    title={
                        <div className="flex items-center gap-2">
                            <Hash className="w-4 h-4 text-violet-400" />
                            <span className="text-sm font-bold text-violet-400 tracking-wider">
                                DTMF + VOICE AI GATHER (TELNYX)
                            </span>
                        </div>
                    }
                >
                    <div className="space-y-6">

                        {/* DTMF Pipeline */}
                        <div className="bg-slate-900/30 p-4 rounded-xl border border-slate-800">
                            <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center gap-2">
                                    <Hash className="w-4 h-4 text-violet-400" />
                                    <span className="text-xs font-bold text-slate-300">Pipeline DTMF Activo</span>
                                </div>
                                <input
                                    type="checkbox"
                                    aria-label="DTMF Enabled"
                                    checked={browser.dtmfEnabled}
                                    onChange={(e) => update('dtmfEnabled', e.target.checked)}
                                    className="toggle-checkbox"
                                />
                            </div>
                            <p className="text-[10px] text-slate-500 mb-3">
                                Enruta señales de teclado del usuario al orquestador:
                                <span className="text-violet-400 font-mono ml-1">0→Agente · #→Colgar · 9→Repetir</span>
                            </p>
                            <div>
                                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">
                                    Mapa Custom (JSON)
                                </label>
                                <Input
                                    aria-label="DTMF Map"
                                    value={browser.dtmfMap}
                                    onChange={(e) => update('dtmfMap', e.target.value)}
                                    placeholder='{"1": "confirm", "2": "cancel"}'
                                />
                                <p className="text-[9px] text-slate-500 mt-1">Opcional — sobreescribe el mapa por defecto.</p>
                            </div>
                        </div>

                        {/* gather_using_ai */}
                        <div className="bg-slate-900/30 p-4 rounded-xl border border-slate-800">
                            <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center gap-2">
                                    <Cpu className="w-4 h-4 text-violet-400" />
                                    <span className="text-xs font-bold text-slate-300">Voice AI Gather</span>
                                </div>
                                <input
                                    type="checkbox"
                                    aria-label="Gather AI Enabled"
                                    checked={browser.gatherAiEnabled}
                                    onChange={(e) => update('gatherAiEnabled', e.target.checked)}
                                    className="toggle-checkbox"
                                />
                            </div>
                            <p className="text-[10px] text-slate-500 mb-4">
                                Telnyx captura datos estructurados (nombre, intención) antes de pasar al pipeline LLM.
                                Solo activo al contestar la llamada.
                            </p>
                            <div className="space-y-3">
                                <div>
                                    <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">
                                        Greeting del Gather
                                    </label>
                                    <Input
                                        aria-label="Gather AI Greeting"
                                        value={browser.gatherAiGreeting}
                                        onChange={(e) => update('gatherAiGreeting', e.target.value)}
                                        placeholder="¿Con quién tengo el gusto de hablar?"
                                        disabled={!browser.gatherAiEnabled}
                                        className={!browser.gatherAiEnabled ? 'opacity-40 cursor-not-allowed' : ''}
                                    />
                                </div>
                                <div>
                                    <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">
                                        Voz TTS del Gather
                                    </label>
                                    <Input
                                        aria-label="Gather AI Voice"
                                        value={browser.gatherAiVoice}
                                        onChange={(e) => update('gatherAiVoice', e.target.value)}
                                        placeholder="Polly.Lupe-Neural"
                                        disabled={!browser.gatherAiEnabled}
                                        className={!browser.gatherAiEnabled ? 'opacity-40 cursor-not-allowed' : ''}
                                    />
                                    <p className="text-[9px] text-slate-500 mt-1">
                                        Vacío = voz del agente. Usa nombres Amazon Polly o Azure Neural.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </Accordion>
            )}
        </div>
    )
}
