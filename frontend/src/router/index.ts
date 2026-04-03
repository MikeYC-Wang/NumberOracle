import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { title: '總覽儀表板' },
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
  ],
})

router.beforeEach((to) => {
  const title = to.meta.title as string
  document.title = title ? `${title} | NumberOracle` : 'NumberOracle'
})

export default router
