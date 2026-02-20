import { screen, fireEvent } from '@testing-library/react'
import { renderWithProviders } from '@/utils/test-utils'
import { HistoryTable } from '../HistoryTable'
import { Call } from '@/types/call'

const mockCalls: Call[] = [
    {
        id: '1',
        sid: 'CA123',
        from_number: '+1234567890',
        to_number: '+0987654321',
        status: 'completed',
        direction: 'inbound',
        duration: 60,
        started_at: '2023-01-01T10:00:00Z',
        provider: 'browser',
        client_type: 'browser'
    },
    {
        id: '2',
        sid: 'CA456',
        from_number: '+1112223333',
        to_number: '+4445556666',
        status: 'in-progress',
        direction: 'outbound',
        duration: 0,
        started_at: '2023-01-01T11:00:00Z',
        provider: 'twilio',
        client_type: 'twilio'
    }
]

describe('HistoryTable', () => {
    const mockSelectCall = jest.fn()
    const mockSelectAll = jest.fn()
    const mockViewDetail = jest.fn()

    test('renders calls', () => {
        renderWithProviders(
            <HistoryTable
                calls={mockCalls}
                selectedCalls={[]}
                onSelectCall={mockSelectCall}
                onSelectAll={mockSelectAll}
                onViewDetail={mockViewDetail}
                isLoading={false}
            />
        )
        expect(screen.getByText('Simulador')).toBeInTheDocument()
        expect(screen.getByText('Twilio')).toBeInTheDocument()
        expect(screen.getByText('60s')).toBeInTheDocument()
    })

    test('handles selection', () => {
        renderWithProviders(
            <HistoryTable
                calls={mockCalls}
                selectedCalls={[]}
                onSelectCall={mockSelectCall}
                onSelectAll={mockSelectAll}
                onViewDetail={mockViewDetail}
                isLoading={false}
            />
        )
        // Select first row checkbox (index 1 because index 0 is header)
        const checkboxes = screen.getAllByRole('checkbox')
        fireEvent.click(checkboxes[1])
        expect(mockSelectCall).toHaveBeenCalledWith('1', true)
    })

    test('handles view detail', () => {
        renderWithProviders(
            <HistoryTable
                calls={mockCalls}
                selectedCalls={[]}
                onSelectCall={mockSelectCall}
                onSelectAll={mockSelectAll}
                onViewDetail={mockViewDetail}
                isLoading={false}
            />
        )
        const viewButtons = screen.getAllByText('Ver')
        fireEvent.click(viewButtons[0])
        expect(mockViewDetail).toHaveBeenCalledWith(mockCalls[0])
    })
})
