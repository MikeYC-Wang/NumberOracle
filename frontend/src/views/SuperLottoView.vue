<script setup lang="ts">
import { computed, ref, watch, onMounted } from 'vue'
import { useLotteryStore } from '../stores/lotteryStore'
import { useAnalysisStore } from '../stores/analysisStore'
import StatCard from '../components/common/StatCard.vue'
import PeriodSelector from '../components/common/PeriodSelector.vue'
import HotColdChart from '../components/charts/HotColdChart.vue'
import MissingValueChart from '../components/charts/MissingValueChart.vue'
import TrendLineChart from '../components/charts/TrendLineChart.vue'
import ConsecutiveTailChart from '../components/charts/ConsecutiveTailChart.vue'
import ZoneDistributionChart from '../components/charts/ZoneDistributionChart.vue'
import OddEvenSizeChart from '../components/charts/OddEvenSizeChart.vue'
import AcValueChart from '../components/charts/AcValueChart.vue'
import PairFrequencyChart from '../components/charts/PairFrequencyChart.vue'
import DataTable from '../components/common/DataTable.vue'
import RoadMapChart from '../components/charts/RoadMapChart.vue'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'

const GAME_CODE = 'super_lotto'
const POOL_SIZE = 38

const selectedRecent = computed(() => analysisStore.selectedRecent)

function exportDrawsCsv() {
  window.open(`${API_BASE}/draws/export_csv/?game=${GAME_CODE}`)
}
function exportStatsCsv() {
  window.open(`${API_BASE}/draws/export_stats_csv/?game=${GAME_CODE}&recent=${selectedRecent.value}`)
}

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

async function fetchAdvanced() {
  const recent = analysisStore.selectedRecent
  await Promise.all([
    analysisStore.fetchConsecutiveTail(GAME_CODE, recent),
    analysisStore.fetchZoneDistribution(GAME_CODE, recent),
    analysisStore.fetchOddEvenSize(GAME_CODE, recent),
    analysisStore.fetchAcValue(GAME_CODE, recent),
    analysisStore.fetchPairFrequency(GAME_CODE, recent),
    analysisStore.fetchRoadMap(GAME_CODE, recent),
  ])
}

watch(() => analysisStore.selectedRecent, async () => {
  await Promise.all([
    analysisStore.fetchHotCold(GAME_CODE, analysisStore.selectedRecent),
    analysisStore.fetchMissingValues(GAME_CODE),
    fetchAdvanced(),
  ])
})

onMounted(async () => {
  lotteryStore.selectGame(GAME_CODE)
  await Promise.all([
    analysisStore.fetchDraws(GAME_CODE),
    analysisStore.fetchHotCold(GAME_CODE, analysisStore.selectedRecent),
    analysisStore.fetchMissingValues(GAME_CODE),
    fetchAdvanced(),
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

        <!-- 期數篩選 -->
        <PeriodSelector v-model="analysisStore.selectedRecent" />

        <!-- 圖表區 -->
        <div class="charts-grid">
          <section class="card">
            <h2><i class="fas fa-fire"></i> 冷熱門號碼</h2>
            <HotColdChart
              :frequencies="analysisStore.frequencies"
              :pool-size="POOL_SIZE"
            />
            <p class="chart-note"><i class="fas fa-info-circle"></i> 統計近 {{ analysisStore.selectedRecent }} 期每個號碼的出現次數，紅色為熱門、綠色為冷門</p>
          </section>
          <section class="card">
            <h2><i class="fas fa-search"></i> 遺漏值分析</h2>
            <MissingValueChart
              :missing-values="analysisStore.missingValues"
            />
            <p class="chart-note"><i class="fas fa-info-circle"></i> 每個號碼距離上次開出已間隔幾期，綠色=近期出現、紅色=長期未開</p>
          </section>
        </div>

        <!-- 進階分析 -->
        <h2 class="section-title"><i class="fas fa-chart-pie"></i> 進階分析</h2>
        <div class="advanced-grid">
          <section class="card">
            <h3>連號/同尾分析</h3>
            <ConsecutiveTailChart
              v-if="analysisStore.consecutiveTail"
              :data="analysisStore.consecutiveTail"
            />
            <p class="chart-note"><i class="fas fa-info-circle"></i> 左：近 {{ analysisStore.selectedRecent }} 期中連續號碼對數的分布；右：尾數 0~9 各出現幾次</p>
          </section>
          <section class="card">
            <h3>區間分布</h3>
            <ZoneDistributionChart
              v-if="analysisStore.zoneDistribution?.zones"
              :zones="analysisStore.zoneDistribution.zones"
            />
            <p class="chart-note"><i class="fas fa-info-circle"></i> 將號碼分為每 10 個一區間，統計近 {{ analysisStore.selectedRecent }} 期各區間被開出的次數</p>
          </section>
          <section class="card">
            <h3>奇偶比/大小比</h3>
            <OddEvenSizeChart
              v-if="analysisStore.oddEvenSize?.data"
              :data="analysisStore.oddEvenSize.data"
            />
            <p class="chart-note"><i class="fas fa-info-circle"></i> 每期開獎號碼中奇數/偶數及大號/小號的個數走勢</p>
          </section>
          <section class="card">
            <h3>AC 值分析</h3>
            <AcValueChart
              v-if="analysisStore.acValue?.data && analysisStore.acValue?.summary"
              :data="analysisStore.acValue.data"
              :summary="analysisStore.acValue.summary"
            />
            <p class="chart-note"><i class="fas fa-info-circle"></i> AC 值 = 號碼兩兩差值的不重複個數 - (開出球數-1)，數值越高代表號碼越分散</p>
          </section>
          <section class="card advanced-full">
            <h3>號碼組合頻率</h3>
            <PairFrequencyChart
              v-if="analysisStore.pairFrequency?.top_pairs"
              :pairs="analysisStore.pairFrequency.top_pairs"
            />
            <p class="chart-note"><i class="fas fa-info-circle"></i> 近 {{ analysisStore.selectedRecent }} 期中最常同時出現的兩個號碼組合 (前 20 名)</p>
          </section>
        </div>

        <!-- 號碼走勢路珠圖 -->
        <section
          v-if="analysisStore.roadMapData?.draws"
          class="card full-width-section"
        >
          <h2><i class="fas fa-th"></i> 號碼走勢路珠圖</h2>
          <RoadMapChart
            :draws="analysisStore.roadMapData.draws"
            :pool-size="POOL_SIZE"
            :show-special="true"
          />
          <p class="chart-note"><i class="fas fa-info-circle"></i> 矩陣圖：Y 軸為號碼，X 軸為期數，黃色圓點為一般號碼、紫色圓點為特別號；可橫向捲動查看更多期</p>
        </section>

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
          <div class="section-header">
            <h2><i class="fas fa-history"></i> 歷史開獎紀錄</h2>
            <div class="export-btns">
              <button class="export-btn" @click="exportDrawsCsv">
                <i class="fas fa-file-csv"></i> 匯出開獎紀錄
              </button>
              <button class="export-btn" @click="exportStatsCsv">
                <i class="fas fa-file-csv"></i> 匯出統計數據
              </button>
            </div>
          </div>
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

h1, h2 { display: flex; align-items: center; gap: var(--spacing-sm); }
h1 i { color: var(--color-primary); }
h3 { display: flex; align-items: center; gap: var(--spacing-sm); }

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
  min-width: 0;
}

.charts-grid .card :deep(.hot-cold-chart),
.charts-grid .card :deep(.missing-value-chart) {
  flex: 1;
  min-height: 320px;
}

.section-title {
  margin-bottom: var(--spacing-md);
}

.advanced-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.advanced-grid .card {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.advanced-grid .card h3 {
  margin-bottom: var(--spacing-sm);
  font-size: 1rem;
  color: var(--color-text, #2D3436);
}

.advanced-full {
  grid-column: 1 / -1;
}

.full-width-section {
  margin-bottom: var(--spacing-lg);
}

.full-width-section h2 {
  margin-bottom: var(--spacing-md);
}

.chart-note {
  margin-top: var(--spacing-sm);
  padding-top: var(--spacing-sm);
  border-top: 1px dashed var(--color-border);
  font-size: 0.8rem;
  color: var(--color-text-muted);
  line-height: 1.5;
}
.chart-note i {
  margin-right: var(--spacing-xs);
  color: var(--color-primary-dark);
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

/* 匯出按鈕 */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}
.section-header h2 {
  margin-bottom: 0;
}
.export-btns {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}
.export-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  font-size: 0.8rem;
  font-family: inherit;
  cursor: pointer;
  transition: border-color 0.2s, color 0.2s;
}
.export-btn:hover {
  border-color: var(--color-primary-dark);
  color: var(--color-text);
}
.export-btn i {
  font-size: 0.85rem;
}

@media (max-width: 768px) {
  .stat-cards {
    grid-template-columns: 1fr;
    gap: var(--spacing-md);
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }

  .advanced-grid {
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
