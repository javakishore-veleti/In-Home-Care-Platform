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
    <div className="auth-page">
      <div className="auth-layout">
        <div className="card auth-aside">
          <p className="eyebrow">Get started</p>
          <h2>Set up your member account for day-to-day care coordination.</h2>
          <p className="muted">
            Create a secure member profile, save service locations, and start requesting care with cleaner follow-up.
          </p>
          <AuthCareIllustration title="Create your account, save addresses, and get started right away." />
          <div className="support-stat-grid">
            <div className="support-stat">
              <strong>Multiple addresses</strong>
              <span>Keep home and family locations ready</span>
            </div>
            <div className="support-stat">
              <strong>Faster booking</strong>
              <span>Reuse saved details when requesting care</span>
            </div>
            <div className="support-stat">
              <strong>Better follow-up</strong>
              <span>Track what happened after each visit</span>
            </div>
          </div>
          <ul className="feature-list">
            <li className="feature-item">
              <strong>Profile foundation</strong>
              <span>Capture the member details the care team needs most often.</span>
            </li>
            <li className="feature-item">
              <strong>Address-driven booking</strong>
              <span>Use saved locations when scheduling in-home services.</span>
            </li>
            <li className="feature-item">
              <strong>One connected experience</strong>
              <span>Appointments, visits, and support stay connected after sign-in.</span>
            </li>
          </ul>
        </div>
        <form className="card auth-card" onSubmit={handleSubmit}>
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
      </div>
    </div>
  )
}
