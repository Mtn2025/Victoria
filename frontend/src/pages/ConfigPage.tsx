import { useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { useAppSelector, useAppDispatch } from "@/hooks/useRedux"
import { setActiveProfile, ProfileId } from "@/store/slices/uiSlice"
import { saveBrowserConfig, fetchAgentConfig } from "@/store/slices/configSlice"
import { cn } from "@/utils/cn"
import { Globe, Smartphone, Radio, LucideIcon, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/Button"
import { ComingSoon } from "@/components/ui/ComingSoon"
import { ModelSettings } from '@/components/features/Config/ModelSettings'
import { VoiceSettings } from '@/components/features/Config/VoiceSettings'
import { TranscriberSettings } from '@/components/features/Config/TranscriberSettings'

// -----------------------------------------------------------------
// Tabs activos: model, voice, transcriber
// El resto → ComingSoon (sin eliminar los componentes originales)
// -----------------------------------------------------------------

const PROFILES: { id: ProfileId; label: string; icon: LucideIcon }[] = [
    { id: 'browser', label: 'Simulador Web', icon: Globe },
    { id: 'twilio', label: 'Telefonía Twilio', icon: Smartphone },
    { id: 'telnyx', label: 'Telefonía Telnyx', icon: Radio },
]

export const ConfigPage = () => {
    const dispatch = useAppDispatch()
    const navigate = useNavigate()
    const activeTab = useAppSelector(state => state.ui.activeTab)
    const activeProfile = useAppSelector(state => state.ui.activeProfile)
    const { browser, isLoadingOptions } = useAppSelector(state => state.config)
    const activeAgent = useAppSelector(state => state.agents.activeAgent)

    // Hydrate config from the active agent on mount,
    // and whenever activeAgent changes (e.g. user activates a different agent).
    useEffect(() => {
        if (!activeAgent) {
            // No active agent in Redux — redirect so the user can pick one
            navigate('/agents')
            return
        }
        // Fetch full config for the active agent. fetchAgentConfig has no params:
        // it always calls GET /api/agents/active, which the backend resolves from DB.
        dispatch(fetchAgentConfig())
    }, [dispatch, navigate, activeAgent])


    // Form Validation Logic — only for active (non-stub) browser profile
    const missingFields = []
    if (!browser.provider) missingFields.push("Proveedor LLM")
    if (!browser.model) missingFields.push("Modelo LLM")
    if (!browser.voiceId) missingFields.push("Voz (TTS)")

    const isBrowserValid = missingFields.length === 0
    const isValid = activeProfile === 'browser' ? isBrowserValid : true

    // Active tabs have real backend connections.
    // All others redirect to ComingSoon — their components are preserved but not imported.
    const ACTIVE_TABS = ['model', 'voice', 'transcriber']
    const isActiveTab = ACTIVE_TABS.includes(activeTab)

    const handleSave = async () => {
        if (activeProfile !== 'browser') {
            // Twilio/Telnyx: no backend endpoint yet — show stub message
            // TODO: Implement Twilio/Telnyx save when backend supports it
            return
        }
        await dispatch(saveBrowserConfig(browser)).unwrap()
    }

    const renderTabContent = () => {
        if (activeTab === 'model') return <ModelSettings />
        if (activeTab === 'voice') return <VoiceSettings />
        if (activeTab === 'transcriber') return <TranscriberSettings />

        // All other tabs: stub while being reconstructed
        const TAB_NAMES: Record<string, string> = {
            connectivity: 'Conectividad (Twilio / Telnyx)',
            tools: 'Herramientas Externas',
            advanced: 'Configuración Avanzada',
            campaigns: 'Campañas',
            analysis: 'Análisis de Llamadas',
            flow: 'Flujo y Orquestación',
            system: 'Sistema y Gobernanza',
        }
        return (
            <ComingSoon
                tabName={TAB_NAMES[activeTab] ?? activeTab}
                reason="Esta sección estará disponible en la próxima fase de reconstrucción."
            />
        )
    }

    return (
        <div className="flex flex-col h-full w-full">
            {/* Config Header */}
            <div className="h-16 flex items-center justify-between px-6 border-b border-white/10 bg-slate-900/50 backdrop-blur shrink-0">
                <h2 className="text-sm font-bold text-slate-100 tracking-wide uppercase">Configuración</h2>

                {/* Profile Switcher */}
                <div className="flex bg-slate-800 rounded-lg p-1 border border-slate-700/50 space-x-1">
                    {PROFILES.map((p) => {
                        const Icon = p.icon
                        const isActive = activeProfile === p.id
                        return (
                            <button
                                key={p.id}
                                onClick={() => dispatch(setActiveProfile(p.id))}
                                title={p.label}
                                className={cn(
                                    "w-8 h-8 rounded-md flex items-center justify-center transition-all relative",
                                    isActive
                                        ? "bg-slate-600 text-white shadow-sm ring-1 ring-white/10"
                                        : "text-slate-400 hover:text-slate-200 hover:bg-slate-700/50"
                                )}
                            >
                                <Icon size={16} />
                            </button>
                        )
                    })}
                </div>
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
                <div className="flex items-center space-x-2 text-blue-400 mb-4">
                    <h3 className="text-lg font-bold text-white tracking-tight first-letter:uppercase">
                        {activeTab}
                    </h3>
                </div>

                <div className="p-1">
                    {renderTabContent()}
                </div>
            </div>

            {/* Footer Actions — only shown for active (non-stub) tabs */}
            {isActiveTab && activeProfile === 'browser' && (
                <div className="p-4 border-t border-white/10 bg-slate-900 sticky bottom-0 z-50 space-y-3">

                    {/* Validation Warning */}
                    {missingFields.length > 0 && (
                        <div className="flex items-center gap-2 text-xs text-amber-400 bg-amber-400/10 border border-amber-400/20 p-2 rounded-md">
                            <AlertCircle className="w-4 h-4 shrink-0" />
                            <span>Faltan campos obligatorios para guardar: {missingFields.join(", ")}</span>
                        </div>
                    )}

                    <Button
                        className="w-full"
                        variant="primary"
                        data-testid="btn-save-config"
                        onClick={handleSave}
                        disabled={isLoadingOptions || !isValid}
                    >
                        {isLoadingOptions ? "Guardando..." : "Guardar Configuración"}
                    </Button>
                </div>
            )}

            {/* Stub notice for non-browser profiles */}
            {activeProfile !== 'browser' && (
                <div className="p-4 border-t border-white/10 bg-slate-900 sticky bottom-0 z-50">
                    <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-800/50 border border-slate-700/40 p-2 rounded-md">
                        <AlertCircle className="w-4 h-4 shrink-0 text-slate-600" />
                        <span>El guardado para {activeProfile === 'twilio' ? 'Twilio' : 'Telnyx'} se implementará en una próxima fase.</span>
                    </div>
                </div>
            )}
        </div>
    )
}
