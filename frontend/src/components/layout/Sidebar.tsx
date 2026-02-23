import { useNavigate, useLocation } from "react-router-dom"
import { useAppDispatch, useAppSelector } from "@/hooks/useRedux"
import { setActiveTab, DashboardTab } from "@/store/slices/uiSlice"
import { FEATURES } from "@/utils/featureFlags"
import { cn } from "@/utils/cn"
import {
    Bot,
    Cpu,
    Mic,
    Ear,
    Briefcase,
    Megaphone,
    Zap,
    Shield,
    Settings,
    History,
    GitCompare,
    Activity,
    LogOut,
    LucideIcon,
    Lock,
} from "lucide-react"

// Types of nav items
type NavItemType = 'page' | 'config'

interface NavItem {
    type: NavItemType
    label: string
    icon: LucideIcon
    id?: DashboardTab    // For config items
    path?: string        // For page items
    // Feature flag key that gates this item. If undefined → always accessible.
    featureKey?: keyof typeof FEATURES
    isTelephonyOnly?: boolean
}

const NAV_ITEMS: NavItem[] = [
    // ── Pages ──────────────────────────────────────────────────────────────
    { type: 'page', path: '/agents', label: 'Agentes', icon: Bot, featureKey: 'AGENTS_LIST' },

    // ── Config Tabs (activar uno por uno por fase) ──────────────────────────
    { type: 'config', id: 'model', label: 'Asistente', icon: Cpu, featureKey: 'CONFIG_MODEL' },
    { type: 'config', id: 'voice', label: 'Voz', icon: Mic, featureKey: 'CONFIG_VOICE' },
    { type: 'config', id: 'transcriber', label: 'Oído', icon: Ear, featureKey: 'CONFIG_TRANSCRIBER' },
    { type: 'config', id: 'campaigns', label: 'Campañas', icon: Megaphone, isTelephonyOnly: true, featureKey: 'CONFIG_CAMPAIGNS' },
    { type: 'config', id: 'flow', label: 'Flujo', icon: GitCompare, featureKey: 'CONFIG_FLOW' },
    { type: 'config', id: 'analysis', label: 'Análisis', icon: Activity, featureKey: 'CONFIG_ANALYSIS' },
    { type: 'config', id: 'connectivity', label: 'Conectividad', icon: Zap, isTelephonyOnly: true, featureKey: 'CONFIG_CONNECTIVITY' },
    { type: 'config', id: 'system', label: 'Sistema', icon: Shield, featureKey: 'CONFIG_SYSTEM' },
    { type: 'config', id: 'advanced', label: 'Avanzado', icon: Settings, featureKey: 'CONFIG_ADVANCED' },
    { type: 'config', id: 'tools', label: 'Herramientas', icon: Briefcase, featureKey: 'CONFIG_TOOLS' },

    // ── Pages (continued) ──────────────────────────────────────────────────
    { type: 'page', path: '/history', label: 'Historial', icon: History, featureKey: 'HISTORY_LIST' },
]

export const Sidebar = () => {
    const dispatch = useAppDispatch()
    const navigate = useNavigate()
    const location = useLocation()
    const activeTab = useAppSelector((state) => state.ui.activeTab)
    const activeProfile = useAppSelector((state) => state.ui.activeProfile)
    const activeAgent = useAppSelector((state) => state.agents.activeAgent)

    const handleNavigation = (item: NavItem) => {
        // If gated by a feature flag that is off → do nothing
        if (item.featureKey && !FEATURES[item.featureKey]) return

        // Config tabs without a featureKey are still stubs (FASE 9) → do nothing
        if (item.type === 'config' && !item.featureKey) return

        if (item.type === 'page' && item.path) {
            navigate(item.path)
        } else if (item.type === 'config' && item.id) {
            dispatch(setActiveTab(item.id))
            if (location.pathname !== '/simulator') {
                navigate('/simulator')
            }
        }
    }

    const handleLogout = () => {
        localStorage.removeItem('api_key')
        localStorage.removeItem('apiKey')
        window.location.href = '/'
    }

    return (
        <nav className="w-16 flex-none bg-slate-950 border-r border-slate-800 flex flex-col items-center py-4 z-30">
            {/* Brand Logo */}
            <div className="mb-6 w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white font-bold shadow-lg shadow-blue-500/20">
                <span className="text-sm">IA</span>
            </div>

            {/* Nav Items */}
            <div className="flex-1 w-full px-2 space-y-2 flex flex-col items-center overflow-y-auto custom-scrollbar">
                {NAV_ITEMS.map((item, index) => {
                    const Icon = item.icon

                    // Telephony specific tabs hidden from Browser profile
                    if ((item as any).isTelephonyOnly && activeProfile === 'browser') {
                        return null
                    }

                    // Is this item gated and disabled?
                    let isDisabled = (item.featureKey && !FEATURES[item.featureKey]) ||
                        (item.type === 'config' && !item.featureKey)

                    // NEW RULE: If it's a config tab, it MUST have an active agent to click it.
                    if (item.type === 'config' && !activeAgent) {
                        isDisabled = true
                    }

                    // Determine Active State
                    let isActive = false
                    if (!isDisabled) {
                        if (item.type === 'page') {
                            isActive = location.pathname === item.path
                        } else if (item.type === 'config') {
                            isActive = location.pathname === '/simulator' && activeTab === item.id
                        }
                    }

                    return (
                        <div key={index} className="group relative flex flex-col items-center justify-center w-full">
                            <button
                                onClick={() => handleNavigation(item)}
                                title={item.label}
                                disabled={!!isDisabled}
                                className={cn(
                                    "w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 relative",
                                    isDisabled
                                        ? "text-slate-800 cursor-not-allowed"
                                        : isActive
                                            ? "bg-blue-600 text-white shadow-lg shadow-blue-900/20 group-hover:scale-105"
                                            : "text-slate-500 hover:text-slate-300 hover:bg-slate-800/50 group-hover:scale-105"
                                )}
                            >
                                <Icon size={20} />
                                {/* Lock icon for disabled items */}
                                {isDisabled && (
                                    <Lock
                                        size={8}
                                        className="absolute bottom-1.5 right-1.5 text-slate-700"
                                    />
                                )}
                            </button>

                            {/* Agent name below Bot icon */}
                            {item.path === '/agents' && !isDisabled && (
                                <span className={cn(
                                    "text-[9px] leading-tight text-center max-w-[52px] truncate mt-0.5",
                                    activeAgent ? "text-blue-400" : "text-amber-500"
                                )}>
                                    {activeAgent ? activeAgent.name : "Sin agente"}
                                </span>
                            )}

                            {/* Tooltip */}
                            <div className="absolute left-14 bg-slate-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50 border border-slate-700 font-medium">
                                {item.label}
                                {isDisabled && (item.type === 'config' && !activeAgent && FEATURES[item.featureKey!]
                                    ? <span className="ml-1 text-slate-500">(Requiere Agent Activo)</span>
                                    : <span className="ml-1 text-slate-500">(próx. fase)</span>
                                )}
                            </div>
                        </div>
                    )
                })}
            </div>

            {/* Bottom Actions */}
            <div className="mt-auto px-2 space-y-2 pt-4">
                <button
                    onClick={handleLogout}
                    title="Cerrar Sesión"
                    className="w-10 h-10 rounded-xl flex items-center justify-center text-red-500 hover:text-red-300 hover:bg-red-500/10 transition-all font-medium"
                >
                    <LogOut size={20} />
                </button>
            </div>
        </nav>
    )
}
