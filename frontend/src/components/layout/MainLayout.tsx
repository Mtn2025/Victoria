import { useState, useEffect, useCallback } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { DashboardLayout } from './DashboardLayout'
import { ConfigPage } from '../../pages/ConfigPage'
import SimulatorPage from '../../pages/SimulatorPage'
import { useAppDispatch, useAppSelector } from '@/hooks/useRedux'
import { setSidebarWidth } from '@/store/slices/uiSlice'
import { fetchActiveAgent } from '@/store/slices/agentsSlice'
import { FeatureGate } from '../ui/FeatureGate'

/**
 * MainLayout — Restores the original three-panel design:
 *
 *  ┌──────┬──────────────────────┬──────────────────┐
 *  │ Side │  LEFT PANEL (aside)  │  RIGHT PANEL     │
 *  │  bar │  - /simulator →      │  SimulatorPage   │
 *  │      │    ConfigPage        │  (always visible) │
 *  │      │  - /agents →         │                  │
 *  │      │    AgentsPanel       │                  │
 *  │      │  - /config →         │                  │
 *  │      │    ConfigPage        │                  │
 *  └──────┴──────────────────────┴──────────────────┘
 *
 *  Special routes (/history) are rendered full-width
 *  without the split (Outlet replaces both panels).
 *
 *  CRITICAL: ConfigPage is NOT hardcoded here.
 *  It appears in the left panel ONLY when the route is
 *  /simulator or /config. The router drives the left panel.
 *  The right panel (SimulatorPage) is always mounted but
 *  hidden via CSS when not needed.
 *
 *  This prevents the double-render bug: the router Outlet
 *  renders the left panel content, SimulatorPage lives
 *  permanently in the right panel.
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

    // Fetch global active agent on mount so ConfigPage doesn't redirect
    // to frozen /agents panel.
    useEffect(() => {
        dispatch(fetchActiveAgent())
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

    // /simulator shows ConfigPage in left + SimulatorPage in right
    // /agents and /config show Outlet content in left + SimulatorPage in right
    const isSimulatorRoute = location.pathname === '/simulator'

    return (
        <DashboardLayout>
            {/* LEFT PANEL — resizable */}
            <aside
                className="flex-none flex flex-col bg-slate-900/90 backdrop-blur-md border-r border-white/5 z-20 relative shadow-2xl shrink-0"
                style={{ width: sidebarWidth }}
            >
                {/* Resize Handle */}
                <div
                    className="absolute top-0 right-0 w-1.5 h-full cursor-col-resize hover:bg-blue-500/50 z-[100] transition-colors"
                    onMouseDown={startResizing}
                />

                {/*
                 * /simulator → shows ConfigPage (driven by Redux activeTab)
                 * /agents    → shows AgentsPanel  (via Outlet)
                 * /config    → shows ConfigPage   (via Outlet — same component)
                 *
                 * We render both but only show the relevant one to avoid
                 * remounting SimulatorPage or losing its WebSocket state.
                 */}
                {isSimulatorRoute ? (
                    <FeatureGate feature="SIMULATOR_CONFIG">
                        <ConfigPage />
                    </FeatureGate>
                ) : (
                    <Outlet />
                )}
            </aside>

            {/* RIGHT PANEL — always SimulatorPage */}
            <div className="flex-1 overflow-hidden bg-slate-950 relative min-w-0">
                <FeatureGate feature="SIMULATOR_PANEL">
                    <SimulatorPage />
                </FeatureGate>
            </div>
        </DashboardLayout>
    )
}
