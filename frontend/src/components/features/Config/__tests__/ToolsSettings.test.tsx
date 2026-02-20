import { screen, fireEvent } from '@testing-library/react'
import { renderWithProviders } from '@/utils/test-utils'
import { ToolsSettings } from '@/components/features/Config/ToolsSettings'

describe('ToolsSettings Integration', () => {
    test('renders main schema editor', () => {
        renderWithProviders(<ToolsSettings />)
        expect(screen.getByText('Herramientas & Acciones')).toBeInTheDocument()
        expect(screen.getByLabelText('JSON Schema Editor')).toBeInTheDocument()
    })

    test('profile selector switches config target', () => {
        const { store } = renderWithProviders(<ToolsSettings />)

        // Default: Browser
        const schemaEditor = screen.getByLabelText('JSON Schema Editor')
        fireEvent.change(schemaEditor, { target: { value: '[{"type":"browser"}]' } })
        expect(store.getState().config.browser.toolsSchema).toBe('[{"type":"browser"}]')

        // Switch to Telnyx
        const selector = screen.getByLabelText('Profile Selector')
        fireEvent.change(selector, { target: { value: 'telnyx' } })

        // Edit Schema for Telnyx
        fireEvent.change(schemaEditor, { target: { value: '[{"type":"telnyx"}]' } })
        expect(store.getState().config.telnyx.toolsSchema).toBe('[{"type":"telnyx"}]')
    })

    test('prettify button formats json', () => {
        renderWithProviders(<ToolsSettings />)
        const schemaEditor = screen.getByLabelText('JSON Schema Editor')
        const uglyJSON = '{"key":"value"}'
        fireEvent.change(schemaEditor, { target: { value: uglyJSON } })

        const prettifyBtn = screen.getByText('Prettify')
        fireEvent.click(prettifyBtn)

        expect(schemaEditor).toHaveValue('{\n  "key": "value"\n}')
    })

    test('updates n8n server settings', () => {
        const { store } = renderWithProviders(<ToolsSettings />)

        fireEvent.click(screen.getByText('🌍 Server (n8n)'))

        const urlInput = screen.getByLabelText('Server URL')
        fireEvent.change(urlInput, { target: { value: 'https://webhook.site/123' } })
        expect(store.getState().config.browser.toolServerUrl).toBe('https://webhook.site/123')

        const retrySelect = screen.getByLabelText('Retry Count')
        fireEvent.change(retrySelect, { target: { value: '1' } })
        expect(store.getState().config.browser.toolRetryCount).toBe(1)
    })
})
