import { screen, fireEvent } from '@testing-library/react'
import { renderWithProviders } from '@/utils/test-utils'
import { AnalysisSettings } from '@/components/features/Config/AnalysisSettings'
import { FlowSettings } from '@/components/features/Config/FlowSettings'

describe('AnalysisSettings Integration', () => {
    test('renders tabs and contents', () => {
        renderWithProviders(<AnalysisSettings />)
        expect(screen.getByText('Análisis & Datos')).toBeInTheDocument()

        // Default prompt tab
        expect(screen.getByLabelText('Analysis Prompt')).toBeInTheDocument()
    })

    test('switches inner tabs', () => {
        renderWithProviders(<AnalysisSettings />)

        const dataTab = screen.getByText('💾 Extraction Data')
        fireEvent.click(dataTab)
        expect(screen.getByLabelText('Extraction Schema')).toBeInTheDocument()

        const webhookTab = screen.getByText('📡 Webhooks')
        fireEvent.click(webhookTab)
        expect(screen.getByLabelText('Log Webhook URL')).toBeInTheDocument()
    })

    test('updates redux state', () => {
        const { store } = renderWithProviders(<AnalysisSettings />)
        const promptInput = screen.getByLabelText('Analysis Prompt')
        fireEvent.change(promptInput, { target: { value: 'New Prompt' } })
        expect(store.getState().config.browser.analysisPrompt).toBe('New Prompt')
    })
})

describe('FlowSettings Integration', () => {
    test('renders flow settings', () => {
        renderWithProviders(<FlowSettings />)
        expect(screen.getByText('Interrupciones (Barge-in)')).toBeInTheDocument()
    })

    test('updates barge-in checkbox', () => {
        const { store } = renderWithProviders(<FlowSettings />)
        const checkbox = screen.getByLabelText('Barge-in Logic')
        // Toggle from default true -> false
        fireEvent.click(checkbox)
        expect(store.getState().config.browser.bargeInEnabled).toBe(false)
    })

    test('updates response delay', () => {
        const { store } = renderWithProviders(<FlowSettings />)
        const slider = screen.getByLabelText('Response Delay')
        fireEvent.change(slider, { target: { value: '1.5' } })
        expect(store.getState().config.browser.responseDelaySeconds).toBe(1.5)
    })
})
