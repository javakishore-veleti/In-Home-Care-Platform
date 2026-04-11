import { useEffect, useState, type FormEvent } from 'react'

import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import type { CaseRow, PaginatedResponse } from '../types'

const PRIORITY_COLORS: Record<string, string> = {
  low: '#2D8A4E',
  medium: '#E8A317',
  high: '#E8612D',
  urgent: '#D32F2F',
}

const STATUS_COLORS: Record<string, string> = {
  open: '#1976D2',
  in_progress: '#E8A317',
  resolved: '#2D8A4E',
  escalated: '#D32F2F',
}

export function CasesPage() {
  const { token } = useAuth()
  const [data, setData] = useState<PaginatedResponse<CaseRow> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // New-case form
  const [showForm, setShowForm] = useState(false)
  const [memberId, setMemberId] = useState('')
  const [subject, setSubject] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState('medium')
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  async function loadCases() {
    if (!token) return
    setLoading(true)
    try {
      const res = await api.listCases(token, new URLSearchParams({ page: '1', page_size: '50' }))
      setData(res)
      setError(null)
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : 'Failed to load.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadCases()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token])

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!token) return
    setFormError(null)
    setSubmitting(true)
    try {
      const member_id_num = Number(memberId)
      if (!Number.isFinite(member_id_num) || member_id_num <= 0) {
        throw new Error('Member ID must be a positive integer.')
      }
      await api.createCase(token, {
        member_id: member_id_num,
        subject: subject.trim(),
        description: description.trim() || undefined,
        priority,
      })
      setMemberId('')
      setSubject('')
      setDescription('')
      setPriority('medium')
      setShowForm(false)
      await loadCases()
    } catch (exc) {
      setFormError(exc instanceof Error ? exc.message : 'Could not create case.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-[#0D7377]">Support Cases</h2>
        <button
          type="button"
          onClick={() => setShowForm((v) => !v)}
          className="px-3 py-1.5 rounded bg-[#0D7377] hover:bg-[#084C4F] text-white text-xs font-semibold"
        >
          {showForm ? 'Cancel' : '+ New case'}
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="bg-white border border-[#0D7377]/10 rounded-xl shadow p-4 space-y-3"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-[#3D5A73] mb-1">Member ID</label>
              <input
                value={memberId}
                onChange={(e) => setMemberId(e.target.value)}
                type="number"
                required
                placeholder="e.g. 1"
                className="w-full px-3 py-2 rounded border border-[#0D7377]/20 text-sm focus:outline-none focus:ring-2 focus:ring-[#0D7377]"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#3D5A73] mb-1">Priority</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="w-full px-3 py-2 rounded border border-[#0D7377]/20 text-sm bg-white"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-[#3D5A73] mb-1">Subject</label>
            <input
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              required
              maxLength={255}
              placeholder="Short summary of the issue"
              className="w-full px-3 py-2 rounded border border-[#0D7377]/20 text-sm focus:outline-none focus:ring-2 focus:ring-[#0D7377]"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-[#3D5A73] mb-1">Description (optional)</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              placeholder="Context, what the member said, what we tried..."
              className="w-full px-3 py-2 rounded border border-[#0D7377]/20 text-sm focus:outline-none focus:ring-2 focus:ring-[#0D7377]"
            />
          </div>
          {formError && (
            <div className="text-xs text-[#D32F2F] bg-[#FCEAEA] border border-[#D32F2F]/20 rounded px-3 py-2">
              {formError}
            </div>
          )}
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 rounded bg-[#0D7377] hover:bg-[#084C4F] text-white text-sm font-semibold disabled:opacity-60"
            >
              {submitting ? 'Creating...' : 'Create case'}
            </button>
          </div>
        </form>
      )}

      {loading && <p className="text-sm text-[#3D5A73]">Loading...</p>}
      {error && <div className="text-sm text-[#D32F2F]">{error}</div>}
      {!loading && data && data.items.length === 0 && (
        <div className="bg-white rounded-xl shadow p-8 text-center text-sm text-[#3D5A73]">
          No support cases yet. Click <strong>+ New case</strong> above to open one.
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
              <th className="px-4 py-3">Opened</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((c) => (
              <tr key={c.id} className="border-b border-[#0D7377]/10 text-sm">
                <td className="px-4 py-3 font-mono">C-{c.id}</td>
                <td className="px-4 py-3">M-{c.member_id}</td>
                <td className="px-4 py-3">{c.subject}</td>
                <td className="px-4 py-3">
                  <span
                    className="px-2 py-1 rounded text-xs font-bold text-white uppercase"
                    style={{ backgroundColor: PRIORITY_COLORS[c.priority] ?? '#3D5A73' }}
                  >
                    {c.priority}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span
                    className="px-2 py-1 rounded text-xs font-bold text-white uppercase"
                    style={{ backgroundColor: STATUS_COLORS[c.status] ?? '#3D5A73' }}
                  >
                    {c.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-[#3D5A73]">{c.created_at?.slice(0, 16) ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
