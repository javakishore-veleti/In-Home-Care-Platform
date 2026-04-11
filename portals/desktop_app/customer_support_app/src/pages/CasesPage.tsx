import { useEffect, useState } from 'react'

import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import type { CaseRow, PaginatedResponse } from '../types'

export function CasesPage() {
  const { token } = useAuth()
  const [data, setData] = useState<PaginatedResponse<CaseRow> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token) return
    let cancelled = false
    async function load() {
      try {
        const res = await api.listCases(token!, new URLSearchParams({ page: '1', page_size: '20' }))
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
      <h2 className="text-xl font-bold text-[#0D7377]">Open Cases</h2>
      {loading && <p className="text-sm text-[#3D5A73]">Loading...</p>}
      {error && <div className="text-sm text-[#D32F2F]">{error}</div>}
      {!loading && data && data.items.length === 0 && (
        <div className="bg-white rounded-xl shadow p-8 text-center text-sm text-[#3D5A73]">
          No cases yet. The <code>support_cases</code> table is not yet implemented in the
          backend; this view will populate once it exists.
        </div>
      )}
      {data && data.items.length > 0 && (
        <table className="w-full text-left border-collapse bg-white rounded-xl shadow overflow-hidden">
          <thead>
            <tr className="bg-[#0D7377] text-white text-sm">
              <th className="px-4 py-3">Case</th>
              <th className="px-4 py-3">Member</th>
              <th className="px-4 py-3">Subject</th>
              <th className="px-4 py-3">Priority</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((c) => (
              <tr key={c.id} className="border-b border-[#0D7377]/10 text-sm">
                <td className="px-4 py-3 font-mono">C-{c.id}</td>
                <td className="px-4 py-3">{c.member_id ? `M-${c.member_id}` : '—'}</td>
                <td className="px-4 py-3">{c.subject ?? '—'}</td>
                <td className="px-4 py-3">{c.priority ?? '—'}</td>
                <td className="px-4 py-3">{c.status ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
