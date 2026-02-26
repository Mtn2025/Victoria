import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './styles/globals.css'
import { Provider } from 'react-redux'
import { store } from './store/store.ts'
import { I18nProvider } from './i18n/I18nContext.tsx'

// Aplicar escala de fuente inmediatamente para evitar FOUC
const savedScale = localStorage.getItem('fontScale') || 'sm';
document.body.setAttribute('data-font-scale', savedScale);

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <Provider store={store}>
            <I18nProvider>
                <App />
            </I18nProvider>
        </Provider>
    </React.StrictMode>,
)
