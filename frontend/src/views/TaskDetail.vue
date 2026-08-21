<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { createShare, deleteTask, exportCsv, getShare, getTask, revokeShare } from '@/api'
import AdminAccess from '@/components/AdminAccess.vue'
import StepResult from '@/components/StepResult.vue'
import { useToast } from '@/composables/useToast'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const toast = useToast()

const task = ref(null)
const loading = ref(true)
const shareInfo = ref(null)
const shareExpiryDays = ref(7)
const copied = ref(false)
const loadError = ref('')

const load = async () => {
  loading.value = true
  loadError.value = ''
  try {
    const data = await getTask(route.params.id)
    task.value = data
    shareInfo.value = null
    if (data.can_manage) {
      try {
        shareInfo.value = await getShare(route.params.id)
      } catch (e) {
        if (e.response?.status !== 404) throw e
      }
    }
  } catch (e) {
    loadError.value = e.response?.status === 401
      ? t('auth.accessRequired')
      : e.response?.status === 404
        ? t('detail.notFound')
        : t('alerts.loadFailed')
  } finally {
    loading.value = false
  }
}

const handleDelete = async () => {
  if (!confirm(t('detail.confirmDelete'))) return
  try {
    await deleteTask(route.params.id)
    router.push('/')
  } catch (e) {
    toast.error(`${t('alerts.deleteFailed')}${errorMessage(e, e.message)}`)
  }
}

const errorMessage = (error, fallback) => error.response?.data?.error?.message || error.response?.data?.detail || fallback

const handleShare = async () => {
  try {
    const r = await createShare(route.params.id, { expires_in_days: shareExpiryDays.value })
    shareInfo.value = r
    const url = `${window.location.origin}/share/${r.token}`
    let copiedToClipboard = true
    try {
      await navigator.clipboard.writeText(url)
    } catch {
      copiedToClipboard = false
    }
    copied.value = true
    setTimeout(() => (copied.value = false), 2000)
    toast.success(copiedToClipboard ? t('detail.shareCopied') : t('detail.shareCreated'))
  } catch (e) {
    toast.error(`${t('alerts.shareFailed')}${errorMessage(e, e.message)}`)
  }
}

const handleRevokeShare = async () => {
  if (!confirm(t('detail.confirmRevokeShare'))) return
  try {
    await revokeShare(route.params.id)
    shareInfo.value = null
    toast.success(t('detail.shareRevoked'))
  } catch (e) {
    toast.error(`${t('alerts.shareFailed')}${errorMessage(e, e.message)}`)
  }
}

const handleExport = async () => {
  try {
    const response = await exportCsv(route.params.id)
    const url = URL.createObjectURL(response.data)
    const link = document.createElement('a')
    link.href = url
    link.download = `diff-${route.params.id}.csv`
    link.click()
    URL.revokeObjectURL(url)
    toast.success(t('detail.exportStarted'))
  } catch (e) {
    toast.error(`${t('alerts.exportFailed')}${errorMessage(e, e.message)}`)
  }
}

const formatDate = (iso) => new Date(iso).toLocaleString(i18nLocaleRef.value)

import { getLocale } from '@/i18n'
const i18nLocaleRef = ref(getLocale())

const stats = computed(() => task.value?.result_meta || {})
// 原始输入仅用于审计与定位，不表达跨列匹配关系。
const sourceRows = computed(() => {
  if (!task.value) return { left: [], right: [] }
  const a = task.value.column_a
  const b = task.value.column_b
  const left = []
  const right = []

  for (let i = 0; i < Math.max(a.length, b.length); i++) {
    left.push({ idx: i + 1, value: a[i] ?? null })
    right.push({ idx: i + 1, value: b[i] ?? null })
  }
  return { left, right }
})

onMounted(load)
</script>

<template>
  <div class="page">
    <header class="topbar">
      <router-link to="/" class="back">← {{ t('common.back') }}</router-link>
      <div class="actions">
        <label v-if="task?.can_manage" class="share-expiry">
          {{ t('detail.shareExpiryDays') }}
          <input v-model.number="shareExpiryDays" type="number" min="1" max="90" />
        </label>
        <button v-if="task?.can_manage" class="btn" @click="handleShare">
          {{ copied ? '✓ ' + t('common.copied') : '🔗 ' + t('detail.generateShare') }}
        </button>
        <button v-if="task?.can_manage && shareInfo" class="btn btn-danger" @click="handleRevokeShare">{{ t('detail.revokeShare') }}</button>
        <button v-if="task" class="btn" @click="handleExport">📥 {{ t('detail.exportCsv') }}</button>
        <button v-if="task?.can_manage" class="btn btn-danger" @click="handleDelete">🗑 {{ t('common.delete') }}</button>
        <AdminAccess @changed="load" />
      </div>
    </header>

    <main class="wrap">
      <div v-if="loading" class="loading-skeleton" aria-busy="true">
        <div class="skeleton-heading"></div>
        <div class="skeleton-summary"><span v-for="index in 3" :key="index"></span></div>
        <div class="skeleton-panel"></div>
      </div>
      <div v-else-if="loadError || !task" class="error">
        <h2>{{ loadError || t('detail.notFound') }}</h2>
        <button class="btn" type="button" @click="load">{{ t('common.retry') }}</button>
        <router-link to="/" class="btn btn-primary">{{ t('detail.backHome') }}</router-link>
      </div>
      <template v-else>
        <header class="task-head">
          <h1>{{ task.title }}</h1>
          <div class="meta">
            {{ t('detail.createdAt') }} {{ formatDate(task.created_at) }} ·
            {{ t(`modes.${task.mode}.name`) }} ·
            A <strong>{{ task.column_a.length }}</strong> / B <strong>{{ task.column_b.length }}</strong>
          </div>
          <div v-if="shareInfo" class="share-meta">
            {{ t('detail.shareExpiresAt') }} {{ formatDate(shareInfo.expires_at) }}
          </div>
        </header>

        <!-- 摘要卡片 -->
        <div class="summary">
          <div class="stat total">
            <div class="stat-label">{{ t('summary.total') }}</div>
            <div class="stat-num">{{ stats.total || 0 }}</div>
          </div>
          <div v-if="stats.match" class="stat ok">
            <div class="stat-label">{{ t('summary.match') }}</div>
            <div class="stat-num">{{ stats.match }}</div>
          </div>
          <div v-if="stats.intersect" class="stat ok">
            <div class="stat-label">{{ t('summary.intersect') }}</div>
            <div class="stat-num">{{ stats.intersect }}</div>
          </div>
          <div v-if="stats.diff_a || stats.diff_b" class="stat diff">
            <div class="stat-label">{{ t('summary.diff') }}</div>
            <div class="stat-num">{{ (stats.diff_a || 0) + (stats.diff_b || 0) }}</div>
          </div>
        </div>

        <section class="result-section">
          <h2>{{ t('detail.resultView') }}</h2>
          <StepResult :result="task.diff_result" />
        </section>

        <details class="source-data">
          <summary>{{ t('detail.sourceData') }}</summary>
          <p>{{ t('detail.sourceDataHint') }}</p>
          <div class="source-grid">
            <div class="source-column">
              <div class="col-head">{{ t('detail.colA') }}</div>
              <div class="rows">
                <div v-for="r in sourceRows.left" :key="`a-${r.idx}`" class="row">
                  <span class="row-num">{{ r.idx }}</span>
                  <span class="row-val">{{ r.value ?? t('detail.emptyValue') }}</span>
                </div>
              </div>
            </div>
            <div class="source-column">
              <div class="col-head">{{ t('detail.colB') }}</div>
              <div class="rows">
                <div v-for="r in sourceRows.right" :key="`b-${r.idx}`" class="row">
                  <span class="row-num">{{ r.idx }}</span>
                  <span class="row-val">{{ r.value ?? t('detail.emptyValue') }}</span>
                </div>
              </div>
            </div>
          </div>
        </details>
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
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky; top: 0; z-index: 10;
}
.back { color: #635bff; text-decoration: none; font-size: 14px; font-weight: 500; }
.actions { display: flex; gap: 8px; }
.share-expiry { display: inline-flex; align-items: center; gap: 5px; color: #697386; font-size: 12px; }
.share-expiry input { width: 46px; padding: 6px; border: 1px solid #d6dbe2; border-radius: 5px; }
.btn {
  background: white;
  border: 1px solid #d6dbe2;
  color: #1a1f36;
  padding: 7px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  text-decoration: none;
  display: inline-flex; align-items: center;
}
.btn:hover { background: #f7f7f7; }
.btn-danger { color: #b3093f; border-color: #fbd0d6; }
.btn-danger:hover { background: #fff0f2; }
.btn-primary { background: #635bff; border-color: #635bff; color: white; }
.wrap {
  max-width: 1100px;
  margin: 0 auto;
  padding: 32px 24px 80px;
}
.loading-skeleton { padding: 32px 0; }
.skeleton-heading, .skeleton-summary span, .skeleton-panel { display: block; background: linear-gradient(90deg, #edf1f5 25%, #f8fafc 37%, #edf1f5 63%); background-size: 400% 100%; animation: shimmer 1.4s ease infinite; }
.skeleton-heading { width: 240px; height: 32px; border-radius: 6px; margin-bottom: 32px; }
.skeleton-summary { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 24px; }
.skeleton-summary span { height: 96px; border-radius: 8px; }
.skeleton-panel { height: 300px; border-radius: 12px; }
.error { display: flex; align-items: center; justify-content: center; flex-wrap: wrap; gap: 12px; text-align: center; padding: 64px 0; color: #697386; }
.error h2 { width: 100%; margin-bottom: 4px; }
@keyframes shimmer { to { background-position: -400% 0; } }
.task-head { margin-bottom: 24px; }
h1 { font-size: 28px; font-weight: 700; margin-bottom: 6px; }
.meta { color: #697386; font-size: 14px; }
.share-meta { margin-top: 4px; color: #697386; font-size: 12px; }
.meta strong { color: #1a1f36; }

.summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}
.stat {
  background: white;
  border: 1px solid #e6ebf1;
  border-radius: 8px;
  padding: 16px;
}
.stat-label { font-size: 12px; color: #697386; margin-bottom: 6px; }
.stat-num { font-size: 28px; font-weight: 700; }
.stat.ok { border-left: 3px solid #0fb27a; }
.stat.ok .stat-num { color: #0fb27a; }
.stat.diff { border-left: 3px solid #e03e3e; }
.stat.diff .stat-num { color: #e03e3e; }
.stat.total { border-left: 3px solid #635bff; }

.result-section, .source-data {
  background: white;
  border: 1px solid #e6ebf1;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
}
h2 { font-size: 15px; font-weight: 600; }
.result-section h2 { margin-bottom: 16px; }
.source-data { padding: 0; overflow: hidden; }
.source-data summary { padding: 16px 20px; cursor: pointer; font-size: 14px; font-weight: 600; }
.source-data > p { padding: 0 20px 16px; color: #697386; font-size: 12px; }
.source-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; background: #e6ebf1; }
.source-column { background: white; }
.col-head {
  padding: 10px 14px;
  font-weight: 600; font-size: 13px;
  background: #f6f9fc;
  border-bottom: 1px solid #e6ebf1;
}
.rows { max-height: 460px; overflow-y: auto; }
.row {
  display: flex; align-items: center;
  padding: 7px 14px;
  border-bottom: 1px solid #f4f4f4;
  font-family: "SF Mono", Menlo, monospace;
  font-size: 13px;
}
.row-num { color: #c8c8c8; font-size: 11px; width: 36px; }
.row-val { flex: 1; }
.row.empty .row-val { color: #c8c8c8; font-style: italic; }
@media (max-width: 640px) {
  .topbar {
    align-items: flex-start;
    flex-wrap: wrap;
    padding: 10px 16px;
    gap: 10px;
  }
  .back { padding: 8px 0; }
  .actions {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    width: 100%;
  }
  .actions > * { min-width: 0; }
  .actions .btn, .actions :deep(.trigger) { justify-content: center; min-height: 38px; }
  .share-expiry { grid-column: 1 / -1; justify-content: center; }
  .actions > .btn-danger:last-of-type { grid-column: 1 / -1; }
  .actions :deep(.admin-access) { grid-column: 1 / -1; }
  .actions :deep(.panel) { left: 0; right: auto; width: min(260px, 100%); }
  .wrap { padding: 24px 16px 48px; }
  h1 { font-size: 24px; line-height: 1.3; }
  .meta { font-size: 13px; }
  .summary { grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
  .skeleton-summary { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .stat { padding: 12px; }
  .stat-num { font-size: 24px; }
  .result-section { padding: 16px; }
  .source-data summary { padding: 16px; }
  .source-data > p { padding: 0 16px 16px; }
  .row { padding: 7px 8px; }
  .row-num { width: 28px; }
  .row-val { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
}
</style>
