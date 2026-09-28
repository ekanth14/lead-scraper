import React, { useState, useEffect } from 'react'
import { useBrandStore } from '../store/useBrand'
import { useToast } from './Toast'
import { scrapeLeads } from '../api/client'
import { Search, Loader2 } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'

export default function SearchBar() {
  const { brand, niche, setNiche, source, setSource } = useBrandStore()
  const [city, setCity] = useState('Bangalore')
  const [apiKey, setApiKey] = useState('')
  const [loading, setLoading] = useState(false)
  const { success, error } = useToast()
  const queryClient = useQueryClient()

  // Default source to maps if 'all' is selected for scraping
  const targetSource = source === 'all' ? 'maps' : source

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!niche) return error('Please enter a niche')

    setLoading(true)
    try {
      const data = await scrapeLeads({
        source: targetSource,
        niche,
        city,
        brand,
        apiKey: apiKey.trim() || undefined
      })
      success(`Successfully scraped ${data.count || ''} leads!`)
      // Invalidate queries to refresh tables and stats
      queryClient.invalidateQueries({ queryKey: ['leads'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    } catch (err) {
      error(err.response?.data?.detail || 'Failed to scrape leads')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-card border border-border p-4 rounded-xl shadow-sm">
      <form onSubmit={handleSearch} className="flex flex-wrap md:flex-nowrap gap-3 items-end">
        <div className="flex-1 min-w-[200px]">
          <label className="block text-xs font-medium text-muted mb-1">Niche (Ctrl+K)</label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" size={16} />
            <input
              id="niche-input"
              type="text"
              value={niche}
              onChange={(e) => setNiche(e.target.value)}
              placeholder="e.g. restaurant"
              className="w-full bg-bg border border-border rounded-lg pl-9 pr-3 py-2 text-sm focus:outline-none focus:border-[var(--accent)] text-white"
            />
          </div>
        </div>
        <div className="w-full md:w-40">
          <label className="block text-xs font-medium text-muted mb-1">City</label>
          <input
            type="text"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            className="w-full bg-bg border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[var(--accent)] text-white"
          />
        </div>
        <div className="w-full md:w-36">
          <label className="block text-xs font-medium text-muted mb-1">Source</label>
          <select
            value={targetSource}
            onChange={(e) => setSource(e.target.value)}
            className="w-full bg-bg border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[var(--accent)] text-white appearance-none"
          >
            <option value="maps">Google Maps</option>
            <option value="instagram">Instagram</option>
            <option value="linkedin">LinkedIn</option>
          </select>
        </div>
        <div className="w-full md:w-48">
          <label className="block text-xs font-medium text-muted mb-1">API Key (Optional)</label>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="Uses server key by default"
            className="w-full bg-bg border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[var(--accent)] text-white"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="w-full md:w-auto bg-[var(--accent)] hover:opacity-90 text-white font-medium px-6 py-2 rounded-lg text-sm flex items-center justify-center gap-2 h-[38px] disabled:opacity-50"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : 'Find Leads'}
        </button>
      </form>
    </div>
  )
}
