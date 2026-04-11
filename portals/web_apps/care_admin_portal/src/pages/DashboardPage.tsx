import { useEffect, useState } from 'react'

import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import type { AppointmentRow, DashboardStats } from '../types'

export function DashboardPage() {
  const { token } = useAuth()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [recent, setRecent] = useState<AppointmentRow[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!token) return
    let cancelled = false
    async function load() {
      try {
        const [s, recentRes] = await Promise.all([
          api.dashboardStats(token!),
          api.listAppointments(token!, new URLSearchParams({ page: '1', page_size: '5' })),
        ])
        if (cancelled) return
        setStats(s)
        setRecent(recentRes.items)
      } catch (exc) {
        if (cancelled) return
        setError(exc instanceof Error ? exc.message : 'Failed to load dashboard.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [token])

  const cards: { label: string; value: number; color: string }[] = stats
    ? [
        { label: 'Open Appointments', value: stats.open_appointments, color: '#E8612D' },
        { label: 'Claimed (Slack)', value: stats.claimed_appointments, color: '#0D7377' },
        { label: "Today's Visits", value: stats.todays_visits, color: '#1976D2' },
        { label: 'Total Members', value: stats.total_members, color: '#2D8A4E' },
      ]
    : []

  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-bold text-[#1A2B3C]">Dashboard</h2>
      {loading && <p className="text-sm text-[#3D5A73]">Loading...</p>}
      {error && (
        <div className="text-sm text-[#D32F2F] bg-[#FCEAEA] border border-[#D32F2F]/20 rounded px-3 py-2">{error}</div>
      )}
      {!loading && !error && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {cards.map((c) => (
              <div
                key={c.label}
                className="rounded-xl p-6 text-white shadow-md"
                style={{ backgroundColor: c.color }}
              >
                <p className="text-3xl font-bold">{c.value}</p>
                <p className="text-sm font-medium mt-1">{c.label}</p>
              </div>
            ))}
          </div>
          <div>
            <h3 className="text-lg font-bold text-[#1A2B3C] mb-3">Recent Appointments</h3>
            {recent.length === 0 ? (
              <p className="text-sm text-[#3D5A73]">No appointments yet.</p>
            ) : (
              <table className="w-full text-left border-collapse bg-white rounded-xl shadow overflow-hidden">
                <thead>
                  <tr className="bg-[#0D7377] text-white text-sm">
                    <th className="px-4 py-3">ID</th>
                    <th className="px-4 py-3">Member</th>
                    <th className="px-4 py-3">Service</th>
                    <th className="px-4 py-3">Date</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Claimed by</th>
                  </tr>
                </thead>
                <tbody>
                  {recent.map((row) => (
                    <tr key={row.id} className="border-b border-[#0D7377]/10 text-sm">
                      <td className="px-4 py-3 font-mono">A-{row.id}</td>
                      <td className="px-4 py-3">M-{row.member_id}</td>
                      <td className="px-4 py-3">{row.service_type}</td>
                      <td className="px-4 py-3">
                        {row.requested_date} {row.requested_time_slot}
                      </td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-1 rounded text-xs font-bold bg-[#0D7377]/10 text-[#0D7377] uppercase">
                          {row.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-[#3D5A73]">
                        {row.claimed_by_slack_user_name ?? row.claimed_by_slack_user_id ?? '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </div>
  )
}
