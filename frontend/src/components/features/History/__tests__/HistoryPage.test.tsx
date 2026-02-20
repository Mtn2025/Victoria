/* eslint-disable @typescript-eslint/no-explicit-any */
import { screen, waitFor, fireEvent } from '@testing-library/react'
import { renderWithProviders } from '@/utils/test-utils'
import { HistoryPage } from '@/pages/HistoryPage'
import { callsService } from '@/services/callsService'

// Mock callsService
jest.mock('@/services/callsService')

describe('HistoryPage Integration', () => {
    beforeEach(() => {
        jest.clearAllMocks()
    })

    test('loads and displays history', async () => {
        (callsService.getHistory as any).mockResolvedValue({
            data: {
                items: [
                    {
                        id: '1',
                        started_at: '2023-01-01T12:00:00Z',
                        duration: 120,
                        provider: 'telnyx',
                        client_type: 'telnyx'
                    }
                ],
                total: 1
            }
        })

        renderWithProviders(<HistoryPage />)

        expect(screen.getByText('Registro de Llamadas')).toBeInTheDocument()

        await waitFor(() => {
            expect(screen.getAllByText('Telnyx').length).toBeGreaterThan(0)
            expect(screen.getByText('120s')).toBeInTheDocument()
        })
    })

    test('filters calls', async () => {
        (callsService.getHistory as any).mockResolvedValue({
            data: { items: [], total: 0 }
        })

        renderWithProviders(<HistoryPage />)

        const filterTwilio = screen.getByText('Twilio')
        fireEvent.click(filterTwilio)

        await waitFor(() => {
            // Check if API was called again (useEffect dependency)
            expect(callsService.getHistory).toHaveBeenCalledTimes(2) // Initial + Filter change
        })
    })
})
