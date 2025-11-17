import { useState } from 'react'
import axios from 'axios'

const API_URL = 'http://localhost:8000'

export default function UploadForm({ onResults, onLoading, disabled }) {
  const [cvFile, setCvFile] = useState(null)
  const [jobDescription, setJobDescription] = useState('')
  const [jobUrl, setJobUrl] = useState('')
  const [linkedinUrl, setLinkedinUrl] = useState('')
  const [useUrl, setUseUrl] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!cvFile) {
      setError('Please upload your CV')
      return
    }

    if (!useUrl && !jobDescription) {
      setError('Please provide a job description')
      return
    }

    if (useUrl && !jobUrl) {
      setError('Please provide a job URL')
      return
    }

    onLoading(true)

    try {
      const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

      // Record consent
      await axios.post(`${API_URL}/api/consent`,
        new URLSearchParams({ session_id: sessionId })
      )

      // Prepare form data
      const formData = new FormData()
      formData.append('cv_file', cvFile)
      formData.append('session_id', sessionId)

      if (useUrl) {
        formData.append('job_url', jobUrl)
      } else {
        formData.append('job_description', jobDescription)
      }

      if (linkedinUrl) {
        formData.append('linkedin_url', linkedinUrl)
      }

      // Submit analysis
      const response = await axios.post(`${API_URL}/api/analyze`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      onResults(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed. Please try again.')
    } finally {
      onLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-xl p-8">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* CV Upload */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Upload Your CV (PDF)
          </label>
          <input
            type="file"
            accept=".pdf"
            onChange={(e) => setCvFile(e.target.files[0])}
            disabled={disabled}
            className="block w-full text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 disabled:opacity-50"
          />
          {cvFile && (
            <p className="mt-2 text-sm text-green-600">✓ {cvFile.name}</p>
          )}
        </div>

        {/* Job Description Toggle */}
        <div>
          <div className="flex items-center gap-4 mb-2">
            <label className="block text-sm font-semibold text-gray-700">
              Job Description
            </label>
            <button
              type="button"
              onClick={() => setUseUrl(!useUrl)}
              className="text-sm text-indigo-600 hover:text-indigo-800 underline"
            >
              {useUrl ? 'Paste text instead' : 'Use URL instead'}
            </button>
          </div>

          {useUrl ? (
            <input
              type="url"
              value={jobUrl}
              onChange={(e) => setJobUrl(e.target.value)}
              placeholder="https://example.com/job-posting"
              disabled={disabled}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:opacity-50"
            />
          ) : (
            <textarea
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the job description here..."
              rows="8"
              disabled={disabled}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:opacity-50"
            />
          )}
        </div>

        {/* LinkedIn URL (Optional) */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            LinkedIn Profile URL (Optional)
          </label>
          <input
            type="url"
            value={linkedinUrl}
            onChange={(e) => setLinkedinUrl(e.target.value)}
            placeholder="https://linkedin.com/in/your-profile"
            disabled={disabled}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:opacity-50"
          />
          <p className="mt-1 text-xs text-gray-500">
            We'll check for additional skills and experience to suggest
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={disabled}
          className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-6 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Analyze My CV
        </button>
      </form>
    </div>
  )
}
