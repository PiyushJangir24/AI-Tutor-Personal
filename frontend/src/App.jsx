import React, { useMemo, useState } from 'react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export default function App() {
  const [message, setMessage] = useState('Explain derivatives in calculus and make flashcards')
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState(null)
  const [error, setError] = useState(null)
  const [userId, setUserId] = useState(null)
  const [chatId, setChatId] = useState(null)

  const disabled = loading || !message.trim()

  async function send() {
    setLoading(true)
    setError(null)
    try {
      const { data } = await axios.post(`${API_BASE}/chat`, {
        user_id: userId,
        chat_id: chatId,
        message
      })
      setResponse(data)
      if (!userId) setUserId(1) // simple client-side sticky id for demo
      if (!chatId) setChatId(1)
    } catch (err) {
      setError(err?.response?.data || { error: 'network_error', detail: String(err) })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container py-8 space-y-6">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Autonomous AI Tutor Orchestrator</h1>
        <span className="text-sm text-gray-500">Backend: {API_BASE}</span>
      </header>

      <section className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 space-y-3">
        <label htmlFor="message" className="block text-sm font-medium">Student message</label>
        <textarea
          id="message"
          className="w-full h-28 p-3 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900"
          value={message}
          onChange={e => setMessage(e.target.value)}
        />
        <div className="flex gap-3">
          <button
            onClick={send}
            disabled={disabled}
            className="px-4 py-2 rounded bg-indigo-600 text-white disabled:opacity-50"
          >{loading ? 'Thinking…' : 'Send'}</button>
          <button
            onClick={() => { setResponse(null); setError(null); }}
            className="px-3 py-2 rounded border"
          >Clear</button>
        </div>
      </section>

      {error && (
        <section className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4 rounded">
          <pre className="text-sm overflow-auto">{JSON.stringify(error, null, 2)}</pre>
        </section>
      )}

      {response && (
        <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 space-y-2">
            <h2 className="font-semibold">Chosen Tool</h2>
            <div className="text-sm"><span className="font-mono">{response.chosen_tool}</span></div>
            <h3 className="font-semibold mt-3">Extracted Parameters</h3>
            <pre className="text-xs overflow-auto">{JSON.stringify(response.parameters, null, 2)}</pre>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 space-y-2">
            <h2 className="font-semibold">Context Analysis</h2>
            <pre className="text-xs overflow-auto">{JSON.stringify(response.analysis, null, 2)}</pre>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 space-y-2">
            <h2 className="font-semibold">API Result</h2>
            <pre className="text-xs overflow-auto">{JSON.stringify(response.result, null, 2)}</pre>
          </div>
        </section>
      )}

      <footer className="text-xs text-gray-500">/ — chat + response viewer</footer>
    </div>
  )
}
