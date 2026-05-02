import axios from 'axios'

// Vite injects env vars via import.meta.env
const API_BASE = (import.meta as any).env?.VITE_API_URL || '/api/v1'

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})
