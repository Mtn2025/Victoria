import { useAppSelector, useAppDispatch } from "@/hooks/useRedux"
import { setActiveProfile, ProfileId } from "@/store/slices/uiSlice"
import { saveBrowserConfig } from "@/store/slices/configSlice"
import { cn } from "@/utils/cn"
import { Globe, Smartphone, Radio, LucideIcon, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/Button"
import { ModelSettings } from '@/components/features/Config/ModelSettings'
import { VoiceSettings } from '@/components/features/Config/VoiceSettings'
import { TranscriberSettings } from '@/components/features/Config/TranscriberSettings'
import { ConnectivitySettings } from '@/components/features/Config/ConnectivitySettings'
import { ToolsSettings } from '@/components/features/Config/ToolsSettings'
import { AdvancedSettings } from "@/components/features/Config/AdvancedSettings"
import { CampaignSettings } from "@/components/features/Config/CampaignSettings"
import { SystemSettings } from "@/components/features/Config/SystemSettings"
import { AnalysisSettings } from "@/components/features/Config/AnalysisSettings"
import { FlowSettings } from "@/components/features/Config/FlowSettings"

const PROFILES: { id: ProfileId; label: string; icon: LucideIcon }[] = [
    { id: 'browser', label: 'Simulador Web', icon: Globe },
    { id: 'twilio', label: 'Telefonía Twilio', icon: Smartphone },
    { id: 'telnyx', label: 'Telefonía Telnyx', icon: Radio },
]

export const ConfigPage = () => {
    const dispatch = useAppDispatch()
    const activeTab = useAppSelector(state => state.ui.activeTab)
    const activeProfile = useAppSelector(state => state.ui.activeProfile)
    const { browser, isLoadingOptions } = useAppSelector(state => state.config)

    // Form Validation Logic
    const missingFields = []
    if (!browser.provider) missingFields.push("Proveedor LLM")
    if (!browser.model) missingFields.push("Modelo LLM")
    if (!browser.voiceId) missingFields.push("Voz (TTS)")

    const isBrowserValid = missingFields.length === 0
    const isValid = activeProfile === 'browser' ? isBrowserValid : true

    const handleSave = async () => {
        if (activeProfile === 'browser') {
            await dispatch(saveBrowserConfig(browser)).unwrap()
            // Could add a toast notification here
        } else {
            alert("El guardado para telefonía (Twilio/Telnyx) aún no está implementado")
        }
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
                    {activeTab === 'model' ? (
                        <ModelSettings />
                    ) : activeTab === 'voice' ? (
                        <VoiceSettings />
                    ) : activeTab === 'transcriber' ? (
                        <TranscriberSettings />
                    ) : activeTab === 'connectivity' ? (
                        <ConnectivitySettings />
                    ) : activeTab === 'tools' ? (
                        <ToolsSettings />
                    ) : activeTab === 'advanced' ? (
                        <AdvancedSettings />
                    ) : activeTab === 'campaigns' ? (
                        <CampaignSettings />
                    ) : activeTab === 'analysis' ? (
                        <AnalysisSettings />
                    ) : activeTab === 'flow' ? (
                        <FlowSettings />
                    ) : activeTab === 'system' ? (
                        <SystemSettings />
                    ) : (
                        <div className="p-4 border border-blue-500/20 rounded-xl bg-blue-900/10 text-blue-200">
                            <p>Contenido para la pestaña: <strong>{activeTab}</strong></p>
                            <p className="text-sm mt-2 text-blue-300/60">Los formularios se migrarán uno a uno.</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Footer Actions */}
            <div className="p-4 border-t border-white/10 bg-slate-900 sticky bottom-0 z-50 space-y-3">

                {/* Validation Warning */}
                {activeProfile === 'browser' && missingFields.length > 0 && (
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
        </div>
    )
}
