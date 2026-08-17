import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

// 任务相关
export const createTask = (data) => api.post('/tasks', data).then(r => r.data)
export const listTasks = () => api.get('/tasks').then(r => r.data)
export const getTask = (id) => api.get(`/tasks/${id}`).then(r => r.data)
export const deleteTask = (id) => api.delete(`/tasks/${id}`)
export const createShare = (id) => api.post(`/tasks/${id}/share`).then(r => r.data)

// 实时预览（不存 DB）
export const previewDiff = (data) => api.post('/preview', data).then(r => r.data)

// 分享访问
export const accessByToken = (token) => api.get(`/share/${token}`).then(r => r.data)

// 导出 CSV（直接返回 blob URL）
export const exportCsvUrl = (taskId) => `${api.defaults.baseURL}/tasks/${taskId}/export`

export default api