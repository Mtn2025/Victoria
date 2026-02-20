import { useNavigate, useLocation } from "react-router-dom"
import { useAppDispatch, useAppSelector } from "@/hooks/useRedux"
import { setActiveTab, DashboardTab } from "@/store/slices/uiSlice"
import { cn } from "@/utils/cn"
import {
    Cpu,
    Mic,
    Ear,
    Briefcase,
    Megaphone,
    Zap,
    Shield,
    Settings,
    History,
    Info,
    GitCompare,
    Activity,
    LucideIcon,
    Globe
} from "lucide-react"

// Types of nav items
type NavItemType = 'page' | 'config'

interface NavItem {
    type: NavItemType
    label: string
    icon: LucideIcon
    id?: DashboardTab    // For config items
    path?: string        // For page items
}

const NAV_ITEMS: NavItem[] = [
    // --- Pages ---
    { type: 'page', path: '/simulator', label: 'Simulador', icon: Globe }, // Main view

    // --- Config Tabs (Update Redux + Ensure on Simulator) ---
    { type: 'config', id: 'model', label: 'Modelo', icon: Cpu },
    { type: 'config', id: 'voice', label: 'Voz', icon: Mic },
    { type: 'config', id: 'transcriber', label: 'Oído', icon: Ear },
    { type: 'config', id: 'tools', label: 'Herramientas', icon: Briefcase },
    { type: 'config', id: 'campaigns', label: 'Campañas', icon: Megaphone },
    { type: 'config', id: 'flow', label: 'Flujo', icon: GitCompare },
    { type: 'config', id: 'analysis', label: 'Análisis', icon: Activity },
    { type: 'config', id: 'connectivity', label: 'Conectividad', icon: Zap },
    { type: 'config', id: 'system', label: 'Sistema', icon: Shield },
    { type: 'config', id: 'advanced', label: 'Avanzado', icon: Settings },

    // --- Pages ---
    { type: 'page', path: '/history', label: 'Historial', icon: History },
]

export const Sidebar = () => {
    const dispatch = useAppDispatch()
    const navigate = useNavigate()
    const location = useLocation()
    const activeTab = useAppSelector((state) => state.ui.activeTab)

    const handleNavigation = (item: NavItem) => {
        if (item.type === 'page' && item.path) {
            navigate(item.path)
        } else if (item.type === 'config' && item.id) {
            // Update config tab
            dispatch(setActiveTab(item.id))
            // Ensure we are on the simulator page to see the agent + config
            if (location.pathname !== '/simulator') {
                navigate('/simulator')
            }
        }
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

                    // Determine Active State
                    let isActive = false
                    if (item.type === 'page') {
                        isActive = location.pathname === item.path
                    } else if (item.type === 'config') {
                        // It's active if we are on simulator AND this tab is selected
                        isActive = location.pathname === '/simulator' && activeTab === item.id
                    }

                    return (
                        <div key={index} className="group relative flex items-center justify-center">
                            <button
                                onClick={() => handleNavigation(item)}
                                title={item.label}
                                className={cn(
                                    "w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 relative group-hover:scale-105",
                                    isActive
                                        ? "bg-blue-600 text-white shadow-lg shadow-blue-900/20"
                                        : "text-slate-500 hover:text-slate-300 hover:bg-slate-800/50"
                                )}
                            >
                                <Icon size={20} />
                            </button>

                            {/* Tooltip */}
                            <div className="absolute left-14 bg-slate-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50 border border-slate-700 font-medium">
                                {item.label}
                            </div>
                        </div>
                    )
                })}
            </div>

            {/* Bottom Actions */}
            <div className="mt-auto px-2 space-y-2 pt-4">
                <button className="w-10 h-10 rounded-xl flex items-center justify-center text-slate-500 hover:text-slate-300 hover:bg-slate-800/50 transition-all">
                    <Info size={20} />
                </button>
            </div>
        </nav>
    )
}
