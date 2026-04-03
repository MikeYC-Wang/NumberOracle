<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useLotteryStore } from '../stores/lotteryStore'
import { useAnalysisStore } from '../stores/analysisStore'
import StatCard from '../components/common/StatCard.vue'
import HotColdChart from '../components/charts/HotColdChart.vue'
import MissingValueChart from '../components/charts/MissingValueChart.vue'
import TrendLineChart from '../components/charts/TrendLineChart.vue'
import DataTable from '../components/common/DataTable.vue'

const GAME_CODE = 'super_lotto'
const POOL_SIZE = 38

const trendInput = ref<number | null>(null)
const trendError = ref<string | null>(null)

async function queryTrend() {
  trendError.value = null
  if (trendInput.value === null || trendInput.value < 1 || trendInput.value > POOL_SIZE) {
    trendError.value = `請輸入 1 ~ ${POOL_SIZE} 之間的號碼`
    return
  }
  await analysisStore.fetchTrend(GAME_CODE, trendInput.value)
}

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
        <i class="fas fa-bolt"></i>
        威力彩 分析
      </h1>
      <p class="subtitle">6/38 + 第二區 1/8 -- 每週一、四開獎</p>

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

        <!-- 號碼追蹤 -->
        <section class="card full-width-section trend-section">
          <h2><i class="fas fa-crosshairs"></i> 號碼追蹤</h2>
          <div class="trend-controls">
            <input
              v-model.number="trendInput"
              type="number"
              :min="1"
              :max="POOL_SIZE"
              :placeholder="`輸入號碼 (1~${POOL_SIZE})`"
              class="trend-input"
              @keyup.enter="queryTrend"
            />
            <button class="trend-btn" @click="queryTrend">
              <i class="fas fa-search"></i> 查詢
            </button>
          </div>
          <p v-if="trendError" class="trend-error">{{ trendError }}</p>
          <TrendLineChart
            v-if="analysisStore.trendData.length > 0 && analysisStore.trendNumber !== null"
            :trend-data="analysisStore.trendData"
            :number="analysisStore.trendNumber"
          />
        </section>

        <!-- 歷史開獎紀錄 -->
        <section class="card full-width-section">
          <h2><i class="fas fa-history"></i> 歷史開獎紀錄</h2>
          <DataTable
            :draws="analysisStore.draws"
            :show-special="true"
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

/* 號碼追蹤 */
.trend-section h2 {
  margin-bottom: var(--spacing-md);
}

.trend-controls {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
  margin-bottom: var(--spacing-md);
  flex-wrap: wrap;
}

.trend-input {
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border, #DFE6E9);
  border-radius: var(--radius-md, 8px);
  font-size: 1rem;
  font-family: var(--font-mono);
  width: 180px;
  background: var(--color-surface, #fff);
  color: var(--color-text, #2D3436);
}

.trend-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(42, 157, 143, 0.2);
}

.trend-btn {
  padding: var(--spacing-sm) var(--spacing-lg);
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-md, 8px);
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s ease;
}

.trend-btn:hover {
  opacity: 0.9;
}

.trend-btn i {
  margin-right: var(--spacing-xs);
}

.trend-error {
  color: var(--color-accent, #E76F51);
  font-size: 0.875rem;
  margin-bottom: var(--spacing-sm);
}

@media (max-width: 768px) {
  .stat-cards {
    grid-template-columns: 1fr;
    gap: var(--spacing-md);
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }

  .trend-input {
    width: 100%;
  }

  .trend-controls {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
