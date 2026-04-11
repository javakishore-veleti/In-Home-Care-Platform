import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import type { PaginatedResponse, VisitRow } from '../types'

export function VisitsPage() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const [data, setData] = useState<PaginatedResponse<VisitRow> | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!token) return
    let cancelled = false
    async function load() {
      try {
        const res = await api.listVisits(token!, new URLSearchParams({ page: '1', page_size: '30' }))
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
  }, [token])

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-[#0D7377]">Visits (read-only)</h2>
      {loading && <p className="text-sm text-[#3D5A73]">Loading...</p>}
      {error && <div className="text-sm text-[#D32F2F]">{error}</div>}
      {data && data.items.length === 0 && <p className="text-sm text-[#3D5A73]">No visits.</p>}
      {data && data.items.length > 0 && (
        <table className="w-full text-left border-collapse bg-white rounded-xl shadow overflow-hidden">
          <thead>
            <tr className="bg-[#0D7377] text-white text-sm">
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Member</th>
              <th className="px-4 py-3">Appointment</th>
              <th className="px-4 py-3">Date</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Notes</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((row) => (
              <tr
                key={row.id}
                onClick={() => navigate(`/app/visits/${row.id}`)}
                className="border-b border-[#0D7377]/10 text-sm cursor-pointer hover:bg-[#0D7377]/5"
              >
                <td className="px-4 py-3 font-mono">V-{row.id}</td>
                <td className="px-4 py-3">M-{row.member_id}</td>
                <td className="px-4 py-3">{row.appointment_id ? `A-${row.appointment_id}` : '—'}</td>
                <td className="px-4 py-3">{row.visit_date ?? '—'}</td>
                <td className="px-4 py-3 uppercase text-xs font-bold text-[#0D7377]">{row.status}</td>
                <td className="px-4 py-3 text-[#3D5A73] truncate max-w-[240px]">{row.notes_summary ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
