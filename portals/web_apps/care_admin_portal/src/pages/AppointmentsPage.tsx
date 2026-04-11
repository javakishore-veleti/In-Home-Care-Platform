import { useEffect, useState } from 'react'

import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import type { AppointmentRow, PaginatedResponse } from '../types'

const STATUSES = ['', 'requested', 'claimed', 'cancelled']

export function AppointmentsPage() {
  const { token } = useAuth()
  const [data, setData] = useState<PaginatedResponse<AppointmentRow> | null>(null)
  const [query, setQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [page, setPage] = useState(1)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!token) return
    let cancelled = false
    async function load() {
      setLoading(true)
      try {
        const params = new URLSearchParams({ page: String(page), page_size: '20' })
        if (query) params.set('query', query)
        if (statusFilter) params.set('status_filter', statusFilter)
        const res = await api.listAppointments(token!, params)
        if (!cancelled) setData(res)
      } catch (exc) {
        if (!cancelled) setError(exc instanceof Error ? exc.message : 'Failed to load.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [token, page, query, statusFilter])

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-[#1A2B3C]">All Appointments</h2>
      <div className="flex flex-wrap gap-3">
        <input
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            setPage(1)
          }}
          placeholder="Search by id, service, status..."
          className="flex-1 min-w-[240px] px-3 py-2 rounded border border-[#0D7377]/20 text-sm focus:outline-none focus:ring-2 focus:ring-[#0D7377]"
        />
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value)
            setPage(1)
          }}
          className="px-3 py-2 rounded border border-[#0D7377]/20 text-sm bg-white"
        >
          {STATUSES.map((s) => (
            <option key={s || 'all'} value={s}>
              {s || 'All statuses'}
            </option>
          ))}
        </select>
      </div>
      {error && <div className="text-sm text-[#D32F2F]">{error}</div>}
      {loading && <p className="text-sm text-[#3D5A73]">Loading...</p>}
      {data && data.items.length === 0 && <p className="text-sm text-[#3D5A73]">No appointments found.</p>}
      {data && data.items.length > 0 && (
        <table className="w-full text-left border-collapse bg-white rounded-xl shadow overflow-hidden">
          <thead>
            <tr className="bg-[#0D7377] text-white text-sm">
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Member</th>
              <th className="px-4 py-3">Service</th>
              <th className="px-4 py-3">Area</th>
              <th className="px-4 py-3">Requested</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Claimed by</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((row) => (
              <tr key={row.id} className="border-b border-[#0D7377]/10 text-sm">
                <td className="px-4 py-3 font-mono">A-{row.id}</td>
                <td className="px-4 py-3">M-{row.member_id}</td>
                <td className="px-4 py-3">{row.service_type}</td>
                <td className="px-4 py-3">{row.service_area ?? '—'}</td>
                <td className="px-4 py-3">
                  {row.requested_date} {row.requested_time_slot}
                </td>
                <td className="px-4 py-3 uppercase text-xs font-bold text-[#0D7377]">{row.status}</td>
                <td className="px-4 py-3 text-[#3D5A73]">
                  {row.claimed_by_slack_user_name ?? row.claimed_by_slack_user_id ?? '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {data && data.total_pages > 1 && (
        <Pager
          page={data.page}
          totalPages={data.total_pages}
          onChange={setPage}
        />
      )}
    </div>
  )
}

export function Pager({
  page,
  totalPages,
  onChange,
}: {
  page: number
  totalPages: number
  onChange: (page: number) => void
}) {
  return (
    <div className="flex items-center gap-3 text-sm">
      <button
        type="button"
        disabled={page <= 1}
        onClick={() => onChange(page - 1)}
        className="px-3 py-1.5 rounded bg-white border border-[#0D7377]/20 disabled:opacity-50"
      >
        Previous
      </button>
      <span className="text-[#3D5A73]">
        Page {page} of {totalPages}
      </span>
      <button
        type="button"
        disabled={page >= totalPages}
        onClick={() => onChange(page + 1)}
        className="px-3 py-1.5 rounded bg-white border border-[#0D7377]/20 disabled:opacity-50"
      >
        Next
      </button>
    </div>
  )
}
