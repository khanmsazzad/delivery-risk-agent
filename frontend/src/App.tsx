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

type Assessment = {
  executive_summary: string
  prioritized_risks: PrioritizedRisk[]
  recommended_actions: RecommendedAction[]
}

type AnalysisResponse = {
  project_name: string
  captured_at: string
  assessment: Assessment
}

type JiraAnalysisResponse = AnalysisResponse & {
  issues_inspected: number
}

type AnalysisResult =
  | { source: 'github'; target: string; data: AnalysisResponse }
  | { source: 'jira'; target: string; data: JiraAnalysisResponse }

function AssessmentView({ result }: { result: AnalysisResult }) {
  return (
        <section className="assessment">
          <h3>{result.source === 'github' ? 'GitHub assessment' : 'Jira assessment'}</h3>
          <p><strong>Analyzed:</strong> {result.target}</p>
          <p>{result.data.project_name}</p>
          <p>
            Snapshot captured:{' '}
            {new Date(result.data.captured_at).toLocaleString()}
          </p>

          {result.source === 'jira' && (
            <p>Issues inspected: {result.data.issues_inspected}</p>
          )}

          <h4>Executive summary</h4>
          <p>{result.data.assessment.executive_summary}</p>

          <h4>Detected risks</h4>
          <p>
            Total findings: {result.data.assessment.prioritized_risks.length}
          </p>

          {result.data.assessment.prioritized_risks.length === 0 ? (
            <p>No risks detected by the current rules in the inspected data.</p>
          ) : (
            result.data.assessment.prioritized_risks.map((risk) => (
              <article key={risk.rank}>
                <h5>{risk.rank}. {risk.title}</h5>
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

          <p>
            This assessment covers the current rules and accessible data,
            rather than all possible delivery risks.
          </p>

          {result.data.assessment.recommended_actions.length > 0 && (
            <>
              <h4>Recommended actions</h4>
              {result.data.assessment.recommended_actions.map((action) => (
                <article key={action.priority}>
                  <h5>{action.priority}. {action.action}</h5>
                  <p>{action.rationale}</p>
                </article>
              ))}
            </>
          )}
        </section>
  )
}

function App() {
  const [repositoryUrl, setRepositoryUrl] = useState('')
  const [projectKey, setProjectKey] = useState('RISK')
  const [results, setResults] = useState<Record<'github' | 'jira', AnalysisResult | null>>({ github: null, jira: null })
  const [loading, setLoading] = useState({
    github: false,
    jira: false,
  })
  const [errors, setErrors] = useState<Record<'github' | 'jira', string | null>>({ github: null, jira: null })

  async function analyze(
    event: FormEvent<HTMLFormElement>,
    source: 'github' | 'jira',
  ) {
    event.preventDefault()
    setLoading((current) => ({ ...current, [source]: true }))
    setErrors((current) => ({ ...current, [source]: null }))
    setResults((current) => ({ ...current, [source]: null }))
    const target = source === 'github' ? repositoryUrl.trim() : projectKey.trim().toUpperCase()

    const endpoint = `/api/analyze/${source}`
    const body =
      source === 'github'
        ? { repository_url: repositoryUrl.trim() }
        : { project_key: projectKey.trim() }

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
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

      if (source === 'jira') {
        const data: JiraAnalysisResponse = await response.json()
        setResults((current) => ({ ...current, jira: { source: 'jira', target, data } }))
      } else {
        const data: AnalysisResponse = await response.json()
        setResults((current) => ({ ...current, github: { source: 'github', target, data } }))
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to complete analysis'
      setErrors((current) => ({ ...current, [source]: message }))
    } finally {
      setLoading((current) => ({ ...current, [source]: false }))
    }
  }

  return (
    <main>
      <h1>Delivery Risk Dashboard</h1>

      <div className="analysis-grid">
      <section className="analysis-panel" aria-labelledby="github-heading">
        <h2 id="github-heading">Public GitHub repository</h2>
        <p>Check CI risks in the first five open pull requests.</p>

        <form onSubmit={(event) => void analyze(event, 'github')}>
          <label htmlFor="repository-url">Repository URL</label>
          <input
            id="repository-url"
            type="url"
            placeholder="https://github.com/owner/repo"
            value={repositoryUrl}
            onChange={(event) => setRepositoryUrl(event.target.value)}
            required
            disabled={loading.github}
          />
          <button
            type="submit"
            disabled={loading.github || !repositoryUrl.trim()}
          >
            {loading.github ? 'Analyzing GitHub…' : 'Analyze GitHub'}
          </button>
        </form>
        {loading.github && <p role="status">Analyzing GitHub. AI advice may take 5–10 minutes.</p>}
        {errors.github && <p role="alert">{errors.github}</p>}
        {results.github && <AssessmentView result={results.github} />}
      </section>

      <section className="analysis-panel" aria-labelledby="jira-heading">
        <h2 id="jira-heading">Jira project</h2>
        <p>
          Check unassigned high-priority work in the Jira site connected
          to this application.
        </p>

        <form onSubmit={(event) => void analyze(event, 'jira')}>
          <label htmlFor="project-key">Project key</label>
          <input
            id="project-key"
            type="text"
            placeholder="RISK"
            value={projectKey}
            onChange={(event) => setProjectKey(event.target.value)}
            required
            disabled={loading.jira}
          />
          <button
            type="submit"
            disabled={loading.jira || !projectKey.trim()}
          >
            {loading.jira ? 'Analyzing Jira…' : 'Analyze Jira'}
          </button>
        </form>
        {loading.jira && <p role="status">Analyzing Jira. AI advice may take 5–10 minutes.</p>}
        {errors.jira && <p role="alert">{errors.jira}</p>}
        {results.jira && <AssessmentView result={results.jira} />}
      </section>

      </div>
    </main>
  )
}

export default App
