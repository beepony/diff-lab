<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import StepImport from '../components/StepImport.vue'
import StepMode from '../components/StepMode.vue'
import StepResult from '../components/StepResult.vue'
import { createTask, previewDiff, listTasks } from '../api'

const router = useRouter()

// 表单状态
const title = ref('')
const columnA = ref('')
const columnB = ref('')
const mode = ref('find_diff')
const options = ref({ ignore_case: false, trim: false, skip_empty: true })

// 结果状态
const previewResult = ref(null)
const saving = ref(false)
const previewing = ref(false)

// 历史
const history = ref([])

const canPreview = computed(() => columnA.value.trim() && columnB.value.trim())
const canSave = computed(() => canPreview.value && title.value.trim())

const loadHistory = async () => {
  try {
    history.value = await listTasks()
  } catch (e) {
    console.error('Failed to load history:', e)
  }
}

const handlePreview = async () => {
  if (!canPreview.value) return
  previewing.value = true
  previewResult.value = null
  try {
    previewResult.value = await previewDiff({
      title: title.value || 'preview',
      mode: mode.value,
      column_a: columnA.value,
      column_b: columnB.value,
      options: options.value,
    })
  } catch (e) {
    alert('预览失败：' + (e.response?.data?.detail || e.message))
  } finally {
    previewing.value = false
  }
}

const handleSave = async () => {
  if (!canSave.value) return
  saving.value = true
  try {
    const task = await createTask({
      title: title.value,
      mode: mode.value,
      column_a: columnA.value,
      column_b: columnB.value,
      options: options.value,
    })
    router.push(`/task/${task.id}`)
  } catch (e) {
    alert('保存失败：' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

const loadDemo = () => {
  title.value = '示例：用户名单核验'
  columnA.value = 'user_10234\nuser_10247\nuser_10258\nuser_10271\nuser_10295'
  columnB.value = 'user_10234\nuser_10258\nuser_10301\nuser_10315\nuser_10322\n\nuser_10348'
}

const formatDate = (iso) => {
  const d = new Date(iso)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const modeName = (m) => ({
  find_diff: '找差异',
  vlookup: 'VLOOKUP',
  intersect: '找交集',
}[m] || m)

onMounted(loadHistory)
</script>

<template>
  <div class="page">
    <!-- Hero -->
    <header class="hero">
      <h1>Diff.lab</h1>
      <p class="sub">两列数据差异对比工具 · 支持历史保存与团队分享</p>
      <div class="actions">
        <button class="btn btn-solid" @click="loadDemo">📋 加载示例</button>
      </div>
    </header>

    <main class="wrap">
      <!-- Step 1: 导入 -->
      <section class="step">
        <div class="step-head">
          <div class="step-num">1</div>
          <div class="step-title">导入数据</div>
        </div>
        <div class="step-body">
          <div class="title-input">
            <label>对比名称（可选，用于保存到历史）</label>
            <input v-model="title" type="text" placeholder="例如：2026-Q3 用户名单核验" />
          </div>
          <div class="dual-input">
            <StepImport v-model="columnA" label="A 列（每行一个值）" placeholder="user_10234&#10;user_10247&#10;..." />
            <StepImport v-model="columnB" label="B 列（每行一个值）" placeholder="user_10234&#10;user_10258&#10;..." />
          </div>
        </div>
      </section>

      <!-- Step 2: 模式 -->
      <section class="step">
        <div class="step-head">
          <div class="step-num">2</div>
          <div class="step-title">选择对比模式</div>
        </div>
        <div class="step-body">
          <StepMode v-model="mode" v-model:options="options" />
        </div>
      </section>

      <!-- Step 3: 结果 -->
      <section class="step">
        <div class="step-head">
          <div class="step-num">3</div>
          <div class="step-title">对比结果</div>
          <div class="step-actions">
            <button class="btn" :disabled="!canPreview || previewing" @click="handlePreview">
              {{ previewing ? '对比中...' : '▶ 预览' }}
            </button>
            <button class="btn btn-primary" :disabled="!canSave || saving" @click="handleSave">
              {{ saving ? '保存中...' : '💾 保存到历史' }}
            </button>
          </div>
        </div>
        <div class="step-body">
          <StepResult v-if="previewResult" :result="previewResult" />
          <div v-else class="empty-hint">
            <p>👆 填写 A/B 两列数据，点击「预览」查看对比结果</p>
          </div>
        </div>
      </section>

      <!-- 历史 -->
      <section v-if="history.length" class="history-strip">
        <h3>最近对比 ({{ history.length }})</h3>
        <div class="history-grid">
          <router-link
            v-for="t in history"
            :key="t.id"
            :to="`/task/${t.id}`"
            class="history-tile"
          >
            <div class="name">{{ t.title }}</div>
            <div class="meta">{{ formatDate(t.created_at) }} · {{ modeName(t.mode) }}</div>
            <div v-if="t.result_meta" class="stats">
              <span v-if="t.result_meta.match" class="stat-match">✓ {{ t.result_meta.match }}</span>
              <span v-if="t.result_meta.diff_a || t.result_meta.diff_b" class="stat-diff">✗ {{ (t.result_meta.diff_a || 0) + (t.result_meta.diff_b || 0) }}</span>
              <span v-if="t.result_meta.intersect" class="stat-match">✓ {{ t.result_meta.intersect }}</span>
            </div>
          </router-link>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  background: #f6f9fc;
}
.hero {
  background: linear-gradient(135deg, #635bff 0%, #4f46e5 100%);
  color: white;
  padding: 48px 32px;
  text-align: center;
}
.hero h1 {
  font-size: 36px;
  font-weight: 700;
  margin-bottom: 8px;
}
.hero .sub {
  opacity: 0.85;
  font-size: 15px;
  margin-bottom: 20px;
}
.hero .btn-solid {
  background: white;
  color: #635bff;
  border: none;
  font-weight: 600;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
}
.wrap {
  max-width: 980px;
  margin: 0 auto;
  padding: 0 24px 80px;
  margin-top: -24px;
}
.step {
  background: white;
  border: 1px solid #e6ebf1;
  border-radius: 12px;
  margin-bottom: 16px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.step-head {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f3f7;
  display: flex;
  align-items: center;
  gap: 12px;
}
.step-num {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #635bff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
}
.step-title {
  font-size: 15px;
  font-weight: 600;
  flex: 1;
}
.step-actions {
  display: flex;
  gap: 8px;
}
.step-body {
  padding: 20px;
}
.title-input {
  margin-bottom: 16px;
}
.title-input label {
  display: block;
  font-size: 13px;
  color: #697386;
  margin-bottom: 6px;
}
.title-input input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d6dbe2;
  border-radius: 6px;
  font-size: 14px;
}
.title-input input:focus {
  outline: none;
  border-color: #635bff;
  box-shadow: 0 0 0 3px rgba(99, 91, 255, 0.1);
}
.dual-input {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.btn {
  background: white;
  border: 1px solid #d6dbe2;
  color: #1a1f36;
  padding: 7px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}
.btn:hover:not(:disabled) {
  background: #f7f7f7;
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-primary {
  background: #635bff;
  border-color: #635bff;
  color: white;
}
.btn-primary:hover:not(:disabled) {
  background: #4f46e5;
}
.empty-hint {
  text-align: center;
  color: #9b9a97;
  padding: 32px;
  font-size: 14px;
}
.history-strip {
  background: white;
  border: 1px solid #e6ebf1;
  border-radius: 12px;
  padding: 16px 20px;
}
.history-strip h3 {
  font-size: 13px;
  color: #697386;
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.history-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}
.history-tile {
  display: block;
  border: 1px solid #e6ebf1;
  border-radius: 8px;
  padding: 12px;
  text-decoration: none;
  color: inherit;
  transition: all 0.15s;
}
.history-tile:hover {
  border-color: #635bff;
  transform: translateY(-2px);
}
.history-tile .name {
  font-weight: 600;
  font-size: 13px;
  margin-bottom: 4px;
}
.history-tile .meta {
  font-size: 11px;
  color: #697386;
  margin-bottom: 8px;
}
.history-tile .stats {
  display: flex;
  gap: 6px;
  font-size: 11px;
}
.stat-match {
  padding: 1px 6px;
  border-radius: 3px;
  background: #d1f4e0;
  color: #0a6b48;
}
.stat-diff {
  padding: 1px 6px;
  border-radius: 3px;
  background: #ffe5e9;
  color: #b3093f;
}
</style>