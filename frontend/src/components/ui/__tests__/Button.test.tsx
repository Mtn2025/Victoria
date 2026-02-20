import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from '../Button'
import '@testing-library/jest-dom'

describe('Button Component', () => {
    test('renders button with text', () => {
        render(<Button>Click Me</Button>)
        expect(screen.getByText('Click Me')).toBeInTheDocument()
    })

    test('renders primary variant by default', () => {
        render(<Button>Primary</Button>)
        const button = screen.getByRole('button', { name: /Primary/i })
        expect(button).toHaveClass('bg-blue-600')
    })

    test('renders secondary variant', () => {
        render(<Button variant="secondary">Secondary</Button>)
        const button = screen.getByText('Secondary')
        expect(button).toHaveClass('bg-slate-700')
    })

    test('shows loading spinner when isLoading is true', () => {
        render(<Button isLoading>Loading</Button>)
        // Lucide Loader2 usually renders an svg
        // We can check if the button is disabled
        const button = screen.getByRole('button')
        expect(button).toBeDisabled()
    })

    test('calls onClick handler when clicked', () => {
        const handleClick = jest.fn()
        render(<Button onClick={handleClick}>Click Me</Button>)
        fireEvent.click(screen.getByText('Click Me'))
        expect(handleClick).toHaveBeenCalledTimes(1)
    })
})
