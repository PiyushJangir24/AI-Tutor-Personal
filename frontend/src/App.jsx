import React, { useMemo, useState } from 'react'

const initialState = {
  message: '',
  response: null,
  loading: false,
  error: null,
}

export default function App() {
  const [state, setState] = useState(initialState)
  const backendUrl = useMemo(() => '/api', [])

  async function sendMessage(e) {
    e.preventDefault()
    setState((s) => ({ ...s, loading: true, error: null }))
    try {
      const r = await fetch(`${backendUrl}/orchestrate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: state.message, user_id: 'demo_user' }),
      })
      if (!r.ok) {
        const err = await r.json().catch(() => ({ message: r.statusText }))
        throw new Error(err?.message || JSON.stringify(err))
      }
      const data = await r.json()
      setState((s) => ({ ...s, response: data, loading: false }))
    } catch (err) {
      setState((s) => ({ ...s, error: err.message, loading: false }))
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto p-6">
        <header className="mb-6">
          <h1 className="text-2xl font-semibold">Autonomous AI Tutor Orchestrator</h1>
          <p className="text-sm text-gray-600">Type a prompt, the backend analyzes intent, extracts parameters, routes to a tool, and returns results.</p>
        </header>

        <form onSubmit={sendMessage} className="bg-white rounded-lg shadow p-4 space-y-3">
          <label className="block text-sm font-medium">Student message</label>
          <textarea
            className="w-full border rounded-md p-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 min-h-[100px]"
            placeholder="e.g., Make concise notes about derivatives for a beginner" 
            value={state.message}
            onChange={(e) => setState((s) => ({ ...s, message: e.target.value }))}
          />
          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={state.loading || !state.message.trim()}
              className="px-4 py-2 rounded-md bg-indigo-600 text-white disabled:opacity-60"
            >
              {state.loading ? 'Analyzing...' : 'Send to Orchestrator'}
            </button>
            {state.error && <span className="text-red-600 text-sm">{state.error}</span>}
          </div>
        </form>

        {state.response && (
          <section className="mt-6 grid md:grid-cols-2 gap-4">
            <div className="bg-white rounded-lg shadow p-4">
              <h2 className="font-semibold mb-2">Chosen Tool</h2>
              <div className="text-sm">
                <div><span className="font-medium">Tool:</span> {state.response.chosen_tool}</div>
              </div>

              <h2 className="font-semibold mt-4 mb-2">Extracted Parameters</h2>
              <pre className="text-xs bg-gray-100 p-3 rounded overflow-auto">{JSON.stringify(state.response.extracted_parameters, null, 2)}</pre>

              <h2 className="font-semibold mt-4 mb-2">Analysis</h2>
              <pre className="text-xs bg-gray-100 p-3 rounded overflow-auto">{JSON.stringify(state.response.analysis, null, 2)}</pre>
            </div>

            <div className="bg-white rounded-lg shadow p-4">
              <h2 className="font-semibold mb-2">API Result</h2>
              <pre className="text-xs bg-gray-100 p-3 rounded overflow-auto">{JSON.stringify(state.response.result, null, 2)}</pre>
            </div>
          </section>
        )}

        <footer className="mt-10 text-center text-xs text-gray-500">
          Backend docs at <a className="text-indigo-600 underline" href="/api/docs" target="_blank" rel="noreferrer">/docs</a>
        </footer>
      </div>
    </div>
  )
}
