import { useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'

type PrioritizedRisk = {
  rank: number
  title: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  impact: string
  evidence: string[]
}

type RecommendedAction = {
  priority: number
  action: string
  rationale: string
}

type GitHubAnalysisResponse = {
  project_name: string
  captured_at: string
  assessment: {
    executive_summary: string
    prioritized_risks: PrioritizedRisk[]
    recommended_actions: RecommendedAction[]
  }
}

function App() {
  const [repositoryUrl, setRepositoryUrl] = useState('')
  const [result, setResult] = useState<GitHubAnalysisResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch('/api/analyze/github', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          repository_url: repositoryUrl.trim(),
        }),
      })

      if (!response.ok) {
        const errorBody: unknown = await response.json().catch(() => null)
        let message = `Analysis failed (${response.status})`

        if (
          typeof errorBody === 'object' &&
          errorBody !== null &&
          'detail' in errorBody &&
          typeof errorBody.detail === 'string'
        ) {
          message = errorBody.detail
        }

        throw new Error(message)
      }

      const data: GitHubAnalysisResponse = await response.json()
      setResult(data)
    } catch (error) {
      setError(
        error instanceof Error ? error.message : 'Unable to analyze repository',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <main>
      <h1>Delivery Risk Dashboard</h1>
      <p>Analyze CI risks in the first five open PRs of a public GitHub repository.</p>

      <form onSubmit={handleSubmit}>
        <label htmlFor="repository-url">GitHub repository URL</label>
        <input
          id="repository-url"
          type="url"
          placeholder="https://github.com/owner/repo"
          value={repositoryUrl}
          onChange={(event) => setRepositoryUrl(event.target.value)}
          required
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !repositoryUrl.trim()}
        >
          {loading ? 'Analyzing…' : 'Analyze repository'}
        </button>
      </form>

      {loading && (
        <p role="status">
          Fetching GitHub checks and generating AI advice. This may take a 5 - 10 minutes.
        </p>
      )}

      {error && <p role="alert">{error}</p>}

      {result && (
        <section>
          <h2>{result.project_name}</h2>
          <p>
            Snapshot captured: {new Date(result.captured_at).toLocaleString()}
          </p>

          <h3>Executive summary</h3>
          <p>{result.assessment.executive_summary}</p>

          <h3>Detected risks</h3>
          <p>Total findings: {result.assessment.prioritized_risks.length}</p>

          {result.assessment.prioritized_risks.length === 0 ? (
            <p>
              No risks detected by the current rules in the inspected PRs.
              This is a limited check, not a complete repository assessment.
            </p>
          ) : (
            result.assessment.prioritized_risks.map((risk) => (
              <article key={risk.rank}>
                <h2>{risk.rank}. {risk.title}</h2>
                <p><strong>Severity:</strong> {risk.severity}</p>
                <p><strong>Potential impact:</strong> {risk.impact}</p>
                <ul>
                  {risk.evidence.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              </article>
            ))
          )}

          {result.assessment.recommended_actions.length > 0 && (
            <>
              <h3>Recommended actions</h3>
              {result.assessment.recommended_actions.map((action) => (
                <article key={action.priority}>
                  <h2>{action.priority}. {action.action}</h2>
                  <p>{action.rationale}</p>
                </article>
              ))}
            </>
          )}
        </section>
      )}
    </main>
  )
}

export default App