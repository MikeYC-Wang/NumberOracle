<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useLotteryStore } from '../stores/lotteryStore'
import StatCard from '../components/common/StatCard.vue'
import * as echarts from 'echarts'
import { nextTick } from 'vue'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'
const lotteryStore = useLotteryStore()

// --- 設定面板 ---
const selectedGame = ref('')
const selectedStrategy = ref<'random' | 'hot_weighted' | 'cold_weighted' | 'balanced'>('random')
const analysisPeriods = ref(50)
const testPeriods = ref(30)
const simulations = ref(100)

interface StrategyOption {
  value: 'random' | 'hot_weighted' | 'cold_weighted' | 'balanced'
  label: string
  description: string
  icon: string
}

const strategies: StrategyOption[] = [
  { value: 'random', label: '純隨機', description: '每個號碼等機率抽出，作為對照基準', icon: 'fas fa-dice' },
  { value: 'hot_weighted', label: '熱門加權', description: '近期常出現的號碼機率較高', icon: 'fas fa-fire' },
  { value: 'cold_weighted', label: '冷門加權', description: '近期少出現的號碼機率較高', icon: 'fas fa-snowflake' },
  { value: 'balanced', label: '均衡策略', description: '從熱門取一半、冷門取一半', icon: 'fas fa-balance-scale' },
]

// --- 回測結果 (對應 API 回傳格式) ---
interface BacktestResults {
  avg_match: number
  max_match: number
  match_distribution: Record<string, number>
  hit_rate_any: number
  hit_rate_3plus: number
}

interface BacktestResponse {
  game: string
  strategy: string
  test_draws: number
  simulations_per_draw: number
  total_simulations: number
  results: BacktestResults
  comparison: BacktestResults | null
}

const backtestResult = ref<BacktestResponse | null>(null)
const backtesting = ref(false)
const backtestError = ref<string | null>(null)

const chartRef = ref<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts | null = null

const canStart = computed(() => {
  return selectedGame.value !== '' && !backtesting.value
})

const strategyLabel = computed(() => {
  return strategies.find(s => s.value === selectedStrategy.value)?.label ?? ''
})

const summaryText = computed(() => {
  if (!backtestResult.value) return ''
  const b = backtestResult.value
  const r = b.results
  let text = `${strategyLabel.value} 在 ${b.test_draws} 期 x ${b.simulations_per_draw} 次模擬 (共 ${b.total_simulations} 次) 中，平均命中 ${r.avg_match} 個號碼`
  if (b.comparison) {
    const diff = r.avg_match - b.comparison.avg_match
    const word = diff > 0 ? '優於' : diff < 0 ? '劣於' : '等於'
    text += `，${word}隨機策略的 ${b.comparison.avg_match}。`
  } else {
    text += '。'
  }
  return text
})

async function startBacktest() {
  if (!canStart.value) return

  backtesting.value = true
  backtestError.value = null
  backtestResult.value = null

  try {
    const res = await fetch(`${API_BASE}/draws/backtest/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        game: selectedGame.value,
        strategy: selectedStrategy.value,
        recent: analysisPeriods.value,
        test_draws: testPeriods.value,
        simulations: simulations.value,
      }),
    })

    if (!res.ok) {
      const data = await res.json().catch(() => ({}))
      throw new Error(data.detail || data.message || `API 錯誤: ${res.status}`)
    }

    backtestResult.value = await res.json()
    await nextTick()
    renderChart()
  } catch (e) {
    backtestError.value = e instanceof Error ? e.message : '回測失敗'
  } finally {
    backtesting.value = false
  }
}

function renderChart() {
  if (!chartRef.value || !backtestResult.value) return

  if (chartInstance) {
    chartInstance.dispose()
  }
  chartInstance = echarts.init(chartRef.value)

  const result = backtestResult.value.results
  const comparison = backtestResult.value.comparison

  // Determine max hit count from distribution keys
  const allKeys = new Set<number>()
  for (const k of Object.keys(result.match_distribution)) allKeys.add(Number(k))
  if (comparison) {
    for (const k of Object.keys(comparison.match_distribution)) allKeys.add(Number(k))
  }
  const maxKey = Math.max(...allKeys, 5)
  const categories: string[] = []
  for (let i = 0; i <= maxKey; i++) categories.push(String(i))

  const barColors = ['#B2BEC3', '#2A9D8F', '#E9C46A', '#E76F51', '#C95A3E', '#8B0000']

  const strategyData = categories.map((c, i) => ({
    value: result.match_distribution[c] ?? 0,
    itemStyle: {
      color: barColors[Math.min(i, barColors.length - 1)],
    },
  }))

  const series: echarts.SeriesOption[] = [
    {
      name: strategyLabel.value,
      type: 'bar',
      data: strategyData,
      barMaxWidth: 50,
    },
  ]

  if (comparison) {
    const compData = categories.map(c => comparison.match_distribution[c] ?? 0)
    series.push({
      name: '隨機對照',
      type: 'bar',
      data: compData,
      barMaxWidth: 50,
      itemStyle: { color: 'rgba(178, 190, 195, 0.5)' },
    })
  }

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
    },
    legend: comparison ? { data: [strategyLabel.value, '隨機對照'] } : undefined,
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: categories,
      name: '命中數',
      axisLabel: { color: '#636E72' },
    },
    yAxis: {
      type: 'value',
      name: '出現次數',
      axisLabel: { color: '#636E72' },
    },
    series,
  }

  chartInstance.setOption(option)

  const resizeObserver = new ResizeObserver(() => {
    chartInstance?.resize()
  })
  resizeObserver.observe(chartRef.value)
}

onMounted(async () => {
  if (lotteryStore.games.length === 0) {
    await lotteryStore.fetchGames()
  }
  if (lotteryStore.games.length > 0 && !selectedGame.value) {
    selectedGame.value = lotteryStore.games[0].code
  }
})
</script>

<template>
  <div class="page-content">
    <div class="container">
      <h1>
        <i class="fas fa-flask"></i>
        回測系統
      </h1>
      <p class="subtitle">驗證選號策略在歷史數據中的表現</p>

      <!-- 設定面板 -->
      <div class="settings-panel card">
        <h2 class="settings-title">
          <i class="fas fa-sliders-h"></i>
          回測設定
        </h2>

        <div class="settings-grid">
          <!-- 彩種選擇 -->
          <div class="setting-group">
            <label for="bt-game">
              <i class="fas fa-dice"></i> 彩種
            </label>
            <select id="bt-game" v-model="selectedGame" :disabled="backtesting">
              <option value="" disabled>-- 請選擇 --</option>
              <option
                v-for="game in lotteryStore.games"
                :key="game.code"
                :value="game.code"
              >
                {{ game.name }}
              </option>
            </select>
          </div>

          <!-- 策略選擇 -->
          <div class="setting-group setting-group--full">
            <label>
              <i class="fas fa-chess-knight"></i> 策略
            </label>
            <div class="strategy-options">
              <label
                v-for="opt in strategies"
                :key="opt.value"
                class="strategy-radio"
                :class="{ 'strategy-radio--active': selectedStrategy === opt.value }"
              >
                <input
                  type="radio"
                  name="bt-strategy"
                  :value="opt.value"
                  v-model="selectedStrategy"
                  :disabled="backtesting"
                />
                <span class="strategy-radio__content">
                  <span class="strategy-radio__label">
                    <i :class="opt.icon"></i>
                    {{ opt.label }}
                  </span>
                  <span class="strategy-radio__desc">{{ opt.description }}</span>
                </span>
              </label>
            </div>
          </div>

          <!-- 數值參數 -->
          <div class="setting-group">
            <label for="bt-analysis">
              <i class="fas fa-chart-bar"></i> 分析期數
            </label>
            <input
              id="bt-analysis"
              type="number"
              v-model.number="analysisPeriods"
              :min="10"
              :max="200"
              :disabled="backtesting"
            />
          </div>

          <div class="setting-group">
            <label for="bt-test">
              <i class="fas fa-vial"></i> 測試期數
            </label>
            <input
              id="bt-test"
              type="number"
              v-model.number="testPeriods"
              :min="10"
              :max="200"
              :disabled="backtesting"
            />
          </div>

          <div class="setting-group">
            <label for="bt-sim">
              <i class="fas fa-redo"></i> 模擬次數
            </label>
            <input
              id="bt-sim"
              type="number"
              v-model.number="simulations"
              :min="10"
              :max="500"
              :disabled="backtesting"
            />
          </div>
        </div>

        <button
          class="start-btn"
          :disabled="!canStart"
          @click="startBacktest"
        >
          <i :class="backtesting ? 'fas fa-spinner fa-spin' : 'fas fa-play'"></i>
          {{ backtesting ? '回測中，請稍候...' : '開始回測' }}
        </button>
      </div>

      <!-- Loading -->
      <div v-if="backtesting" class="loading">
        <i class="fas fa-cog fa-spin fa-2x"></i>
        <p>正在進行回測模擬，可能需要幾秒鐘...</p>
      </div>

      <!-- Error -->
      <div v-if="backtestError" class="error-msg">
        <i class="fas fa-exclamation-triangle"></i> {{ backtestError }}
      </div>

      <!-- 結果區 -->
      <template v-if="backtestResult && !backtesting">
        <!-- 摘要卡片 -->
        <div class="stat-cards">
          <StatCard
            title="平均命中數"
            :value="backtestResult.results.avg_match"
            icon="fas fa-bullseye"
          />
          <StatCard
            title="最高命中數"
            :value="backtestResult.results.max_match"
            icon="fas fa-trophy"
            trend="up"
          />
          <StatCard
            title="至少中1個比例"
            :value="backtestResult.results.hit_rate_any + '%'"
            icon="fas fa-percentage"
          />
        </div>

        <!-- 圖表 -->
        <section class="card chart-section">
          <h2><i class="fas fa-chart-bar"></i> 命中數分布</h2>
          <div class="chart-scroll-wrapper">
            <div ref="chartRef" class="backtest-chart"></div>
          </div>
        </section>

        <!-- 文字總結 -->
        <div class="summary-text card">
          <i class="fas fa-info-circle"></i>
          {{ summaryText }}
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.subtitle {
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-xl);
}

h1, h2 {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}
h1 i { color: var(--color-secondary); }
h2 i { color: var(--color-primary-dark); }

/* 設定面板 */
.settings-panel {
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-lg);
}
.settings-title {
  font-size: 1.15rem;
  margin-bottom: var(--spacing-lg);
}
.settings-title i {
  color: var(--color-primary);
}

.settings-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}
.setting-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}
.setting-group--full {
  flex-basis: 100%;
}
.setting-group > label {
  font-weight: 600;
  color: var(--color-text);
  white-space: nowrap;
  font-size: 0.95rem;
}
.setting-group > label i {
  color: var(--color-primary-dark);
  margin-right: var(--spacing-xs);
}
.setting-group select,
.setting-group input[type="number"] {
  padding: var(--spacing-sm) var(--spacing-md);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: 1rem;
  font-family: inherit;
  cursor: pointer;
  transition: border-color 0.2s;
  min-width: 140px;
}
.setting-group select:focus,
.setting-group input[type="number"]:focus {
  outline: none;
  border-color: var(--color-primary);
}
.setting-group input[type="number"] {
  max-width: 140px;
}

/* 策略 radio */
.strategy-options {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}
.strategy-radio {
  display: flex;
  align-items: center;
  cursor: pointer;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-sm) var(--spacing-md);
  transition: border-color 0.2s, background 0.2s;
  flex: 1 1 180px;
  max-width: 280px;
}
.strategy-radio:hover {
  border-color: var(--color-primary);
}
.strategy-radio--active {
  border-color: var(--color-accent);
  background: rgba(231, 111, 81, 0.06);
}
.strategy-radio input[type="radio"] {
  margin-right: var(--spacing-sm);
  accent-color: var(--color-accent);
  flex-shrink: 0;
}
.strategy-radio__content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.strategy-radio__label {
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--color-text);
}
.strategy-radio__label i {
  margin-right: var(--spacing-xs);
  font-size: 0.85rem;
  color: var(--color-primary-dark);
}
.strategy-radio__desc {
  font-size: 0.78rem;
  color: var(--color-text-muted);
  line-height: 1.3;
}

/* 開始回測按鈕 */
.start-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-xl);
  background: linear-gradient(135deg, var(--color-secondary), var(--color-secondary-dark));
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-size: 1.1rem;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 4px 12px rgba(42, 157, 143, 0.3);
}
.start-btn:hover:not(:disabled) {
  transform: scale(1.03);
  box-shadow: 0 6px 18px rgba(42, 157, 143, 0.45);
}
.start-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Loading */
.loading {
  text-align: center;
  padding: var(--spacing-2xl);
  color: var(--color-text-muted);
  font-size: 1rem;
}
.loading i {
  display: block;
  margin-bottom: var(--spacing-md);
  color: var(--color-secondary);
}
.loading p {
  margin-top: var(--spacing-sm);
}

.error-msg {
  text-align: center;
  padding: var(--spacing-lg);
  color: var(--color-accent);
  font-size: 1rem;
}

/* 統計卡片 */
.stat-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

/* 圖表 */
.chart-section {
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-lg);
}
.chart-section h2 {
  margin-bottom: var(--spacing-md);
}

.chart-scroll-wrapper {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.backtest-chart {
  width: 100%;
  min-width: 400px;
  height: 400px;
}

/* 文字總結 */
.summary-text {
  padding: var(--spacing-lg);
  font-size: 1rem;
  line-height: 1.6;
  color: var(--color-text);
}
.summary-text i {
  color: var(--color-secondary);
  margin-right: var(--spacing-sm);
}

@media (max-width: 768px) {
  .stat-cards {
    grid-template-columns: 1fr;
    gap: var(--spacing-md);
  }

  .settings-grid {
    flex-direction: column;
  }

  .strategy-options {
    flex-direction: column;
  }

  .strategy-radio {
    max-width: 100%;
  }

  .setting-group input[type="number"] {
    max-width: 100%;
    min-width: 100%;
  }

  .setting-group select {
    min-width: 100%;
  }

  .backtest-chart {
    height: 300px;
  }
}
</style>
