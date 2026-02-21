import { Provider } from 'react-redux'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { store } from './store/store'
import { MainLayout } from './components/layout/MainLayout'
import SimulatorPage from './pages/SimulatorPage'
import { HistoryPage } from './pages/HistoryPage'
import { LoginPage } from './pages/LoginPage'
import { AgentsPanel } from './components/features/Agents/AgentsPanel'
import { ConfigPage } from './pages/ConfigPage'

function AppWithActiveAgent() {
    return (
        <Routes>
            <Route path="/" element={<MainLayout />}>
                <Route index element={<Navigate to="/agents" replace />} />
                <Route path="simulator" element={<SimulatorPage />} />
                <Route path="history" element={<HistoryPage />} />
                <Route path="agents" element={<AgentsPanel />} />
                <Route path="config" element={<ConfigPage />} />
                {/* Unknown paths → agent selection */}
                <Route path="*" element={<Navigate to="/agents" replace />} />
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
