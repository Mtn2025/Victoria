import { screen, fireEvent } from '@testing-library/react'
import { renderWithProviders } from '@/utils/test-utils'
import { ConnectivitySettings } from '@/components/features/Config/ConnectivitySettings'

describe('ConnectivitySettings Integration', () => {
    test('renders main sections', () => {
        renderWithProviders(<ConnectivitySettings />)
        expect(screen.getByText('Conectividad & Hardware')).toBeInTheDocument()
    })

    test('switches tabs and updates redux keys', () => {
        const { store } = renderWithProviders(<ConnectivitySettings />)

        // Default Tab: Keys
        const fromNumberInput = screen.getByLabelText('Twilio From Number')
        fireEvent.change(fromNumberInput, { target: { value: '+15550001' } })
        expect(store.getState().config.twilio.twilioFromNumber).toBe('+15550001')

        // Switch to SIP Tab
        fireEvent.click(screen.getByText('📡 SIP & Trunking'))

        // Verify SIP inputs visible
        const sipUriInput = screen.getByLabelText('Twilio SIP Trunk URI')
        fireEvent.change(sipUriInput, { target: { value: 'sip:example.com' } })
        expect(store.getState().config.twilio.sipTrunkUriPhone).toBe('sip:example.com')

        // Verify Fallback Number (Added field)
        const fallbackInput = screen.getByLabelText('Fallback Number')
        fireEvent.change(fallbackInput, { target: { value: '+19999999' } })
        expect(store.getState().config.twilio.fallbackNumberPhone).toBe('+19999999')
    })

    test('updates features tab settings', () => {
        const { store } = renderWithProviders(<ConnectivitySettings />)

        // Switch to Features Tab
        fireEvent.click(screen.getByText('⚙️ Opciones Llamada'))

        // Toggle HIPAA
        const hipaaTwilio = screen.getByLabelText('Enable Twilio HIPAA')
        fireEvent.click(hipaaTwilio)
        expect(store.getState().config.twilio.hipaaEnabledPhone).toBe(true)

        // Change Telnyx Recording Channels
        const telnyxChannels = screen.getByLabelText('Telnyx Recording Channels')
        fireEvent.change(telnyxChannels, { target: { value: 'dual' } })
        expect(store.getState().config.telnyx.recordingChannelsTelnyx).toBe('dual')
    })
})
