import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import type { KBCollection } from '../types'

const STATUS_COLORS: Record<string, string> = {
  running: '#1976D2',
  completed: '#2D8A4E',
  failed: '#D32F2F',
}

interface SetupJob {
  id: number
  status: string
  repos_created: number
  repos_skipped: number
  items_created: number
  error?: string | null
  started_at?: string | null
  completed_at?: string | null
}

export function KBCollectionsPage() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const [collections, setCollections] = useState<KBCollection[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [job, setJob] = useState<SetupJob | null>(null)
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    if (!token) return
    setLoading(true)
    try {
      const [colRes, statusRes] = await Promise.all([
        api.listKBCollections(token),
        api.getKBSetupStatus(token),
      ])
      setCollections(colRes.items)
      setJob((statusRes.job as unknown as SetupJob) ?? null)
      setError(null)
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : 'Failed to load.')
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    void load()
  }, [load])

  // Auto-poll while job is running
  useEffect(() => {
    if (!job || job.status !== 'running') return
    const interval = setInterval(() => void load(), 2000)
    return () => clearInterval(interval)
  }, [job, load])

  async function handleSetup() {
    if (!token) return
    setBusy(true)
    try {
      await api.setupKBDefaults(token)
      await load()
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : 'Setup failed.')
    } finally {
      setBusy(false)
    }
  }

  async function handleReset() {
    if (!token) return
    setBusy(true)
    try {
      await api.resetKBSetup(token)
      await load()
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : 'Reset failed.')
    } finally {
      setBusy(false)
    }
  }

  const isRunning = job?.status === 'running'
  const isCompleted = job?.status === 'completed'
  const isFailed = job?.status === 'failed'

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-[#1A2B3C]">Knowledge Base</h2>
        <p className="text-sm text-[#3D5A73] mt-1">
          Collections are auto-seeded from appointment service types. Click one to manage its repositories.
        </p>
      </div>

      {/* Setup Defaults status card */}
      <div className="bg-white rounded-xl shadow border border-[#0D7377]/10 p-5">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-bold text-[#1A2B3C] text-sm">Setup Defaults</h3>
          <div className="flex items-center gap-2">
            {(!job || isCompleted || isFailed) && (
              <button
                type="button"
                disabled={busy}
                onClick={handleSetup}
                className="px-3 py-1.5 rounded bg-[#0D7377] hover:bg-[#084C4F] text-white text-xs font-semibold disabled:opacity-50"
              >
                {busy ? 'Starting...' : job ? '🔄 Re-run' : '⚡ Setup Defaults'}
              </button>
            )}
            {(isCompleted || isFailed) && (
              <button
                type="button"
                disabled={busy}
                onClick={handleReset}
                className="px-3 py-1.5 rounded bg-[#3D5A73] hover:bg-[#2a3f52] text-white text-xs font-semibold disabled:opacity-50"
              >
                Reset
              </button>
            )}
          </div>
        </div>

        {!job && (
          <p className="text-xs text-[#3D5A73]">
            Click "Setup Defaults" to populate 25 repositories with ~80 items of real healthcare knowledge
            (CDC, CMS, WHO guidelines, clinical notes, announcements) across all service types. Runs in
            the background — the page auto-refreshes while it's working.
          </p>
        )}

        {job && (
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <span
                className="px-2 py-1 rounded text-xs font-bold text-white uppercase"
                style={{ backgroundColor: STATUS_COLORS[job.status] ?? '#3D5A73' }}
              >
                {job.status === 'running' && '🔄 '}{job.status}
              </span>
              {job.started_at && (
                <span className="text-[10px] text-[#3D5A73]">
                  Started: {new Date(job.started_at).toLocaleString()}
                </span>
              )}
              {job.completed_at && (
                <span className="text-[10px] text-[#3D5A73]">
                  Completed: {new Date(job.completed_at).toLocaleString()}
                </span>
              )}
            </div>
            <div className="flex items-center gap-4 text-xs text-[#1A2B3C]">
              <span><strong>{job.repos_created}</strong> repos created</span>
              <span><strong>{job.repos_skipped}</strong> skipped (already exist)</span>
              <span><strong>{job.items_created}</strong> items created</span>
            </div>
            {job.error && (
              <div className="text-xs text-[#D32F2F] bg-[#FCEAEA] border border-[#D32F2F]/20 rounded px-3 py-2">
                Error: {job.error}
              </div>
            )}
            {isRunning && (
              <p className="text-[10px] text-[#3D5A73] animate-pulse">
                Working in the background — this card auto-refreshes every 2 seconds...
              </p>
            )}
          </div>
        )}
      </div>

      {loading && <p className="text-sm text-[#3D5A73]">Loading...</p>}
      {error && <div className="text-sm text-[#D32F2F]">{error}</div>}
      {!loading && collections.length === 0 && (
        <p className="text-sm text-[#3D5A73]">No collections found. Restart knowledge_svc to seed defaults.</p>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
        {collections.map((col) => (
          <div
            key={col.id}
            onClick={() => navigate(`/app/knowledge-base/${col.id}`)}
            className="bg-white rounded-xl shadow border border-[#0D7377]/10 p-5 cursor-pointer hover:shadow-lg hover:border-[#0D7377]/30 transition-all"
          >
            <div className="text-3xl mb-2">{col.icon_emoji}</div>
            <h3 className="font-bold text-[#1A2B3C] text-sm">{col.name}</h3>
            {col.description && (
              <p className="text-xs text-[#3D5A73] mt-1 line-clamp-2">{col.description}</p>
            )}
            <div className="mt-3 flex items-center gap-3 text-[10px] text-[#3D5A73]">
              <span>{col.repo_count} repo{col.repo_count !== 1 ? 's' : ''}</span>
              <span>{col.total_chunks} chunks</span>
              {col.jurisdiction && (
                <span className="px-1.5 py-0.5 rounded bg-[#0D7377]/10 text-[#0D7377] font-semibold uppercase">
                  {col.jurisdiction}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
