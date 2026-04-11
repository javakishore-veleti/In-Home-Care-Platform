import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import { DetailCard, DetailField, DetailLayout } from '../components/DetailLayout'
import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import type { MemberRow } from '../types'

export function MemberDetailPage() {
  const { token } = useAuth()
  const { memberId } = useParams<{ memberId: string }>()
  const [member, setMember] = useState<MemberRow | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token || !memberId) return
    let cancelled = false
    async function load() {
      try {
        const m = await api.getMember(token!, Number(memberId))
        if (!cancelled) setMember(m)
      } catch (exc) {
        if (!cancelled) setError(exc instanceof Error ? exc.message : 'Failed to load member.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [token, memberId])

  return (
    <DetailLayout
      title={member ? `Member M-${member.id}` : 'Member'}
      subtitle={member ? [member.first_name, member.last_name].filter(Boolean).join(' ') || member.email : undefined}
      backTo="/app/members"
      backLabel="← Back to members"
      loading={loading}
      error={error}
    >
      {member && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <DetailCard title="Profile">
            <div className="grid grid-cols-2 gap-4">
              <DetailField label="ID" value={`M-${member.id}`} />
              <DetailField label="Tenant" value={member.tenant_id} />
              <DetailField label="First name" value={member.first_name} />
              <DetailField label="Last name" value={member.last_name} />
              <DetailField label="Email" value={member.email} />
              <DetailField label="Phone" value={member.phone} />
              <DetailField label="DOB" value={member.dob} />
              <DetailField label="Insurance" value={member.insurance_id} />
            </div>
          </DetailCard>
          <DetailCard title="Linked user">
            <div className="grid grid-cols-2 gap-4">
              <DetailField label="User ID" value={`U-${member.user_id}`} />
              <DetailField label="Created" value={member.created_at} />
              <DetailField label="Updated" value={member.updated_at} />
            </div>
          </DetailCard>
        </div>
      )}
    </DetailLayout>
  )
}
