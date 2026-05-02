import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Cpu, Film, Gauge, Timer, Save } from 'lucide-react'
import { api } from '../api/client'
import type { BenchmarkResult } from '../types'

export default function ResultDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data: result, isLoading } = useQuery({
    queryKey: ['result', id],
    queryFn: async () => {
      const { data } = await api.get<BenchmarkResult>(`/results/${id}`)
      return data
    },
    enabled: !!id,
  })

  if (isLoading) {
    return <div className="text-center py-12 text-gray-500">Loading...</div>
  }

  if (!result) {
    return <div className="text-center py-12 text-gray-500">Result not found</div>
  }

  // Group jobs by video
  const jobsByVideo = result.results.reduce((acc, job) => {
    if (!acc[job.video]) acc[job.video] = []
    acc[job.video].push(job)
    return acc
  }, {} as Record<string, typeof result.results>)

  return (
    <div>
      <button
        onClick={() => navigate('/results')}
        className="flex items-center text-sm text-gray-600 hover:text-blue-600 mb-4"
      >
        <ArrowLeft className="h-4 w-4 mr-1" />
        Back to results
      </button>

      <h1 className="text-2xl font-bold mb-6">Benchmark Job Details</h1>

      {/* System Info Card */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Cpu className="h-5 w-5 text-blue-600" />
          System Information
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-xs text-gray-500 uppercase tracking-wide">CPU Model</div>
            <div className="font-medium text-gray-900 mt-1">{result.system.cpu_model}</div>
            <div className="text-sm text-gray-500 mt-1">
              {result.system.cpu_cores} cores / {result.system.cpu_threads} threads
            </div>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-xs text-gray-500 uppercase tracking-wide">Platform</div>
            <div className="font-medium text-gray-900 mt-1">{result.system.os}</div>
            <div className="text-sm text-gray-500 mt-1">
              {result.system.arch} · {result.system.ram_gb} GB RAM
            </div>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-xs text-gray-500 uppercase tracking-wide">Environment</div>
            <div className="font-medium mt-1">
              {result.system.is_virtualized ? (
                <span className="text-yellow-700">
                  Virtualized ({result.system.virtualization_platform || 'unknown'})
                </span>
              ) : (
                <span className="text-green-700">Bare Metal</span>
              )}
            </div>
            <div className="text-sm text-gray-500 mt-1">
              Run ID: <code className="text-xs">{result.run_id.slice(0, 8)}...</code>
            </div>
          </div>
        </div>
      </div>

      {/* Encode Jobs by Video */}
      {Object.entries(jobsByVideo).map(([videoName, jobs]) => (
        <div key={videoName} className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Film className="h-5 w-5 text-blue-600" />
            {videoName}
          </h2>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Codec
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Preset
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    CRF
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    <span className="flex items-center justify-end gap-1">
                      <Timer className="h-3 w-3" /> Time
                    </span>
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    <span className="flex items-center justify-end gap-1">
                      <Gauge className="h-3 w-3" /> FPS
                    </span>
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    <span className="flex items-center justify-end gap-1">
                      <Save className="h-3 w-3" /> Size
                    </span>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {jobs.map((job, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">
                      {job.codec}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">{job.preset}</td>
                    <td className="px-4 py-3 text-sm text-gray-500">{job.crf}</td>
                    <td className="px-4 py-3 text-sm text-right font-mono text-gray-900">
                      {job.encode_time_seconds.toFixed(1)}s
                    </td>
                    <td className="px-4 py-3 text-sm text-right font-mono font-semibold text-blue-600">
                      {job.fps.toFixed(1)}
                    </td>
                    <td className="px-4 py-3 text-sm text-right font-mono text-gray-900">
                      {job.output_size_mb.toFixed(1)} MB
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Video summary stats */}
          <div className="mt-4 pt-4 border-t grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-xs text-gray-500">Total Encode Time</div>
              <div className="text-lg font-mono font-semibold text-gray-900">
                {jobs.reduce((sum, j) => sum + j.encode_time_seconds, 0).toFixed(1)}s
              </div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-500">Average FPS</div>
              <div className="text-lg font-mono font-semibold text-blue-600">
                {(jobs.reduce((sum, j) => sum + j.fps, 0) / jobs.length).toFixed(1)}
              </div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-500">Total Output Size</div>
              <div className="text-lg font-mono font-semibold text-gray-900">
                {jobs.reduce((sum, j) => sum + j.output_size_mb, 0).toFixed(1)} MB
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
