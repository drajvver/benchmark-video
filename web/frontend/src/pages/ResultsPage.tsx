import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Clock, Cpu, Monitor, HardDrive, ChevronRight } from 'lucide-react'
import { api } from '../api/client'
import type { BenchmarkResult } from '../types'

export default function ResultsPage() {
  const navigate = useNavigate()
  const [cpuFilter, setCpuFilter] = useState('')

  const { data: results, isLoading } = useQuery({
    queryKey: ['results', cpuFilter],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (cpuFilter) params.append('cpu_model', cpuFilter)
      params.append('limit', '100')
      const { data } = await api.get<BenchmarkResult[]>(`/results?${params}`)
      return data
    },
  })

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Recent Results</h1>

      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex items-center gap-2">
          <Cpu className="h-4 w-4 text-gray-500" />
          <input
            type="text"
            placeholder="Filter by CPU model..."
            value={cpuFilter}
            onChange={(e) => setCpuFilter(e.target.value)}
            className="border rounded-md px-3 py-2 text-sm w-64"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-gray-500">Loading...</div>
      ) : (
        <div className="space-y-4">
          {results?.map((result) => (
            <div
              key={result.id}
              onClick={() => navigate(`/result/${result.id}`)}
              className="bg-white rounded-lg shadow p-5 cursor-pointer hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-start gap-4">
                  <div className="bg-blue-50 p-3 rounded-lg">
                    <Cpu className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{result.system.cpu_model}</h3>
                    <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                      <span className="flex items-center gap-1">
                        <Monitor className="h-3.5 w-3.5" />
                        {result.system.os} ({result.system.arch})
                      </span>
                      <span className="flex items-center gap-1">
                        <HardDrive className="h-3.5 w-3.5" />
                        {result.system.ram_gb} GB RAM
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3.5 w-3.5" />
                        {new Date(result.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mt-2">
                      {result.system.is_virtualized ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                          VM
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                          Bare Metal
                        </span>
                      )}
                      <span className="text-xs text-gray-400">
                        {result.results.length} jobs
                      </span>
                    </div>
                  </div>
                </div>
                <ChevronRight className="h-5 w-5 text-gray-400" />
              </div>

              {/* Quick job summary */}
              <div className="mt-4 pt-4 border-t grid grid-cols-2 md:grid-cols-4 gap-3">
                {result.results.slice(0, 4).map((job, idx) => (
                  <div key={idx} className="bg-gray-50 rounded-md px-3 py-2">
                    <div className="text-xs text-gray-500 truncate">{job.video}</div>
                    <div className="text-xs font-medium text-gray-700">{job.codec}</div>
                    <div className="text-sm font-mono text-blue-600">{job.fps.toFixed(1)} fps</div>
                  </div>
                ))}
                {result.results.length > 4 && (
                  <div className="bg-gray-50 rounded-md px-3 py-2 flex items-center justify-center text-xs text-gray-400">
                    +{result.results.length - 4} more
                  </div>
                )}
              </div>
            </div>
          ))}
          {results?.length === 0 && (
            <div className="text-center py-12 text-gray-500">No results found</div>
          )}
        </div>
      )}
    </div>
  )
}
