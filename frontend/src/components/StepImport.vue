<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()

const props = defineProps({
  modelValue: String,
  label: String,  // 可选：传入翻译 key；否则用 placeholder 推断
  placeholder: String,
})
const emit = defineEmits(['update:modelValue'])

// 支持两种用法：
//   <StepInput v-model="x" label="input.columnA" />
//   <StepInput v-model="x" :label="'A 列'" />  ← 兼容：传入原文则直接显示
const displayLabel = () => {
  if (!props.label) return ''
  // 如果 label 以 "input." / "home." 等开头，认为是 i18n key
  if (props.label.includes('.')) return t(props.label)
  return props.label
}
</script>

<template>
  <div class="input-block">
    <label>{{ displayLabel() }}</label>
    <textarea
      :value="modelValue"
      :placeholder="placeholder || t('input.placeholder')"
      @input="emit('update:modelValue', $event.target.value)"
      rows="8"
    ></textarea>
  </div>
</template>

<style scoped>
.input-block label {
  display: block;
  font-size: 13px;
  color: #697386;
  margin-bottom: 6px;
  font-weight: 500;
}
.input-block textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #d6dbe2;
  border-radius: 6px;
  font-family: "SF Mono", Menlo, monospace;
  font-size: 12px;
  color: #1a1f36;
  resize: vertical;
  transition: all 0.15s;
}
.input-block textarea:focus {
  outline: none;
  border-color: #635bff;
  box-shadow: 0 0 0 3px rgba(99, 91, 255, 0.1);
}
</style>