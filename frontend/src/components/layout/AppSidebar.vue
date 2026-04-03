<script setup lang="ts">
import { useLotteryStore } from '../../stores/lotteryStore'

const lotteryStore = useLotteryStore()

const gameRouteMap: Record<string, string> = {
  daily_cash: '/daily-cash',
  lotto649: '/lotto649',
  super_lotto: '/super-lotto',
}

const gameIconMap: Record<string, string> = {
  daily_cash: 'fas fa-star',
  lotto649: 'fas fa-trophy',
  super_lotto: 'fas fa-bolt',
}
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar__section">
      <h3 class="sidebar__heading">
        <i class="fas fa-dice"></i> 彩種選單
      </h3>
      <ul class="sidebar__list">
        <li v-for="game in lotteryStore.games" :key="game.code">
          <router-link
            :to="gameRouteMap[game.code] || '/'"
            class="sidebar__link"
          >
            <i :class="gameIconMap[game.code] || 'fas fa-circle'"></i>
            <span>{{ game.name }}</span>
            <small>{{ game.main_pick_count }}/{{ game.main_pool_size }}</small>
          </router-link>
        </li>
      </ul>
    </div>

    <div class="sidebar__section">
      <h3 class="sidebar__heading">
        <i class="fas fa-tools"></i> 工具
      </h3>
      <ul class="sidebar__list">
        <li>
          <router-link to="/prediction" class="sidebar__link">
            <i class="fas fa-magic"></i>
            <span>預測搖獎</span>
          </router-link>
        </li>
      </ul>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  background-color: var(--color-surface);
  border-right: 1px solid var(--color-border);
  padding: var(--spacing-lg) 0;
  overflow-y: auto;
  flex-shrink: 0;
}

.sidebar__section {
  margin-bottom: var(--spacing-xl);
}

.sidebar__heading {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--color-text-muted);
  padding: 0 var(--spacing-lg);
  margin-bottom: var(--spacing-sm);
  letter-spacing: 0.05em;
}
.sidebar__heading i {
  margin-right: var(--spacing-xs);
}

.sidebar__list {
  display: flex;
  flex-direction: column;
}

.sidebar__link {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-lg);
  color: var(--color-text);
  font-size: 0.9375rem;
  transition: background-color 0.15s ease;
}
.sidebar__link:hover {
  background-color: var(--color-surface-hover);
}
.sidebar__link.router-link-active {
  background-color: var(--color-primary-light);
  color: var(--color-text);
  font-weight: 500;
}

.sidebar__link small {
  margin-left: auto;
  color: var(--color-text-muted);
  font-size: 0.75rem;
}

@media (max-width: 768px) {
  .sidebar {
    display: none;
  }
}
</style>
