import { useState } from 'react'

export default function ConsentBanner({ onAccept }) {
  const [showDetails, setShowDetails] = useState(false)

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-gray-900 text-white p-6 shadow-2xl z-50">
      <div className="container mx-auto max-w-4xl">
        <h3 className="text-lg font-bold mb-2">🔒 Privacy & Data Protection</h3>
        <p className="text-sm mb-4">
          We process your CV and job data temporarily to provide analysis.
          No data is permanently stored. By continuing, you consent to this processing.
        </p>

        {showDetails && (
          <div className="bg-gray-800 p-4 rounded mb-4 text-xs">
            <h4 className="font-bold mb-2">What we collect:</h4>
            <ul className="list-disc list-inside space-y-1">
              <li>CV content (processed in memory only)</li>
              <li>Job description text</li>
              <li>LinkedIn profile URL (optional)</li>
              <li>Session ID for rate limiting</li>
            </ul>
            <h4 className="font-bold mt-3 mb-2">Your rights:</h4>
            <ul className="list-disc list-inside space-y-1">
              <li>Data is not stored after analysis</li>
              <li>No tracking cookies</li>
              <li>GDPR compliant</li>
            </ul>
          </div>
        )}

        <div className="flex gap-4">
          <button
            onClick={onAccept}
            className="bg-indigo-600 hover:bg-indigo-700 px-6 py-2 rounded-lg font-semibold transition"
          >
            Accept & Continue
          </button>
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-indigo-300 hover:text-indigo-200 underline"
          >
            {showDetails ? 'Hide Details' : 'View Details'}
          </button>
        </div>
      </div>
    </div>
  )
}
