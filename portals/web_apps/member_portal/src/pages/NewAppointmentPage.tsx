import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import { api, ApiError } from '../lib/api'
import type { Address } from '../types'

export function NewAppointmentPage() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const [addresses, setAddresses] = useState<Address[]>([])
  const [form, setForm] = useState({
    address_id: '',
    service_type: 'Skilled Nursing',
    service_area: '',
    requested_date: '',
    requested_time_slot: 'Morning',
    reason: '',
    notes: '',
  })
  const [error, setError] = useState('')

  useEffect(() => {
    if (!token) return
    void api.listAddresses(token).then((nextAddresses) => {
      setAddresses(nextAddresses)
      const defaultAddress = nextAddresses.find((address) => address.is_default) ?? nextAddresses[0]
      if (defaultAddress) {
        setForm((current) => ({ ...current, address_id: String(defaultAddress.id) }))
      }
    })
  }, [token])

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!token) return
    try {
      const created = await api.createAppointment(token, { ...form, address_id: Number(form.address_id) })
      navigate(`/app/appointments/${created.id}`)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to create appointment.')
    }
  }

  return (
    <section className="card stack-md">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Book care</p>
          <h2>Request a new in-home appointment</h2>
          <p className="muted">Choose a saved address, confirm the service window, and add useful context for the care team.</p>
        </div>
        <Link className="secondary-button" to="/app/profile">Manage addresses</Link>
      </div>
      {addresses.length === 0 ? (
        <div className="subcard">
          Save at least one address before booking care. <Link to="/app/profile">Add an address in your profile.</Link>
        </div>
      ) : (
        <form className="form-grid two-col" onSubmit={handleSubmit}>
          <label>
            Service location
            <select value={form.address_id} onChange={(event) => setForm({ ...form, address_id: event.target.value })} required>
              {addresses.map((address) => (
                <option key={address.id} value={address.id}>{address.label} · {address.line1}</option>
              ))}
            </select>
          </label>
          <label>
            Service type
            <select value={form.service_type} onChange={(event) => setForm({ ...form, service_type: event.target.value })}>
              <option>Skilled Nursing</option>
              <option>Home Health Aide</option>
              <option>Physical Therapy</option>
              <option>Companion Care</option>
            </select>
          </label>
          <label>
            Service area
            <input value={form.service_area} onChange={(event) => setForm({ ...form, service_area: event.target.value })} placeholder="Post-discharge support" />
          </label>
          <label>
            Requested date
            <input type="date" value={form.requested_date} onChange={(event) => setForm({ ...form, requested_date: event.target.value })} required />
          </label>
          <label>
            Preferred time
            <select value={form.requested_time_slot} onChange={(event) => setForm({ ...form, requested_time_slot: event.target.value })}>
              <option>Morning</option>
              <option>Afternoon</option>
              <option>Evening</option>
            </select>
          </label>
          <label>
            Reason for care
            <input value={form.reason} onChange={(event) => setForm({ ...form, reason: event.target.value })} placeholder="Medication management" />
          </label>
          <label className="full-width">
            Notes for your care team
            <textarea rows={4} value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} placeholder="Share timing preferences, mobility notes, or special instructions." />
          </label>
          {error ? <p className="error-text full-width">{error}</p> : null}
          <div className="form-actions full-width">
            <button className="primary-button" type="submit">Confirm request</button>
          </div>
        </form>
      )}
    </section>
  )
}
