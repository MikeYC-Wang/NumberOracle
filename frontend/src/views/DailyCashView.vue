<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useLotteryStore } from '../stores/lotteryStore'
import { useAnalysisStore } from '../stores/analysisStore'
import StatCard from '../components/common/StatCard.vue'
import HotColdChart from '../components/charts/HotColdChart.vue'
import MissingValueChart from '../components/charts/MissingValueChart.vue'
import DataTable from '../components/common/DataTable.vue'

const GAME_CODE = 'daily_cash'
const POOL_SIZE = 39

const lotteryStore = useLotteryStore()
const analysisStore = useAnalysisStore()

const totalDraws = computed(() => analysisStore.totalCount)

const latestDrawDate = computed(() => {
  if (analysisStore.draws.length === 0) return '--'
  return analysisStore.draws[0].draw_date
})

const hottestNumber = computed(() => {
  if (analysisStore.frequencies.length === 0) return '--'
  const sorted = [...analysisStore.frequencies].sort((a, b) => b.count - a.count)
  return sorted[0].number
})

onMounted(async () => {
  lotteryStore.selectGame(GAME_CODE)
  await Promise.all([
    analysisStore.fetchDraws(GAME_CODE),
    analysisStore.fetchHotCold(GAME_CODE),
    analysisStore.fetchMissingValues(GAME_CODE),
  ])
})
</script>

<template>
  <div class="page-content">
    <div class="container">
      <h1>
        <i class="fas fa-star"></i>
        今彩539 分析
      </h1>
      <p class="subtitle">5/39 -- 每週一至六開獎</p>

      <div v-if="analysisStore.loading" class="loading">
        <i class="fas fa-spinner fa-spin"></i> 載入中...
      </div>

      <template v-else>
        <!-- 統計卡片 -->
        <div class="stat-cards">
          <StatCard
            title="總開獎期數"
            :value="totalDraws"
            icon="fas fa-database"
          />
          <StatCard
            title="最近開獎日"
            :value="latestDrawDate"
            icon="far fa-calendar-alt"
          />
          <StatCard
            title="最熱門號碼"
            :value="hottestNumber"
            icon="fas fa-fire"
            trend="up"
          />
        </div>

        <!-- 圖表區 -->
        <div class="charts-grid">
          <section class="card">
            <h2><i class="fas fa-fire"></i> 冷熱門號碼</h2>
            <HotColdChart
              :frequencies="analysisStore.frequencies"
              :pool-size="POOL_SIZE"
            />
          </section>
          <section class="card">
            <h2><i class="fas fa-search"></i> 遺漏值分析</h2>
            <MissingValueChart
              :missing-values="analysisStore.missingValues"
            />
          </section>
        </div>

        <!-- 歷史開獎紀錄 -->
        <section class="card full-width-section">
          <h2><i class="fas fa-history"></i> 歷史開獎紀錄</h2>
          <DataTable
            :draws="analysisStore.draws"
            :show-special="false"
          />
        </section>
      </template>
    </div>
  </div>
</template>

<style scoped>
.subtitle {
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-xl);
}

h1 i { color: var(--color-primary); margin-right: var(--spacing-sm); }
h2 i { margin-right: var(--spacing-sm); }

.loading {
  text-align: center;
  padding: var(--spacing-2xl);
  color: var(--color-text-muted);
  font-size: 1.125rem;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.charts-grid .card {
  display: flex;
  flex-direction: column;
}

.charts-grid .card :deep(.hot-cold-chart),
.charts-grid .card :deep(.missing-value-chart) {
  flex: 1;
  min-height: 320px;
}

.full-width-section {
  margin-bottom: var(--spacing-lg);
}

.full-width-section h2 {
  margin-bottom: var(--spacing-md);
}

@media (max-width: 1024px) {
  .stat-cards {
    grid-template-columns: repeat(3, 1fr);
    gap: var(--spacing-md);
  }
}

@media (max-width: 768px) {
  .stat-cards {
    grid-template-columns: 1fr;
    gap: var(--spacing-md);
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }
}
</style>
