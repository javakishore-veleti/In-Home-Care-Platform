import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
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
  const page = Number(searchParams.get('page') ?? '1')

  useEffect(() => {
    if (!token) return
    setLoading(true)
    const params = new URLSearchParams({ query, page: String(page), page_size: '6' })
    void api.listAppointments(token, params).then(setData).finally(() => setLoading(false))
  }, [page, query, token])

  return (
    <div className="stack-xl">
      <section className="card stack-md">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Appointments</p>
            <h2>Search and review your care requests</h2>
          </div>
          <Link className="primary-button" to="/app/appointments/new">Book appointment</Link>
        </div>
        <div className="toolbar-row">
          <input
            placeholder="Search by service, area, status, or ID"
            value={query}
            onChange={(event) => setSearchParams({ query: event.target.value, page: '1' })}
          />
          <span className="tag">{data.total} result(s)</span>
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
              <p>{appointment.service_area || 'General care coordination'}</p>
              <p className="muted">Reason: {appointment.reason || 'No reason provided yet.'}</p>
            </Link>
          ))}
          {!loading && data.items.length === 0 ? <div className="subcard">No appointments match your search yet.</div> : null}
        </div>
        <div className="pagination-row">
          <button className="secondary-button" disabled={page <= 1} onClick={() => setSearchParams({ query, page: String(page - 1) })}>Previous</button>
          <span>Page {data.page} of {data.total_pages}</span>
          <button className="secondary-button" disabled={page >= data.total_pages} onClick={() => setSearchParams({ query, page: String(page + 1) })}>Next</button>
        </div>
      </section>
    </div>
  )
}
