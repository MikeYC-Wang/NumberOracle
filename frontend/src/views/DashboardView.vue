<script setup lang="ts">
import { onMounted } from 'vue'
import { useLotteryStore } from '../stores/lotteryStore'

const lotteryStore = useLotteryStore()

onMounted(() => {
  lotteryStore.fetchGames()
})
</script>

<template>
  <div class="page-content">
    <div class="container">
      <h1>
        <i class="fas fa-chart-line"></i>
        總覽儀表板
      </h1>
      <p class="subtitle">NumberOracle 彩券數據分析平台</p>

      <div v-if="lotteryStore.loading" class="loading">
        <i class="fas fa-spinner fa-spin"></i> 載入中...
      </div>

      <div v-else class="game-cards">
        <router-link
          v-for="game in lotteryStore.games"
          :key="game.code"
          :to="`/${game.code.replace('_', '-').replace('lotto649', 'lotto649')}`"
          class="game-card card"
        >
          <div class="game-card__icon">
            <i class="fas fa-dice"></i>
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
        </router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.subtitle {
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-xl);
}

h1 {
  margin-bottom: var(--spacing-sm);
}

h1 i {
  color: var(--color-primary);
  margin-right: var(--spacing-sm);
}

.loading {
  text-align: center;
  padding: var(--spacing-2xl);
  color: var(--color-text-muted);
  font-size: 1.125rem;
}

.game-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--spacing-lg);
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
</style>
