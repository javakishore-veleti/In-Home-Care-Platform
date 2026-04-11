import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import { DetailCard, DetailField, DetailLayout } from '../components/DetailLayout'
import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import type { AppointmentRow, MemberRow } from '../types'

export function AppointmentDetailPage() {
  const { token } = useAuth()
  const { appointmentId } = useParams<{ appointmentId: string }>()
  const [appointment, setAppointment] = useState<AppointmentRow | null>(null)
  const [member, setMember] = useState<MemberRow | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token || !appointmentId) return
    let cancelled = false
    async function load() {
      try {
        const appt = await api.getAppointment(token!, Number(appointmentId))
        if (cancelled) return
        setAppointment(appt)
        // Best-effort member fetch — failures are non-fatal.
        try {
          const m = await api.getMember(token!, appt.member_id)
          if (!cancelled) setMember(m)
        } catch {
          /* ignore */
        }
      } catch (exc) {
        if (!cancelled) setError(exc instanceof Error ? exc.message : 'Failed to load appointment.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [token, appointmentId])

  return (
    <DetailLayout
      title={appointment ? `Appointment A-${appointment.id}` : 'Appointment'}
      subtitle={appointment?.service_type}
      backTo="/app/appointments"
      backLabel="← Back to appointments"
      loading={loading}
      error={error}
    >
      {appointment && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <DetailCard title="Request">
            <div className="grid grid-cols-2 gap-4">
              <DetailField label="ID" value={`A-${appointment.id}`} />
              <DetailField
                label="Status"
                value={
                  <span className="px-2 py-1 rounded text-xs font-bold uppercase bg-[#0D7377]/10 text-[#0D7377]">
                    {appointment.status}
                  </span>
                }
              />
              <DetailField label="Service type" value={appointment.service_type} />
              <DetailField label="Service area" value={appointment.service_area} />
              <DetailField label="Requested date" value={appointment.requested_date} />
              <DetailField label="Time slot" value={appointment.requested_time_slot} />
              <DetailField label="Assigned staff" value={appointment.assigned_staff_id ?? '—'} />
              <DetailField label="Address" value={`#${appointment.address_id}`} />
            </div>
          </DetailCard>
          <DetailCard title="Member">
            <div className="grid grid-cols-2 gap-4">
              <DetailField label="Member ID" value={`M-${appointment.member_id}`} />
              {member ? (
                <>
                  <DetailField
                    label="Name"
                    value={[member.first_name, member.last_name].filter(Boolean).join(' ') || '—'}
                  />
                  <DetailField label="Email" value={member.email} />
                  <DetailField label="Phone" value={member.phone} />
                  <DetailField label="Tenant" value={member.tenant_id} />
                </>
              ) : (
                <DetailField label="Profile" value="(not loaded)" />
              )}
            </div>
          </DetailCard>
          <DetailCard title="Notes & reason">
            <div className="space-y-4">
              <DetailField label="Reason" value={appointment.notes ?? '—'} />
              <DetailField label="Notes" value={appointment.notes ?? '—'} />
            </div>
          </DetailCard>
          <DetailCard title="Slack claim">
            <div className="grid grid-cols-2 gap-4">
              <DetailField
                label="Claimed by"
                value={appointment.claimed_by_slack_user_name ?? appointment.claimed_by_slack_user_id ?? '—'}
              />
              <DetailField label="Claimed at" value={appointment.claimed_at} />
              <DetailField label="Slack channel" value={appointment.slack_channel_id} />
              <DetailField label="Message TS" value={appointment.slack_message_ts} />
            </div>
          </DetailCard>
          <DetailCard title="Audit">
            <div className="grid grid-cols-2 gap-4">
              <DetailField label="Created" value={appointment.created_at} />
              <DetailField label="Updated" value={appointment.updated_at} />
              <DetailField label="Cancelled" value={appointment.cancelled_at} />
            </div>
          </DetailCard>
        </div>
      )}
    </DetailLayout>
  )
}
