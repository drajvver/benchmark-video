export interface SystemInfo {
  os: string
  os_version: string
  arch: string
  cpu_model: string
  cpu_cores: number
  cpu_threads: number
  ram_gb: number
  is_virtualized: boolean
  virtualization_platform: string | null
}

export interface EncodeResult {
  video: string
  codec: string
  preset: string
  crf: number
  encode_time_seconds: number
  fps: number
  output_size_mb: number
}

export interface BenchmarkResult {
  id: string
  benchmark_version: string
  run_id: string
  timestamp: string
  system: SystemInfo
  results: EncodeResult[]
}

export interface LeaderboardEntry {
  cpu_model: string
  codec: string
  avg_fps: number
  best_fps: number
  run_count: number
  is_virtualized: boolean
}

export interface CPUStats {
  cpu_model: string
  avg_fps: number
  best_fps: number
  run_count: number
  bare_metal_count: number
  virtualized_count: number
}
