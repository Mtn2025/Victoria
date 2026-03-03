import { SignalHigh, Globe, Smartphone, Radio, LucideIcon } from "lucide-react"
import { useAppSelector, useAppDispatch } from "@/hooks/useRedux"
import { setActiveProfile, ProfileId } from "@/store/slices/uiSlice"
import { cn } from "@/utils/cn"

const PROFILES: { id: ProfileId; label: string; icon: LucideIcon }[] = [
    { id: 'browser', label: 'Navegador Web', icon: Globe },
    { id: 'twilio', label: 'Red Twilio', icon: Smartphone },
    { id: 'telnyx', label: 'Red Telnyx', icon: Radio },
]

export const Header = () => {
    const dispatch = useAppDispatch()
    const activeAgent = useAppSelector(state => state.agents.activeAgent)
    const activeProfile = useAppSelector(state => state.ui.activeProfile)

    return (
        <div className="h-16 flex items-center justify-between px-8 border-b border-white/5 shrink-0 bg-slate-950/50 backdrop-blur-sm z-50">
            <div className="flex items-center space-x-6">
                <h1 className="font-bold text-lg text-slate-100">Simulador de Conversación</h1>

                {/* Global Provider Switcher */}
                <div className="flex bg-slate-900 rounded-lg p-1 border border-slate-800 space-x-1 shadow-inner">
                    {PROFILES.map((p) => {
                        const Icon = p.icon
                        const isActive = activeProfile === p.id
                        return (
                            <button
                                key={p.id}
                                onClick={() => dispatch(setActiveProfile(p.id))}
                                title={p.label}
                                className={cn(
                                    "w-8 h-8 rounded-md flex items-center justify-center transition-all relative flex-shrink-0 group",
                                    isActive
                                        ? "bg-blue-600/20 text-blue-400 shadow-sm ring-1 ring-blue-500/30"
                                        : "text-slate-500 hover:text-slate-300 hover:bg-slate-800/50"
                                )}
                            >
                                <Icon size={16} className={cn("transition-transform", isActive ? "scale-110" : "group-hover:scale-110")} />
                            </button>
                        )
                    })}
                </div>
            </div>
            <div className="flex items-center space-x-4 text-xs text-slate-500">
                {/* Active Agent Indicator */}
                <span className={activeAgent ? "text-blue-400 font-medium" : "text-amber-500"}>
                    {activeAgent ? `Agente: ${activeAgent.name}` : "Sin agente activo"}
                </span>
                <div className="h-4 w-px bg-white/10" />
                <span className="flex items-center gap-2">
                    <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                    </span>
                    Sistema en línea
                </span>
                <div className="h-4 w-px bg-white/10" />
                <span className="flex items-center gap-2 text-slate-400">
                    <SignalHigh size={14} />
                    5ms
                </span>
            </div>
        </div>
    )
}

