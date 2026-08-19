import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

const ADMIN_TOKEN_KEY = 'diff-lab-admin-token'

api.interceptors.request.use((config) => {
  const isPublicShareRequest = config.url?.startsWith('/share/')
  const token = sessionStorage.getItem(ADMIN_TOKEN_KEY)
  if (token && !isPublicShareRequest) {
    config.headers.set('X-Admin-Token', token)
  }
  return config
})

export const getAdminToken = () => sessionStorage.getItem(ADMIN_TOKEN_KEY) || ''
export const setAdminToken = (token) => sessionStorage.setItem(ADMIN_TOKEN_KEY, token.trim())
export const clearAdminToken = () => sessionStorage.removeItem(ADMIN_TOKEN_KEY)

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
