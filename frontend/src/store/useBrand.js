import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useBrandStore = create(
  persist(
    (set) => ({
      brand: 'orv', // 'orv' | 'zien'
      source: 'all', // 'maps' | 'instagram' | 'linkedin' | 'all'
      niche: '',
      leads: { maps: [], instagram: [], linkedin: [] },
      setBrand: (brand) => set({ brand }),
      setSource: (source) => set({ source }),
      setNiche: (niche) => set({ niche }),
      setLeads: (source, newLeads) =>
        set((state) => ({
          leads: { ...state.leads, [source]: newLeads },
        })),
      clearLeads: () =>
        set({ leads: { maps: [], instagram: [], linkedin: [] } }),
    }),
    {
      name: 'lead-scraper-storage',
      partialize: (state) => ({ brand: state.brand, source: state.source, niche: state.niche }),
    }
  )
)
