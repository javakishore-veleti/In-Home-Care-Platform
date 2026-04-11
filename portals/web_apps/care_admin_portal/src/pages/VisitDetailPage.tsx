import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { DetailCard, DetailField, DetailLayout } from '../components/DetailLayout'
import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import type { VisitRow } from '../types'

export function VisitDetailPage() {
  const { token } = useAuth()
  const { visitId } = useParams<{ visitId: string }>()
  const [visit, setVisit] = useState<VisitRow | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token || !visitId) return
    let cancelled = false
    async function load() {
      try {
        const v = await api.getVisit(token!, Number(visitId))
        if (!cancelled) setVisit(v)
      } catch (exc) {
        if (!cancelled) setError(exc instanceof Error ? exc.message : 'Failed to load visit.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [token, visitId])

  return (
    <DetailLayout
      title={visit ? `Visit V-${visit.id}` : 'Visit'}
      subtitle={visit?.status}
      backTo="/app/visits"
      backLabel="← Back to visits"
      loading={loading}
      error={error}
    >
      {visit && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <DetailCard title="Visit">
            <div className="grid grid-cols-2 gap-4">
              <DetailField label="ID" value={`V-${visit.id}`} />
              <DetailField
                label="Status"
                value={
                  <span className="px-2 py-1 rounded text-xs font-bold uppercase bg-[#0D7377]/10 text-[#0D7377]">
                    {visit.status}
                  </span>
                }
              />
              <DetailField label="Visit date" value={visit.visit_date} />
              <DetailField label="Started at" value={visit.started_at} />
              <DetailField label="Completed at" value={visit.completed_at} />
              <DetailField label="Staff" value={visit.staff_id} />
            </div>
          </DetailCard>
          <DetailCard title="Linked records">
            <div className="grid grid-cols-2 gap-4">
              <DetailField
                label="Member"
                value={
                  <Link
                    to={`/app/members/${visit.member_id}`}
                    style={{ color: '#0D7377' }}
                    className="hover:underline"
                  >
                    M-{visit.member_id}
                  </Link>
                }
              />
              <DetailField
                label="Appointment"
                value={
                  visit.appointment_id ? (
                    <Link
                      to={`/app/appointments/${visit.appointment_id}`}
                      style={{ color: '#0D7377' }}
                      className="hover:underline"
                    >
                      A-{visit.appointment_id}
                    </Link>
                  ) : (
                    '—'
                  )
                }
              />
              <DetailField label="Created" value={visit.created_at} />
            </div>
          </DetailCard>
          <DetailCard title="Notes">
            <DetailField label="Summary" value={visit.notes_summary ?? '—'} />
          </DetailCard>
        </div>
      )}
    </DetailLayout>
  )
}
