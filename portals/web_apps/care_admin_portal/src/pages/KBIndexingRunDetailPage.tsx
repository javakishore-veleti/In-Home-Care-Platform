import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import type { ChunkRow, IndexingRun, PaginatedResponse } from '../types'

const STATUS_COLORS: Record<string, string> = {
  success: '#2D8A4E', running: '#1976D2', failed: '#D32F2F',
}
const ITEM_ICONS: Record<string, string> = {
  document: '📄', announcement: '📢', link: '🔗', note: '📝', image: '🖼️',
}

export function KBIndexingRunDetailPage() {
  const { token } = useAuth()
  const { collectionId, repoId, runId } = useParams<{
    collectionId: string; repoId: string; runId: string
  }>()
  const [run, setRun] = useState<IndexingRun | null>(null)
  const [chunks, setChunks] = useState<PaginatedResponse<ChunkRow> | null>(null)
  const [chunkPage, setChunkPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token || !runId || !repoId) return
    let cancelled = false
    async function load() {
      setLoading(true)
      try {
        const [r, c] = await Promise.all([
          api.getKBIndexingRun(token!, Number(runId)),
          api.listKBChunks(token!, Number(repoId), new URLSearchParams({
            page: String(chunkPage), page_size: '20',
          })),
        ])
        if (!cancelled) {
          setRun(r)
          setChunks(c)
          setError(null)
        }
      } catch (exc) {
        if (!cancelled) setError(exc instanceof Error ? exc.message : 'Failed to load.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void load()
    return () => { cancelled = true }
  }, [token, runId, repoId, chunkPage])

  return (
    <div className="space-y-6">
      <div>
        <Link
          to={`/app/knowledge-base/${collectionId}/repo/${repoId}`}
          style={{ color: '#0D7377' }}
          className="text-xs font-semibold hover:underline"
        >
          ← Back to repository
        </Link>
        <h2 className="text-2xl font-bold text-[#1A2B3C] mt-1">
          Indexing Run #{runId}
        </h2>
      </div>

      {loading && <p className="text-sm text-[#3D5A73]">Loading...</p>}
      {error && <div className="text-sm text-[#D32F2F]">{error}</div>}

      {run && (
        <div className="bg-white rounded-xl shadow border border-[#0D7377]/10 p-5 space-y-4">
          <h3 className="text-sm font-bold text-[#1A2B3C] pb-2 border-b border-[#0D7377]/10">
            Run Details
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
            <div>
              <p className="text-[10px] uppercase text-[#3D5A73] font-semibold">Status</p>
              <span
                className="inline-block mt-1 px-2 py-1 rounded text-xs font-bold text-white uppercase"
                style={{ backgroundColor: STATUS_COLORS[run.status] ?? '#3D5A73' }}
              >
                {run.status}
              </span>
            </div>
            <div>
              <p className="text-[10px] uppercase text-[#3D5A73] font-semibold">Vector DB</p>
              <span className="inline-block mt-1 px-2 py-1 rounded bg-[#0D7377]/10 text-[#0D7377] font-semibold">
                {run.vectordb_engine}
              </span>
            </div>
            <div>
              <p className="text-[10px] uppercase text-[#3D5A73] font-semibold">Duration</p>
              <p className="mt-1 text-[#1A2B3C]">
                {run.duration_seconds ? `${run.duration_seconds.toFixed(1)}s` : '—'}
              </p>
            </div>
            <div>
              <p className="text-[10px] uppercase text-[#3D5A73] font-semibold">Repository</p>
              <p className="mt-1 text-[#1A2B3C]">#{run.repository_id}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase text-[#3D5A73] font-semibold">Chunks indexed</p>
              <p className="mt-1 text-[#1A2B3C] font-bold text-lg">{run.chunks_indexed}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase text-[#3D5A73] font-semibold">Chunks skipped</p>
              <p className="mt-1 text-[#1A2B3C]">{run.chunks_skipped}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase text-[#3D5A73] font-semibold">Chunks expired</p>
              <p className="mt-1 text-[#1A2B3C]">{run.chunks_expired}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase text-[#3D5A73] font-semibold">Started</p>
              <p className="mt-1 text-[#1A2B3C] text-[11px]">
                {run.started_at ? new Date(run.started_at).toLocaleString() : '—'}
              </p>
            </div>
          </div>
          {run.error && (
            <div className="text-xs text-[#D32F2F] bg-[#FCEAEA] border border-[#D32F2F]/20 rounded px-3 py-2">
              Error: {run.error}
            </div>
          )}
        </div>
      )}

      {/* Chunks stored in pgvector */}
      <div>
        <h3 className="text-lg font-bold text-[#1A2B3C] mb-3">
          Stored Chunks {chunks ? `(${chunks.total} active)` : ''}
        </h3>
        {chunks && chunks.items.length === 0 && (
          <p className="text-sm text-[#3D5A73]">No active chunks for this repository.</p>
        )}
        {chunks && chunks.items.length > 0 && (
          <>
            <table className="w-full text-left border-collapse bg-white rounded-xl shadow overflow-hidden">
              <thead>
                <tr className="bg-[#0D7377] text-white text-sm">
                  <th className="px-4 py-3">ID</th>
                  <th className="px-4 py-3">Source Item</th>
                  <th className="px-4 py-3">Chunk</th>
                  <th className="px-4 py-3">Text Preview</th>
                  <th className="px-4 py-3">Tokens</th>
                  <th className="px-4 py-3">Hash</th>
                </tr>
              </thead>
              <tbody>
                {chunks.items.map(chunk => (
                  <tr key={chunk.id} className="border-b border-[#0D7377]/10 text-sm">
                    <td className="px-4 py-3 font-mono text-xs">C-{chunk.id}</td>
                    <td className="px-4 py-3">
                      <div className="text-xs">
                        {ITEM_ICONS[chunk.item_type ?? ''] ?? '📎'}{' '}
                        {chunk.item_title ?? `Item #${chunk.item_id}`}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-xs text-[#3D5A73]">#{chunk.chunk_index}</td>
                    <td className="px-4 py-3">
                      <p className="text-xs text-[#1A2B3C] max-w-[400px] line-clamp-3">
                        {chunk.chunk_text}
                      </p>
                    </td>
                    <td className="px-4 py-3 text-xs text-[#3D5A73]">{chunk.token_count ?? '—'}</td>
                    <td className="px-4 py-3 font-mono text-[10px] text-[#3D5A73]">
                      {chunk.content_hash_short}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {chunks.total_pages > 1 && (
              <div className="flex items-center gap-3 text-sm mt-3">
                <button type="button" disabled={chunkPage <= 1}
                  onClick={() => setChunkPage(p => p - 1)}
                  className="px-3 py-1.5 rounded bg-white border border-[#0D7377]/20 disabled:opacity-50">
                  Previous
                </button>
                <span className="text-[#3D5A73]">Page {chunks.page} of {chunks.total_pages}</span>
                <button type="button" disabled={chunkPage >= chunks.total_pages}
                  onClick={() => setChunkPage(p => p + 1)}
                  className="px-3 py-1.5 rounded bg-white border border-[#0D7377]/20 disabled:opacity-50">
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
