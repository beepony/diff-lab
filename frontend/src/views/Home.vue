<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import StepImport from '@/components/StepImport.vue'
import StepMode from '@/components/StepMode.vue'
import StepResult from '@/components/StepResult.vue'
import LanguageSwitcher from '@/components/LanguageSwitcher.vue'
import AdminAccess from '@/components/AdminAccess.vue'
import { createTask, previewDiff, listTasks } from '@/api'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const { t, locale } = useI18n()
const toast = useToast()

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
const historyLoading = ref(true)
const historyError = ref('')

const canPreview = computed(() => columnA.value.trim() && columnB.value.trim())
const canSave = computed(() => canPreview.value)

const loadHistory = async () => {
  historyLoading.value = true
  historyError.value = ''
  try {
    history.value = await listTasks()
  } catch (e) {
    historyError.value = e.response?.status === 401 ? t('auth.historyRequired') : t('alerts.loadFailed')
  } finally {
    historyLoading.value = false
  }
}

const errorMessage = (error, fallback) => error.response?.data?.error?.message || error.response?.data?.detail || fallback

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
    toast.error(`${t('alerts.previewFailed')}${errorMessage(e, e.message)}`)
  } finally {
    previewing.value = false
  }
}

const handleSave = async () => {
  if (!canSave.value) return
  saving.value = true
  try {
    const task = await createTask({
      title: title.value.trim() || t('home.defaultTitle'),
      mode: mode.value,
      column_a: columnA.value,
      column_b: columnB.value,
      options: options.value,
    })
    router.push(`/task/${task.id}`)
  } catch (e) {
    toast.error(`${t('alerts.saveFailed')}${errorMessage(e, e.message)}`)
  } finally {
    saving.value = false
  }
}

const loadDemo = () => {
  title.value = locale.value === 'zh-CN' ? '示例：用户名单核验' : 'Demo: User List Verification'
  columnA.value = 'user_10234\nuser_10247\nuser_10258\nuser_10271\nuser_10295'
  columnB.value = 'user_10234\nuser_10258\nuser_10301\nuser_10315\nuser_10322\n\nuser_10348'
}

const formatDate = (iso) => {
  const d = new Date(iso)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const modeName = (m) => t(`modes.${m}.name`)

onMounted(loadHistory)
</script>

<template>
  <div class="page">
    <!-- Hero -->
    <header class="hero">
      <h1>{{ t('app.name') }}</h1>
      <p class="sub">{{ t('app.tagline') }} · {{ t('app.description') }}</p>
      <div class="actions">
        <button class="btn btn-solid" @click="loadDemo">📋 {{ t('app.loadDemo') }}</button>
        <LanguageSwitcher />
        <AdminAccess />
      </div>
    </header>

    <main class="wrap">
      <!-- Step 1: 导入 -->
      <section class="step">
        <div class="step-head">
          <div class="step-num">1</div>
          <div class="step-title">{{ t('home.stepImport') }}</div>
        </div>
        <div class="step-body">
          <div class="title-input">
            <label>{{ t('home.titleLabel') }}</label>
            <input v-model="title" type="text" :placeholder="t('home.titlePlaceholder')" />
          </div>
          <div class="dual-input">
            <StepImport v-model="columnA" :label="'input.columnA'" />
            <StepImport v-model="columnB" :label="'input.columnB'" />
          </div>
        </div>
      </section>

      <!-- Step 2: 模式 -->
      <section class="step">
        <div class="step-head">
          <div class="step-num">2</div>
          <div class="step-title">{{ t('home.stepMode') }}</div>
        </div>
        <div class="step-body">
          <StepMode v-model="mode" v-model:options="options" />
        </div>
      </section>

      <!-- Step 3: 结果 -->
      <section class="step">
        <div class="step-head">
          <div class="step-num">3</div>
          <div class="step-title">{{ t('home.stepResult') }}</div>
          <div class="step-actions">
            <button class="btn" :disabled="!canPreview || previewing" @click="handlePreview">
              {{ previewing ? t('home.previewing') : '▶ ' + t('home.preview') }}
            </button>
            <button class="btn btn-primary" :disabled="!canSave || saving" @click="handleSave">
              {{ saving ? t('home.saving') : '💾 ' + t('home.saveToHistory') }}
            </button>
          </div>
        </div>
        <div class="step-body">
          <StepResult v-if="previewResult" :result="previewResult" />
          <div v-else class="empty-hint">
            <p>{{ t('home.emptyHint') }}</p>
          </div>
        </div>
      </section>

      <!-- 历史 -->
      <section v-if="historyLoading" class="history-strip history-loading" aria-busy="true">
        <div class="skeleton-title"></div>
        <div class="skeleton-grid">
          <div v-for="index in 3" :key="index" class="skeleton-card"></div>
        </div>
      </section>
      <section v-else-if="historyError" class="history-strip recoverable-state">
        <p>{{ historyError }}</p>
        <button class="btn" type="button" @click="loadHistory">{{ t('common.retry') }}</button>
      </section>
      <section v-else-if="history.length" class="history-strip">
        <h3>{{ t('home.historyCount', { count: history.length }) }}</h3>
        <div class="history-grid">
          <router-link
            v-for="t_item in history"
            :key="t_item.id"
            :to="`/task/${t_item.id}`"
            class="history-tile"
          >
            <div class="name">{{ t_item.title }}</div>
            <div class="meta">
              {{ formatDate(t_item.created_at) }} ·
              A {{ t_item.column_a_count ?? '—' }} / B {{ t_item.column_b_count ?? '—' }} {{ t('history.rows') }} ·
              {{ modeName(t_item.mode) }}
            </div>
            <div v-if="t_item.result_meta" class="stats">
              <span v-if="t_item.result_meta.match" class="stat-match">✓ {{ t_item.result_meta.match }}</span>
              <span v-if="(t_item.result_meta.diff_a || 0) + (t_item.result_meta.diff_b || 0)" class="stat-diff">✗ {{ (t_item.result_meta.diff_a || 0) + (t_item.result_meta.diff_b || 0) }}</span>
              <span v-if="t_item.result_meta.intersect" class="stat-match">✓ {{ t_item.result_meta.intersect }}</span>
            </div>
          </router-link>
        </div>
      </section>
      <section v-else class="history-strip history-empty">
        <h3>{{ t('home.historyCount', { count: 0 }) }}</h3>
        <p>{{ t('home.historyEmpty') }}</p>
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
.hero .actions {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
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
.history-loading { min-height: 132px; }
.skeleton-title, .skeleton-card { background: linear-gradient(90deg, #f1f4f7 25%, #f8fafc 37%, #f1f4f7 63%); background-size: 400% 100%; animation: shimmer 1.4s ease infinite; }
.skeleton-title { width: 120px; height: 14px; border-radius: 4px; margin-bottom: 14px; }
.skeleton-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.skeleton-card { height: 66px; border-radius: 8px; }
.recoverable-state, .history-empty { color: #697386; font-size: 14px; }
.recoverable-state { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.history-empty p { padding-top: 2px; }
@keyframes shimmer { to { background-position: -400% 0; } }
@media (max-width: 640px) {
  .hero { padding: 36px 16px 44px; }
  .hero h1 { font-size: 30px; }
  .hero .sub { font-size: 14px; }
  .wrap { padding: 0 16px 48px; margin-top: -20px; }
  .step-head { flex-wrap: wrap; padding: 14px 16px; }
  .step-actions { width: 100%; margin-left: 40px; }
  .step-actions .btn { flex: 1; }
  .step-body { padding: 16px; }
  .dual-input { grid-template-columns: 1fr; gap: 12px; }
  .history-grid { grid-template-columns: 1fr; }
  .skeleton-grid { grid-template-columns: 1fr; }
  .recoverable-state { align-items: flex-start; flex-direction: column; }
}
</style>
