import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { useBrandStore } from '../store/useBrand'
import { fetchLeads, exportLeads, deleteLead } from '../api/client'
import { Download, Trash2, Send } from 'lucide-react'
import { useToast } from './Toast'
import { useQueryClient } from '@tanstack/react-query'

export default function LeadsTable({ onLeadClick }) {
  const { brand, source } = useBrandStore()
  const { error, success } = useToast()
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['leads', brand, source],
    queryFn: () => fetchLeads({ brand, source, limit: 100 }),
  })
  const leads = data?.leads ?? []

  const handleExport = async () => {
    try {
      const blob = await exportLeads({ brand, source })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `leads-${brand}-${source}-${new Date().toISOString().split('T')[0]}.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      error('Failed to export leads')
    }
  }

  const handleDelete = async (e, id) => {
    e.stopPropagation()
    if (!window.confirm('Delete this lead?')) return
    try {
      await deleteLead(id)
      success('Lead deleted')
      queryClient.invalidateQueries({ queryKey: ['leads'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    } catch (err) {
      error('Failed to delete lead')
    }
  }

  const getScoreBadge = (score) => {
    if (score >= 70) return <span className="bg-emerald-500/10 text-emerald-400 px-2 py-1 rounded text-xs font-medium">Hot 🔥</span>
    if (score >= 45) return <span className="bg-amber-500/10 text-amber-400 px-2 py-1 rounded text-xs font-medium">Warm</span>
    return <span className="bg-rose-500/10 text-rose-400 px-2 py-1 rounded text-xs font-medium">Cold</span>
  }

  return (
    <div className="bg-card border border-border rounded-xl shadow-sm flex-1 flex flex-col overflow-hidden">
      <div className="p-4 border-b border-border flex justify-between items-center bg-surface/50">
        <h2 className="font-semibold text-lg">Leads</h2>
        <button
          onClick={handleExport}
          className="flex items-center gap-2 text-sm bg-bg border border-border px-3 py-1.5 rounded-lg hover:border-muted transition-colors"
        >
          <Download size={14} />
          Export CSV
        </button>
      </div>

      <div className="flex-1 overflow-auto">
        <table className="w-full text-left text-sm whitespace-nowrap">
          <thead className="bg-surface sticky top-0 text-muted border-b border-border z-10">
            <tr>
              <th className="px-4 py-3 font-medium">Business</th>
              <th className="px-4 py-3 font-medium">Location / Info</th>
              <th className="px-4 py-3 font-medium">Source</th>
              <th className="px-4 py-3 font-medium">Score</th>
              <th className="px-4 py-3 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {isLoading ? (
              <tr><td colSpan="5" className="p-8 text-center text-muted">Loading...</td></tr>
            ) : leads.length === 0 ? (
              <tr>
                <td colSpan="5" className="p-8 text-center text-muted">
                  {source === 'maps' ? "Search for local businesses by niche and city" :
                   source === 'instagram' ? "Find businesses by hashtag using Apify" :
                   source === 'linkedin' ? "Find companies and founders by keyword" :
                   "Start scraping to find leads"}
                </td>
              </tr>
            ) : (
              leads.map((lead) => (
                <tr
                  key={lead.id}
                  onClick={() => onLeadClick(lead)}
                  className="hover:bg-surface/50 cursor-pointer transition-colors"
                >
                  <td className="px-4 py-3">
                    <div className="font-medium text-white">{lead.name}</div>
                    <div className="text-xs text-muted mt-0.5">{lead.category || 'Business'}</div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-white truncate max-w-[200px]">{lead.city || lead.address || 'N/A'}</div>
                    <div className="text-xs text-muted mt-0.5">
                      {lead.rating ? `⭐ ${lead.rating}` : lead.followers ? `👥 ${lead.followers}` : ''}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="bg-bg border border-border px-2 py-1 rounded text-xs text-muted uppercase">
                      {lead.source}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {getScoreBadge(lead.score || 0)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={(e) => { e.stopPropagation(); onLeadClick(lead) }}
                        className="p-1.5 text-muted hover:text-[var(--accent)] transition-colors bg-bg rounded-md border border-transparent hover:border-[var(--accent-dim)]"
                        title="Draft Outreach"
                      >
                        <Send size={14} />
                      </button>
                      <button
                        onClick={(e) => handleDelete(e, lead.id)}
                        className="p-1.5 text-muted hover:text-rose-400 transition-colors bg-bg rounded-md border border-transparent hover:border-rose-500/20"
                        title="Delete Lead"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
