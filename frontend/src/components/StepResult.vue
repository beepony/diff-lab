<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()

const props = defineProps({
  result: Object,  // { rows, summary }
})

function statusLabel(s) {
  return t(`status.${s}`)
}

function displayValue(value) {
  return value === null || value === undefined ? '—' : value
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

    <table>
      <thead>
        <tr>
          <th style="width: 40px">#</th>
          <th>{{ t('result.headerA') }}</th>
          <th>{{ t('result.headerB') }}</th>
          <th style="width: 120px">{{ t('result.status') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, idx) in result.rows" :key="idx">
          <td class="idx">{{ idx + 1 }}</td>
          <td>{{ displayValue(row.a) }}</td>
          <td>{{ displayValue(row.b) }}</td>
          <td>
            <span class="status-badge" :class="row.status">
              {{ statusLabel(row.status) }}
            </span>
          </td>
        </tr>
        <tr v-if="!result.rows.length">
          <td colspan="4" class="empty">{{ t('result.noData') }}</td>
        </tr>
      </tbody>
    </table>
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
table {
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
</style>
