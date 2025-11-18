import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ConsentBanner from '../components/ConsentBanner'

describe('ConsentBanner', () => {
  it('renders the consent banner with main text', () => {
    render(<ConsentBanner onAccept={() => {}} />)

    expect(screen.getByText(/Privacy & Data Protection/i)).toBeInTheDocument()
    expect(screen.getByText(/We process your CV and job data temporarily/i)).toBeInTheDocument()
  })

  it('shows Accept & Continue button', () => {
    render(<ConsentBanner onAccept={() => {}} />)

    const acceptButton = screen.getByRole('button', { name: /Accept & Continue/i })
    expect(acceptButton).toBeInTheDocument()
  })

  it('calls onAccept when Accept button is clicked', () => {
    const mockOnAccept = vi.fn()
    render(<ConsentBanner onAccept={mockOnAccept} />)

    const acceptButton = screen.getByRole('button', { name: /Accept & Continue/i })
    fireEvent.click(acceptButton)

    expect(mockOnAccept).toHaveBeenCalledTimes(1)
  })

  it('toggles details visibility when View Details is clicked', () => {
    render(<ConsentBanner onAccept={() => {}} />)

    // Initially details are hidden
    expect(screen.queryByText(/What we collect:/i)).not.toBeInTheDocument()

    // Click View Details
    const viewDetailsButton = screen.getByRole('button', { name: /View Details/i })
    fireEvent.click(viewDetailsButton)

    // Details should now be visible
    expect(screen.getByText(/What we collect:/i)).toBeInTheDocument()
    expect(screen.getByText(/Your rights:/i)).toBeInTheDocument()
    expect(screen.getByText(/CV content \(processed in memory only\)/i)).toBeInTheDocument()

    // Button text should change
    expect(screen.getByRole('button', { name: /Hide Details/i })).toBeInTheDocument()

    // Click again to hide
    fireEvent.click(screen.getByRole('button', { name: /Hide Details/i }))
    expect(screen.queryByText(/What we collect:/i)).not.toBeInTheDocument()
  })

  it('displays GDPR compliance information in details', () => {
    render(<ConsentBanner onAccept={() => {}} />)

    // Open details
    fireEvent.click(screen.getByRole('button', { name: /View Details/i }))

    // Check for GDPR-related content
    expect(screen.getByText(/GDPR compliant/i)).toBeInTheDocument()
    expect(screen.getByText(/No tracking cookies/i)).toBeInTheDocument()
    expect(screen.getByText(/Data is not stored after analysis/i)).toBeInTheDocument()
  })
})
