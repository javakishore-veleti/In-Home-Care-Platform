import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import type { KBCollection, KBRepository } from '../types'

const REPO_TYPES = ['policies', 'announcements', 'notes', 'knowledgebases', 'research', 'experiences', 'others']
const STATUS_COLORS: Record<string, string> = {
  draft: '#3D5A73', locked: '#E8A317', publishing: '#1976D2', indexed: '#2D8A4E', failed: '#D32F2F',
}
const STATUS_ICONS: Record<string, string> = {
  draft: '✏️', locked: '🔒', publishing: '🔄', indexed: '✅', failed: '❌',
}

export function KBCollectionDetailPage() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const { collectionId } = useParams<{ collectionId: string }>()
  const [collection, setCollection] = useState<KBCollection | null>(null)
  const [repos, setRepos] = useState<KBRepository[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [newName, setNewName] = useState('')
  const [newType, setNewType] = useState('policies')
  const [newDesc, setNewDesc] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function load() {
    if (!token || !collectionId) return
    setLoading(true)
    try {
      const [col, repoRes] = await Promise.all([
        api.getKBCollection(token, Number(collectionId)),
        api.listKBRepositories(token, Number(collectionId)),
      ])
      setCollection(col)
      setRepos(repoRes.items)
      setError(null)
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : 'Failed to load.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { void load() }, [token, collectionId]) // eslint-disable-line

  async function handleCreate(e: FormEvent) {
    e.preventDefault()
    if (!token || !collectionId) return
    setSubmitting(true)
    try {
      await api.createKBRepository(token, Number(collectionId), {
        name: newName.trim(), repo_type: newType, description: newDesc.trim() || undefined,
      })
      setNewName(''); setNewDesc(''); setShowForm(false)
      await load()
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : 'Create failed.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <Link to="/app/knowledge-base" style={{ color: '#0D7377' }} className="text-xs font-semibold hover:underline">
          ← Back to Knowledge Base
        </Link>
        <h2 className="text-2xl font-bold text-[#1A2B3C] mt-1">
          {collection ? `${collection.icon_emoji} ${collection.name}` : 'Collection'}
        </h2>
        {collection?.description && <p className="text-sm text-[#3D5A73] mt-1">{collection.description}</p>}
      </div>
      {error && <div className="text-sm text-[#D32F2F]">{error}</div>}
      {loading && <p className="text-sm text-[#3D5A73]">Loading...</p>}

      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-[#1A2B3C]">Repositories</h3>
        <button
          type="button"
          onClick={() => setShowForm(v => !v)}
          className="px-3 py-1.5 rounded bg-[#0D7377] hover:bg-[#084C4F] text-white text-xs font-semibold"
        >
          {showForm ? 'Cancel' : '+ Create repository'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="bg-white border border-[#0D7377]/10 rounded-xl shadow p-4 space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-[#3D5A73] mb-1">Name</label>
              <input value={newName} onChange={e => setNewName(e.target.value)} required maxLength={255}
                className="w-full px-3 py-2 rounded border border-[#0D7377]/20 text-sm focus:outline-none focus:ring-2 focus:ring-[#0D7377]" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#3D5A73] mb-1">Type</label>
              <select value={newType} onChange={e => setNewType(e.target.value)}
                className="w-full px-3 py-2 rounded border border-[#0D7377]/20 text-sm bg-white">
                {REPO_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-[#3D5A73] mb-1">Description (optional)</label>
            <textarea value={newDesc} onChange={e => setNewDesc(e.target.value)} rows={2}
              className="w-full px-3 py-2 rounded border border-[#0D7377]/20 text-sm focus:outline-none focus:ring-2 focus:ring-[#0D7377]" />
          </div>
          <div className="flex justify-end">
            <button type="submit" disabled={submitting}
              className="px-4 py-2 rounded bg-[#0D7377] hover:bg-[#084C4F] text-white text-sm font-semibold disabled:opacity-60">
              {submitting ? 'Creating...' : 'Create'}
            </button>
          </div>
        </form>
      )}

      {repos.length === 0 && !loading && (
        <p className="text-sm text-[#3D5A73]">No repositories yet. Click "+ Create repository" to add one.</p>
      )}

      {repos.length > 0 && (
        <table className="w-full text-left border-collapse bg-white rounded-xl shadow overflow-hidden">
          <thead>
            <tr className="bg-[#0D7377] text-white text-sm">
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Items</th>
              <th className="px-4 py-3">Chunks</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {repos.map(repo => (
              <tr key={repo.id}
                onClick={() => navigate(`/app/knowledge-base/${collectionId}/repo/${repo.id}`)}
                className="border-b border-[#0D7377]/10 text-sm cursor-pointer hover:bg-[#0D7377]/5">
                <td className="px-4 py-3 font-semibold">{repo.name}</td>
                <td className="px-4 py-3 text-[#3D5A73]">{repo.repo_type}</td>
                <td className="px-4 py-3">{repo.item_count}</td>
                <td className="px-4 py-3">{repo.chunk_count}</td>
                <td className="px-4 py-3">
                  <span className="px-2 py-1 rounded text-xs font-bold text-white uppercase"
                    style={{ backgroundColor: STATUS_COLORS[repo.status] ?? '#3D5A73' }}>
                    {STATUS_ICONS[repo.status] ?? ''} {repo.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
