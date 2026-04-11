import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import type { AppointmentRow, PaginatedResponse } from '../types'
import { Pager } from './AppointmentsPage'

export function ClaimsPage() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const [data, setData] = useState<PaginatedResponse<AppointmentRow> | null>(null)
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
        const res = await api.listClaims(token!, params)
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
  }, [token, page])

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-[#1A2B3C]">Slack Claims</h2>
        <p className="text-sm text-[#3D5A73] mt-1">
          Appointments that field staff have claimed via the
          #in-home-help-member-appointment-requests Slack channel.
        </p>
      </div>
      {error && <div className="text-sm text-[#D32F2F]">{error}</div>}
      {loading && <p className="text-sm text-[#3D5A73]">Loading...</p>}
      {data && data.items.length === 0 && (
        <p className="text-sm text-[#3D5A73]">No claimed appointments yet.</p>
      )}
      {data && data.items.length > 0 && (
        <table className="w-full text-left border-collapse bg-white rounded-xl shadow overflow-hidden">
          <thead>
            <tr className="bg-[#0D7377] text-white text-sm">
              <th className="px-4 py-3">Appointment</th>
              <th className="px-4 py-3">Member</th>
              <th className="px-4 py-3">Service</th>
              <th className="px-4 py-3">When</th>
              <th className="px-4 py-3">Claimed by</th>
              <th className="px-4 py-3">Claimed at</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((row) => (
              <tr
                key={row.id}
                onClick={() => navigate(`/app/appointments/${row.id}`)}
                className="border-b border-[#0D7377]/10 text-sm cursor-pointer hover:bg-[#0D7377]/5"
              >
                <td className="px-4 py-3 font-mono">A-{row.id}</td>
                <td className="px-4 py-3">M-{row.member_id}</td>
                <td className="px-4 py-3">{row.service_type}</td>
                <td className="px-4 py-3">
                  {row.requested_date} {row.requested_time_slot}
                </td>
                <td className="px-4 py-3">
                  {row.claimed_by_slack_user_name ?? row.claimed_by_slack_user_id ?? '—'}
                </td>
                <td className="px-4 py-3 text-[#3D5A73]">{row.claimed_at ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {data && data.total_pages > 1 && (
        <Pager page={data.page} totalPages={data.total_pages} onChange={setPage} />
      )}
    </div>
  )
}
