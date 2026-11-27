import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import HomePage from './components/HomePage.vue'
import AuthPage from './components/AuthPage.vue'
import WorkspacePage from './components/WorkspacePage.vue'
import { loadUser, user } from './auth'
import './style.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: HomePage },
    { path: '/login', component: AuthPage },
    { path: '/studio', component: WorkspacePage, meta: { protected: true } },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior(to) {
    return to.hash ? { el: to.hash, top: 80, behavior: 'smooth' } : { top: 0 }
  },
})
router.beforeEach(async (to) => {
  await loadUser()
  if (to.meta.protected && !user.value) return '/login'
})
createApp(App).use(router).mount('#app')
