import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import UploadForm from '../components/UploadForm'

// Mock fetch
global.fetch = vi.fn()

describe('UploadForm', () => {
  const mockOnResults = vi.fn()
  const mockOnLoading = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders all form fields', () => {
    render(<UploadForm onResults={mockOnResults} onLoading={mockOnLoading} />)

    expect(screen.getByText(/Upload Your CV/i)).toBeInTheDocument()
    expect(screen.getByText(/Job Description/i)).toBeInTheDocument()
    expect(screen.getByText(/LinkedIn Profile URL/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Analyze My CV/i })).toBeInTheDocument()
  })

  it('shows error when submitting without CV', async () => {
    render(<UploadForm onResults={mockOnResults} onLoading={mockOnLoading} />)

    const submitButton = screen.getByRole('button', { name: /Analyze My CV/i })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Please upload your CV/i)).toBeInTheDocument()
    })
  })

  it('toggles between text input and URL input for job description', () => {
    render(<UploadForm onResults={mockOnResults} onLoading={mockOnLoading} />)

    // Initially shows textarea
    expect(screen.getByPlaceholderText(/Paste the job description here/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Use URL instead/i })).toBeInTheDocument()

    // Click to switch to URL
    fireEvent.click(screen.getByRole('button', { name: /Use URL instead/i }))

    // Should now show URL input
    expect(screen.getByPlaceholderText(/example.com\/job-posting/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Paste text instead/i })).toBeInTheDocument()
  })

  it('disables form when disabled prop is true', () => {
    const { container } = render(<UploadForm onResults={mockOnResults} onLoading={mockOnLoading} disabled={true} />)

    const fileInput = container.querySelector('input[type="file"]')
    const submitButton = screen.getByRole('button', { name: /Analyze My CV/i })

    expect(fileInput).toBeDisabled()
    expect(submitButton).toBeDisabled()
  })

  it('submits form with valid data', async () => {

    // Mock consent fetch
    fetch.mockResolvedValueOnce({ ok: true, json: async () => ({}) })
    // Mock analyze fetch
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        overall: 75.5,
        keyword_similarity: 68.0,
        skills_coverage: 82.0,
        matched_keywords: ['python', 'react'],
        missing_keywords: ['kubernetes']
      })
    })

    const { container } = render(<UploadForm onResults={mockOnResults} onLoading={mockOnLoading} />)

    // Upload file
    const file = new File(['dummy content'], 'resume.pdf', { type: 'application/pdf' })
    const fileInput = container.querySelector('input[type="file"]')
    await userEvent.upload(fileInput, file)

    // Enter job description
    const jobDescTextarea = screen.getByPlaceholderText(/Paste the job description here/i)
    await userEvent.type(jobDescTextarea, 'Senior Python Developer needed')

    // Submit
    const submitButton = screen.getByRole('button', { name: /Analyze My CV/i })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(mockOnLoading).toHaveBeenCalledWith(true)
      expect(fetch).toHaveBeenCalledTimes(2)
      expect(mockOnResults).toHaveBeenCalledWith(
        expect.objectContaining({
          overall: 75.5,
          matched_keywords: expect.arrayContaining(['python', 'react'])
        })
      )
      expect(mockOnLoading).toHaveBeenCalledWith(false)
    })
  })
})
