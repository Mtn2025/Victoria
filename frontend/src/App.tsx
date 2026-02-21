import { Provider } from 'react-redux'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { store } from './store/store'
import { MainLayout } from './components/layout/MainLayout'
import { LoginPage } from './pages/LoginPage'
import { FeatureGate } from './components/ui/FeatureGate'

// Lazy-imported pages — only mounted when their feature flag is ON
import { HistoryPage } from './pages/HistoryPage'
import { AgentsPanel } from './components/features/Agents/AgentsPanel'
import { ConfigPage } from './pages/ConfigPage'

/**
 * App — Router principal
 *
 * Cada ruta está envuelta con <FeatureGate feature="..."> para poder
 * activarse/desactivarse sin tocar código de negocio.
 *
 * Orden de activación (ver featureFlags.ts):
 *   AUTH              → siempre activo
 *   SIMULATOR_PANEL   → Fase 2
 *   AGENTS_LIST       → Fase 3
 *   CONFIG_MODEL      → Fase 4
 *   HISTORY_LIST      → Fase 5
 */
function AppRoutes() {
    return (
        <Routes>
            <Route path="/" element={<MainLayout />}>
                <Route index element={<Navigate to="/simulator" replace />} />

                {/* /simulator: el layout maneja los paneles internamente */}
                <Route path="simulator" element={null} />

                {/* /history — Fase 5 */}
                <Route
                    path="history"
                    element={
                        <FeatureGate feature="HISTORY_LIST">
                            <HistoryPage />
                        </FeatureGate>
                    }
                />

                {/* /agents — Fase 3 */}
                <Route
                    path="agents"
                    element={
                        <FeatureGate feature="AGENTS_LIST">
                            <AgentsPanel />
                        </FeatureGate>
                    }
                />

                {/* /config — Fase 4 */}
                <Route
                    path="config"
                    element={
                        <FeatureGate feature="CONFIG_MODEL">
                            <ConfigPage />
                        </FeatureGate>
                    }
                />

                {/* Fallback → simulator */}
                <Route path="*" element={<Navigate to="/simulator" replace />} />
            </Route>
        </Routes>
    )
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
