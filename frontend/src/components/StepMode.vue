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

const toggleOption = (key) => {
  // 内部 option key 仍是英文（与后端 options schema 保持一致）
  emit('update:options', { ...props.options, [key]: !props.options[key] })
}
</script>

<template>
  <div class="mode-selector">
    <div class="mode-grid">
      <div
        v-for="m in modes"
        :key="m.key"
        class="mode-card"
        :class="{ selected: modelValue === m.key }"
        @click="emit('update:modelValue', m.key)"
      >
        <div class="icon">{{ m.icon }}</div>
        <div class="name">{{ t(`modes.${m.key}.name`) }}</div>
        <div class="desc">{{ t(`modes.${m.key}.desc`) }}</div>
      </div>
    </div>

    <div class="options">
      <div class="options-label">{{ t('modes.options') }}</div>
      <div class="toggle-list">
        <div
          class="toggle"
          :class="{ on: options.ignore_case }"
          @click="toggleOption('ignore_case')"
        >{{ t('modes.ignoreCase') }}</div>
        <div
          class="toggle"
          :class="{ on: options.trim }"
          @click="toggleOption('trim')"
        >{{ t('modes.trim') }}</div>
        <div
          class="toggle"
          :class="{ on: options.skip_empty }"
          @click="toggleOption('skip_empty')"
        >{{ t('modes.skipEmpty') }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mode-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.mode-card {
  border: 2px solid #e6ebf1;
  border-radius: 8px;
  padding: 14px;
  cursor: pointer;
  transition: all 0.15s;
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
</style>