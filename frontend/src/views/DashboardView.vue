<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useLotteryStore } from '../stores/lotteryStore'
import type { DrawResult } from '../types/lottery'
import LotteryBall from '../components/common/LotteryBall.vue'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'

interface GameSummary {
  game: string
  game_name: string
  total_draws: number
  date_range: { earliest: string; latest: string }
  latest_draw: DrawResult | null
  top5_hot: number[]
  top5_cold: number[]
}

const lotteryStore = useLotteryStore()

const latestDraws = ref<Record<string, DrawResult | null>>({})
const gameSummaries = ref<Record<string, GameSummary | null>>({})
const loadingDraws = ref(false)

/** 根據 game code 產生對應路由路徑 */
function gameRoute(code: string): string {
  const map: Record<string, string> = {
    daily_cash: '/daily-cash',
    lotto649: '/lotto649',
    super_lotto: '/super-lotto',
  }
  return map[code] ?? `/${code}`
}

/** 根據 game code 取得圖示 */
function gameIcon(code: string): string {
  const map: Record<string, string> = {
    daily_cash: 'fas fa-star',
    lotto649: 'fas fa-trophy',
    super_lotto: 'fas fa-bolt',
  }
  return map[code] ?? 'fas fa-dice'
}

async function fetchLatestDraw(gameCode: string) {
  try {
    const res = await fetch(`${API_BASE}/draws/?game=${gameCode}&page=1`)
    if (!res.ok) return null
    const data = await res.json()
    const results = data.results ?? data
    return results.length > 0 ? (results[0] as DrawResult) : null
  } catch {
    return null
  }
}

async function fetchSummary(gameCode: string): Promise<GameSummary | null> {
  try {
    const res = await fetch(`${API_BASE}/draws/summary/?game=${gameCode}`)
    if (!res.ok) return null
    return (await res.json()) as GameSummary
  } catch {
    return null
  }
}

onMounted(async () => {
  await lotteryStore.fetchGames()

  if (lotteryStore.games.length > 0) {
    loadingDraws.value = true
    const promises = lotteryStore.games.map(async (game) => {
      const [draw, summary] = await Promise.all([
        fetchLatestDraw(game.code),
        fetchSummary(game.code),
      ])
      latestDraws.value[game.code] = draw
      gameSummaries.value[game.code] = summary
    })
    await Promise.all(promises)
    loadingDraws.value = false
  }
})
</script>

<template>
  <div class="page-content">
    <div class="container">
      <!-- Logo 區塊 -->
      <div class="hero">
        <img src="/NumberOracle_LOGO.svg" alt="NumberOracle Logo" class="hero__logo" />
        <h1 class="hero__title">NumberOracle</h1>
        <p class="hero__tagline">歷史數據統計與機率運算的彩券分析平台</p>
      </div>

      <h2 class="section-title">
        <i class="fas fa-chart-line"></i>
        總覽
      </h2>

      <div v-if="lotteryStore.loading" class="loading">
        <i class="fas fa-spinner fa-spin"></i> 載入中...
      </div>

      <template v-else>
        <!-- 遊戲卡片 -->
        <div class="game-cards">
          <router-link
            v-for="game in lotteryStore.games"
            :key="game.code"
            :to="gameRoute(game.code)"
            class="game-card card"
          >
            <div class="game-card__icon">
              <i :class="gameIcon(game.code)"></i>
            </div>
            <h2 class="game-card__name">{{ game.name }}</h2>
            <p class="game-card__info">
              {{ game.main_pick_count }} 個號碼 / {{ game.main_pool_size }} 選
              <span v-if="game.has_special"> + 特別號</span>
            </p>
            <p class="game-card__schedule">
              <i class="far fa-calendar-alt"></i>
              {{ game.draw_schedule }}
            </p>
            <template v-if="gameSummaries[game.code]">
              <p class="game-card__summary">
                <i class="fas fa-database"></i>
                總期數: {{ gameSummaries[game.code]!.total_draws }}
              </p>
              <p class="game-card__summary">
                <i class="fas fa-calendar-check"></i>
                資料範圍: {{ gameSummaries[game.code]!.date_range.earliest }} ~ {{ gameSummaries[game.code]!.date_range.latest }}
              </p>
            </template>
          </router-link>
        </div>

        <!-- 最新開獎區塊 -->
        <section class="latest-draws">
          <h2><i class="fas fa-clock"></i> 最新開獎</h2>

          <div v-if="loadingDraws" class="loading">
            <i class="fas fa-spinner fa-spin"></i> 載入最新開獎...
          </div>

          <div v-else class="latest-draws__grid">
            <div
              v-for="game in lotteryStore.games"
              :key="game.code"
              class="latest-draws__item card"
            >
              <div class="latest-draws__header">
                <i :class="gameIcon(game.code)" class="latest-draws__icon"></i>
                <h3>{{ game.name }}</h3>
              </div>

              <template v-if="latestDraws[game.code]">
                <p class="latest-draws__meta">
                  第 {{ latestDraws[game.code]!.draw_term }} 期
                  <span class="latest-draws__date">
                    {{ latestDraws[game.code]!.draw_date }}
                  </span>
                </p>
                <div class="latest-draws__balls">
                  <LotteryBall
                    v-for="num in latestDraws[game.code]!.numbers_sorted"
                    :key="num"
                    :number="num"
                    type="normal"
                    size="md"
                  />
                  <template v-if="game.has_special && latestDraws[game.code]!.special_number !== null">
                    <span class="latest-draws__separator">+</span>
                    <LotteryBall
                      :number="latestDraws[game.code]!.special_number!"
                      type="special"
                      size="md"
                    />
                  </template>
                </div>
              </template>

              <p v-else class="latest-draws__empty">
                <i class="fas fa-inbox"></i> 暫無資料
              </p>
            </div>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>

<style scoped>
/* Hero / Logo */
.hero {
  text-align: center;
  padding: var(--spacing-xl) 0 var(--spacing-lg);
}

.hero__logo {
  height: 350px;
  width: auto;
  margin: 0 auto var(--spacing-md);
  display: block;
}

.hero__title {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: var(--spacing-xs);
}

.hero__tagline {
  color: var(--color-text-secondary);
  font-size: 1rem;
}

.section-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
}

.section-title i {
  color: var(--color-primary);
}

.loading {
  text-align: center;
  padding: var(--spacing-2xl);
  color: var(--color-text-muted);
  font-size: 1.125rem;
}

/* 遊戲卡片 */
.game-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.game-card {
  display: block;
  text-decoration: none;
  color: inherit;
  text-align: center;
  padding: var(--spacing-xl);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.game-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.game-card__icon {
  font-size: 2.5rem;
  color: var(--color-primary);
  margin-bottom: var(--spacing-md);
}

.game-card__name {
  margin-bottom: var(--spacing-sm);
}

.game-card__info {
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-sm);
}

.game-card__schedule {
  color: var(--color-text-muted);
  font-size: 0.875rem;
}
.game-card__schedule i {
  margin-right: var(--spacing-xs);
}

.game-card__summary {
  color: var(--color-text-muted);
  font-size: 0.8125rem;
  margin-top: var(--spacing-xs);
  font-family: var(--font-mono);
}
.game-card__summary i {
  margin-right: var(--spacing-xs);
  color: var(--color-primary);
}

/* 最新開獎 */
.latest-draws {
  margin-top: var(--spacing-lg);
}

.latest-draws > h2 {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
}

.latest-draws > h2 i {
  color: var(--color-accent);
}

.latest-draws__grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-lg);
}

.latest-draws__item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.latest-draws__header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.latest-draws__icon {
  color: var(--color-primary);
  font-size: 1.125rem;
}

.latest-draws__header h3 {
  font-size: 1.125rem;
}

.latest-draws__meta {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  font-family: var(--font-mono);
}

.latest-draws__date {
  margin-left: var(--spacing-sm);
  color: var(--color-text-muted);
}

.latest-draws__balls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-xs);
  margin-top: var(--spacing-xs);
}

.latest-draws__separator {
  font-weight: 700;
  color: var(--color-text-muted);
  font-size: 1.25rem;
  margin: 0 var(--spacing-xs);
}

.latest-draws__empty {
  color: var(--color-text-muted);
  font-size: 0.875rem;
  padding: var(--spacing-md) 0;
}

.latest-draws__empty i {
  margin-right: var(--spacing-xs);
}

@media (max-width: 1024px) {
  .game-cards {
    grid-template-columns: repeat(3, 1fr);
    gap: var(--spacing-md);
  }

  .latest-draws__grid {
    grid-template-columns: repeat(3, 1fr);
    gap: var(--spacing-md);
  }
}

@media (max-width: 768px) {
  .game-cards {
    grid-template-columns: 1fr;
  }

  .latest-draws__grid {
    grid-template-columns: 1fr;
  }
}
</style>
