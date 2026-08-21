<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { clearAdminToken, getAdminToken, setAdminToken, verifyAdminToken } from '@/api'

const { t } = useI18n()
const emit = defineEmits(['changed'])
const editing = ref(false)
const token = ref(getAdminToken())
const configured = ref(Boolean(token.value))
const saving = ref(false)
const error = ref('')

const save = async () => {
  error.value = ''
  if (!token.value.trim()) {
    clear()
    return
  }
  saving.value = true
  setAdminToken(token.value)
  try {
    await verifyAdminToken()
    configured.value = true
    editing.value = false
    emit('changed')
  } catch {
    clearAdminToken()
    configured.value = false
    error.value = t('auth.invalidToken')
  } finally {
    saving.value = false
  }
}

const clear = () => {
  clearAdminToken()
  token.value = ''
  configured.value = false
  error.value = ''
  emit('changed')
}

onMounted(async () => {
  if (!configured.value) return
  try {
    await verifyAdminToken()
  } catch {
    clearAdminToken()
    token.value = ''
    configured.value = false
    error.value = t('auth.invalidToken')
    editing.value = true
    emit('changed')
  }
})
</script>

<template>
  <div class="admin-access">
    <button class="trigger" type="button" :aria-expanded="editing" aria-controls="admin-token-panel" @click="editing = !editing">
      {{ configured ? t('auth.configured') : t('auth.configure') }}
    </button>
    <form v-if="editing" id="admin-token-panel" class="panel" @submit.prevent="save">
      <label for="admin-token">{{ t('auth.adminToken') }}</label>
      <input id="admin-token" v-model="token" type="password" autocomplete="off" :placeholder="t('auth.tokenHint')" />
      <p v-if="error" class="error">{{ error }}</p>
      <div class="actions">
        <button type="submit" :disabled="saving">{{ saving ? t('auth.verifying') : t('common.save') }}</button>
        <button v-if="configured" type="button" class="clear" @click="clear">{{ t('auth.clearToken') }}</button>
      </div>
    </form>
  </div>
</template>

<style scoped>
.admin-access { position: relative; z-index: 20; }
.trigger, .actions button {
  border: 1px solid #d6dbe2; border-radius: 6px; background: white; color: #1a1f36;
  padding: 7px 10px; font-size: 12px; cursor: pointer;
}
.panel {
  position: absolute; right: 0; top: calc(100% + 8px); width: 260px; padding: 12px; border: 1px solid #e6ebf1;
  border-radius: 8px; background: white; box-shadow: 0 8px 22px rgba(26, 31, 54, .14);
}
label { display: block; margin-bottom: 6px; color: #697386; font-size: 12px; }
input { width: 100%; padding: 8px; border: 1px solid #d6dbe2; border-radius: 5px; }
.actions { display: flex; gap: 8px; margin-top: 10px; }
.clear { color: #b3093f; }
.error { margin: 8px 0 0; color: #b3093f; font-size: 12px; }
</style>
