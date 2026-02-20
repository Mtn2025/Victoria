import { screen, fireEvent } from '@testing-library/react'
import { renderWithProviders } from '@/utils/test-utils'
import { VoiceSettings } from '@/components/features/Config/VoiceSettings'

describe('VoiceSettings Integration', () => {
    test('renders all sections correctly', () => {
        renderWithProviders(<VoiceSettings />)

        expect(screen.getByText('Configuración de Voz (TTS)')).toBeInTheDocument()

        // Humanization section
        expect(screen.getByText('🗣️ Humanización')).toBeInTheDocument()

        // Tech section
        expect(screen.getByText('⚙️ Ajustes Técnicos')).toBeInTheDocument()
    })

    test('updates redux state when inputs change', () => {
        // Mock state with ElevenLabs provider to show advanced settings
        const preloadedState = {
            config: {
                browser: {
                    voiceProvider: 'elevenlabs',
                    voiceStability: 0.5
                },
                availableLanguages: [],
                availableVoices: [],
                availableStyles: []
            }
        }

        const { store } = renderWithProviders(<VoiceSettings />, { preloadedState })

        // Verify ElevenLabs section is visible
        expect(screen.getByText('🧪 ElevenLabs Avanzado')).toBeInTheDocument()

        // Change Stability
        const stabilityInput = screen.getByLabelText('Estabilidad')
        fireEvent.change(stabilityInput, { target: { value: '0.8' } })

        expect(store.getState().config.browser.voiceStability).toBe(0.8)
    })
})
