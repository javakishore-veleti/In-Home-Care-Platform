import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import type { KBCollection } from '../types'

export function KBCollectionsPage() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const [collections, setCollections] = useState<KBCollection[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [seeding, setSeeding] = useState(false)
  const [seedMsg, setSeedMsg] = useState<string | null>(null)

  async function load() {
    if (!token) return
    setLoading(true)
    try {
      const res = await api.listKBCollections(token)
      setCollections(res.items)
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : 'Failed to load.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [token]) // eslint-disable-line

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold text-[#1A2B3C]">Knowledge Base</h2>
          <p className="text-sm text-[#3D5A73] mt-1">
            Collections are auto-seeded from appointment service types. Click one to manage its repositories.
          </p>
        </div>
        <button
          type="button"
          disabled={seeding}
          onClick={async () => {
            if (!token) return
            setSeeding(true)
            setSeedMsg(null)
            try {
              const res = await api.setupKBDefaults(token)
              setSeedMsg(
                res.status === 'already_running'
                  ? 'Setup is already running — refresh in a few seconds.'
                  : 'Populating default repositories in the background. Refresh in 5-10 seconds to see them.',
              )
              setTimeout(() => void load(), 5000)
            } catch (exc) {
              setSeedMsg(exc instanceof Error ? exc.message : 'Setup failed.')
            } finally {
              setSeeding(false)
            }
          }}
          className="px-4 py-2 rounded bg-[#0D7377] hover:bg-[#084C4F] text-white text-xs font-semibold disabled:opacity-50 whitespace-nowrap"
        >
          {seeding ? 'Setting up...' : '⚡ Setup Defaults'}
        </button>
      </div>
      {seedMsg && (
        <div className="text-xs bg-[#0D7377]/10 border border-[#0D7377]/20 text-[#0D7377] rounded px-3 py-2">{seedMsg}</div>
      )}
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
