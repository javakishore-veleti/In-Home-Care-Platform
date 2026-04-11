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
    <div className="auth-page compact-auth-page">
      <div className="auth-layout compact-auth-layout">
        <form className="card auth-card compact-auth-card" onSubmit={handleSubmit}>
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
        <div className="card auth-aside compact-auth-aside">
          <p className="eyebrow">Welcome back</p>
          <h2>Pick up where you left off.</h2>
          <p className="muted">
            Review appointments, check visit updates, and manage service details in one clear place.
          </p>
          <AuthCareIllustration title="Appointments, visit updates, and account details stay connected." />
          <div className="support-stat-grid">
            <div className="support-stat">
              <strong>Find care details</strong>
              <span>Appointments and visit history</span>
            </div>
            <div className="support-stat">
              <strong>Ask for help</strong>
              <span>Documents, notes, and next steps</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
