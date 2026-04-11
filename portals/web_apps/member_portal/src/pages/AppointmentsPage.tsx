import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { CareTypeIllustration } from '../components/CareVisuals'
import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import { careTypes } from '../lib/careTypes'
import type { AppointmentListResponse } from '../types'

const emptyResponse: AppointmentListResponse = {
  items: [],
  page: 1,
  page_size: 6,
  total: 0,
  total_pages: 1,
}

export function AppointmentsPage() {
  const { token } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()
  const [data, setData] = useState<AppointmentListResponse>(emptyResponse)
  const [loading, setLoading] = useState(true)

  const query = searchParams.get('query') ?? ''
  const serviceType = searchParams.get('service_type') ?? ''
  const page = Number(searchParams.get('page') ?? '1')
  const scheduledCount = data.items.filter((appointment) => appointment.status === 'scheduled' || appointment.status === 'pending').length
  const completedCount = data.items.filter((appointment) => appointment.status === 'completed').length

  const setParams = (updates: Record<string, string | null>) => {
    const next = new URLSearchParams(searchParams)
    Object.entries(updates).forEach(([key, value]) => {
      if (!value) {
        next.delete(key)
      } else {
        next.set(key, value)
      }
    })
    if (!updates.page) {
      next.set('page', '1')
    }
    setSearchParams(next)
  }

  useEffect(() => {
    if (!token) return
    setLoading(true)
    const params = new URLSearchParams({ query, page: String(page), page_size: '6' })
    if (serviceType) {
      params.set('service_type', serviceType)
    }
    void api.listAppointments(token, params).then(setData).finally(() => setLoading(false))
  }, [page, query, serviceType, token])

  return (
    <div className="stack-xl">
      <section className="search-surface">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Appointments</p>
            <h2>Find and follow your care requests</h2>
            <p className="muted">Search by service, reason for care, status, or appointment ID.</p>
          </div>
          <Link className="primary-button" to="/app/appointments/new">Book appointment</Link>
        </div>
        <div className="search-input-shell">
          <span className="search-icon">⌕</span>
          <input
            placeholder="Search appointments"
            value={query}
            onChange={(event) => setParams({ query: event.target.value })}
          />
          <span className="tag">{data.total} results</span>
        </div>
        <div className="care-type-grid">
          {careTypes.map((careType) => {
            const isActive = serviceType === careType.label
            return (
              <button
                className={`care-type-card care-type-filter ${isActive ? 'active' : ''}`}
                key={careType.slug}
                type="button"
                onClick={() => setParams({ service_type: isActive ? null : careType.label })}
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
      </section>
      <div className="stats-strip compact">
        <div className="metric-card">
          <strong>{data.total}</strong>
          <span>Total appointments</span>
        </div>
        <div className="metric-card">
          <strong>{scheduledCount}</strong>
          <span>Open requests</span>
        </div>
        <div className="metric-card">
          <strong>{completedCount}</strong>
          <span>Completed</span>
        </div>
      </div>
      <section className="card stack-md">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Results</p>
            <h2>Your appointments</h2>
            <p className="muted">
              {serviceType
                ? `Showing ${serviceType} appointments. Tap the same care card again to return to all appointments.`
                : 'Review upcoming care, follow-ups, and completed requests.'}
            </p>
          </div>
        </div>
        {loading ? <p className="muted">Loading appointments…</p> : null}
        <div className="appointment-grid">
          {data.items.map((appointment) => (
            <Link className="subcard appointment-card" key={appointment.id} to={`/app/appointments/${appointment.id}`}>
              <div className="row-between">
                <strong>{appointment.service_type}</strong>
                <span className="tag capitalize">{appointment.status}</span>
              </div>
              <p>{appointment.requested_date} · {appointment.requested_time_slot}</p>
              {appointment.service_area ? <p>Care focus: {appointment.service_area}</p> : null}
              <p className="muted">Reason: {appointment.reason || 'No reason provided yet.'}</p>
            </Link>
          ))}
          {!loading && data.items.length === 0 ? <div className="subcard empty-state-card">No appointments match the current filters yet.</div> : null}
        </div>
        <div className="pagination-row">
          <button className="secondary-button" disabled={page <= 1} onClick={() => setParams({ page: String(page - 1) })}>Previous</button>
          <span>Page {data.page} of {data.total_pages}</span>
          <button className="secondary-button" disabled={page >= data.total_pages} onClick={() => setParams({ page: String(page + 1) })}>Next</button>
        </div>
      </section>
    </div>
  )
}
