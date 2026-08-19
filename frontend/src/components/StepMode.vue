<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()

const props = defineProps({
  modelValue: String,
  options: Object,
})
const emit = defineEmits(['update:modelValue', 'update:options'])

const modes = [
  { key: 'find_diff', icon: '🔍' },
  { key: 'vlookup', icon: '🎯' },
  { key: 'intersect', icon: '🤝' },
]

const setOption = (key, value) => {
  // 内部 option key 仍是英文（与后端 options schema 保持一致）
  emit('update:options', { ...props.options, [key]: value })
}
</script>

<template>
  <fieldset class="mode-selector">
    <legend class="sr-only">{{ t('home.stepMode') }}</legend>
    <div class="mode-grid">
      <label
        v-for="m in modes"
        :key="m.key"
        class="mode-card"
        :class="{ selected: modelValue === m.key }"
      >
        <input
          class="mode-input"
          type="radio"
          name="diff-mode"
          :value="m.key"
          :checked="modelValue === m.key"
          @change="emit('update:modelValue', m.key)"
        />
        <div class="icon">{{ m.icon }}</div>
        <div class="name">{{ t(`modes.${m.key}.name`) }}</div>
        <div class="desc">{{ t(`modes.${m.key}.desc`) }}</div>
      </label>
    </div>

    <div class="options">
      <div class="options-label">{{ t('modes.options') }}</div>
      <div class="toggle-list">
        <label
          class="toggle"
          :class="{ on: options.ignore_case }"
        >
          <input type="checkbox" :checked="options.ignore_case" @change="setOption('ignore_case', $event.target.checked)" />
          {{ t('modes.ignoreCase') }}
        </label>
        <label
          class="toggle"
          :class="{ on: options.trim }"
        >
          <input type="checkbox" :checked="options.trim" @change="setOption('trim', $event.target.checked)" />
          {{ t('modes.trim') }}
        </label>
        <label
          class="toggle"
          :class="{ on: options.skip_empty }"
        >
          <input type="checkbox" :checked="options.skip_empty" @change="setOption('skip_empty', $event.target.checked)" />
          {{ t('modes.skipEmpty') }}
        </label>
      </div>
    </div>
  </fieldset>
</template>

<style scoped>
.mode-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.mode-card {
  position: relative;
  border: 2px solid #e6ebf1;
  border-radius: 8px;
  padding: 14px;
  cursor: pointer;
  transition: all 0.15s;
}
.mode-input {
  position: absolute;
  opacity: 0;
  inset: 0;
  cursor: pointer;
}
.mode-card:focus-within {
  outline: 3px solid rgba(99, 91, 255, 0.25);
  outline-offset: 2px;
}
.mode-card:hover {
  border-color: #c7d2fe;
}
.mode-card.selected {
  border-color: #635bff;
  background: #f4f3ff;
}
.mode-card .icon {
  font-size: 22px;
  margin-bottom: 8px;
}
.mode-card .name {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 4px;
}
.mode-card .desc {
  font-size: 12px;
  color: #697386;
  line-height: 1.4;
}
.options {
  margin-top: 16px;
}
.options-label {
  font-size: 13px;
  color: #697386;
  margin-bottom: 8px;
}
.toggle-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 16px;
  background: #f6f9fc;
  border: 1px solid #e6ebf1;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}
.toggle.on {
  background: #e0e7ff;
  border-color: #635bff;
  color: #4f46e5;
}
.toggle input { accent-color: #635bff; }
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
  .mode-grid { grid-template-columns: 1fr; }
  .mode-card { min-height: 96px; }
}
</style>
