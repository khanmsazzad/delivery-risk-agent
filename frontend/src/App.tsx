import { useEffect, useState } from 'react'
import './App.css'

type RiskFinding = {
  rule_id: string
  title: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  work_item_id: string | null
  pull_request_number: number | null
  evidence: string[]
  recommendation: string
}

type DashboardResponse = {
  project_name: string
  captured_at: string
  findings: RiskFinding[]
}

function App() {
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()

    async function loadDashboard() {
      try {
        const response = await fetch('/api/dashboard', {
          signal: controller.signal,
        })

        if (!response.ok) {
          throw new Error(`Dashboard request failed (${response.status})`)
        }

        const data: DashboardResponse = await response.json()

        if (!controller.signal.aborted) {
          setDashboard(data)
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          setError(
            error instanceof Error ? error.message : 'Unable to load dashboard',
          )
        }
      }
    }

    void loadDashboard()

    return () => controller.abort()
  }, [])

  if (error) {
    return <main><p role="alert">{error}</p></main>
  }

  if (!dashboard) {
    return <main><p>Loading dashboard…</p></main>
  }

  return (
    <main>
      <h1>{dashboard.project_name}</h1>
      <p>
        Snapshot captured: {new Date(dashboard.captured_at).toLocaleString()}
      </p>
      <p>Total findings: {dashboard.findings.length}</p>

      {dashboard.findings.length === 0 ? (
        <p>No delivery risks detected.</p>
      ) : (
        dashboard.findings.map((finding, index) => (
          <article key={`${finding.rule_id}-${index}`}>
            <h2>{finding.title}</h2>
            <p><strong>Severity:</strong> {finding.severity}</p>

            <ul>
              {finding.evidence.map((item, evidenceIndex) => (
                <li key={evidenceIndex}>{item}</li>
              ))}
            </ul>

            <p><strong>Recommendation:</strong> {finding.recommendation}</p>
          </article>
        ))
      )}
    </main>
  )
}

export default App