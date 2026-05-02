import axios from 'axios'

// Support runtime env override (injected by container entrypoint)
// Falls back to Vite build-time env, then same-origin default
const RUNTIME_API_URL = (window as any).ENV?.API_URL
const BUILD_API_URL = (import.meta as any).env?.VITE_API_URL
const API_BASE = RUNTIME_API_URL || BUILD_API_URL || '/api/v1'

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})
