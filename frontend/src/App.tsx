import { Provider } from 'react-redux'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { store } from './store/store'
import { MainLayout } from './components/layout/MainLayout'
import { HistoryPage } from './pages/HistoryPage'
import { LoginPage } from './pages/LoginPage'
import { AgentsPanel } from './components/features/Agents/AgentsPanel'
import { ConfigPage } from './pages/ConfigPage'

/**
 * Router structure
 *
 * MainLayout renders:
 *   - Full-screen for /history
 *   - Split layout (left aside + always-on SimulatorPage) for all other routes
 *
 * The left aside switches content via Outlet:
 *   /simulator → ConfigPage rendered directly by MainLayout (no Outlet needed)
 *   /agents    → AgentsPanel via Outlet
 *   /config    → ConfigPage via Outlet
 *
 * SimulatorPage is always mounted in the right panel by MainLayout.
 * It is NOT a router child to avoid double-mounting.
 */
function AppWithActiveAgent() {
    return (
        <Routes>
            <Route path="/" element={<MainLayout />}>
                <Route index element={<Navigate to="/simulator" replace />} />
                {/* /simulator: MainLayout handles left panel directly (ConfigPage) */}
                {/* No child route needed — MainLayout mounts SimulatorPage in right panel */}
                <Route path="simulator" element={null} />
                <Route path="history" element={<HistoryPage />} />
                <Route path="agents" element={<AgentsPanel />} />
                <Route path="config" element={<ConfigPage />} />
                {/* Unknown paths → simulator */}
                <Route path="*" element={<Navigate to="/simulator" replace />} />
            </Route>
        </Routes>
    )
}

function App() {
    const apiKey = localStorage.getItem('api_key') || localStorage.getItem('apiKey');

    if (!apiKey) {
        return (
            <Provider store={store}>
                <BrowserRouter>
                    <Routes>
                        <Route path="*" element={<LoginPage />} />
                    </Routes>
                </BrowserRouter>
            </Provider>
        );
    }
    return (
        <Provider store={store}>
            <BrowserRouter>
                <AppWithActiveAgent />
            </BrowserRouter>
        </Provider>
    )
}

export default App
