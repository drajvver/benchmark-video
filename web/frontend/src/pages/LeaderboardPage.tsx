import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, Search, Filter, Film } from 'lucide-react'
import { api } from '../api/client'
import type { LeaderboardEntry } from '../types'

export default function LeaderboardPage() {
  const [codec, setCodec] = useState('')
  const [video, setVideo] = useState('')
  const [cpuFilter, setCpuFilter] = useState('')
  const [includeVirtualized, setIncludeVirtualized] = useState(true)

  const { data: entries, isLoading } = useQuery({
    queryKey: ['leaderboard', codec, video, includeVirtualized],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (codec) params.append('codec', codec)
      if (video) params.append('video', video)
      if (!includeVirtualized) params.append('is_virtualized', 'false')
      const { data } = await api.get<LeaderboardEntry[]>(`/leaderboard?${params}`)
      return data
    },
  })

  const filtered = entries?.filter((e) =>
    cpuFilter ? e.cpu_model.toLowerCase().includes(cpuFilter.toLowerCase()) : true
  )

  const codecs = ['H.264 / x264', 'H.265 / x265', 'VP9', 'AV1 / SVT-AV1']
  const videos = ['Tears of Steel 1080p', 'Big Buck Bunny 1080p', 'Game 60fps', 'Tears of Steel 4K']

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Leaderboard</h1>

      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex flex-wrap gap-4 items-center">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-500" />
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
          </div>

          <div className="flex items-center gap-2">
            <Film className="h-4 w-4 text-gray-500" />
            <select
              value={video}
              onChange={(e) => setVideo(e.target.value)}
              className="border rounded-md px-3 py-2 text-sm"
            >
              <option value="">All Videos</option>
              {videos.map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <Search className="h-4 w-4 text-gray-500" />
            <input
              type="text"
              placeholder="Filter by CPU model..."
              value={cpuFilter}
              onChange={(e) => setCpuFilter(e.target.value)}
              className="border rounded-md px-3 py-2 text-sm w-64"
            />
          </div>

          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={includeVirtualized}
              onChange={(e) => setIncludeVirtualized(e.target.checked)}
              className="rounded"
            />
            Include virtualized results
          </label>
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-gray-500">Loading...</div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rank
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  CPU Model
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Codec
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Avg FPS
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Best FPS
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Runs
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filtered?.map((entry, idx) => (
                <tr key={`${entry.cpu_model}-${entry.codec}-${idx}`} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {idx + 1}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {entry.cpu_model}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {entry.codec}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-mono text-gray-900">
                    {entry.avg_fps.toFixed(1)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-mono text-gray-900">
                    {entry.best_fps.toFixed(1)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-500">
                    {entry.run_count}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    {entry.is_virtualized ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                        <AlertTriangle className="h-3 w-3 mr-1" />
                        VM
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                        Bare Metal
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filtered?.length === 0 && (
            <div className="text-center py-12 text-gray-500">No results found</div>
          )}
        </div>
      )}
    </div>
  )
}
