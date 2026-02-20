import { Provider } from 'react-redux'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { store } from './store/store'
import { MainLayout } from './components/layout/MainLayout'
import SimulatorPage from './pages/SimulatorPage'
import { HistoryPage } from './pages/HistoryPage'
import { LoginPage } from './pages/LoginPage'

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
                <Routes>
                    <Route path="/" element={<MainLayout />}>
                        <Route index element={<Navigate to="/simulator" replace />} />
                        <Route path="simulator" element={<SimulatorPage />} />
                        <Route path="history" element={<HistoryPage />} />
                        {/* Fallback to simulator */}
                        <Route path="*" element={<Navigate to="/simulator" replace />} />
                    </Route>
                </Routes>
            </BrowserRouter>
        </Provider>
    )
}

export default App
