import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { title: '總覽' },
    },
    {
      path: '/daily-cash',
      name: 'daily-cash',
      component: () => import('../views/DailyCashView.vue'),
      meta: { title: '今彩539 分析' },
    },
    {
      path: '/lotto649',
      name: 'lotto649',
      component: () => import('../views/Lotto649View.vue'),
      meta: { title: '大樂透 分析' },
    },
    {
      path: '/super-lotto',
      name: 'super-lotto',
      component: () => import('../views/SuperLottoView.vue'),
      meta: { title: '威力彩 分析' },
    },
    {
      path: '/prediction',
      name: 'prediction',
      component: () => import('../views/PredictionView.vue'),
      meta: { title: '預測搖獎區' },
    },
    {
      path: '/check',
      name: 'check',
      component: () => import('../views/CheckNumbersView.vue'),
      meta: { title: '對獎' },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { title: '登入' },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue'),
      meta: { title: '註冊' },
    },
  ],
})

router.beforeEach(async (to) => {
  const title = to.meta.title as string
  document.title = title ? `${title} | NumberOracle` : 'NumberOracle'

  if (to.meta.requiresAuth) {
    const { useAuthStore } = await import('../stores/authStore')
    const authStore = useAuthStore()
    if (!authStore.isLoggedIn) {
      return { path: '/login', query: { redirect: to.fullPath } }
    }
  }
})

export default router
