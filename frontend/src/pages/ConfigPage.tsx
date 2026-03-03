import { useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { useAppSelector, useAppDispatch } from "@/hooks/useRedux"
import { fetchAgentConfig } from "@/store/slices/configSlice"

import { AlertCircle } from "lucide-react"
import { FEATURES } from "@/utils/featureFlags"
import { ModelSettings } from '@/components/features/Config/ModelSettings'
import { VoiceSettings } from '@/components/features/Config/VoiceSettings'
import { TranscriberSettings } from '@/components/features/Config/TranscriberSettings'
import { ToolsSettings } from '@/components/features/Config/ToolsSettings'
import { FlowSettings } from '@/components/features/Config/FlowSettings'
import { ConnectivitySettings } from '@/components/features/Config/ConnectivitySettings'
import { AdvancedSettings } from '@/components/features/Config/AdvancedSettings'
import { CampaignSettings } from '@/components/features/Config/CampaignSettings'
import { AnalysisSettings } from '@/components/features/Config/AnalysisSettings'
import { SystemSettings } from '@/components/features/Config/SystemSettings'
import { useAutoSave } from '@/components/features/Config/hooks/useAutoSave'
import { Check, Loader2, XCircle } from 'lucide-react'

// -----------------------------------------------------------------
// Tabs activos: model, voice, transcriber
// El resto → ComingSoon (sin eliminar los componentes originales)
// -----------------------------------------------------------------

export const ConfigPage = () => {
    const dispatch = useAppDispatch()
    const navigate = useNavigate()
    const activeTab = useAppSelector(state => state.ui.activeTab)
    const activeProfile = useAppSelector(state => state.ui.activeProfile)
    const { browser } = useAppSelector(state => state.config)
    const activeAgent = useAppSelector(state => state.agents.activeAgent)

    // Hydrate config from the active agent on mount,
    // and whenever activeAgent changes (e.g. user activates a different agent).
    useEffect(() => {
        if (!FEATURES.AGENTS_LIST) return

        // 1) Si no hay agente activo, ir a la lista
        if (!activeAgent) {
            navigate('/agents')
            return
        }

        // 2) Si el agente activo pertenece a un proveedor distinto al que acabamos de seleccionar
        // en la barra lateral, entonces no debemos mostrar la conf de ese agente en este contexto.
        // Lo redirigimos a la lista para que seleccione un agente válido para este proveedor.
        if (activeAgent && activeAgent.provider !== activeProfile) {
            navigate('/agents')
            return
        }

        dispatch(fetchAgentConfig())
    }, [dispatch, navigate, activeAgent, activeProfile])

    // Form Validation Logic — only for active (non-stub) browser profile
    const missingFields = []
    if (!browser.provider) missingFields.push("Proveedor LLM")
    if (!browser.model) missingFields.push("Modelo LLM")
    if (!browser.voiceId) missingFields.push("Voz (TTS)")

    // Setup zero-click auto-save
    const { saveStatus } = useAutoSave(800)

    const renderTabContent = () => {
        if (activeTab === 'model') return <ModelSettings />
        if (activeTab === 'voice') return <VoiceSettings />
        if (activeTab === 'transcriber') return <TranscriberSettings />
        if (activeTab === 'tools') return <ToolsSettings />
        if (activeTab === 'flow') return <FlowSettings />
        if (activeTab === 'connectivity') return <ConnectivitySettings />
        if (activeTab === 'advanced') return <AdvancedSettings />
        if (activeTab === 'campaigns') return <CampaignSettings />
        if (activeTab === 'analysis') return <AnalysisSettings />
        if (activeTab === 'system') return <SystemSettings />

        return <div className="text-white p-4">Panel en reconstrucción.</div>
    }

    return (
        <div className="flex flex-col h-full w-full">
            {/* Config Header */}
            <div className="h-16 flex items-center justify-between px-6 border-b border-white/10 bg-slate-900/50 backdrop-blur shrink-0">
                <h2 className="text-sm font-bold text-slate-100 tracking-wide uppercase">Configuración</h2>
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-2 text-blue-400">
                        <h3 className="text-lg font-bold text-white tracking-tight first-letter:uppercase">
                            {activeTab}
                        </h3>
                    </div>

                    {/* Auto-Save Toast Status */}
                    {activeProfile && (
                        <div className="flex items-center gap-2 h-7 px-3 rounded-full text-[11px] font-medium transition-all bg-slate-800 border border-slate-700">
                            {saveStatus === 'saving' && (
                                <>
                                    <Loader2 size={12} className="animate-spin text-blue-400" />
                                    <span className="text-blue-400">Guardando...</span>
                                </>
                            )}
                            {saveStatus === 'saved' && (
                                <>
                                    <Check size={12} className="text-emerald-400" />
                                    <span className="text-emerald-400">
                                        Guardado exitoso
                                    </span>
                                </>
                            )}
                            {saveStatus === 'error' && (
                                <>
                                    <XCircle size={12} className="text-red-400" />
                                    <span className="text-red-400">Error al guardar</span>
                                    {/* Make it clickable later to open logs panel */}
                                </>
                            )}
                            {saveStatus === 'idle' && (
                                <span className="text-slate-500">Sin cambios</span>
                            )}
                        </div>
                    )}
                </div>

                <div className="p-1">
                    {renderTabContent()}
                </div>
            </div>

            {/* Footer Actions — validation block */}
            {missingFields.length > 0 && (
                <div className="p-4 border-t border-white/10 bg-slate-900 sticky bottom-0 z-50">
                    <div className="flex items-center gap-2 text-xs text-amber-400 bg-amber-400/10 border border-amber-400/20 p-2 rounded-md">
                        <AlertCircle className="w-4 h-4 shrink-0" />
                        <span>Faltan campos obligatorios para operar: {missingFields.join(", ")}</span>
                    </div>
                </div>
            )}

            {/* Stub notice for non-browser profiles */}
            {activeProfile !== 'browser' && (
                <div className="p-4 border-t border-white/10 bg-slate-900 sticky bottom-0 z-50">
                    <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-800/50 border border-slate-700/40 p-2 rounded-md">
                        <AlertCircle className="w-4 h-4 shrink-0 text-slate-600" />
                        <span>Las configuraciones de telefonía {activeProfile === 'twilio' ? 'Twilio' : 'Telnyx'} se implementarán en una próxima fase.</span>
                    </div>
                </div>
            )}
        </div>
    )
}
