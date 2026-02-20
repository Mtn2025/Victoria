import { screen, fireEvent } from '@testing-library/react'
import { renderWithProviders } from '@/utils/test-utils'
import { CampaignSettings } from '@/components/features/Config/CampaignSettings'

describe('CampaignSettings Integration', () => {
    test('shows warning in browser profile', () => {
        // Redux default is activeProfile='browser'
        renderWithProviders(<CampaignSettings />)
        expect(screen.getByText(/Las campañas Outbound no están disponibles en modo Simulador/i)).toBeInTheDocument()
    })

    test('renders campaign form when profile is twilio/telnyx', () => {
        const preloadedState = {
            ui: { activeProfile: 'twilio', activeTab: 'campaigns', sidebarOpen: true }
        }
        renderWithProviders(<CampaignSettings />, { preloadedState })

        expect(screen.getByLabelText('Nombre de la Campaña')).toBeInTheDocument()
        expect(screen.getByLabelText('Enable CRM')).toBeInTheDocument()
    })

    test('updates integration settings', () => {
        const preloadedState = {
            ui: { activeProfile: 'telnyx', activeTab: 'campaigns', sidebarOpen: true }
        }
        const { store } = renderWithProviders(<CampaignSettings />, { preloadedState })

        const webhookInput = screen.getByLabelText('Webhook URL')
        fireEvent.change(webhookInput, { target: { value: 'https://test.com' } })

        expect(store.getState().config.browser.webhookUrl).toBe('https://test.com')
    })
})
