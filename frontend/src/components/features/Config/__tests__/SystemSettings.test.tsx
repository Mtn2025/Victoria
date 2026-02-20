import { screen, fireEvent } from '@testing-library/react'
import { renderWithProviders } from '@/utils/test-utils'
import { SystemSettings } from '@/components/features/Config/SystemSettings'

describe('SystemSettings Integration', () => {
    test('renders system settings sections', () => {
        renderWithProviders(<SystemSettings />)
        expect(screen.getByText('Sistema & Gobierno')).toBeInTheDocument()
        expect(screen.getByText('Límites de Seguridad')).toBeInTheDocument()
    })

    test('updates security limits', () => {
        const { store } = renderWithProviders(<SystemSettings />)

        const concurrencyInput = screen.getByLabelText('Concurrency Limit')
        fireEvent.change(concurrencyInput, { target: { value: '50' } })
        expect(store.getState().config.browser.concurrencyLimit).toBe(50)

        const spendInput = screen.getByLabelText('Daily Spend Limit')
        fireEvent.change(spendInput, { target: { value: '25.5' } })
        expect(store.getState().config.browser.spendLimitDaily).toBe(25.5)
    })

    test('updates environment and privacy settings', () => {
        const { store } = renderWithProviders(<SystemSettings />)

        const envSelect = screen.getByLabelText('Environment Tag')
        fireEvent.change(envSelect, { target: { value: 'production' } })
        expect(store.getState().config.browser.environment).toBe('production')

        const privacyToggle = screen.getByLabelText('Privacy Mode')
        fireEvent.click(privacyToggle)
        expect(store.getState().config.browser.privacyMode).toBe(true)
    })
})
