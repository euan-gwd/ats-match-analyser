export default function Results({ data }) {
  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getScoreBg = (score) => {
    if (score >= 80) return 'bg-green-100'
    if (score >= 60) return 'bg-yellow-100'
    return 'bg-red-100'
  }

  const getPriorityColor = (priority) => {
    if (priority.includes('CRITICAL')) return 'bg-red-100 text-red-800 border-red-300'
    if (priority.includes('HIGH')) return 'bg-yellow-100 text-yellow-800 border-yellow-300'
    return 'bg-green-100 text-green-800 border-green-300'
  }

  return (
    <div className="mt-8 space-y-6">
      {/* Overall Score */}
      <div className="bg-white rounded-lg shadow-xl p-8 text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">ATS Match Score</h2>
        <div className={`text-7xl font-bold ${getScoreColor(data.overall)} mb-2`}>
          {data.overall.toFixed(0)}%
        </div>
        <p className="text-gray-600">
          {data.overall >= 80 && 'Excellent match! Your CV is well-optimized.'}
          {data.overall >= 60 && data.overall < 80 && 'Good start, but room for improvement.'}
          {data.overall < 60 && 'Needs work. Follow the recommendations below.'}
        </p>
      </div>

      {/* Score Breakdown */}
      <div className="bg-white rounded-lg shadow-xl p-8">
        <h3 className="text-xl font-bold text-gray-900 mb-6">Score Breakdown</h3>
        <div className="space-y-4">
          <ScoreBar
            label="Keyword Match"
            score={data.keyword_similarity}
            getScoreColor={getScoreColor}
            getScoreBg={getScoreBg}
          />
          <ScoreBar
            label="Skills Coverage"
            score={data.skills_coverage}
            getScoreColor={getScoreColor}
            getScoreBg={getScoreBg}
          />
          <ScoreBar
            label="Seniority Alignment"
            score={data.seniority_alignment}
            getScoreColor={getScoreColor}
            getScoreBg={getScoreBg}
          />
          <ScoreBar
            label="ATS Friendliness"
            score={data.ats_friendliness}
            getScoreColor={getScoreColor}
            getScoreBg={getScoreBg}
          />
        </div>
      </div>

      {/* Keywords */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-xl p-6">
          <h3 className="text-lg font-bold text-green-700 mb-4">✓ Matched Keywords</h3>
          <div className="flex flex-wrap gap-2">
            {data.matched_keywords.slice(0, 15).map((kw, idx) => (
              <span key={idx} className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
                {kw}
              </span>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-xl p-6">
          <h3 className="text-lg font-bold text-red-700 mb-4">✗ Missing Keywords</h3>
          <div className="flex flex-wrap gap-2">
            {data.missing_keywords.slice(0, 15).map((kw, idx) => (
              <span key={idx} className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm">
                {kw}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Seniority */}
      {data.seniority_explanation && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-bold text-blue-900 mb-2">📊 Seniority Analysis</h3>
          <p className="text-blue-800">{data.seniority_explanation}</p>
        </div>
      )}

      {/* Actionable Steps */}
      <div className="bg-white rounded-lg shadow-xl p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">🎯 Action Items</h2>
        <div className="space-y-6">
          {data.actionable_steps.map((step, idx) => (
            <div
              key={idx}
              className={`border-2 rounded-lg p-6 ${getPriorityColor(step.priority)}`}
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <span className="text-xs font-bold px-2 py-1 rounded bg-white">
                    {step.priority}
                  </span>
                  <h3 className="text-lg font-bold mt-2">{step.category}</h3>
                </div>
              </div>

              <p className="font-semibold mb-3">{step.action}</p>

              <div className="space-y-2 bg-white bg-opacity-50 rounded p-4">
                {Array.isArray(step.details) ? (
                  step.details.map((detail, detailIdx) => (
                    <div key={detailIdx} className="text-sm whitespace-pre-line">
                      {detail}
                    </div>
                  ))
                ) : (
                  <div className="text-sm whitespace-pre-line">{step.details}</div>
                )}
              </div>

              <div className="mt-3 text-sm font-semibold opacity-75">
                💡 {step.impact}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function ScoreBar({ label, score, getScoreColor, getScoreBg }) {
  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-sm font-semibold text-gray-700">{label}</span>
        <span className={`text-sm font-bold ${getScoreColor(score)}`}>
          {score.toFixed(0)}%
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-3">
        <div
          className={`h-3 rounded-full ${getScoreBg(score)} transition-all duration-500`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  )
}
