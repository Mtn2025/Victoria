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
 *  │  bar │  ConfigPage / Outlet │  SimulatorPage   │
 *  └──────┴──────────────────────┴──────────────────┘
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
    const isFullScreenRoute = ['/history'].includes(location.pathname)

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
            {/* ── LEFT PANEL (resizable) ───────────────────────────── */}
            <aside
                className="flex-none flex flex-col bg-slate-900/90 backdrop-blur-md border-r border-white/5 z-20 relative shadow-2xl shrink-0"
                style={{ width: sidebarWidth }}
            >
                {/* Resize handle */}
                <div
                    className="absolute top-0 right-0 w-1.5 h-full cursor-col-resize hover:bg-blue-500/50 z-[100] transition-colors"
                    onMouseDown={startResizing}
                />

                {/* Content: ConfigPage (simulator) | Outlet (agents/config) | placeholder */}
                {FEATURES.SIMULATOR_CONFIG ? (
                    isSimulatorRoute ? <ConfigPage /> : <Outlet />
                ) : (
                    <PanelPlaceholder label="panel config" />
                )}
            </aside>

            {/* ── RIGHT PANEL ──────────────────────────────────────── */}
            <div className="flex-1 overflow-hidden bg-slate-950 relative min-w-0">
                {FEATURES.SIMULATOR_PANEL
                    ? <SimulatorPage />
                    : <PanelPlaceholder label="simulador" />
                }
            </div>
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
