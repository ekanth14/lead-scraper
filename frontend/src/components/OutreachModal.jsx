import React, { useEffect, useState } from 'react'
import { generateOutreach } from '../api/client'
import { useBrandStore } from '../store/useBrand'
import { useToast } from './Toast'
import { X, Copy, RefreshCw, ExternalLink } from 'lucide-react'

const hasWebsite = (website) => {
  if (!website) return false
  const trimmed = String(website).trim().toLowerCase()
  return trimmed !== '' && trimmed !== 'none found' && trimmed !== 'none' && trimmed !== 'null'
}

export default function OutreachModal({ lead, onClose }) {
  const brand = useBrandStore((state) => state.brand)
  const [draft, setDraft] = useState('')
  const [loading, setLoading] = useState(false)
  const { success, error } = useToast()

  const draftMessage = async () => {
    setLoading(true)
    try {
      const data = await generateOutreach({ lead, brand })
      setDraft(data.dm || '')
    } catch (err) {
      error('Failed to generate outreach message')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    draftMessage()
    
    const handleEsc = (e) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
    // eslint-disable-next-line
  }, [lead.id])

  const handleCopy = () => {
    if (draft) {
      navigator.clipboard.writeText(draft)
      success('Copied to clipboard!')
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div 
        className="bg-card border border-border rounded-xl w-full max-w-2xl shadow-2xl flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center p-4 border-b border-border bg-surface/50 rounded-t-xl">
          <h2 className="font-semibold text-lg flex items-center gap-2">
            Lead Details & Outreach
          </h2>
          <button onClick={onClose} className="p-1 text-muted hover:text-white rounded-md hover:bg-bg transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          {/* Lead Info */}
          <div>
            <h3 className="text-xl font-bold text-white mb-1">{lead.name}</h3>
            <div className="text-sm text-muted flex flex-wrap gap-x-4 gap-y-2">
              {lead.category && <span>{lead.category}</span>}
              {(lead.city || lead.address) && <span>📍 {lead.city || lead.address}</span>}
              {lead.rating && <span>⭐ {lead.rating}</span>}
              {lead.followers && <span>👥 {lead.followers}</span>}
            </div>

            {/* Prominent Website Row */}
            <div className="mt-4 p-3 bg-surface/80 border border-border rounded-xl">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-muted uppercase tracking-wider">Website Details</span>
                {lead.phone && (
                  <span className="text-xs text-muted flex items-center gap-1">
                    📞 {lead.phone}
                  </span>
                )}
              </div>

              {hasWebsite(lead.website) ? (
                <div className="flex items-center gap-2.5 flex-wrap">
                  <span className="text-xs font-bold text-[#22D07A] bg-[#22D07A]/10 border border-[#22D07A]/30 px-2.5 py-1 rounded-full">
                    ✅ Active website
                  </span>
                  <a
                    href={lead.website.startsWith('http') ? lead.website : `https://${lead.website}`}
                    target="_blank"
                    rel="noreferrer"
                    className="text-sm font-medium text-[#22D07A] hover:underline flex items-center gap-1"
                  >
                    <ExternalLink size={14} />
                    {lead.website}
                  </a>
                </div>
              ) : (
                <div className="space-y-1">
                  <div className="text-base font-bold text-[#FF5370] flex items-center gap-1.5">
                    <span>🔴</span> No website found
                  </div>
                  <div className="text-xs text-muted">
                    → Perfect pitch: offer {brand === 'orv' ? 'Orvyqmedia digital presence package' : 'Zien Technologies website package'}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Why this lead */}
          {lead.why && (
            <div className="bg-bg border border-border p-3 rounded-lg text-sm">
              <strong className="text-white block mb-1">Why this lead?</strong>
              <p className="text-muted leading-relaxed">{lead.why}</p>
            </div>
          )}

          {/* Outreach */}
          <div>
            <div className="flex justify-between items-end mb-2">
              <strong className="text-white text-sm">AI-Drafted Outreach</strong>
              <button 
                onClick={draftMessage} 
                disabled={loading}
                className="text-xs text-muted hover:text-[var(--accent)] flex items-center gap-1 transition-colors"
              >
                <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
                Regenerate
              </button>
            </div>
            
            <div className="bg-bg border border-border rounded-lg relative min-h-[120px]">
              {loading ? (
                <div className="p-4 space-y-2 animate-pulse">
                  <div className="h-4 bg-surface rounded w-3/4"></div>
                  <div className="h-4 bg-surface rounded w-full"></div>
                  <div className="h-4 bg-surface rounded w-5/6"></div>
                </div>
              ) : (
                <>
                  <textarea
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    className="w-full h-full min-h-[160px] bg-transparent p-4 text-sm text-text focus:outline-none focus:ring-1 focus:ring-[var(--accent)] rounded-lg resize-y"
                  />
                  <div className="absolute bottom-3 right-3">
                    <button
                      onClick={handleCopy}
                      className="bg-surface hover:bg-[var(--accent-dim)] text-white hover:text-[var(--accent)] border border-border p-2 rounded-md transition-colors"
                      title="Copy to clipboard"
                    >
                      <Copy size={14} />
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
      {/* Overlay click */}
      <div className="absolute inset-0 -z-10" onClick={onClose}></div>
    </div>
  )
}
