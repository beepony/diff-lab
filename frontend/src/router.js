import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/views/Home.vue'
import TaskDetail from '@/views/TaskDetail.vue'
import ShareView from '@/views/ShareView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Home },
    { path: '/task/:id', component: TaskDetail },
    { path: '/share/:token', component: ShareView },
  ],
})

export default router