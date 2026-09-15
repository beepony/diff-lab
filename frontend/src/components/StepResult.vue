<script setup>
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from '@/composables/useToast'
import { formatColumnForClipboard, resultColumnValues } from '@/utils/resultClipboard'
const { t } = useI18n()
const toast = useToast()

const props = defineProps({
  result: Object,  // { rows, summary }
})

const activeStatus = ref('all')
const search = ref('')
const page = ref(1)
const pageSize = ref(25)

const statusOptions = computed(() => {
  const statuses = ['match', 'intersect', 'diff_a', 'diff_b', 'match_only']
  const rows = props.result?.rows || []
  return [
    { key: 'all', label: t('result.filterAll'), count: rows.length },
    ...statuses
      .map(key => ({ key, label: statusLabel(key), count: rows.filter(row => row.status === key).length }))
      .filter(option => option.count > 0),
  ]
})

const filteredRows = computed(() => {
  const keyword = search.value.trim().toLocaleLowerCase()
  return (props.result?.rows || []).map((row, index) => ({ ...row, resultIndex: index + 1 })).filter((row) => {
    const statusMatches = activeStatus.value === 'all' || row.status === activeStatus.value
    const textMatches = !keyword || [row.a, row.b]
      .filter(value => value !== null && value !== undefined)
      .some(value => String(value).toLocaleLowerCase().includes(keyword))
    return statusMatches && textMatches
  })
})

const pageCount = computed(() => Math.max(1, Math.ceil(filteredRows.value.length / pageSize.value)))
const visibleRows = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filteredRows.value.slice(start, start + pageSize.value)
})
const columnValues = computed(() => ({
  a: resultColumnValues(filteredRows.value, 'a'),
  b: resultColumnValues(filteredRows.value, 'b'),
}))

watch([activeStatus, search, pageSize], () => { page.value = 1 })
watch(pageCount, (count) => { if (page.value > count) page.value = count })

function statusLabel(s) {
  return t(`status.${s}`)
}

function displayValue(value) {
  return value === null || value === undefined ? '—' : value
}

async function copyColumn(column) {
  const values = columnValues.value[column]
  if (!values.length) return
  const text = formatColumnForClipboard(values)

  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
    } else {
      const input = document.createElement('textarea')
      input.value = text
      input.style.position = 'fixed'
      input.style.opacity = '0'
      document.body.appendChild(input)
      try {
        input.select()
        if (!document.execCommand('copy')) throw new Error('Clipboard unavailable')
      } finally {
        input.remove()
      }
    }
    toast.success(t('result.copyColumnSuccess', { column: t(`result.header${column.toUpperCase()}`), count: values.length }))
  } catch {
    toast.error(t('result.copyFailed'))
  }
}
</script>

<template>
  <div v-if="result" class="step-result">
    <div class="result-meta">
      <span>{{ t('result.total') }} <strong>{{ result.summary.total }}</strong></span>
      <span v-if="result.summary.match" class="green">{{ t('result.match') }} {{ result.summary.match }}</span>
      <span v-if="result.summary.intersect" class="green">{{ t('result.intersect') }} {{ result.summary.intersect }}</span>
      <span v-if="(result.summary.diff_a || 0) + (result.summary.diff_b || 0)" class="red">
        {{ t('result.diff') }} {{ (result.summary.diff_a || 0) + (result.summary.diff_b || 0) }}
      </span>
      <span class="meta-time">{{ t('result.duration') }} {{ result.summary.duration_ms }}{{ t('result.ms') }}</span>
    </div>

    <div class="result-tools">
      <label class="search-field">
        <span class="sr-only">{{ t('result.searchLabel') }}</span>
        <input v-model="search" type="search" :placeholder="t('result.searchPlaceholder')" />
      </label>
      <div class="filter-list" :aria-label="t('result.filterLabel')">
        <button
          v-for="option in statusOptions"
          :key="option.key"
          type="button"
          class="filter-chip"
          :class="{ active: activeStatus === option.key }"
          :aria-pressed="activeStatus === option.key"
          @click="activeStatus = option.key"
        >
          {{ option.label }} <span>{{ option.count }}</span>
        </button>
      </div>
    </div>

    <div class="result-list-meta">
      {{ t('result.shown', { shown: visibleRows.length, total: filteredRows.length }) }}
    </div>

    <div class="table-scroll" tabindex="0" :aria-label="t('result.tableLabel')">
      <table>
        <thead>
          <tr>
            <th style="width: 64px">#</th>
            <th>
              <div class="column-heading">
                <span>{{ t('result.headerA') }}</span>
                <button type="button" class="column-copy-button" :disabled="!columnValues.a.length"
                  :aria-label="t('result.copyColumnAria', { column: t('result.headerA'), count: columnValues.a.length })"
                  @click="copyColumn('a')">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                    <rect x="8" y="8" width="13" height="13" rx="2" />
                    <path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3" />
                  </svg>
                </button>
              </div>
            </th>
            <th>
              <div class="column-heading">
                <span>{{ t('result.headerB') }}</span>
                <button type="button" class="column-copy-button" :disabled="!columnValues.b.length"
                  :aria-label="t('result.copyColumnAria', { column: t('result.headerB'), count: columnValues.b.length })"
                  @click="copyColumn('b')">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                    <rect x="8" y="8" width="13" height="13" rx="2" />
                    <path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3" />
                  </svg>
                </button>
              </div>
            </th>
            <th style="width: 120px">{{ t('result.status') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in visibleRows" :key="`${row.resultIndex}-${row.status}`">
            <td class="idx">{{ row.resultIndex }}</td>
            <td>{{ displayValue(row.a) }}</td>
            <td>{{ displayValue(row.b) }}</td>
            <td>
              <span class="status-badge" :class="row.status">
                {{ statusLabel(row.status) }}
              </span>
            </td>
          </tr>
          <tr v-if="!visibleRows.length">
            <td colspan="4" class="empty">{{ search || activeStatus !== 'all' ? t('result.noMatch') : t('result.noData') }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="filteredRows.length" class="pagination">
      <label class="page-size">
        {{ t('result.pageSize') }}
        <select v-model.number="pageSize">
          <option :value="25">25</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
        </select>
      </label>
      <div class="page-actions">
        <button type="button" class="page-button" :disabled="page === 1" @click="page -= 1">{{ t('result.previous') }}</button>
        <span>{{ t('result.pageInfo', { page, totalPages: pageCount }) }}</span>
        <button type="button" class="page-button" :disabled="page === pageCount" @click="page += 1">{{ t('result.next') }}</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.result-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  font-size: 13px;
  align-items: center;
}
.result-meta strong { color: #1a1f36; }
.result-meta .green { color: #0fb27a; }
.result-meta .orange { color: #ff8a00; }
.result-meta .red { color: #e5294a; }
.result-meta .meta-time {
  margin-left: auto;
  color: #9b9a97;
  font-size: 12px;
}
.result-tools {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}
.search-field { flex: 0 1 260px; }
.search-field input {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #d6dbe2;
  border-radius: 6px;
  font: inherit;
}
.search-field input:focus { outline: none; border-color: #635bff; box-shadow: 0 0 0 3px rgba(99, 91, 255, .12); }
.filter-list { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 6px; }
.filter-chip, .page-button, .page-size select {
  border: 1px solid #d6dbe2;
  border-radius: 6px;
  background: white;
  color: #4c566a;
  font: inherit;
  font-size: 12px;
}
.filter-chip { padding: 6px 9px; cursor: pointer; }
.filter-chip span { color: #697386; margin-left: 3px; }
.filter-chip.active { border-color: #635bff; background: #f4f3ff; color: #4f46e5; font-weight: 600; }
.result-list-meta { color: #697386; font-size: 12px; margin-bottom: 8px; }
.column-heading { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.column-copy-button { display: inline-flex; align-items: center; justify-content: center; flex: 0 0 26px; width: 26px; height: 26px; padding: 5px; border: 0; border-radius: 5px; background: transparent; color: #697386; cursor: pointer; }
.column-copy-button svg { width: 16px; height: 16px; }
.column-copy-button:hover:not(:disabled) { background: #e9e7ff; color: #4f46e5; }
.column-copy-button:focus-visible { outline: 2px solid #635bff; outline-offset: 2px; }
.column-copy-button:disabled { opacity: .45; cursor: default; }
.table-scroll { overflow-x: auto; }
table {
  min-width: 620px;
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
th {
  text-align: left;
  padding: 10px 12px;
  background: #f6f9fc;
  color: #697386;
  font-size: 12px;
  font-weight: 600;
  border-bottom: 1px solid #e6ebf1;
}
td {
  padding: 10px 12px;
  border-bottom: 1px solid #f0f3f7;
  font-family: "SF Mono", Menlo, monospace;
}
.idx { color: #c8c8c8; }
tr:hover td { background: #fafbfc; }
.empty { text-align: center; color: #9b9a97; padding: 24px; }
.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 14px;
  color: #697386;
  font-size: 12px;
}
.page-size { display: inline-flex; align-items: center; gap: 6px; }
.page-size select { padding: 5px 7px; }
.page-actions { display: flex; align-items: center; gap: 8px; }
.page-button { padding: 6px 10px; cursor: pointer; }
.page-button:disabled { opacity: .5; cursor: not-allowed; }
.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
}
.status-badge.match, .status-badge.intersect {
  background: #d1f4e0;
  color: #0a6b48;
}
.status-badge.diff_a, .status-badge.diff_b {
  background: #ffe5e9;
  color: #b3093f;
}
.status-badge.match_only {
  background: #fff0d9;
  color: #8a5300;
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
@media (max-width: 640px) {
  .result-meta { flex-wrap: wrap; gap: 8px 12px; }
  .result-meta .meta-time { width: 100%; margin-left: 0; }
  .result-tools { align-items: stretch; flex-direction: column; }
  .search-field { flex-basis: auto; }
  .filter-list { justify-content: flex-start; }
  .pagination { align-items: flex-start; flex-direction: column; }
}
</style>
