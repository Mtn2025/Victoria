import { screen, fireEvent } from '@testing-library/react'
import { renderWithProviders } from '@/utils/test-utils'
import { ModelSettings } from '@/components/features/Config/ModelSettings'

describe('ModelSettings Integration', () => {
    test('renders all sections correctly', () => {
        renderWithProviders(<ModelSettings />)

        expect(screen.getByText('Proveedor LLM')).toBeInTheDocument()
        expect(screen.getByText('Estilo de Conversación')).toBeInTheDocument()
        expect(screen.getByText('Controles Avanzados de Inteligencia')).toBeInTheDocument()
        expect(screen.getByText('Lista Negra (Hallucination Safety)')).toBeInTheDocument()
    })

    test('updates redux state when inputs change', () => {
        const { store } = renderWithProviders(<ModelSettings />)

        // Initial State
        expect(store.getState().config.browser.temp).toBe(0.5)

        // Change Temperature
        const tempInput = screen.getByLabelText('Creatividad (Temperature)')
        fireEvent.change(tempInput, { target: { value: '0.8' } })

        expect(store.getState().config.browser.temp).toBe(0.8)
    })
})
