import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import type { IndexingRun, KBItem, KBRepository, PaginatedResponse, VectorDBOption } from '../types'

const ITEM_TYPES = ['document', 'announcement', 'link', 'note']
const ITEM_ICONS: Record<string, string> = {
  document: '📄', announcement: '📢', link: '🔗', note: '📝', image: '🖼️',
}
const STATUS_COLORS: Record<string, string> = {
  draft: '#3D5A73', locked: '#E8A317', publishing: '#1976D2', indexed: '#2D8A4E', failed: '#D32F2F',
}

export function KBRepositoryDetailPage() {
  const { token } = useAuth()
  const { collectionId, repoId } = useParams<{ collectionId: string; repoId: string }>()
  const [repo, setRepo] = useState<KBRepository | null>(null)
  const [items, setItems] = useState<KBItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionMsg, setActionMsg] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const [vectordbs, setVectordbs] = useState<VectorDBOption[]>([])
  const [history, setHistory] = useState<PaginatedResponse<IndexingRun> | null>(null)
  const [historyPage, setHistoryPage] = useState(1)

  // New item form
  const [showForm, setShowForm] = useState(false)
  const [newType, setNewType] = useState('note')
  const [newTitle, setNewTitle] = useState('')
  const [newContent, setNewContent] = useState('')
  const [newUrl, setNewUrl] = useState('')

  const load = useCallback(async () => {
    if (!token || !repoId) return
    setLoading(true)
    try {
      const [r, itemRes, vdbRes, histRes] = await Promise.all([
        api.getKBRepository(token, Number(repoId)),
        api.listKBItems(token, Number(repoId)),
        api.listSupportedVectorDBs(token),
        api.listKBIndexingHistory(token, Number(repoId), new URLSearchParams({ page: String(historyPage), page_size: '10' })),
      ])
      setRepo(r)
      setItems(itemRes.items)
      setVectordbs(vdbRes.items)
      setHistory(histRes)
      setError(null)
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : 'Failed to load.')
    } finally {
      setLoading(false)
    }
  }, [token, repoId, historyPage])

  useEffect(() => { void load() }, [load])

  async function toggleVectorDB(vdbId: string, checked: boolean) {
    if (!token || !repo) return
    const current = repo.target_vectordbs ?? ['pgvector']
    const updated = checked ? [...new Set([...current, vdbId])] : current.filter(v => v !== vdbId)
    await doAction(
      () => api.updateKBTargetVectorDBs(token!, repo!.id, updated),
      `Vector DB targets updated.`,
    )
  }

  async function doAction(fn: () => Promise<unknown>, msg: string) {
    setBusy(true); setActionMsg(null)
    try {
      await fn()
      setActionMsg(msg)
      await load()
    } catch (exc) {
      setActionMsg(exc instanceof Error ? exc.message : 'Action failed.')
    } finally {
      setBusy(false)
    }
  }

  async function handleCreateItem(e: FormEvent) {
    e.preventDefault()
    if (!token || !repoId) return
    await doAction(
      () => api.createKBItem(token!, Number(repoId), {
        item_type: newType, title: newTitle.trim(),
        content_text: newContent.trim() || undefined,
        source_url: newUrl.trim() || undefined,
      }),
      'Item created.',
    )
    setNewTitle(''); setNewContent(''); setNewUrl(''); setShowForm(false)
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file || !token || !repoId) return
    await doAction(
      () => api.uploadKBFile(token!, Number(repoId), file),
      `Uploaded "${file.name}".`,
    )
    if (fileRef.current) fileRef.current.value = ''
  }

  async function handleDelete(itemId: number) {
    if (!token) return
    await doAction(() => api.deleteKBItem(token!, itemId), 'Item deleted.')
  }

  const isDraft = repo?.status === 'draft'
  const isLocked = repo?.status === 'locked'
  const isIndexed = repo?.status === 'indexed'
  const isFailed = repo?.status === 'failed'

  return (
    <div className="space-y-6">
      <div>
        <Link to={`/app/knowledge-base/${collectionId}`} style={{ color: '#0D7377' }} className="text-xs font-semibold hover:underline">
          ← Back to collection
        </Link>
        <h2 className="text-2xl font-bold text-[#1A2B3C] mt-1">{repo?.name ?? 'Repository'}</h2>
        <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-[#3D5A73]">
          {repo && (
            <>
              <span className="px-2 py-1 rounded text-xs font-bold text-white uppercase"
                style={{ backgroundColor: STATUS_COLORS[repo.status] ?? '#3D5A73' }}>
                {repo.status}
              </span>
              <span>Type: {repo.repo_type}</span>
              <span>{repo.item_count} items</span>
              <span>{repo.chunk_count} chunks</span>
              {repo.source_path && <span className="font-mono text-[10px]">{repo.source_path}</span>}
            </>
          )}
        </div>
      </div>

      {actionMsg && (
        <div className="text-xs bg-[#0D7377]/10 border border-[#0D7377]/20 text-[#0D7377] rounded px-3 py-2">{actionMsg}</div>
      )}
      {error && <div className="text-sm text-[#D32F2F]">{error}</div>}
      {repo?.last_error && (
        <div className="text-xs text-[#D32F2F] bg-[#FCEAEA] border border-[#D32F2F]/20 rounded px-3 py-2">
          Last error: {repo.last_error}
        </div>
      )}
      {loading && <p className="text-sm text-[#3D5A73]">Loading...</p>}

      {/* Actions bar */}
      {repo && (
        <div className="flex flex-wrap gap-2">
          {isDraft && (
            <button type="button" disabled={busy} onClick={() => doAction(() => api.lockKBRepository(token!, repo.id), 'Repository locked.')}
              className="px-3 py-1.5 rounded bg-[#E8A317] text-white text-xs font-semibold disabled:opacity-50">
              🔒 Lock
            </button>
          )}
          {isLocked && (
            <>
              <button type="button" disabled={busy} onClick={() => doAction(() => api.unlockKBRepository(token!, repo.id), 'Repository unlocked.')}
                className="px-3 py-1.5 rounded bg-[#3D5A73] text-white text-xs font-semibold disabled:opacity-50">
                ✏️ Unlock
              </button>
              <button type="button" disabled={busy} onClick={() => doAction(() => api.publishKBRepository(token!, repo.id), 'Published to indexing.')}
                className="px-3 py-1.5 rounded bg-[#0D7377] hover:bg-[#084C4F] text-white text-xs font-semibold disabled:opacity-50">
                🚀 Publish to indexing
              </button>
            </>
          )}
          {(isIndexed || isFailed) && (
            <>
              <button type="button" disabled={busy} onClick={() => doAction(() => api.unlockKBRepository(token!, repo.id), 'Repository unlocked for editing.')}
                className="px-3 py-1.5 rounded bg-[#3D5A73] text-white text-xs font-semibold disabled:opacity-50">
                ✏️ Unlock to edit
              </button>
              <button type="button" disabled={busy} onClick={() => doAction(() => api.publishKBRepository(token!, repo.id), 'Re-indexing started.')}
                className="px-3 py-1.5 rounded bg-[#0D7377] hover:bg-[#084C4F] text-white text-xs font-semibold disabled:opacity-50">
                🔄 Re-index
              </button>
            </>
          )}
        </div>
      )}

      {/* Vector DB targets */}
      {repo && vectordbs.length > 0 && (
        <div className="bg-white rounded-xl shadow border border-[#0D7377]/10 p-5">
          <h3 className="text-sm font-bold text-[#1A2B3C] mb-3">Index Targets</h3>
          <p className="text-[10px] text-[#3D5A73] mb-3">
            Select which vector databases this repository should be indexed into when published.
            Disabled options are not configured at the system level (set VECTORDB_&lt;ID&gt;_ENABLED=true in .env.local).
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
            {vectordbs.map(vdb => {
              const checked = (repo.target_vectordbs ?? ['pgvector']).includes(vdb.id)
              return (
                <label
                  key={vdb.id}
                  className={`flex items-start gap-2 p-2 rounded border text-xs ${
                    vdb.enabled
                      ? 'border-[#0D7377]/20 hover:border-[#0D7377]/40 cursor-pointer'
                      : 'border-gray-200 opacity-50 cursor-not-allowed'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    disabled={!vdb.enabled || busy}
                    onChange={(e) => toggleVectorDB(vdb.id, e.target.checked)}
                    className="mt-0.5 accent-[#0D7377]"
                  />
                  <div>
                    <div className="font-semibold text-[#1A2B3C]">{vdb.name}</div>
                    <div className="text-[10px] text-[#3D5A73]">
                      {vdb.description}
                      {!vdb.enabled && ' (not enabled)'}
                    </div>
                  </div>
                </label>
              )
            })}
          </div>
        </div>
      )}

      {/* Items section */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-[#1A2B3C]">Items</h3>
        {isDraft && (
          <div className="flex items-center gap-2">
            <label className="px-3 py-1.5 rounded bg-[#1976D2] hover:bg-[#155a9c] text-white text-xs font-semibold cursor-pointer">
              📤 Upload file
              <input ref={fileRef} type="file" className="hidden" onChange={handleUpload} />
            </label>
            <button type="button" onClick={() => setShowForm(v => !v)}
              className="px-3 py-1.5 rounded bg-[#0D7377] hover:bg-[#084C4F] text-white text-xs font-semibold">
              {showForm ? 'Cancel' : '+ Add item'}
            </button>
          </div>
        )}
      </div>

      {showForm && isDraft && (
        <form onSubmit={handleCreateItem} className="bg-white border border-[#0D7377]/10 rounded-xl shadow p-4 space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-[#3D5A73] mb-1">Title</label>
              <input value={newTitle} onChange={e => setNewTitle(e.target.value)} required maxLength={255}
                className="w-full px-3 py-2 rounded border border-[#0D7377]/20 text-sm focus:outline-none focus:ring-2 focus:ring-[#0D7377]" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#3D5A73] mb-1">Type</label>
              <select value={newType} onChange={e => setNewType(e.target.value)}
                className="w-full px-3 py-2 rounded border border-[#0D7377]/20 text-sm bg-white">
                {ITEM_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          </div>
          {(newType === 'note' || newType === 'announcement') && (
            <div>
              <label className="block text-xs font-semibold text-[#3D5A73] mb-1">Content</label>
              <textarea value={newContent} onChange={e => setNewContent(e.target.value)} rows={3}
                className="w-full px-3 py-2 rounded border border-[#0D7377]/20 text-sm focus:outline-none focus:ring-2 focus:ring-[#0D7377]" />
            </div>
          )}
          {newType === 'link' && (
            <div>
              <label className="block text-xs font-semibold text-[#3D5A73] mb-1">URL</label>
              <input value={newUrl} onChange={e => setNewUrl(e.target.value)} type="url"
                className="w-full px-3 py-2 rounded border border-[#0D7377]/20 text-sm focus:outline-none focus:ring-2 focus:ring-[#0D7377]" />
            </div>
          )}
          <div className="flex justify-end">
            <button type="submit" disabled={busy}
              className="px-4 py-2 rounded bg-[#0D7377] hover:bg-[#084C4F] text-white text-sm font-semibold disabled:opacity-60">
              {busy ? 'Adding...' : 'Add item'}
            </button>
          </div>
        </form>
      )}

      {items.length === 0 && !loading && (
        <p className="text-sm text-[#3D5A73]">
          {isDraft ? 'No items yet. Upload a file or add an item above.' : 'No items in this repository.'}
        </p>
      )}

      {items.length > 0 && (
        <table className="w-full text-left border-collapse bg-white rounded-xl shadow overflow-hidden">
          <thead>
            <tr className="bg-[#0D7377] text-white text-sm">
              <th className="px-4 py-3">Title</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Size</th>
              <th className="px-4 py-3">Added</th>
              {isDraft && <th className="px-4 py-3 text-right">Actions</th>}
            </tr>
          </thead>
          <tbody>
            {items.map(item => (
              <tr key={item.id} className="border-b border-[#0D7377]/10 text-sm">
                <td className="px-4 py-3 font-semibold">
                  {ITEM_ICONS[item.item_type] ?? '📎'} {item.title}
                </td>
                <td className="px-4 py-3 text-[#3D5A73]">{item.item_type}</td>
                <td className="px-4 py-3 text-[#3D5A73]">
                  {item.file_size_bytes ? `${Math.round(item.file_size_bytes / 1024)} KB` : '—'}
                </td>
                <td className="px-4 py-3 text-[#3D5A73]">{item.created_at?.slice(0, 10) ?? '—'}</td>
                {isDraft && (
                  <td className="px-4 py-3 text-right">
                    <button type="button" disabled={busy} onClick={() => handleDelete(item.id)}
                      className="text-[10px] text-[#D32F2F] hover:underline disabled:opacity-50">
                      remove
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Publishing History */}
      <div>
        <h3 className="text-lg font-bold text-[#1A2B3C] mt-6 mb-3">Publishing History</h3>
        {history && history.items.length === 0 && (
          <p className="text-sm text-[#3D5A73]">No indexing runs yet. Lock the repository and click Publish.</p>
        )}
        {history && history.items.length > 0 && (
          <>
            <table className="w-full text-left border-collapse bg-white rounded-xl shadow overflow-hidden">
              <thead>
                <tr className="bg-[#0D7377] text-white text-sm">
                  <th className="px-4 py-3">Run</th>
                  <th className="px-4 py-3">Vector DB</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Chunks</th>
                  <th className="px-4 py-3">Duration</th>
                  <th className="px-4 py-3">Started</th>
                </tr>
              </thead>
              <tbody>
                {history.items.map(run => (
                  <tr key={run.id} className="border-b border-[#0D7377]/10 text-sm">
                    <td className="px-4 py-3 font-mono">#{run.id}</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-1 rounded bg-[#0D7377]/10 text-[#0D7377] text-xs font-semibold">
                        {run.vectordb_engine}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded text-xs font-bold text-white uppercase ${
                        run.status === 'success' ? 'bg-[#2D8A4E]' :
                        run.status === 'running' ? 'bg-[#1976D2]' :
                        run.status === 'failed' ? 'bg-[#D32F2F]' : 'bg-[#3D5A73]'
                      }`}>
                        {run.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-[#3D5A73]">
                      {run.chunks_indexed} indexed / {run.chunks_skipped} skipped
                    </td>
                    <td className="px-4 py-3 text-[#3D5A73]">
                      {run.duration_seconds ? `${run.duration_seconds.toFixed(1)}s` : '—'}
                    </td>
                    <td className="px-4 py-3 text-[#3D5A73] text-xs">
                      {run.started_at ? new Date(run.started_at).toLocaleString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {history.total_pages > 1 && (
              <div className="flex items-center gap-3 text-sm mt-3">
                <button type="button" disabled={historyPage <= 1}
                  onClick={() => setHistoryPage(p => p - 1)}
                  className="px-3 py-1.5 rounded bg-white border border-[#0D7377]/20 disabled:opacity-50">
                  Previous
                </button>
                <span className="text-[#3D5A73]">Page {history.page} of {history.total_pages}</span>
                <button type="button" disabled={historyPage >= history.total_pages}
                  onClick={() => setHistoryPage(p => p + 1)}
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
