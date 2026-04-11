import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import type {
  Appointment,
  Visit,
  VisitActionItem,
  VisitDecision,
  VisitDocument,
  VisitNote,
} from '../types'

export function AppointmentDetailPage() {
  const { appointmentId } = useParams()
  const { token } = useAuth()
  const [appointment, setAppointment] = useState<Appointment | null>(null)
  const [visits, setVisits] = useState<Visit[]>([])
  const [selectedVisitId, setSelectedVisitId] = useState<number | null>(null)
  const [selectedVisit, setSelectedVisit] = useState<Visit | null>(null)
  const [documents, setDocuments] = useState<VisitDocument[]>([])
  const [notes, setNotes] = useState<VisitNote[]>([])
  const [decisions, setDecisions] = useState<VisitDecision[]>([])
  const [actionItems, setActionItems] = useState<VisitActionItem[]>([])

  useEffect(() => {
    if (!token || !appointmentId) return
    const appointmentNumber = Number(appointmentId)
    void Promise.all([
      api.getAppointment(token, appointmentNumber),
      api.listAppointmentVisits(token, appointmentNumber),
    ]).then(([appointmentResponse, visitResponse]) => {
      setAppointment(appointmentResponse)
      setVisits(visitResponse)
      setSelectedVisitId(visitResponse[0]?.id ?? null)
    })
  }, [appointmentId, token])

  useEffect(() => {
    if (!token || !selectedVisitId) {
      setSelectedVisit(null)
      setDocuments([])
      setNotes([])
      setDecisions([])
      setActionItems([])
      return
    }
    void Promise.all([
      api.getVisit(token, selectedVisitId),
      api.listVisitDocuments(token, selectedVisitId),
      api.listVisitNotes(token, selectedVisitId),
      api.listVisitDecisions(token, selectedVisitId),
      api.listVisitActionItems(token, selectedVisitId),
    ]).then(([visit, docs, nextNotes, nextDecisions, nextActionItems]) => {
      setSelectedVisit(visit)
      setDocuments(docs)
      setNotes(nextNotes)
      setDecisions(nextDecisions)
      setActionItems(nextActionItems)
    })
  }, [selectedVisitId, token])

  const cancelAppointment = async () => {
    if (!token || !appointment) return
    const cancelled = await api.cancelAppointment(token, appointment.id)
    setAppointment(cancelled)
  }

  return (
    <div className="stack-xl">
      <section className="card stack-md">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Appointment detail</p>
            <h2>{appointment?.service_type ?? 'Loading appointment…'}</h2>
          </div>
          <div className="action-row">
            <Link className="secondary-button" to="/app/appointments">Back to appointments</Link>
            {appointment && appointment.status !== 'cancelled' ? <button className="secondary-button" type="button" onClick={() => void cancelAppointment()}>Cancel request</button> : null}
          </div>
        </div>
        {appointment ? (
          <div className="detail-grid">
            <div className="subcard">
              <strong>Status</strong>
              <p className="capitalize">{appointment.status}</p>
            </div>
            <div className="subcard">
              <strong>Requested schedule</strong>
              <p>{appointment.requested_date} · {appointment.requested_time_slot}</p>
              {appointment.preferred_hour && appointment.preferred_minute ? (
                <p className="muted">Preferred arrival: {appointment.preferred_hour}:{appointment.preferred_minute}</p>
              ) : null}
            </div>
            <div className="subcard">
              <strong>Care focus</strong>
              <p>{appointment.service_area || 'Not specified'}</p>
            </div>
            <div className="subcard">
              <strong>Reason</strong>
              <p>{appointment.reason || 'No reason provided.'}</p>
            </div>
            <div className="subcard full-span">
              <strong>Notes</strong>
              <p>{appointment.notes || 'No extra notes yet.'}</p>
            </div>
          </div>
        ) : null}
      </section>

      <section className="card stack-md">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Related visits</p>
            <h2>Review visit follow-ups</h2>
          </div>
        </div>
        <div className="visit-layout">
          <div className="visit-list">
            {visits.length === 0 ? <div className="subcard">No visits have been attached to this appointment yet.</div> : null}
            {visits.map((visit) => (
              <button
                key={visit.id}
                type="button"
                className={`subcard visit-selector ${selectedVisitId === visit.id ? 'selected' : ''}`}
                onClick={() => setSelectedVisitId(visit.id)}
              >
                <strong>Visit #{visit.id}</strong>
                <p>{visit.visit_date || 'Date pending'} · {visit.status}</p>
                <p className="muted">{visit.notes_summary || 'No summary yet.'}</p>
              </button>
            ))}
          </div>
          <div className="stack-md">
            {selectedVisit ? (
              <>
                <article className="subcard stack-sm">
                  <strong>Visit overview</strong>
                  <p>{selectedVisit.notes_summary || 'No summary recorded yet.'}</p>
                  <p className="muted">Status: {selectedVisit.status}</p>
                </article>
                <div className="detail-grid">
                  <ArtifactPanel title="Documents" items={documents.map((document) => `${document.title} · ${document.doc_type}${document.summary ? ` — ${document.summary}` : ''}`)} />
                  <ArtifactPanel title="Notes" items={notes.map((note) => `${note.note}${note.author_name ? ` — ${note.author_name}` : ''}`)} />
                  <ArtifactPanel title="Decisions" items={decisions.map((decision) => `${decision.decision}${decision.owner_name ? ` — ${decision.owner_name}` : ''}`)} />
                  <ArtifactPanel title="Action items" items={actionItems.map((item) => `${item.description} (${item.status})${item.due_date ? ` · due ${item.due_date}` : ''}`)} />
                </div>
              </>
            ) : (
              <div className="subcard">Select a visit to review related documents, notes, decisions, and action items.</div>
            )}
          </div>
        </div>
      </section>
    </div>
  )
}

function ArtifactPanel({ title, items }: { title: string; items: string[] }) {
  return (
    <article className="subcard stack-sm">
      <strong>{title}</strong>
      {items.length === 0 ? <p className="muted">No {title.toLowerCase()} yet.</p> : null}
      <ul className="artifact-list">
        {items.map((item) => <li key={item}>{item}</li>)}
      </ul>
    </article>
  )
}
