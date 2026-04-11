import { useEffect, useState } from 'react'

import { useAuth } from '../context/AuthContext'
import { api, ApiError } from '../lib/api'
import type { ChatMessage } from '../types'

export function ChatPage() {
  const { token } = useAuth()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [draft, setDraft] = useState('')
  const [error, setError] = useState('')
  const [sending, setSending] = useState(false)

  useEffect(() => {
    if (!token) return
    void api.listChatMessages(token).then((response) => setMessages(response.messages))
  }, [token])

  const sendMessage = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!token || !draft.trim()) return
    setSending(true)
    setError('')
    try {
      const response = await api.sendChatMessage(token, { message: draft.trim() })
      setMessages(response.messages)
      setDraft('')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to send message right now.')
    } finally {
      setSending(false)
    }
  }

  return (
    <section className="card stack-md chat-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Care concierge</p>
          <h2>Chat with a guided assistant</h2>
        </div>
      </div>
      <div className="chat-thread">
        {messages.length === 0 ? <div className="subcard">Ask about appointments, visits, or managing your saved service addresses.</div> : null}
        {messages.map((message) => (
          <div key={message.id} className={`chat-bubble ${message.role}`}>
            <strong>{message.role === 'assistant' ? 'Assistant' : 'You'}</strong>
            <p>{message.message}</p>
          </div>
        ))}
      </div>
      <form className="chat-compose" onSubmit={sendMessage}>
        <textarea rows={3} value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="How can I help today?" />
        <div className="form-actions">
          {error ? <p className="error-text">{error}</p> : null}
          <button className="primary-button" type="submit" disabled={sending}>{sending ? 'Sending…' : 'Send message'}</button>
        </div>
      </form>
    </section>
  )
}
