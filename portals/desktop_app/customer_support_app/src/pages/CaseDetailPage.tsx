import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { DetailCard, DetailField, DetailLayout } from '../components/DetailLayout'
import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import type { CaseRow, MemberRow } from '../types'

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

export function CaseDetailPage() {
  const { token } = useAuth()
  const { caseId } = useParams<{ caseId: string }>()
  const [supportCase, setSupportCase] = useState<CaseRow | null>(null)
  const [member, setMember] = useState<MemberRow | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token || !caseId) return
    let cancelled = false
    async function load() {
      try {
        const c = await api.getCase(token!, Number(caseId))
        if (cancelled) return
        setSupportCase(c)
        try {
          const m = await api.getMember(token!, c.member_id)
          if (!cancelled) setMember(m)
        } catch {
          /* ignore */
        }
      } catch (exc) {
        if (!cancelled) setError(exc instanceof Error ? exc.message : 'Failed to load case.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [token, caseId])

  return (
    <DetailLayout
      title={supportCase ? `Case C-${supportCase.id}` : 'Case'}
      subtitle={supportCase?.subject}
      backTo="/app"
      backLabel="← Back to cases"
      loading={loading}
      error={error}
    >
      {supportCase && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <DetailCard title="Case">
            <div className="grid grid-cols-2 gap-3">
              <DetailField label="ID" value={`C-${supportCase.id}`} />
              <DetailField
                label="Status"
                value={
                  <span
                    className="px-2 py-1 rounded text-xs font-bold text-white uppercase"
                    style={{ backgroundColor: STATUS_COLORS[supportCase.status] ?? '#3D5A73' }}
                  >
                    {supportCase.status}
                  </span>
                }
              />
              <DetailField label="Subject" value={supportCase.subject} />
              <DetailField
                label="Priority"
                value={
                  <span
                    className="px-2 py-1 rounded text-xs font-bold text-white uppercase"
                    style={{ backgroundColor: PRIORITY_COLORS[supportCase.priority] ?? '#3D5A73' }}
                  >
                    {supportCase.priority}
                  </span>
                }
              />
              <DetailField label="Opened" value={supportCase.created_at} />
              <DetailField label="Updated" value={supportCase.updated_at} />
              <DetailField label="Resolved" value={supportCase.resolved_at} />
            </div>
          </DetailCard>
          <DetailCard title="Member">
            <div className="grid grid-cols-2 gap-3">
              <DetailField
                label="Member ID"
                value={
                  <Link
                    to={`/app/members/${supportCase.member_id}`}
                    style={{ color: '#0D7377' }}
                    className="hover:underline"
                  >
                    M-{supportCase.member_id}
                  </Link>
                }
              />
              {member ? (
                <>
                  <DetailField
                    label="Name"
                    value={[member.first_name, member.last_name].filter(Boolean).join(' ') || '—'}
                  />
                  <DetailField label="Email" value={member.email} />
                  <DetailField label="Phone" value={member.phone} />
                </>
              ) : (
                <DetailField label="Profile" value="(not loaded)" />
              )}
            </div>
          </DetailCard>
          <DetailCard title="Description">
            <DetailField label="Description" value={supportCase.description ?? '—'} />
          </DetailCard>
          <DetailCard title="Assignment">
            <div className="grid grid-cols-2 gap-3">
              <DetailField
                label="Created by"
                value={supportCase.created_by_user_id ? `U-${supportCase.created_by_user_id}` : '—'}
              />
              <DetailField
                label="Assigned to"
                value={supportCase.assigned_to_user_id ? `U-${supportCase.assigned_to_user_id}` : '—'}
              />
            </div>
          </DetailCard>
        </div>
      )}
    </DetailLayout>
  )
}
