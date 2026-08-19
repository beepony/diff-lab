<script setup>
import { useI18n } from 'vue-i18n'
import { useToast } from '@/composables/useToast'

const { toasts, dismiss } = useToast()
const { t } = useI18n()
</script>

<template>
  <div class="toast-stack" aria-live="polite" aria-atomic="true">
    <TransitionGroup name="toast">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        class="toast"
        :class="toast.tone"
        :role="toast.tone === 'error' ? 'alert' : 'status'"
      >
        <span>{{ toast.message }}</span>
        <button type="button" :aria-label="t('common.close')" @click="dismiss(toast.id)">×</button>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-stack {
  position: fixed;
  right: 20px;
  bottom: 20px;
  z-index: 100;
  display: grid;
  gap: 8px;
  width: min(360px, calc(100vw - 32px));
}
.toast {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid #d6dbe2;
  border-radius: 8px;
  background: white;
  color: #1a1f36;
  box-shadow: 0 10px 26px rgba(26, 31, 54, .16);
  font-size: 13px;
}
.toast.success { border-color: #9ce3c3; }
.toast.error { border-color: #f7bac6; color: #9f1239; }
.toast button {
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font-size: 20px;
  line-height: 16px;
}
.toast-enter-active, .toast-leave-active { transition: all .2s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(8px); }
@media (max-width: 640px) {
  .toast-stack { right: 16px; bottom: 16px; }
}
</style>
