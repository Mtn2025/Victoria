import { useState, useEffect, useCallback } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { DashboardLayout } from './DashboardLayout'
import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { setSidebarWidth } from '@/store/slices/uiSlice'
import { FEATURES } from '@/utils/featureFlags'
import { ConfigPage } from '../../pages/ConfigPage'
import SimulatorPage from '../../pages/SimulatorPage'

/**
 * MainLayout — Three-panel shell.
 *
 *  ┌──────┬──────────────────────┬──────────────────┐
 *  │ Side │  LEFT PANEL (aside)  │  RIGHT PANEL     │
 *  │  bar │  ConfigPage / Outlet │  Contextual View │
 *  └──────┴──────────────────────┴──────────────────┘
 *
 * El panel derecho depende de qué se está editando en la izquierda.
 * Si la ruta es FullScreen (/agents, /history), todo ocupa el ancho.
 *
 * Cuando un flag está en false → placeholder negro.
 * Los componentes se importan estáticamente (sin require)
 * pero solo se MONTAN cuando el flag es true, evitando así
 * que los hooks internos (WS, requests) se ejecuten prematuramente.
 *
 * ACTIVACIÓN por fase:
 *   FASE 3: SIMULATOR_PANEL + SIMULATOR_WEBSOCKET
 *   FASE 4-6: SIMULATOR_CONFIG
 *   FASE 7: AGENTS_LIST (vía App.tsx route)
 */
export const MainLayout = () => {
    const dispatch = useAppDispatch()
    const location = useLocation()
    const sidebarWidth = useAppSelector(state => state.ui.sidebarWidth)
    const activeProfile = useAppSelector(state => state.ui.activeProfile)

    const [isResizing, setIsResizing] = useState(false)

    const startResizing = useCallback(() => setIsResizing(true), [])
    const stopResizing = useCallback(() => setIsResizing(false), [])

    const resize = useCallback(
        (e: MouseEvent) => {
            if (!isResizing) return
            let w = e.clientX - 64      // 64 = Sidebar icon rail
            if (w < 280) w = 280
            if (w > 800) w = 800
            dispatch(setSidebarWidth(w))
        },
        [isResizing, dispatch]
    )

    useEffect(() => {
        window.addEventListener('mousemove', resize)
        window.addEventListener('mouseup', stopResizing)
        return () => {
            window.removeEventListener('mousemove', resize)
            window.removeEventListener('mouseup', stopResizing)
        }
    }, [resize, stopResizing])

    // Dispatch fetchActiveAgent only when the agents feature is live.
    useEffect(() => {
        if (!FEATURES.AGENTS_LIST) return
        import('@/store/slices/agentsSlice').then(({ fetchActiveAgent }) => {
            dispatch(fetchActiveAgent() as Parameters<typeof dispatch>[0])
        })
    }, [dispatch])

    // Routes that take the full width (no split layout)
    const isFullScreenRoute = ['/history', '/agents'].includes(location.pathname)

    if (isFullScreenRoute) {
        return (
            <DashboardLayout>
                <div className="flex-1 overflow-hidden">
                    <Outlet />
                </div>
            </DashboardLayout>
        )
    }

    const isSimulatorRoute = location.pathname === '/simulator'

    return (
        <DashboardLayout>
            {/* ── LEFT PANEL (resizable context) ───────────────────────────── */}
            <aside
                className="flex-none flex flex-col bg-slate-900/90 backdrop-blur-md border-r border-white/5 z-20 relative shadow-2xl shrink-0"
                style={{ width: isSimulatorRoute ? sidebarWidth : '100%' }}
            >
                {/* Resize handle (only visible when there is a split) */}
                {isSimulatorRoute && (
                    <div
                        className="absolute top-0 right-0 w-1.5 h-full cursor-col-resize hover:bg-blue-500/50 z-[100] transition-colors"
                        onMouseDown={startResizing}
                    />
                )}

                {/* Content: ConfigPage (simulator) | Outlet (other split cases if needed) | placeholder */}
                {FEATURES.SIMULATOR_CONFIG ? (
                    isSimulatorRoute ? <ConfigPage /> : <Outlet />
                ) : (
                    <PanelPlaceholder label="panel config" />
                )}
            </aside>

            {/* ── RIGHT PANEL (Contextual Display) ───────────────────────── */}
            {isSimulatorRoute && (
                <div className="flex-1 overflow-hidden bg-slate-950 relative min-w-0">
                    {!FEATURES.SIMULATOR_PANEL ? (
                        <PanelPlaceholder label="simulador web" />
                    ) : activeProfile === 'browser' ? (
                        <SimulatorPage />
                    ) : (
                        <TelephonyPlaceholder profile={activeProfile} />
                    )}
                </div>
            )}
        </DashboardLayout>
    )
}

// ── Internal placeholder — keeps the DOM clean in FREEZE mode ─────────────────
const PanelPlaceholder = ({ label }: { label: string }) => (
    <div className="h-full w-full flex items-center justify-center bg-slate-950">
        <span className="text-slate-800 text-xs font-mono select-none">
            [ {label} — desactivado ]
        </span>
    </div>
)

const TelephonyPlaceholder = ({ profile }: { profile: string }) => (
    <div className="h-full w-full flex flex-col items-center justify-center bg-slate-950 p-8 text-center space-y-4">
        <div className="w-16 h-16 rounded-full bg-slate-800/80 flex items-center justify-center mb-2 shadow-inner border border-slate-700/50">
            <span className="text-2xl">{profile === 'twilio' ? '📱' : '📡'}</span>
        </div>
        <h3 className="text-slate-200 font-semibold text-lg tracking-wide">
            Pruebas con {profile === 'twilio' ? 'Telefonía Twilio' : 'Telefonía Telnyx'}
        </h3>
        <p className="text-slate-500 text-sm max-w-md">
            El entorno de prueba interactivo de navegador no está disponible para este proveedor.
        </p>
        <div className="mt-4 px-4 py-2 bg-blue-500/10 border border-blue-500/20 rounded-lg">
            <p className="text-blue-400 text-xs">
                La configuración seleccionada se almacenará, pero para probar la respuesta del agente real,
                deberás marcar al número telefónico asignado en tu cuenta desde un teléfono físico.
            </p>
        </div>
    </div>
)
