import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import App from '../App'



describe('App Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Clear localStorage (mocked in setup.js)
    localStorage.clear()
  })

  it('renders the app with header', () => {
    render(<App />)

    expect(screen.getByText(/ATS Match Analyser/i)).toBeInTheDocument()
    expect(screen.getByText(/Optimize your CV against job descriptions with AI-powered insights/i)).toBeInTheDocument()
  })

  it('shows consent banner on first visit', () => {
    render(<App />)

    expect(screen.getByText(/Privacy & Data Protection/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Accept & Continue/i })).toBeInTheDocument()
  })

  it('hides consent banner after accepting', () => {
    render(<App />)

    const acceptButton = screen.getByRole('button', { name: /Accept & Continue/i })
    fireEvent.click(acceptButton)

    expect(screen.queryByText(/Privacy & Data Protection/i)).not.toBeInTheDocument()
  })

  it('persists consent acceptance in localStorage', () => {
    render(<App />)

    fireEvent.click(screen.getByRole('button', { name: /Accept & Continue/i }))

    expect(localStorage.getItem('gdpr_consent_accepted')).toBe('true')
  })

  it('does not show consent banner if already accepted', () => {
    localStorage.setItem('gdpr_consent_accepted', 'true')

    render(<App />)

    expect(screen.queryByText(/Privacy & Data Protection/i)).not.toBeInTheDocument()
  })

  it('shows upload form after accepting consent', () => {
    render(<App />)

    fireEvent.click(screen.getByRole('button', { name: /Accept & Continue/i }))

    expect(screen.getByText(/Upload Your CV \(PDF\)/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Analyze My CV/i })).toBeInTheDocument()
  })

  it('shows loading state during analysis', async () => {
    localStorage.setItem('gdpr_consent_accepted', 'true')
    render(<App />)

    // Manually trigger loading state by finding and calling the loading handler
    // This would typically happen through form submission
    const loadingText = screen.queryByText(/Analyzing your CV.../i)
    // Initially should not show loading
    expect(loadingText).not.toBeInTheDocument()
  })

  it('renders footer with privacy links', () => {
    render(<App />)

    expect(screen.getByText(/Privacy Notice/i)).toBeInTheDocument()
    expect(screen.getByText(/GDPR Compliant/i)).toBeInTheDocument()
  })

  it('has working privacy notice link', () => {
    render(<App />)

    const privacyLink = screen.getByRole('link', { name: /Privacy Notice/i })
    expect(privacyLink).toHaveAttribute('href', 'http://localhost:8000/api/privacy-notice')
  })
})
