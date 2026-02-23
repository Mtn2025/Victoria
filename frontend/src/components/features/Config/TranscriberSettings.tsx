import { useState } from 'react'
import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { updateBrowserConfig } from '@/store/slices/configSlice'
import { Select } from '@/components/ui/Select'
import { BrowserConfig } from '@/types/config'
import { Accordion } from '@/components/ui/Accordion'
import { Ear, Radio } from 'lucide-react'

export const TranscriberSettings = () => {
    const dispatch = useAppDispatch()
    // Use browser config from store
    const { browser } = useAppSelector(state => state.config)

    const [openSection, setOpenSection] = useState<string | null>('core')

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

            {/* Main Content Areas inside Accordions */}
            <div className="space-y-3">
                {/* Core Config */}
                <Accordion
                    isOpen={openSection === 'core'}
                    onToggle={() => setOpenSection(openSection === 'core' ? null : 'core')}
                    className="border-emerald-500/30"
                    headerClassName="hover:bg-emerald-900/20"
                    title={
                        <span className="text-sm font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
                            <Ear className="w-4 h-4" />
                            Configuración Base (Motor STT)
                        </span>
                    }
                >
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-4">
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Proveedor STT</label>
                            <Select
                                aria-label="Proveedor STT"
                                value={browser.sttProvider}
                                onChange={(e) => update('sttProvider', e.target.value)}
                            >
                                <option value="azure">Azure Speech</option>
                            </Select>
                            <p className="text-[10px] text-slate-500 mt-1">El idioma de transcripción (ej. es-MX) se hereda automáticamente de la Configuración Base del Agente.</p>
                        </div>
                    </div>
                </Accordion>

                <Accordion
                    isOpen={openSection === 'vad'}
                    onToggle={() => setOpenSection(openSection === 'vad' ? null : 'vad')}
                    title={
                        <span className="text-sm font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
                            <Radio className="w-4 h-4" />
                            Orquestación y Sensibilidad de Voz (VAD)
                        </span>
                    }
                >
                    <div className="space-y-4 pt-2">
                        {/* Threshold Local VAD */}
                        <div>
                            <div className="flex justify-between mb-1">
                                <span className="text-sm text-slate-300">Sensibilidad VAD Local (Silero)</span>
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
                                <span>0.1 (Muy Sensible a ruidos)</span>
                                <span>0.9 (Sordo)</span>
                            </div>
                        </div>

                        {/* Blacklist Hallucinations */}
                        <div className="pt-2 border-t border-white/5">
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Lista Negra (Falsos Positivos del VAD)</label>
                            <textarea
                                value={browser.hallucination_blacklist}
                                onChange={(e) => update('hallucination_blacklist', e.target.value)}
                                rows={1}
                                className="flex w-full rounded-lg border border-white/10 bg-slate-900/60 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                                placeholder="Pero.,,Y...,Mm.,Oye.,Ah."
                            />
                            <p className="text-[10px] text-slate-500 mt-1">Fragmentos cortos que el VAD captura por error y no deben enviarse al LLM.</p>
                        </div>
                    </div>
                </Accordion>
            </div>
        </div>
    )
}
