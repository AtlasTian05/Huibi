<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { post } from '../api'
import { signIn } from '../auth'
const router = useRouter()
const register = ref(false)
const username = ref('')
const password = ref('')
const error = ref('')
const notice = ref('')
const busy = ref(false)
function switchMode() {
  register.value = !register.value
  error.value = ''
  notice.value = ''
}
async function submit() {
  busy.value = true
  error.value = ''
  notice.value = ''
  try {
    if (register.value) {
      await post('/auth/register', {
        username: username.value,
        password: password.value,
      })
      register.value = false
      notice.value = '注册成功，请登录。'
      password.value = ''
    } else {
      await signIn(username.value, password.value)
      await router.push('/studio')
    }
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="auth-layout">
    <aside class="auth-photo">
      <img src="/images/library.jpg" alt="图书馆中整齐陈列的书架" />
      <div>
        <p class="eyebrow light">HUIBI / WRITING</p>
        <h1>让表达，<br />更进一步。</h1>
      </div>
    </aside>
    <section class="auth-panel" aria-labelledby="auth-title">
      <div class="auth-inner">
        <p class="eyebrow">ACCOUNT</p>
        <h2 id="auth-title">
          {{ register ? '注册' : '登录' }}
        </h2>
        <form @submit.prevent="submit">
          <label for="username">用户名</label
          ><input
            id="username"
            v-model="username"
            autocomplete="username"
            required
            maxlength="50"
            pattern="[\w\-一-鿿]+"
            :disabled="busy"
          /><label for="password">密码</label
          ><input
            id="password"
            v-model="password"
            type="password"
            :autocomplete="register ? 'new-password' : 'current-password'"
            required
            minlength="6"
            maxlength="128"
            :placeholder="register ? '至少 6 位' : ''"
            :disabled="busy"
          />
          <p v-if="error" class="error" role="alert">{{ error }}</p>
          <p v-if="notice" class="notice" role="status">{{ notice }}</p>
          <button class="button dark full" :disabled="busy">
            {{ busy ? '请稍候…' : register ? '创建账号 ↗' : '登录工作台 ↗' }}
          </button>
        </form>
        <p class="auth-switch">
          {{ register ? '已有账号？' : '还没有账号？' }}
          <button class="text-button" :disabled="busy" @click="switchMode">
            {{ register ? '去登录' : '创建账号' }}
          </button>
        </p>
        <p class="privacy-note">作文与题图由 AI 分析。</p>
      </div>
    </section>
  </div>
</template>
