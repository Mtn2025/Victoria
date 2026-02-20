import React from 'react'
import { screen, fireEvent } from '@testing-library/react'
import { renderWithProviders } from '../../utils/test-utils'
import { ConfigPage } from '../ConfigPage'
import '@testing-library/jest-dom'

describe('ConfigPage Integration', () => {
    test('renders Profile Switcher and updates active profile', () => {
        const { store } = renderWithProviders(<ConfigPage />, {
            preloadedState: {
                ui: {
                    activeProfile: 'browser',
                    activeTab: 'model'
                }
            }
        })

        // Check if switcher exists
        const twilioButton = screen.getByTitle('Telefonía Twilio')
        expect(twilioButton).toBeInTheDocument()

        // Click and verify store update
        fireEvent.click(twilioButton)
        expect(store.getState().ui.activeProfile).toBe('twilio')

        // Verify visual feedback (class check implicity via logic)
    })
})
