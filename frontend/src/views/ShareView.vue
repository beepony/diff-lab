<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import StepResult from '@/components/StepResult.vue'
import { accessByToken } from '@/api'

const route = useRoute()
const { t } = useI18n()

const task = ref(null)
const loading = ref(true)
const error = ref(null)

const load = async () => {
  try {
    task.value = await accessByToken(route.params.token)
  } catch (e) {
    error.value = e.response?.status === 404 ? t('share.invalidLink') : e.message
  } finally {
    loading.value = false
  }
}

import { getLocale } from '@/i18n'
const formatDate = (iso) => new Date(iso).toLocaleString(getLocale())

onMounted(load)
</script>

<template>
  <div class="page">
    <header class="topbar">
      <div class="badge">{{ t('share.badge') }}</div>
    </header>

    <main class="wrap">
      <div v-if="loading">{{ t('common.loading') }}</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <template v-else-if="task">
        <h1>{{ task.title }}</h1>
        <div class="meta">{{ t('detail.createdAt') }} {{ formatDate(task.created_at) }}</div>
        <section class="result-section">
          <StepResult :result="task.diff_result" />
        </section>
      </template>
    </main>
  </div>
</template>

<style scoped>
.page { min-height: 100vh; background: #f6f9fc; }
.topbar {
  background: white;
  border-bottom: 1px solid #e6ebf1;
  padding: 12px 24px;
}
.badge {
  display: inline-block;
  background: #f4f3ff;
  color: #4f46e5;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}
.wrap {
  max-width: 980px;
  margin: 0 auto;
  padding: 32px 24px;
}
h1 { font-size: 28px; font-weight: 700; margin-bottom: 6px; }
.meta { color: #697386; font-size: 14px; margin-bottom: 24px; }
.result-section {
  background: white;
  border: 1px solid #e6ebf1;
  border-radius: 12px;
  padding: 20px;
}
.error {
  background: #ffe5e9;
  color: #b3093f;
  padding: 16px;
  border-radius: 8px;
}
</style>