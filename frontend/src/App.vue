<script setup>
import { RouterView } from 'vue-router'
import ToastStack from '@/components/ToastStack.vue'
</script>

<template>
  <RouterView />
  <ToastStack />
</template>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
  color: #1a1f36;
  background: #f6f9fc;
  line-height: 1.5;
}
</style>
