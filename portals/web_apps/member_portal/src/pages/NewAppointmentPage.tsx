import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { CareTypeIllustration } from '../components/CareVisuals'
import { useAuth } from '../context/AuthContext'
import { api, ApiError } from '../lib/api'
import { careTypes, careTypeLabels } from '../lib/careTypes'
import type { Address } from '../types'

export function NewAppointmentPage() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const requestedServiceType = searchParams.get('service_type')
  const [addresses, setAddresses] = useState<Address[]>([])
  const [form, setForm] = useState({
    address_id: '',
    service_type: requestedServiceType && careTypeLabels.includes(requestedServiceType) ? requestedServiceType : 'Skilled Nursing',
    requested_date: '',
    requested_time_slot: 'Morning',
    preferred_hour: '09',
    preferred_minute: '00',
    reason: '',
    notes: '',
  })
  const [error, setError] = useState('')

  const setServiceType = (serviceType: string) => {
    setForm((current) => ({ ...current, service_type: serviceType }))
  }

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

  useEffect(() => {
    if (requestedServiceType && careTypeLabels.includes(requestedServiceType)) {
      setForm((current) => ({ ...current, service_type: requestedServiceType }))
    }
  }, [requestedServiceType])

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!token) return
    try {
      const created = await api.createAppointment(token, {
        ...form,
        address_id: Number(form.address_id),
      })
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
          <p className="muted">Choose the kind of care you need, pick an address, and share the best date and time for the visit.</p>
        </div>
      </div>
      {addresses.length === 0 ? (
        <div className="subcard">
          Save at least one address before booking care. <Link to="/app/profile">Add an address in your profile.</Link>
        </div>
      ) : (
        <form className="form-grid two-col" onSubmit={handleSubmit}>
          <div className="full-width stack-sm">
            <label>Care type</label>
            <div className="care-type-grid">
              {careTypes.map((careType) => {
                const isActive = form.service_type === careType.label
                return (
                  <button
                    className={`care-type-card care-type-filter ${isActive ? 'active' : ''}`}
                    key={careType.slug}
                    type="button"
                    onClick={() => setServiceType(careType.label)}
                  >
                    <CareTypeIllustration variant={careType.slug} title={careType.label} />
                    <div className="care-type-copy">
                      <strong>{careType.label}</strong>
                      <span>{careType.blurb}</span>
                    </div>
                  </button>
                )
              })}
            </div>
          </div>
          <label>
            Address
            <select value={form.address_id} onChange={(event) => setForm({ ...form, address_id: event.target.value })} required>
              {addresses.map((address) => (
                <option key={address.id} value={address.id}>{address.label} · {address.line1}</option>
              ))}
            </select>
          </label>
          <label>
            Service type
            <select value={form.service_type} onChange={(event) => setForm({ ...form, service_type: event.target.value })}>
              {careTypeLabels.map((label) => (
                <option key={label}>{label}</option>
              ))}
            </select>
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
            Preferred hour
            <select value={form.preferred_hour} onChange={(event) => setForm({ ...form, preferred_hour: event.target.value })}>
              {Array.from({ length: 12 }, (_, index) => String(index + 8).padStart(2, '0')).map((hour) => (
                <option key={hour} value={hour}>{hour}</option>
              ))}
            </select>
          </label>
          <label>
            Preferred minute
            <select value={form.preferred_minute} onChange={(event) => setForm({ ...form, preferred_minute: event.target.value })}>
              {['00', '15', '30', '45'].map((minute) => (
                <option key={minute} value={minute}>{minute}</option>
              ))}
            </select>
          </label>
          <label className="full-width">
            Reason for care
            <textarea
              rows={4}
              value={form.reason}
              onChange={(event) => setForm({ ...form, reason: event.target.value })}
              placeholder="For example: recovering after discharge, help with medications, mobility support, wound care, or check-in visits for a parent."
            />
          </label>
          <label className="full-width">
            Notes for your care team
            <textarea rows={4} value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} placeholder="Share timing preferences, mobility notes, building access details, or anything else the care team should know." />
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
