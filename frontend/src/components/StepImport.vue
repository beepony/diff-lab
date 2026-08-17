<script setup>
const props = defineProps({
  modelValue: String,
  label: String,
  placeholder: String,
})
const emit = defineEmits(['update:modelValue'])
</script>

<template>
  <div class="input-block">
    <label>{{ label }}</label>
    <textarea
      :value="modelValue"
      :placeholder="placeholder"
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