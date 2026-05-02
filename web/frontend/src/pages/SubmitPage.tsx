import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Upload, CheckCircle, AlertCircle } from 'lucide-react'
import { api } from '../api/client'

export default function SubmitPage() {
  const [jsonText, setJsonText] = useState('')
  const [file, setFile] = useState<File | null>(null)

  const submitMutation = useMutation({
    mutationFn: async (data: unknown) => {
      // Get token first
      const { data: tokenData } = await api.get<{ token: string }>('/results/token')
      const { data: result } = await api.post('/results', data, {
        headers: { Authorization: `Bearer ${tokenData.token}` },
      })
      return result
    },
  })

  const handleSubmit = async () => {
    let data: unknown
    try {
      if (file) {
        const text = await file.text()
        data = JSON.parse(text)
      } else {
        data = JSON.parse(jsonText)
      }
    } catch {
      alert('Invalid JSON')
      return
    }
    submitMutation.mutate(data)
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Submit Result</h1>

      <div className="bg-white rounded-lg shadow p-6 max-w-2xl">
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Paste JSON result
          </label>
          <textarea
            value={jsonText}
            onChange={(e) => setJsonText(e.target.value)}
            rows={12}
            className="w-full border rounded-md px-3 py-2 text-sm font-mono"
            placeholder='{"benchmark_version": "1.0.0", ...}'
          />
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Or upload a file
          </label>
          <input
            type="file"
            accept=".json"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          />
        </div>

        <button
          onClick={handleSubmit}
          disabled={submitMutation.isPending}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          <Upload className="h-4 w-4 mr-2" />
          {submitMutation.isPending ? 'Uploading...' : 'Submit'}
        </button>

        {submitMutation.isSuccess && (
          <div className="mt-4 flex items-center text-green-600">
            <CheckCircle className="h-5 w-5 mr-2" />
            Result submitted successfully!
          </div>
        )}

        {submitMutation.isError && (
          <div className="mt-4 flex items-center text-red-600">
            <AlertCircle className="h-5 w-5 mr-2" />
            Upload failed. Please check your JSON and try again.
          </div>
        )}
      </div>
    </div>
  )
}
