import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchStats } from '../api/client'
import { useBrandStore } from '../store/useBrand'

export default function StatsBar() {
  const brand = useBrandStore((state) => state.brand)

  const { data: stats } = useQuery({
    queryKey: ['stats', brand],
    queryFn: () => fetchStats(brand),
    refetchInterval: 30000,
  })

  const total = stats?.total ?? 0
  const hot = stats?.hot ?? 0
  const warm = stats?.warm ?? 0
  const cold = stats?.cold ?? 0
  const noWeb = stats?.no_website ?? 0
  const hasWeb = stats?.has_website ?? 0

  const hotPct = total > 0 ? Math.round((hot / total) * 100) : 0
  const warmPct = total > 0 ? Math.round((warm / total) * 100) : 0
  const coldPct = total > 0 ? Math.max(0, 100 - hotPct - warmPct) : 0
  const noWebPct = total > 0 ? Math.round((noWeb / total) * 100) : 0

  const items = [
    { label: 'Total Leads', value: total, color: 'text-white' },
    { label: 'Hot Leads', value: hot, color: 'text-emerald-400', dot: 'bg-emerald-400' },
    { label: 'Warm Leads', value: warm, color: 'text-amber-400', dot: 'bg-amber-400' },
    { label: 'Cold Leads', value: cold, color: 'text-rose-400', dot: 'bg-rose-400' },
    { label: 'No Website', value: noWeb, color: 'text-[#FF5370]', emoji: '🔴' },
    { label: 'Has Website', value: hasWeb, color: 'text-[#22D07A]', emoji: '✅' },
  ]

  return (
    <div className="flex flex-col gap-3">
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        {items.map((item, i) => (
          <div key={i} className="bg-card border border-border p-4 rounded-xl shadow-sm flex flex-col justify-between hover:border-muted/60 transition-colors">
            <div className="text-xs font-medium text-muted flex items-center gap-1.5">
              {item.emoji && <span>{item.emoji}</span>}
              {item.dot && <span className={`w-2 h-2 rounded-full ${item.dot}`}></span>}
              <span>{item.label}</span>
            </div>
            <div className={`text-2xl font-bold mt-1 ${item.color}`}>
              {item.value}
            </div>
          </div>
        ))}
      </div>

      {total > 0 && (
        <div className="bg-card border border-border/80 px-4 py-2.5 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs shadow-sm">
          <div className="flex items-center gap-3">
            <span className="text-muted font-medium">Pipeline Distribution:</span>
            <div className="flex h-2.5 w-44 sm:w-56 bg-surface rounded-full overflow-hidden p-0.5 gap-0.5 border border-border/50">
              {hot > 0 && (
                <div
                  style={{ width: `${hotPct}%` }}
                  title={`Hot Leads: ${hot} (${hotPct}%)`}
                  className="bg-emerald-400 rounded-full transition-all duration-500"
                />
              )}
              {warm > 0 && (
                <div
                  style={{ width: `${warmPct}%` }}
                  title={`Warm Leads: ${warm} (${warmPct}%)`}
                  className="bg-amber-400 rounded-full transition-all duration-500"
                />
              )}
              {cold > 0 && (
                <div
                  style={{ width: `${coldPct}%` }}
                  title={`Cold Leads: ${cold} (${coldPct}%)`}
                  className="bg-rose-400/80 rounded-full transition-all duration-500"
                />
              )}
            </div>
            <span className="text-emerald-400 font-semibold">{hotPct}% Hot Quality</span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-muted">High-Converting Pitch Target:</span>
            <span className="bg-[#FF5370]/15 text-[#FF5370] border border-[#FF5370]/30 px-2 py-0.5 rounded-full font-bold flex items-center gap-1 shadow-sm">
              <span>🔥 {noWebPct}% No Website</span>
              <span className="text-[10px] text-muted font-normal hidden sm:inline">(Easy Pitch)</span>
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
