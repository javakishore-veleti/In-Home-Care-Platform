import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import type { MemberRow, PaginatedResponse } from '../types'
import { Pager } from './AppointmentsPage'

export function MembersPage() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const [data, setData] = useState<PaginatedResponse<MemberRow> | null>(null)
  const [query, setQuery] = useState('')
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
        const res = await api.listMembers(token!, params)
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
  }, [token, page, query])

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-[#1A2B3C]">Members</h2>
      <input
        value={query}
        onChange={(e) => {
          setQuery(e.target.value)
          setPage(1)
        }}
        placeholder="Search by name, email, id..."
        className="w-full max-w-md px-3 py-2 rounded border border-[#0D7377]/20 text-sm focus:outline-none focus:ring-2 focus:ring-[#0D7377]"
      />
      {error && <div className="text-sm text-[#D32F2F]">{error}</div>}
      {loading && <p className="text-sm text-[#3D5A73]">Loading...</p>}
      {data && data.items.length === 0 && <p className="text-sm text-[#3D5A73]">No members found.</p>}
      {data && data.items.length > 0 && (
        <table className="w-full text-left border-collapse bg-white rounded-xl shadow overflow-hidden">
          <thead>
            <tr className="bg-[#0D7377] text-white text-sm">
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Phone</th>
              <th className="px-4 py-3">Tenant</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((row) => (
              <tr
                key={row.id}
                onClick={() => navigate(`/app/members/${row.id}`)}
                className="border-b border-[#0D7377]/10 text-sm cursor-pointer hover:bg-[#0D7377]/5"
              >
                <td className="px-4 py-3 font-mono">M-{row.id}</td>
                <td className="px-4 py-3">
                  {[row.first_name, row.last_name].filter(Boolean).join(' ') || '—'}
                </td>
                <td className="px-4 py-3">{row.email}</td>
                <td className="px-4 py-3">{row.phone ?? '—'}</td>
                <td className="px-4 py-3 text-[#3D5A73]">{row.tenant_id}</td>
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
