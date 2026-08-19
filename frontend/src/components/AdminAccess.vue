<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { clearAdminToken, getAdminToken, setAdminToken } from '@/api'

const { t } = useI18n()
const editing = ref(false)
const token = ref(getAdminToken())
const configured = ref(Boolean(token.value))

const save = () => {
  setAdminToken(token.value)
  configured.value = Boolean(token.value.trim())
  editing.value = false
}

const clear = () => {
  clearAdminToken()
  token.value = ''
  configured.value = false
}
</script>

<template>
  <div class="admin-access">
    <button class="trigger" type="button" @click="editing = !editing">
      {{ configured ? t('auth.configured') : t('auth.configure') }}
    </button>
    <form v-if="editing" class="panel" @submit.prevent="save">
      <label for="admin-token">{{ t('auth.adminToken') }}</label>
      <input id="admin-token" v-model="token" type="password" autocomplete="off" :placeholder="t('auth.tokenHint')" />
      <div class="actions">
        <button type="submit">{{ t('common.save') }}</button>
        <button v-if="configured" type="button" class="clear" @click="clear">{{ t('auth.clearToken') }}</button>
      </div>
    </form>
  </div>
</template>

<style scoped>
.admin-access { position: fixed; right: 16px; bottom: 16px; z-index: 30; }
.trigger, .actions button {
  border: 1px solid #d6dbe2; border-radius: 6px; background: white; color: #1a1f36;
  padding: 7px 10px; font-size: 12px; cursor: pointer;
}
.panel {
  width: 260px; margin-bottom: 8px; padding: 12px; border: 1px solid #e6ebf1;
  border-radius: 8px; background: white; box-shadow: 0 8px 22px rgba(26, 31, 54, .14);
}
label { display: block; margin-bottom: 6px; color: #697386; font-size: 12px; }
input { width: 100%; padding: 8px; border: 1px solid #d6dbe2; border-radius: 5px; }
.actions { display: flex; gap: 8px; margin-top: 10px; }
.clear { color: #b3093f; }
</style>
