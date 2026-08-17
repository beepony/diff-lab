<script setup>
const props = defineProps({
  modelValue: String,
  options: Object,
})
const emit = defineEmits(['update:modelValue', 'update:options'])

const modes = [
  { key: 'find_diff', icon: '🔍', name: '找差异', desc: '显示 A 有但 B 没有 / B 有但 A 没有 的项' },
  { key: 'vlookup', icon: '🎯', name: 'VLOOKUP', desc: '以 A 列为 key，查找 B 列是否有匹配' },
  { key: 'intersect', icon: '🤝', name: '找交集', desc: '只显示双侧都存在的值' },
]

const toggleOption = (key) => {
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
        <div class="name">{{ m.name }}</div>
        <div class="desc">{{ m.desc }}</div>
      </div>
    </div>

    <div class="options">
      <div class="options-label">匹配选项</div>
      <div class="toggle-list">
        <div
          class="toggle"
          :class="{ on: options.ignore_case }"
          @click="toggleOption('ignore_case')"
        >忽略大小写</div>
        <div
          class="toggle"
          :class="{ on: options.trim }"
          @click="toggleOption('trim')"
        >去空格</div>
        <div
          class="toggle"
          :class="{ on: options.skip_empty }"
          @click="toggleOption('skip_empty')"
        >忽略空值</div>
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