<script setup lang="ts">
interface Props {
  title: string
  value: string | number
  icon: string
  trend?: 'up' | 'down' | 'neutral'
}

withDefaults(defineProps<Props>(), {
  trend: 'neutral',
})
</script>

<template>
  <div class="stat-card" :class="`stat-card--${trend}`">
    <div class="stat-card__stripe" />
    <div class="stat-card__body">
      <div class="stat-card__header">
        <i :class="icon" class="stat-card__icon" />
        <span class="stat-card__title">{{ title }}</span>
      </div>
      <div class="stat-card__value">{{ value }}</div>
      <div v-if="trend !== 'neutral'" class="stat-card__trend">
        <i
          :class="trend === 'up' ? 'fas fa-arrow-up' : 'fas fa-arrow-down'"
          class="stat-card__trend-icon"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  display: flex;
  background: var(--color-surface);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  transition: box-shadow 0.2s ease;
}

.stat-card:hover {
  box-shadow: var(--shadow-md);
}

/* 左側色條 */
.stat-card__stripe {
  width: 5px;
  flex-shrink: 0;
  background: var(--color-primary);
}

.stat-card--up .stat-card__stripe {
  background: var(--color-accent);
}

.stat-card--down .stat-card__stripe {
  background: var(--color-secondary);
}

.stat-card__body {
  flex: 1;
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.stat-card__header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.stat-card__icon {
  color: var(--color-text-muted);
  font-size: 14px;
}

.stat-card__title {
  font-family: var(--font-sans);
  font-size: 13px;
  color: var(--color-text-secondary);
}

.stat-card__value {
  font-family: var(--font-mono);
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text);
  line-height: 1.2;
}

.stat-card__trend {
  margin-top: var(--spacing-xs);
}

.stat-card--up .stat-card__trend-icon {
  color: var(--color-accent);
}

.stat-card--down .stat-card__trend-icon {
  color: var(--color-secondary);
}
</style>
