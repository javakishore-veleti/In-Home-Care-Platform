import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import { ApiError } from '../lib/api'

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
      <form className="card auth-card" onSubmit={handleSubmit}>
        <p className="eyebrow">Get started</p>
        <h1>Create your member account</h1>
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
        <p className="muted">Already registered? <Link to="/signin">Sign in</Link>.</p>
      </form>
    </div>
  )
}
