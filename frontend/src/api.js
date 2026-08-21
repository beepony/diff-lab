import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

const ADMIN_TOKEN_KEY = 'diff-lab-admin-token'
const USER_TOKEN_KEY = 'diff-lab-user-token'

const generateUserToken = () => {
  const bytes = new Uint8Array(32)
  crypto.getRandomValues(bytes)
  return Array.from(bytes, byte => byte.toString(16).padStart(2, '0')).join('')
}

const getUserToken = () => {
  let token = localStorage.getItem(USER_TOKEN_KEY)
  if (!/^[0-9a-f]{64}$/.test(token || '')) {
    token = generateUserToken()
    localStorage.setItem(USER_TOKEN_KEY, token)
  }
  return token
}

api.interceptors.request.use((config) => {
  const isPublicShareRequest = config.url?.startsWith('/share/')
  if (!isPublicShareRequest) {
    config.headers.set('X-User-Token', getUserToken())
    const adminToken = sessionStorage.getItem(ADMIN_TOKEN_KEY)
    if (adminToken) {
      config.headers.set('X-Admin-Token', adminToken)
    }
  }
  return config
})

export const getAdminToken = () => sessionStorage.getItem(ADMIN_TOKEN_KEY) || ''
export const setAdminToken = (token) => sessionStorage.setItem(ADMIN_TOKEN_KEY, token.trim())
export const clearAdminToken = () => sessionStorage.removeItem(ADMIN_TOKEN_KEY)
export const verifyAdminToken = () => api.get('/admin/status').then(r => r.data)

// 任务相关
export const createTask = (data) => api.post('/tasks', data).then(r => r.data)
export const listTasks = () => api.get('/tasks').then(r => r.data)
export const getTask = (id) => api.get(`/tasks/${id}`).then(r => r.data)
export const deleteTask = (id) => api.delete(`/tasks/${id}`)
export const getShare = (id) => api.get(`/tasks/${id}/share`).then(r => r.data)
export const createShare = (id, data = {}) => api.post(`/tasks/${id}/share`, data).then(r => r.data)
export const revokeShare = (id) => api.delete(`/tasks/${id}/share`)

// 实时预览（不存 DB）
export const previewDiff = (data) => api.post('/preview', data).then(r => r.data)

// 分享访问
export const accessByToken = (token) => api.get(`/share/${token}`).then(r => r.data)

export const exportCsv = (taskId) => api.get(`/tasks/${taskId}/export`, { responseType: 'blob' })

export default api
