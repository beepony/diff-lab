<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { SUPPORTED_LOCALES, setLocale } from '@/i18n'

const { locale } = useI18n()
const open = ref(false)

const current = computed(() =>
  SUPPORTED_LOCALES.find(l => l.code === locale.value) || SUPPORTED_LOCALES[0]
)

function switchTo(code) {
  setLocale(code)
  open.value = false
}

// 点击外部关闭（用 mousedown 抢先避免冒泡冲突）
import { onMounted, onUnmounted } from 'vue'
const root = ref(null)
function handleClickOutside(e) {
  if (root.value && !root.value.contains(e.target)) open.value = false
}
onMounted(() => document.addEventListener('mousedown', handleClickOutside))
onUnmounted(() => document.removeEventListener('mousedown', handleClickOutside))
</script>

<template>
  <div class="lang-switcher" ref="root">
    <button class="lang-btn" @click="open = !open" :title="'Language / 语言'">
      🌐 {{ current.label }}
    </button>
    <div v-if="open" class="lang-menu">
      <button
        v-for="l in SUPPORTED_LOCALES"
        :key="l.code"
        class="lang-option"
        :class="{ active: l.code === locale }"
        @click="switchTo(l.code)"
      >
        {{ l.label }}
        <span v-if="l.code === locale" class="check">✓</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.lang-switcher {
  position: relative;
  display: inline-block;
}
.lang-btn {
  background: rgba(255, 255, 255, 0.15);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  backdrop-filter: blur(10px);
  transition: background 0.15s;
}
.lang-btn:hover {
  background: rgba(255, 255, 255, 0.25);
}
.lang-menu {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  background: white;
  border: 1px solid #e6ebf1;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  min-width: 140px;
  z-index: 100;
  overflow: hidden;
}
.lang-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 8px 14px;
  background: white;
  border: none;
  color: #1a1f36;
  font-size: 13px;
  cursor: pointer;
  text-align: left;
  transition: background 0.1s;
}
.lang-option:hover {
  background: #f6f9fc;
}
.lang-option.active {
  color: #635bff;
  font-weight: 500;
}
.check {
  color: #635bff;
}
</style>