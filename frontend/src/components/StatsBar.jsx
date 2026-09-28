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

  const items = [
    { label: 'Total Leads', value: stats?.total ?? 0, color: 'text-white' },
    { label: 'Hot Leads', value: stats?.hot ?? 0, color: 'text-emerald-400', dot: 'bg-emerald-400' },
    { label: 'Warm Leads', value: stats?.warm ?? 0, color: 'text-amber-400', dot: 'bg-amber-400' },
    { label: 'Cold Leads', value: stats?.cold ?? 0, color: 'text-rose-400', dot: 'bg-rose-400' },
    { label: 'No Website', value: stats?.no_website ?? 0, color: 'text-[#FF5370]', emoji: '🔴' },
    { label: 'Has Website', value: stats?.has_website ?? 0, color: 'text-[#22D07A]', emoji: '✅' },
  ]

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
      {items.map((item, i) => (
        <div key={i} className="bg-card border border-border p-4 rounded-xl shadow-sm flex flex-col justify-between">
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
  )
}
