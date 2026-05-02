import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { api } from '../api/client'
import type { CPUStats } from '../types'

export default function CPUComparisonPage() {
  const [codec, setCodec] = useState('')
  const [view, setView] = useState<'all' | 'bare_metal'>('bare_metal')

  const { data: stats, isLoading } = useQuery({
    queryKey: ['cpu-stats', codec],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (codec) params.append('codec', codec)
      const { data } = await api.get<CPUStats[]>(`/leaderboard/cpus?${params}`)
      return data
    },
  })

  const filtered = view === 'bare_metal'
    ? stats?.filter((s) => s.bare_metal_count > 0)
    : stats

  const chartData = filtered?.slice(0, 20).map((s) => ({
    name: s.cpu_model.length > 30 ? s.cpu_model.slice(0, 30) + '...' : s.cpu_model,
    avg_fps: s.avg_fps,
    best_fps: s.best_fps,
    run_count: s.run_count,
    bare_metal: s.bare_metal_count,
    virtualized: s.virtualized_count,
  }))

  const codecs = ['H.264 / x264', 'H.265 / x265', 'VP9', 'AV1 / SVT-AV1']

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">CPU Comparison</h1>

      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex flex-wrap gap-4 items-center">
          <select
            value={codec}
            onChange={(e) => setCodec(e.target.value)}
            className="border rounded-md px-3 py-2 text-sm"
          >
            <option value="">All Codecs</option>
            {codecs.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>

          <div className="flex rounded-md overflow-hidden border">
            <button
              onClick={() => setView('bare_metal')}
              className={`px-4 py-2 text-sm ${
                view === 'bare_metal'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              Bare Metal Only
            </button>
            <button
              onClick={() => setView('all')}
              className={`px-4 py-2 text-sm ${
                view === 'all'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              All Results
            </button>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-gray-500">Loading...</div>
      ) : (
        <>
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">Average FPS by CPU</h2>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={chartData} layout="vertical" margin={{ left: 40 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" width={250} style={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="avg_fps" name="Average FPS" fill="#3b82f6" />
                <Bar dataKey="best_fps" name="Best FPS" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    CPU Model
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Avg FPS
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Best FPS
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Total Runs
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Bare Metal
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Virtualized
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filtered?.map((s) => (
                  <tr key={s.cpu_model} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">
                      {s.cpu_model}
                    </td>
                    <td className="px-6 py-4 text-sm text-right font-mono">
                      {s.avg_fps.toFixed(1)}
                    </td>
                    <td className="px-6 py-4 text-sm text-right font-mono">
                      {s.best_fps.toFixed(1)}
                    </td>
                    <td className="px-6 py-4 text-sm text-right">{s.run_count}</td>
                    <td className="px-6 py-4 text-sm text-right text-green-600">
                      {s.bare_metal_count}
                    </td>
                    <td className="px-6 py-4 text-sm text-right text-yellow-600">
                      {s.virtualized_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}
