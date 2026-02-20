import { screen, fireEvent, act } from '@testing-library/react'
import { renderWithProviders } from '@/utils/test-utils'
import { AdvancedSettings } from '@/components/features/Config/AdvancedSettings'

describe('AdvancedSettings Integration', () => {
    test('renders advanced settings sections', () => {
        renderWithProviders(<AdvancedSettings />)
        expect(screen.getByText('Calidad y Latencia')).toBeInTheDocument()
        expect(screen.getByLabelText('Paciencia del Asistente')).toBeInTheDocument()
    })

    test('updates patience slider', () => {
        const { store } = renderWithProviders(<AdvancedSettings />)

        const slider = screen.getByLabelText('Paciencia del Asistente')
        fireEvent.change(slider, { target: { value: '1.0' } })

        // Check Redux (ms)
        expect(store.getState().config.browser.sttSilenceTimeout).toBe(1000)
    })

    test('updates noise suppression level', () => {
        const { store } = renderWithProviders(<AdvancedSettings />)

        const highBtn = screen.getByLabelText('Noise Suppression high')
        fireEvent.click(highBtn)

        expect(store.getState().config.browser.noiseSuppressionLevel).toBe('high')
    })

    test('updates codec', () => {
        const { store } = renderWithProviders(<AdvancedSettings />)
        const select = screen.getByLabelText('Codec Selection')
        fireEvent.change(select, { target: { value: 'OPUS' } })
        expect(store.getState().config.browser.audioCodec).toBe('OPUS')
    })
})
