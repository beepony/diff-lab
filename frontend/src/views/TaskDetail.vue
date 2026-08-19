<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { createShare, deleteTask, exportCsv, getShare, getTask, revokeShare } from '@/api'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const task = ref(null)
const loading = ref(true)
const shareInfo = ref(null)
const shareExpiryDays = ref(7)
const copied = ref(false)

const load = async () => {
  loading.value = true
  try {
    const data = await getTask(route.params.id)
    task.value = data
    try {
      shareInfo.value = await getShare(route.params.id)
    } catch (e) {
      if (e.response?.status !== 404) throw e
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const handleDelete = async () => {
  if (!confirm(t('detail.confirmDelete'))) return
  await deleteTask(route.params.id)
  router.push('/')
}

const handleShare = async () => {
  try {
    const r = await createShare(route.params.id, { expires_in_days: shareExpiryDays.value })
    shareInfo.value = r
    const url = `${window.location.origin}/share/${r.token}`
    await navigator.clipboard.writeText(url)
    copied.value = true
    setTimeout(() => (copied.value = false), 2000)
  } catch (e) {
    alert(t('alerts.shareFailed') + e.message)
  }
}

const handleRevokeShare = async () => {
  if (!confirm(t('detail.confirmRevokeShare'))) return
  try {
    await revokeShare(route.params.id)
    shareInfo.value = null
  } catch (e) {
    alert(t('alerts.shareFailed') + (e.response?.data?.detail || e.message))
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
  } catch (e) {
    alert(t('alerts.exportFailed') + (e.response?.data?.detail || e.message))
  }
}

const formatDate = (iso) => new Date(iso).toLocaleString(i18nLocaleRef.value)

import { getLocale } from '@/i18n'
const i18nLocaleRef = ref(getLocale())

const stats = computed(() => task.value?.result_meta || {})
const displayValue = (value) => value === null || value === undefined ? t('detail.emptyValue') : value

// 构建双列视图
const splitView = computed(() => {
  if (!task.value) return { left: [], right: [] }
  const a = task.value.column_a
  const b = task.value.column_b
  const rows = task.value.diff_result.rows
  const left = []
  const right = []

  for (let i = 0; i < Math.max(a.length, b.length); i++) {
    const aVal = a[i] ?? null
    const bVal = b[i] ?? null
    let status = 'empty'
    if (aVal !== null) {
      const found = rows.find(r => r.a === aVal && (r.b === bVal || (bVal === null && r.status === 'diff_a')))
      status = found?.status || 'empty'
    } else if (bVal !== null) {
      const found = rows.find(r => r.b === bVal && r.status === 'diff_b')
      status = found?.status || 'empty'
    }
    left.push({ idx: i + 1, value: aVal, status })
    right.push({ idx: i + 1, value: bVal, status })
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
        <label v-if="task" class="share-expiry">
          {{ t('detail.shareExpiryDays') }}
          <input v-model.number="shareExpiryDays" type="number" min="1" max="90" />
        </label>
        <button v-if="task" class="btn" @click="handleShare">
          {{ copied ? '✓ ' + t('common.copied') : '🔗 ' + t('detail.generateShare') }}
        </button>
        <button v-if="shareInfo" class="btn btn-danger" @click="handleRevokeShare">{{ t('detail.revokeShare') }}</button>
        <button v-if="task" class="btn" @click="handleExport">📥 {{ t('detail.exportCsv') }}</button>
        <button v-if="task" class="btn btn-danger" @click="handleDelete">🗑 {{ t('common.delete') }}</button>
      </div>
    </header>

    <main class="wrap">
      <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
      <div v-else-if="!task" class="error">
        <h2>{{ t('detail.notFound') }}</h2>
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

        <!-- 双列并排视图 -->
        <section class="split-section">
          <div class="split-head">
            <h2>{{ t('detail.splitView') }}</h2>
            <div class="legend">
              <span class="legend-item ok">{{ t('detail.legendMatch') }}</span>
              <span class="legend-item diff">{{ t('detail.legendDiff') }}</span>
              <span class="legend-item empty">{{ t('detail.legendEmpty') }}</span>
            </div>
          </div>
          <div class="split">
            <div class="col">
              <div class="col-head">{{ t('detail.colA') }}</div>
              <div class="rows">
                <div
                  v-for="r in splitView.left"
                  :key="`a-${r.idx}`"
                  class="row"
                  :class="r.status"
                >
                  <span class="row-num">{{ r.idx }}</span>
                  <span class="row-val">{{ r.value ?? t('detail.emptyValue') }}</span>
                </div>
              </div>
            </div>
            <div class="col">
              <div class="col-head">{{ t('detail.colB') }}</div>
              <div class="rows">
                <div
                  v-for="r in splitView.right"
                  :key="`b-${r.idx}`"
                  class="row"
                  :class="r.status"
                >
                  <span class="row-num">{{ r.idx }}</span>
                  <span class="row-val">{{ r.value ?? t('detail.emptyValue') }}</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- 单表格视图 -->
        <section class="table-section">
          <h2>{{ t('detail.tableView') }}</h2>
          <table>
            <thead>
              <tr>
                <th style="width: 40px">#</th>
                <th>{{ t('result.headerA') }}</th>
                <th>{{ t('result.headerB') }}</th>
                <th style="width: 100px">{{ t('result.status') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in task.diff_result.rows" :key="idx">
                <td class="idx">{{ idx + 1 }}</td>
                <td>{{ displayValue(row.a) }}</td>
                <td>{{ displayValue(row.b) }}</td>
                <td>
                  <span class="status-badge" :class="row.status">
                    {{ t(`status.${row.status}`) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
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
.loading, .error { text-align: center; padding: 64px 0; color: #697386; }
.error h2 { margin-bottom: 16px; }
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

.split-section, .table-section {
  background: white;
  border: 1px solid #e6ebf1;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
}
.split-head {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 12px;
}
h2 { font-size: 15px; font-weight: 600; }
.legend { display: flex; gap: 8px; }
.legend-item {
  padding: 2px 8px; border-radius: 10px; font-size: 11px;
}
.legend-item.ok { background: #d1f4e0; color: #0a6b48; }
.legend-item.diff { background: #ffe5e9; color: #b3093f; }
.legend-item.empty { background: #f0f3f7; color: #697386; }

.split { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; background: #e6ebf1; border-radius: 8px; overflow: hidden; }
.col { background: white; }
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
.row.match { background: #f0faf5; }
.row.diff_a, .row.diff_b { background: #fdf3f3; }
.row.intersect { background: #f0faf5; }
.row.empty .row-val { color: #c8c8c8; font-style: italic; }

table { width: 100%; border-collapse: collapse; font-size: 13px; }
th {
  text-align: left; padding: 10px 12px;
  background: #f6f9fc; color: #697386;
  font-size: 12px; font-weight: 600;
  border-bottom: 1px solid #e6ebf1;
}
td {
  padding: 10px 12px; border-bottom: 1px solid #f0f3f7;
  font-family: "SF Mono", Menlo, monospace;
}
.idx { color: #c8c8c8; }
tr:hover td { background: #fafbfc; }
.status-badge {
  display: inline-block; padding: 2px 8px; border-radius: 10px;
  font-size: 11px; font-weight: 500;
}
.status-badge.match, .status-badge.intersect { background: #d1f4e0; color: #0a6b48; }
.status-badge.diff_a, .status-badge.diff_b { background: #ffe5e9; color: #b3093f; }
</style>
