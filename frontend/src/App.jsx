import { useState, useEffect } from 'react'
import UploadForm from './components/UploadForm'
import Results from './components/Results'
import ConsentBanner from './components/ConsentBanner'

function App() {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [hasConsent, setHasConsent] = useState(() => {
    return localStorage.getItem('gdpr_consent_accepted') === 'true'
  })

  const handleAcceptConsent = () => {
    localStorage.setItem('gdpr_consent_accepted', 'true')
    setHasConsent(true)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {!hasConsent && <ConsentBanner onAccept={handleAcceptConsent} />}

      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            ATS Match Analyser
          </h1>
          <p className="text-xl text-gray-600">
            Optimize your CV against job descriptions with AI-powered insights
          </p>
        </header>

        <div className="max-w-4xl mx-auto">
          <UploadForm
            onResults={setResults}
            onLoading={setLoading}
            disabled={!hasConsent}
          />

          {loading && (
            <div className="mt-8 bg-white rounded-lg shadow-lg p-8 text-center">
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-indigo-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Analyzing your CV...</p>
            </div>
          )}

          {results && !loading && <Results data={results} />}
        </div>

        <footer className="mt-16 text-center text-gray-600 text-sm">
          <div className="flex justify-center items-center gap-6">
            <a
              href="http://localhost:8000/api/privacy-notice"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-indigo-600 underline"
            >
              Privacy Notice
            </a>
            <span>•</span>
            <span className="flex items-center gap-2">
              <span className="text-green-600">✓</span>
              GDPR Compliant
            </span>
          </div>
        </footer>
      </div>
    </div>
  )
}

export default App
