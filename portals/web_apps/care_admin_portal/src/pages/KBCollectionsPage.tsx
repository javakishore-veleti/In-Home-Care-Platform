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

  useEffect(() => {
    if (!token) return
    let cancelled = false
    async function load() {
      try {
        const res = await api.listKBCollections(token!)
        if (!cancelled) setCollections(res.items)
      } catch (exc) {
        if (!cancelled) setError(exc instanceof Error ? exc.message : 'Failed to load.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void load()
    return () => { cancelled = true }
  }, [token])

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-[#1A2B3C]">Knowledge Base</h2>
        <p className="text-sm text-[#3D5A73] mt-1">
          Collections are auto-seeded from appointment service types. Click one to manage its repositories.
        </p>
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
