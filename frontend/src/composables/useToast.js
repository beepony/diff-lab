import { readonly, ref } from 'vue'

const items = ref([])
let nextId = 1

export function useToast() {
  const dismiss = (id) => {
    items.value = items.value.filter(item => item.id !== id)
  }

  const show = (message, tone = 'info') => {
    const id = nextId++
    items.value.push({ id, message, tone })
    window.setTimeout(() => dismiss(id), tone === 'error' ? 6000 : 3500)
  }

  return {
    toasts: readonly(items),
    dismiss,
    success: (message) => show(message, 'success'),
    error: (message) => show(message, 'error'),
    info: (message) => show(message, 'info'),
  }
}
