import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import { ApiError } from '../lib/api'
import { AuthCareIllustration } from '../components/CareVisuals'

export function SignUpPage() {
  const navigate = useNavigate()
  const { signup } = useAuth()
  const [form, setForm] = useState({ first_name: '', last_name: '', phone: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      await signup(form)
      navigate('/app/profile', { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to create your account right now.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="auth-page compact-auth-page">
      <div className="auth-layout compact-auth-layout">
        <form className="card auth-card compact-auth-card" onSubmit={handleSubmit}>
          <p className="eyebrow">Create account</p>
          <h1>Create your member account</h1>
          <p className="muted">Start with your core details. You can add addresses and profile settings right after sign-up.</p>
          <div className="form-grid two-col">
            <label>
              First name
              <input value={form.first_name} onChange={(event) => setForm({ ...form, first_name: event.target.value })} required />
            </label>
            <label>
              Last name
              <input value={form.last_name} onChange={(event) => setForm({ ...form, last_name: event.target.value })} required />
            </label>
          </div>
          <label>
            Phone
            <input value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} placeholder="Optional" />
          </label>
          <label>
            Email
            <input type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} required />
          </label>
          <label>
            Password
            <input type="password" minLength={8} value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} required />
          </label>
          {error ? <p className="error-text">{error}</p> : null}
          <button className="primary-button" disabled={submitting} type="submit">
            {submitting ? 'Creating your account…' : 'Create account'}
          </button>
          <p className="muted auth-footer-link">Already registered? <Link to="/signin">Sign in</Link>.</p>
        </form>
        <div className="card auth-aside compact-auth-aside">
          <p className="eyebrow">Get started</p>
          <h2>Set up your account in a few clear steps.</h2>
          <p className="muted">
            Create your account, save addresses, and start managing care without busy or confusing screens.
          </p>
          <AuthCareIllustration title="Create your account, save addresses, and get started right away." />
          <div className="support-stat-grid">
            <div className="support-stat">
              <strong>Multiple addresses</strong>
              <span>Keep home and family locations ready</span>
            </div>
            <div className="support-stat">
              <strong>Book more easily</strong>
              <span>Reuse saved details when requesting care</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
