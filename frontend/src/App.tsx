import { Provider } from 'react-redux'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { store } from './store/store'
import { MainLayout } from './components/layout/MainLayout'
import { LoginPage } from './pages/LoginPage'
import { FeatureGate } from './components/ui/FeatureGate'

/**
 * App — Router principal
 *
 * Cada ruta está envuelta con <FeatureGate feature="..."> para poder
 * activarse/desactivarse sin tocar código de negocio.
 *
 * Orden de activación (ver featureFlags.ts):
 *   AUTH              → siempre activo
 *   SIMULATOR_PANEL   → FASE 3
 *   AGENTS_LIST       → FASE 7
 *   CONFIG_MODEL      → FASE 4
 *   HISTORY_LIST      → FASE 8
 */
function AppRoutes() {
    return (
        <Routes>
            <Route path="/" element={<MainLayout />}>
                <Route index element={<Navigate to="/simulator" replace />} />

                {/* /simulator: MainLayout maneja los paneles internamente */}
                <Route path="simulator" element={null} />

                {/* /history — FASE 8 */}
                <Route
                    path="history"
                    element={
                        <FeatureGate feature="HISTORY_LIST">
                            {/* Dynamic import here — component only loaded when flag is true */}
                            <LazyHistoryPage />
                        </FeatureGate>
                    }
                />

                {/* /agents — FASE 7 */}
                <Route
                    path="agents"
                    element={
                        <FeatureGate feature="AGENTS_LIST">
                            <LazyAgentsPanel />
                        </FeatureGate>
                    }
                />

                {/* Fallback → simulator */}
                <Route path="*" element={<Navigate to="/simulator" replace />} />
            </Route>
        </Routes>
    )
}

// ── Lazy wrappers (evitan cargar código de features desactivadas) ────────────
const LazyHistoryPage = () => {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { HistoryPage } = require('./pages/HistoryPage')
    return <HistoryPage />
}

const LazyAgentsPanel = () => {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { AgentsPanel } = require('./components/features/Agents/AgentsPanel')
    return <AgentsPanel />
}

function App() {
    const apiKey = localStorage.getItem('api_key')

    if (!apiKey) {
        return (
            <Provider store={store}>
                <BrowserRouter>
                    <Routes>
                        <Route path="*" element={<LoginPage />} />
                    </Routes>
                </BrowserRouter>
            </Provider>
        )
    }

    return (
        <Provider store={store}>
            <BrowserRouter>
                <AppRoutes />
            </BrowserRouter>
        </Provider>
    )
}

export default App
