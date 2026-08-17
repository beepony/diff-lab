import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import i18n from './i18n'

createApp(App).use(router).use(i18n).mount('#app')

// 同步 html lang 属性（用于浏览器字体/无障碍工具）
document.documentElement.lang = i18n.global.locale.value