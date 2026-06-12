import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method.toUpperCase()} request to ${config.url}`)
    return config
  },
  (error) => Promise.reject(error)
)

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const data = error.response.data
      // Handle Python's {"detail": "..."} and {"detail": [...]} as well as {"error": "..."}
      let message
      if (data?.detail) {
        message = Array.isArray(data.detail)
          ? data.detail.join('\n')
          : data.detail
      } else {
        message = data?.error || data?.message || `Request failed with status ${error.response.status}`
      }
      throw new Error(message)
    } else if (error.request) {
      throw new Error('No response from server. Is the Node.js backend running?')
    } else {
      throw new Error(error.message || 'An unexpected error occurred')
    }
  }
)

// ── Health & metrics ──────────────────────────────────────────────────────

export const checkHealth = async () => {
  const response = await apiClient.get('/health')
  return response.data
}

export const getMetrics = async () => {
  const response = await apiClient.get('/api/metrics')
  return response.data
}

// ── Users ─────────────────────────────────────────────────────────────────

export const getUsers = async () => {
  const response = await apiClient.get('/api/users')
  return response.data
}

export const getUserById = async (id) => {
  const response = await apiClient.get(`/api/users/${id}`)
  return response.data
}

export const createUser = async ({ name, email, role }) => {
  const response = await apiClient.post('/api/users', { name, email, role })
  return response.data
}

// ── Tasks ─────────────────────────────────────────────────────────────────

export const getTasks = async (status = '', userId = '') => {
  const params = {}
  if (status) params.status = status
  if (userId) params.userId = userId
  const response = await apiClient.get('/api/tasks', { params })
  return response.data
}

export const createTask = async ({ title, status, userId }) => {
  const response = await apiClient.post('/api/tasks', { title, status, userId })
  return response.data
}

export const updateTask = async (id, fields) => {
  const response = await apiClient.put(`/api/tasks/${id}`, fields)
  return response.data
}

// ── Stats ─────────────────────────────────────────────────────────────────

export const getStats = async () => {
  const response = await apiClient.get('/api/stats')
  return response.data
}
