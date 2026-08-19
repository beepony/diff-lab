<script setup>
import { RouterView } from 'vue-router'
import AdminAccess from '@/components/AdminAccess.vue'
</script>

<template>
  <RouterView />
  <AdminAccess />
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
