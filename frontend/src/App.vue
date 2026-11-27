<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { signOut, user } from './auth'
const route = useRoute()
const router = useRouter()
const menuOpen = ref(false)
const error = ref('')
async function logout() {
  try {
    await signOut()
    await router.push('/')
  } catch (e) {
    error.value = (e as Error).message
  }
}
</script>

<template>
  <a class="skip-link" href="#main">跳至主要内容</a>
  <header class="site-header" :class="{ 'over-hero': route.path === '/' }">
    <RouterLink
      class="brand"
      to="/"
      aria-label="慧笔首页"
      @click="menuOpen = false"
    >
      <svg viewBox="0 0 36 32" aria-hidden="true">
        <path d="M2 29 14 3h7L9 29Zm15 0L29 3h5L22 29Z" fill="currentColor" />
      </svg>
      <span>慧笔 <small>HUIBI</small></span>
    </RouterLink>
    <button
      class="menu-toggle"
      :aria-expanded="menuOpen"
      aria-controls="main-nav"
      @click="menuOpen = !menuOpen"
    >
      {{ menuOpen ? '关闭' : '菜单' }}
    </button>
    <nav
      id="main-nav"
      :class="{ open: menuOpen }"
      aria-label="主导航"
      @click="menuOpen = false"
    >
      <RouterLink to="/">首页</RouterLink>
      <RouterLink to="/#possibilities">写作场景</RouterLink>
      <RouterLink to="/#approach">评阅</RouterLink>
      <RouterLink to="/studio"
        >工作台 <span aria-hidden="true">↗</span></RouterLink
      >
    </nav>
    <div class="header-action">
      <template v-if="user"
        ><span class="user-name">{{ user }}</span
        ><button class="text-button" @click="logout">退出</button></template
      >
      <RouterLink v-else class="header-login" to="/login"
        >登录 / 注册 <span aria-hidden="true">↗</span></RouterLink
      >
    </div>
  </header>
  <p v-if="error" class="global-error" role="alert">{{ error }}</p>
  <main id="main"><RouterView /></main>
  <footer class="site-footer">
    <RouterLink class="footer-brand" to="/">慧笔 <span>HUIBI</span></RouterLink>
    <p>让表达，更进一步。</p>
    <div>
      <span>AI 模拟评分 · 非官方成绩</span>
    </div>
    <a
      href="https://unsplash.com/photos/J2ydRt1TIMw"
      target="_blank"
      rel="noreferrer"
      >摄影来源 · Unsplash ↗</a
    >
  </footer>
</template>
