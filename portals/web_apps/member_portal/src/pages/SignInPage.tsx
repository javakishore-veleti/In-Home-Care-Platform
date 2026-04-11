import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { ApiError } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import { AuthCareIllustration } from '../components/CareVisuals'

export function SignInPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { signin } = useAuth()
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      await signin(form)
      const nextPath = (location.state as { from?: { pathname?: string } } | undefined)?.from?.pathname ?? '/app/appointments'
      navigate(nextPath, { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to sign in right now.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-layout">
        <div className="card auth-aside">
          <p className="eyebrow">Welcome back</p>
          <h2>Everything important in one clear, organized place.</h2>
          <p className="muted">
            Designed for real member tasks: booking care, reviewing visit follow-up, and keeping service locations current.
          </p>
          <AuthCareIllustration title="Appointments, visit updates, and account details stay connected." />
          <div className="support-stat-grid">
            <div className="support-stat">
              <strong>Search fast</strong>
              <span>Appointments and visit history</span>
            </div>
            <div className="support-stat">
              <strong>Stay aligned</strong>
              <span>Documents, notes, and next steps</span>
            </div>
            <div className="support-stat">
              <strong>Get help</strong>
              <span>Concierge chat after sign-in</span>
            </div>
          </div>
          <ul className="feature-list">
            <li className="feature-item">
              <strong>Appointment clarity</strong>
              <span>Quickly find upcoming requests and review status changes.</span>
            </li>
            <li className="feature-item">
              <strong>Visit detail in one place</strong>
              <span>See notes, decisions, action items, and documents without jumping around.</span>
            </li>
            <li className="feature-item">
              <strong>Simple account management</strong>
              <span>Update profile details and maintain multiple service addresses.</span>
            </li>
          </ul>
        </div>
        <form className="card auth-card" onSubmit={handleSubmit}>
          <p className="eyebrow">Sign in</p>
          <h1>Sign in to your account</h1>
          <p className="muted">Use the email and password linked to your member account.</p>
          <label>
            Email
            <input type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} required />
          </label>
          <label>
            Password
            <input type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} required />
          </label>
          {error ? <p className="error-text">{error}</p> : null}
          <button className="primary-button" disabled={submitting} type="submit">
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>
          <p className="muted auth-footer-link">New here? <Link to="/signup">Create your account</Link>.</p>
        </form>
      </div>
    </div>
  )
}
