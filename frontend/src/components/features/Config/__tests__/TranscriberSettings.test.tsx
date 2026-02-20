import { screen, fireEvent } from '@testing-library/react'
import { renderWithProviders } from '@/utils/test-utils'
import { TranscriberSettings } from '@/components/features/Config/TranscriberSettings'

describe('TranscriberSettings Integration', () => {
    test('renders all sections correctly', () => {
        renderWithProviders(<TranscriberSettings />)

        expect(screen.getByText('Configuración de Transcripción (STT)')).toBeInTheDocument()
        expect(screen.getByText('Control de Interrupciones')).toBeInTheDocument()
        expect(screen.getByText('🧠 Inteligencia de Transcripción')).toBeInTheDocument()
    })

    test('updates redux state when inputs change', () => {
        const { store } = renderWithProviders(<TranscriberSettings />)

        // Change Provider
        const providerSelect = screen.getByLabelText('Proveedor STT')
        fireEvent.change(providerSelect, { target: { value: 'deepgram' } })
        expect(store.getState().config.browser.sttProvider).toBe('deepgram')

        // Change Utterance End (Semantic Interruption)
        const interruptionToggle = screen.getByLabelText('Interrupción Inteligente')
        fireEvent.click(interruptionToggle)
        expect(store.getState().config.browser.sttUtteranceEnd).toBe('semantic')

        // Change VAD Sensitivity
        const vadSlider = screen.getByLabelText('Sensibilidad VAD')
        fireEvent.change(vadSlider, { target: { value: '0.9' } })
        expect(store.getState().config.browser.vad_threshold).toBe(0.9)
    })
})
