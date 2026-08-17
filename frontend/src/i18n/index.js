/**
 * i18n 配置：基于浏览器语言自动选择 + localStorage 持久化用户偏好。
 * 自动检测顺序：localStorage > navigator.language > 默认 zh-CN。
 */
import { createI18n } from 'vue-i18n'
import zhCN from './locales/zh-CN.json'
import enUS from './locales/en-US.json'

const STORAGE_KEY = 'diff-lab-lang'

/**
 * 探测浏览器语言 → 返回支持的语言代码。
 * 输入: navigator.language (如 "zh-CN", "en-US", "ja-JP")
 * 输出: "zh-CN" | "en-US"
 */
function detectLocale() {
  // 1. 用户偏好
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored && ['zh-CN', 'en-US'].includes(stored)) {
    return stored
  }
  // 2. 浏览器语言
  const browser = navigator.language || navigator.userLanguage || ''
  if (browser.startsWith('en')) return 'en-US'
  if (browser.startsWith('zh')) return 'zh-CN'
  // 3. 默认中文
  return 'zh-CN'
}

export const SUPPORTED_LOCALES = [
  { code: 'zh-CN', label: '中文' },
  { code: 'en-US', label: 'English' },
]

const i18n = createI18n({
  legacy: false,  // Composition API 模式
  locale: detectLocale(),
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS,
  },
})

/** 切换语言并持久化（全局方法）。 */
export function setLocale(locale) {
  i18n.global.locale.value = locale
  localStorage.setItem(STORAGE_KEY, locale)
  document.documentElement.lang = locale
}

/** 获取当前语言。 */
export function getLocale() {
  return i18n.global.locale.value
}

export default i18n