import { useEffect, useState } from 'react'

import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import type { StaffRow } from '../types'

const ROLE_COLORS: Record<string, string> = {
  admin: '#D32F2F',
  support: '#1976D2',
  field_officer: '#0D7377',
  care_planner: '#E8612D',
  auditor: '#6A1B9A',
}

export function StaffPage() {
  const { token } = useAuth()
  const [staff, setStaff] = useState<StaffRow[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!token) return
    let cancelled = false
    async function load() {
      try {
        const res = await api.listStaff(token!)
        if (!cancelled) setStaff(res.items)
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
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-[#1A2B3C]">Internal Staff</h2>
        <p className="text-sm text-[#3D5A73] mt-1">
          Seeded employee accounts used by the admin, support, field, care-planning, and audit portals.
        </p>
      </div>
      {error && <div className="text-sm text-[#D32F2F]">{error}</div>}
      {loading && <p className="text-sm text-[#3D5A73]">Loading...</p>}
      {staff.length === 0 && !loading && (
        <p className="text-sm text-[#3D5A73]">No internal users found. Did auth_svc seed run?</p>
      )}
      {staff.length > 0 && (
        <table className="w-full text-left border-collapse bg-white rounded-xl shadow overflow-hidden">
          <thead>
            <tr className="bg-[#0D7377] text-white text-sm">
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Role</th>
              <th className="px-4 py-3">Active</th>
              <th className="px-4 py-3">Created</th>
            </tr>
          </thead>
          <tbody>
            {staff.map((row) => (
              <tr key={row.id} className="border-b border-[#0D7377]/10 text-sm">
                <td className="px-4 py-3 font-mono">U-{row.id}</td>
                <td className="px-4 py-3">{row.email}</td>
                <td className="px-4 py-3">
                  <span
                    className="px-2 py-1 rounded text-xs font-bold text-white uppercase"
                    style={{ backgroundColor: ROLE_COLORS[row.role] ?? '#3D5A73' }}
                  >
                    {row.role}
                  </span>
                </td>
                <td className="px-4 py-3">{row.is_active ? 'Yes' : 'No'}</td>
                <td className="px-4 py-3 text-[#3D5A73]">{row.created_at ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
