import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Results from '../components/Results'

describe('Results', () => {
  const mockData = {
    overall: 75.5,
    keyword_similarity: 68.0,
    skills_coverage: 82.0,
    seniority_alignment: 90.0,
    ats_friendliness: 75.0,
    matched_keywords: ['python', 'javascript', 'react', 'docker', 'aws'],
    missing_keywords: ['kubernetes', 'typescript', 'ci/cd'],
    seniority_explanation: 'Your profile shows strong senior-level indicators with 6+ years of experience.',
    ats_reasons: ['Clear section headers', 'Good use of bullet points'],
    actionable_steps: [
      {
        priority: 'HIGH',
        category: 'Missing Skills',
        action: 'Add Kubernetes to your skills',
        details: ['Add to Skills section', 'Mention in project descriptions'],
        impact: 'Critical skill gap'
      }
    ]
  }

  it('renders overall score', () => {
    render(<Results data={mockData} />)

    expect(screen.getByText(/ATS Match Score/i)).toBeInTheDocument()
    expect(screen.getByText('76%')).toBeInTheDocument()
  })

  it('displays correct message for good scores (60-80)', () => {
    render(<Results data={mockData} />)

    expect(screen.getByText(/Good start, but room for improvement/i)).toBeInTheDocument()
  })

  it('displays correct message for excellent scores (80+)', () => {
    const excellentData = { ...mockData, overall: 85.0 }
    render(<Results data={excellentData} />)

    expect(screen.getByText(/Excellent match/i)).toBeInTheDocument()
  })

  it('displays correct message for low scores (<60)', () => {
    const lowData = { ...mockData, overall: 45.0 }
    render(<Results data={lowData} />)

    expect(screen.getByText(/Needs work/i)).toBeInTheDocument()
  })

  it('renders score breakdown with all metrics', () => {
    render(<Results data={mockData} />)

    expect(screen.getByText(/Score Breakdown/i)).toBeInTheDocument()
    expect(screen.getByText(/Keyword Match/i)).toBeInTheDocument()
    expect(screen.getByText(/Skills Coverage/i)).toBeInTheDocument()
    expect(screen.getByText(/Seniority Alignment/i)).toBeInTheDocument()
    expect(screen.getByText(/ATS Friendliness/i)).toBeInTheDocument()
  })

  it('displays matched keywords', () => {
    render(<Results data={mockData} />)

    expect(screen.getByText(/Matched Keywords/i)).toBeInTheDocument()
    expect(screen.getByText('python')).toBeInTheDocument()
    expect(screen.getByText('javascript')).toBeInTheDocument()
    expect(screen.getByText('react')).toBeInTheDocument()
    expect(screen.getByText('docker')).toBeInTheDocument()
    expect(screen.getByText('aws')).toBeInTheDocument()
  })

  it('displays missing keywords', () => {
    render(<Results data={mockData} />)

    expect(screen.getByText(/Missing Keywords/i)).toBeInTheDocument()
    expect(screen.getByText('kubernetes')).toBeInTheDocument()
    expect(screen.getByText('typescript')).toBeInTheDocument()
    expect(screen.getByText('ci/cd')).toBeInTheDocument()
  })

  it('renders seniority analysis when provided', () => {
    render(<Results data={mockData} />)

    expect(screen.getByText(/Seniority Analysis/i)).toBeInTheDocument()
    expect(screen.getByText(/Your profile shows strong senior-level indicators/i)).toBeInTheDocument()
  })

  it('renders actionable steps when provided', () => {
    render(<Results data={mockData} />)

    expect(screen.getByText(/Action Items/i)).toBeInTheDocument()
    expect(screen.getByText(/Missing Skills/i)).toBeInTheDocument()
    expect(screen.getByText(/Add Kubernetes to your skills/i)).toBeInTheDocument()
    expect(screen.getByText(/HIGH/i)).toBeInTheDocument()
  })

  it('applies correct color classes for high scores', () => {
    const highScoreData = { ...mockData, overall: 85 }
    const { container } = render(<Results data={highScoreData} />)

    const overallScore = container.querySelector('.text-7xl')
    expect(overallScore.className).toContain('text-green-600')
  })

  it('applies correct color classes for medium scores', () => {
    const mediumScoreData = { ...mockData, overall: 65 }
    const { container } = render(<Results data={mediumScoreData} />)

    const overallScore = container.querySelector('.text-7xl')
    expect(overallScore.className).toContain('text-yellow-600')
  })

  it('applies correct color classes for low scores', () => {
    const lowScoreData = { ...mockData, overall: 45 }
    const { container } = render(<Results data={lowScoreData} />)

    const overallScore = container.querySelector('.text-7xl')
    expect(overallScore.className).toContain('text-red-600')
  })
})
