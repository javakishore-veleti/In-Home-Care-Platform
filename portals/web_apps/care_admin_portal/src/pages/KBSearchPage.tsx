import { useState, type FormEvent } from 'react'

import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import type { ChunkRow } from '../types'

const STRATEGY_COLORS: Record<string, string> = {
  sentence: 'bg-[#E8612D]/15 text-[#E8612D]',
  recursive: 'bg-[#0D7377]/15 text-[#0D7377]',
  semantic: 'bg-[#6A1B9A]/15 text-[#6A1B9A]',
  parent_doc: 'bg-[#1976D2]/15 text-[#1976D2]',
}

export function KBSearchPage() {
  const { token } = useAuth()
  const [query, setQuery] = useState('')
  const [collectionSlug, setCollectionSlug] = useState('')
  const [strategyFilter, setStrategyFilter] = useState('')
  const [results, setResults] = useState<(ChunkRow & { relevance_score?: number; collection_name?: string; repository_name?: string })[]>([])
  const [searched, setSearched] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSearch(e: FormEvent) {
    e.preventDefault()
    if (!token || !query.trim()) return
    setLoading(true)
    setError(null)
    setSearched(true)
    try {
      const res = await api.searchKnowledge(token, {
        query: query.trim(),
        collection_slug: collectionSlug || undefined,
        top_k: 10,
        strategy_filter: strategyFilter || undefined,
      })
      setResults(res.results as any)
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : 'Search failed.')
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-[#1A2B3C]">Knowledge Search</h2>
        <p className="text-sm text-[#3D5A73] mt-1">
          Semantic search across all indexed knowledge. Uses multi-strategy retrieval with query masking
          and de-duplication. This is the same search the LangGraph briefing agent will call.
        </p>
      </div>

      <form onSubmit={handleSearch} className="bg-white rounded-xl shadow border border-[#0D7377]/10 p-5 space-y-3">
        <div>
          <label className="block text-xs font-semibold text-[#3D5A73] mb-1">Query</label>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            required
            placeholder="e.g. What should I know about fall prevention?"
            className="w-full px-3 py-2 rounded border border-[#0D7377]/20 text-sm focus:outline-none focus:ring-2 focus:ring-[#0D7377]"
          />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="block text-xs font-semibold text-[#3D5A73] mb-1">Collection (optional)</label>
            <input
              value={collectionSlug}
              onChange={(e) => setCollectionSlug(e.target.value)}
              placeholder="e.g. skilled-nursing (or leave empty for all)"
              className="w-full px-3 py-2 rounded border border-[#0D7377]/20 text-sm focus:outline-none focus:ring-2 focus:ring-[#0D7377]"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-[#3D5A73] mb-1">Strategy filter</label>
            <select
              value={strategyFilter}
              onChange={(e) => setStrategyFilter(e.target.value)}
              className="w-full px-3 py-2 rounded border border-[#0D7377]/20 text-sm bg-white"
            >
              <option value="">All strategies</option>
              <option value="sentence">Sentence</option>
              <option value="recursive">Recursive</option>
              <option value="semantic">Semantic</option>
              <option value="parent_doc">Parent doc</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="w-full px-4 py-2 rounded bg-[#0D7377] hover:bg-[#084C4F] text-white text-sm font-semibold disabled:opacity-50"
            >
              {loading ? 'Searching...' : '🔍 Search'}
            </button>
          </div>
        </div>
      </form>

      {error && <div className="text-sm text-[#D32F2F]">{error}</div>}

      {searched && !loading && results.length === 0 && (
        <p className="text-sm text-[#3D5A73]">No results found. Try a different query or index more documents.</p>
      )}

      {results.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-lg font-bold text-[#1A2B3C]">{results.length} results</h3>
          {results.map((r, i) => (
            <div key={r.id} className="bg-white rounded-xl shadow border border-[#0D7377]/10 p-4">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-[#3D5A73]">#{i + 1}</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                    STRATEGY_COLORS[r.chunk_strategy ?? ''] ?? 'bg-[#3D5A73]/15 text-[#3D5A73]'
                  }`}>
                    {r.chunk_strategy}
                  </span>
                  {(r as any).relevance_score != null && (
                    <span className="text-[10px] text-[#3D5A73]">
                      relevance: {((r as any).relevance_score * 100).toFixed(1)}%
                    </span>
                  )}
                </div>
                <span className="text-[10px] text-[#3D5A73]">{r.token_count ?? '?'} tokens</span>
              </div>
              <p className="text-sm text-[#1A2B3C] mb-2 whitespace-pre-wrap">{r.chunk_text}</p>
              <div className="flex items-center gap-3 text-[10px] text-[#3D5A73]">
                <span>Source: {r.item_title ?? `Item #${r.item_id}`}</span>
                {(r as any).collection_name && <span>Collection: {(r as any).collection_name}</span>}
                {(r as any).repository_name && <span>Repo: {(r as any).repository_name}</span>}
                <span className="font-mono">{r.content_hash_short}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
