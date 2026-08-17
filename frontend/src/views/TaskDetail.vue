<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getTask, deleteTask, createShare, exportCsvUrl } from '@/api'

const route = useRoute()
const router = useRouter()
const task = ref(null)
const loading = ref(true)
const shareToken = ref(null)
const copied = ref(false)

const load = async () => {
  loading.value = true
  try {
    const data = await getTask(route.params.id)
    task.value = data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const handleDelete = async () => {
  if (!confirm('确认删除这个对比任务？')) return
  await deleteTask(route.params.id)
  router.push('/')
}

const handleShare = async () => {
  try {
    const r = await createShare(route.params.id)
    shareToken.value = r.token
    const url = `${window.location.origin}/share/${r.token}`
    await navigator.clipboard.writeText(url)
    copied.value = true
    setTimeout(() => (copied.value = false), 2000)
  } catch (e) {
    alert('生成分享链接失败：' + e.message)
  }
}

const handleExport = () => {
  window.open(exportCsvUrl(route.params.id), '_blank')
}

const modeName = (m) => ({
  find_diff: '找差异',
  vlookup: 'VLOOKUP',
  intersect: '找交集',
}[m] || m)

const statusLabel = (s) => ({
  match: '✓ 匹配',
  diff_a: '仅 A',
  diff_b: '仅 B',
  intersect: '✓ 交集',
  match_only: '~ 模糊',
}[s] || s)

const formatDate = (iso) => new Date(iso).toLocaleString('zh-CN')

// 构建双列视图：A 和 B 按行索引并排
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
    // 找该行的状态（按 A 列内容匹配，若 A 为空则用 B）
    let status = 'empty'
    if (aVal !== null) {
      const found = rows.find(r => r.a === aVal && (r.b === bVal || (!bVal && r.status === 'diff_a')))
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

const stats = computed(() => task.value?.result_meta || {})

onMounted(load)
</script>

<template>
  <div class="page">
    <header class="topbar">
      <router-link to="/" class="back">← 返回</router-link>
      <div class="actions">
        <button v-if="task" class="btn" @click="handleShare">
          {{ copied ? '✓ 已复制' : '🔗 生成分享链接' }}
        </button>
        <button v-if="task" class="btn" @click="handleExport">📥 导出 CSV</button>
        <button v-if="task" class="btn btn-danger" @click="handleDelete">🗑 删除</button>
      </div>
    </header>

    <main class="wrap">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="!task" class="error">
        <h2>任务不存在或已删除</h2>
        <router-link to="/" class="btn btn-primary">返回首页</router-link>
      </div>
      <template v-else>
        <header class="task-head">
          <h1>{{ task.title }}</h1>
          <div class="meta">
            创建于 {{ formatDate(task.created_at) }} ·
            模式 <strong>{{ modeName(task.mode) }}</strong> ·
            A <strong>{{ task.column_a.length }}</strong> 行 / B <strong>{{ task.column_b.length }}</strong> 行
          </div>
        </header>

        <!-- 摘要卡片 -->
        <div class="summary">
          <div class="stat total">
            <div class="stat-label">总记录</div>
            <div class="stat-num">{{ stats.total || 0 }}</div>
          </div>
          <div v-if="stats.match" class="stat ok">
            <div class="stat-label">✓ 匹配</div>
            <div class="stat-num">{{ stats.match }}</div>
          </div>
          <div v-if="stats.intersect" class="stat ok">
            <div class="stat-label">✓ 交集</div>
            <div class="stat-num">{{ stats.intersect }}</div>
          </div>
          <div v-if="stats.diff_a || stats.diff_b" class="stat diff">
            <div class="stat-label">✗ 差异</div>
            <div class="stat-num">{{ (stats.diff_a || 0) + (stats.diff_b || 0) }}</div>
          </div>
        </div>

        <!-- 双列并排视图 -->
        <section class="split-section">
          <div class="split-head">
            <h2>双列对比</h2>
            <div class="legend">
              <span class="legend-item ok">✓ 匹配</span>
              <span class="legend-item diff">✗ 差异</span>
              <span class="legend-item empty">— 空值</span>
            </div>
          </div>
          <div class="split">
            <div class="col">
              <div class="col-head">A 列</div>
              <div class="rows">
                <div
                  v-for="r in splitView.left"
                  :key="`a-${r.idx}`"
                  class="row"
                  :class="r.status"
                >
                  <span class="row-num">{{ r.idx }}</span>
                  <span class="row-val">{{ r.value ?? '—' }}</span>
                </div>
              </div>
            </div>
            <div class="col">
              <div class="col-head">B 列</div>
              <div class="rows">
                <div
                  v-for="r in splitView.right"
                  :key="`b-${r.idx}`"
                  class="row"
                  :class="r.status"
                >
                  <span class="row-num">{{ r.idx }}</span>
                  <span class="row-val">{{ r.value ?? '—' }}</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- 单表格视图（备用） -->
        <section class="table-section">
          <h2>逐行详情</h2>
          <table>
            <thead>
              <tr>
                <th style="width: 40px">#</th>
                <th>A 列</th>
                <th>B 列</th>
                <th style="width: 100px">状态</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in task.diff_result.rows" :key="idx">
                <td class="idx">{{ idx + 1 }}</td>
                <td>{{ row.a || '—' }}</td>
                <td>{{ row.b || '—' }}</td>
                <td>
                  <span class="status-badge" :class="row.status">
                    {{ statusLabel(row.status) }}
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