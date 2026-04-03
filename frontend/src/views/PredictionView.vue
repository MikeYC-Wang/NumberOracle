<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useLotteryStore } from '../stores/lotteryStore'
import { useAnalysisStore } from '../stores/analysisStore'
import type { LotteryGame } from '../types/lottery'
import LotteryBall from '../components/common/LotteryBall.vue'

const lotteryStore = useLotteryStore()
const analysisStore = useAnalysisStore()

// --- 策略定義 ---
type Strategy = 'random' | 'hot_weighted' | 'cold_weighted' | 'balanced' | 'manual'

interface StrategyOption {
  value: Strategy
  label: string
  description: string
  icon: string
}

const strategies: StrategyOption[] = [
  { value: 'random', label: '純隨機', description: '每個號碼等機率抽出', icon: 'fas fa-dice' },
  { value: 'hot_weighted', label: '熱門加權', description: '近期常出現的號碼機率較高', icon: 'fas fa-fire' },
  { value: 'cold_weighted', label: '冷門加權', description: '近期少出現的號碼機率較高（遺漏值高者優先）', icon: 'fas fa-snowflake' },
  { value: 'balanced', label: '均衡策略', description: '從熱門取一半、冷門取一半', icon: 'fas fa-balance-scale' },
  { value: 'manual', label: '手動選號', description: '自己點選號碼球', icon: 'fas fa-hand-pointer' },
]

// --- 彩種選擇 ---
const selectedCode = ref<string>('')
const currentGame = computed<LotteryGame | null>(() => lotteryStore.currentGame)

// --- 策略與分析期數 ---
const selectedStrategy = ref<Strategy>('random')
const recentPeriods = ref(50)

const showRecentInput = computed(() =>
  selectedStrategy.value !== 'random' && selectedStrategy.value !== 'manual'
)

function onGameChange() {
  lotteryStore.selectGame(selectedCode.value)
  drawnNumbers.value = []
  specialNumber.value = null
  visibleCount.value = 0
  clearManualSelection()
  if (selectedCode.value && showRecentInput.value) {
    analysisStore.fetchHotCold(selectedCode.value, recentPeriods.value)
  }
}

function onStrategyChange() {
  clearManualSelection()
  drawnNumbers.value = []
  specialNumber.value = null
  visibleCount.value = 0
  if (selectedCode.value && showRecentInput.value) {
    analysisStore.fetchHotCold(selectedCode.value, recentPeriods.value)
  }
}

function onRecentChange() {
  if (selectedCode.value && showRecentInput.value) {
    analysisStore.fetchHotCold(selectedCode.value, recentPeriods.value)
  }
}

// --- 手動選號 ---
const manualMainNumbers = ref<Set<number>>(new Set())
const manualSpecialNumber = ref<number | null>(null)

function clearManualSelection() {
  manualMainNumbers.value = new Set()
  manualSpecialNumber.value = null
}

function toggleMainNumber(num: number) {
  const next = new Set(manualMainNumbers.value)
  if (next.has(num)) {
    next.delete(num)
  } else {
    if (currentGame.value && next.size >= currentGame.value.main_pick_count) return
    next.add(num)
  }
  manualMainNumbers.value = next
}

function toggleSpecialNumber(num: number) {
  if (manualSpecialNumber.value === num) {
    manualSpecialNumber.value = null
  } else {
    manualSpecialNumber.value = num
  }
}

const manualMainFull = computed(() => {
  if (!currentGame.value) return false
  return manualMainNumbers.value.size >= currentGame.value.main_pick_count
})

const manualComplete = computed(() => {
  if (!currentGame.value) return false
  const mainOk = manualMainNumbers.value.size === currentGame.value.main_pick_count
  if (currentGame.value.has_special) {
    return mainOk && manualSpecialNumber.value !== null
  }
  return mainOk
})

// --- 搖獎狀態 ---
const isRolling = ref(false)
const drawnNumbers = ref<number[]>([])
const specialNumber = ref<number | null>(null)
const visibleCount = ref(0)

const totalBalls = computed(() =>
  drawnNumbers.value.length + (specialNumber.value !== null ? 1 : 0)
)

// --- 能否搖獎 ---
const canRoll = computed(() => {
  if (!currentGame.value || isRolling.value) return false
  if (selectedStrategy.value === 'manual') return manualComplete.value
  return true
})

// --- 選號邏輯 ---

/** 加權隨機抽取 (不重複) */
function weightedPick(pool: Map<number, number>, pickCount: number): number[] {
  const picked: number[] = []
  const remaining = new Map(pool)

  while (picked.length < pickCount && remaining.size > 0) {
    let totalWeight = 0
    for (const w of remaining.values()) totalWeight += w

    let rand = Math.random() * totalWeight
    for (const [num, w] of remaining) {
      rand -= w
      if (rand <= 0) {
        picked.push(num)
        remaining.delete(num)
        break
      }
    }
  }

  return picked.sort((a, b) => a - b)
}

/** 純隨機 */
function pickRandom(poolSize: number, pickCount: number): number[] {
  const pool = new Map<number, number>()
  for (let i = 1; i <= poolSize; i++) pool.set(i, 1)
  return weightedPick(pool, pickCount)
}

/** 熱門加權：weight = 1 + count */
function pickHotWeighted(poolSize: number, pickCount: number): number[] {
  const freqs = analysisStore.frequencies
  const pool = new Map<number, number>()
  for (let i = 1; i <= poolSize; i++) {
    const freq = freqs.find(f => f.number === i)
    pool.set(i, 1 + (freq ? freq.count : 0))
  }
  return weightedPick(pool, pickCount)
}

/** 冷門加權：weight = 1 + (maxCount - count) */
function pickColdWeighted(poolSize: number, pickCount: number): number[] {
  const freqs = analysisStore.frequencies
  const maxCount = freqs.reduce((mx, f) => Math.max(mx, f.count), 0)
  const pool = new Map<number, number>()
  for (let i = 1; i <= poolSize; i++) {
    const freq = freqs.find(f => f.number === i)
    pool.set(i, 1 + (maxCount - (freq ? freq.count : 0)))
  }
  return weightedPick(pool, pickCount)
}

/** 均衡策略：熱門取 ceil(n/2)、冷門取其餘 */
function pickBalanced(poolSize: number, pickCount: number): number[] {
  const freqs = analysisStore.frequencies

  // 建立所有號碼的 count 表
  const countMap = new Map<number, number>()
  for (let i = 1; i <= poolSize; i++) {
    const freq = freqs.find(f => f.number === i)
    countMap.set(i, freq ? freq.count : 0)
  }

  // 按 count 降序排列
  const sorted = Array.from(countMap.entries()).sort((a, b) => b[1] - a[1])
  const half = Math.ceil(sorted.length / 2)
  const hotGroup = sorted.slice(0, half).map(e => e[0])
  const coldGroup = sorted.slice(half).map(e => e[0])

  const hotCount = Math.ceil(pickCount / 2)
  const coldCount = pickCount - hotCount

  // 從各組隨機取
  const hotPicked = shuffleAndTake(hotGroup, hotCount)
  const coldPicked = shuffleAndTake(coldGroup, coldCount)

  return [...hotPicked, ...coldPicked].sort((a, b) => a - b)
}

function shuffleAndTake(arr: number[], count: number): number[] {
  const copy = [...arr]
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[copy[i], copy[j]] = [copy[j], copy[i]]
  }
  return copy.slice(0, count)
}

function pickSpecialNumber(poolSize: number): number {
  return Math.floor(Math.random() * poolSize) + 1
}

function generateNumbers(game: LotteryGame): { main: number[]; special: number | null } {
  let main: number[]
  let special: number | null = null

  switch (selectedStrategy.value) {
    case 'random':
      main = pickRandom(game.main_pool_size, game.main_pick_count)
      break
    case 'hot_weighted':
      main = pickHotWeighted(game.main_pool_size, game.main_pick_count)
      break
    case 'cold_weighted':
      main = pickColdWeighted(game.main_pool_size, game.main_pick_count)
      break
    case 'balanced':
      main = pickBalanced(game.main_pool_size, game.main_pick_count)
      break
    case 'manual':
      main = Array.from(manualMainNumbers.value).sort((a, b) => a - b)
      special = game.has_special ? manualSpecialNumber.value : null
      return { main, special }
    default:
      main = pickRandom(game.main_pool_size, game.main_pick_count)
  }

  if (game.has_special && game.special_pool_size) {
    special = pickSpecialNumber(game.special_pool_size)
  }

  return { main, special }
}

// --- 搖獎動畫 ---
async function startRolling() {
  if (!canRoll.value || !currentGame.value) return

  const game = currentGame.value
  isRolling.value = true
  drawnNumbers.value = []
  specialNumber.value = null
  visibleCount.value = 0

  const result = generateNumbers(game)
  drawnNumbers.value = result.main
  specialNumber.value = result.special

  for (let i = 1; i <= totalBalls.value; i++) {
    await delay(300)
    visibleCount.value = i
  }

  isRolling.value = false

  const strategyLabel = strategies.find(s => s.value === selectedStrategy.value)?.label ?? ''

  predictionHistory.value.unshift({
    timestamp: new Date(),
    gameCode: game.code,
    gameName: game.name,
    strategy: selectedStrategy.value,
    strategyLabel,
    numbers: [...result.main],
    special: result.special,
  })
}

function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

// --- 手動選號確認 ---
function confirmManual() {
  if (!manualComplete.value) return
  startRolling()
}

// --- 歷史紀錄 ---
interface PredictionRecord {
  timestamp: Date
  gameCode: string
  gameName: string
  strategy: Strategy
  strategyLabel: string
  numbers: number[]
  special: number | null
}

const predictionHistory = ref<PredictionRecord[]>([])

function formatTime(date: Date): string {
  const h = String(date.getHours()).padStart(2, '0')
  const m = String(date.getMinutes()).padStart(2, '0')
  const s = String(date.getSeconds()).padStart(2, '0')
  return `${h}:${m}:${s}`
}

// --- 初始化 ---
onMounted(async () => {
  if (lotteryStore.games.length === 0) {
    await lotteryStore.fetchGames()
  }
  if (lotteryStore.games.length > 0 && !selectedCode.value) {
    selectedCode.value = lotteryStore.games[0].code
    onGameChange()
  }
})
</script>

<template>
  <div class="page-content">
    <div class="container">
      <h1>
        <i class="fas fa-magic"></i>
        預測搖獎區
      </h1>
      <p class="subtitle">自由選擇策略，掌握你的選號方式</p>

      <!-- ====== 設定面板 ====== -->
      <div class="settings-panel card">
        <h2 class="settings-title">
          <i class="fas fa-sliders-h"></i>
          選號設定
        </h2>

        <div class="settings-grid">
          <!-- 彩種選擇 -->
          <div class="setting-group">
            <label for="game-select">
              <i class="fas fa-dice"></i>
              彩種
            </label>
            <select
              id="game-select"
              v-model="selectedCode"
              @change="onGameChange"
              :disabled="isRolling"
            >
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

          <!-- 選號策略 -->
          <div class="setting-group setting-group--strategy">
            <label>
              <i class="fas fa-chess-knight"></i>
              選號策略
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
                  name="strategy"
                  :value="opt.value"
                  v-model="selectedStrategy"
                  :disabled="isRolling"
                  @change="onStrategyChange"
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

          <!-- 分析期數 -->
          <div v-if="showRecentInput" class="setting-group">
            <label for="recent-input">
              <i class="fas fa-chart-bar"></i>
              分析期數
            </label>
            <div class="recent-input-row">
              <input
                id="recent-input"
                type="number"
                v-model.number="recentPeriods"
                :min="10"
                :max="500"
                :disabled="isRolling"
                @change="onRecentChange"
              />
              <span class="recent-hint">範圍 10 ~ 500 期</span>
            </div>
          </div>
        </div>
      </div>

      <!-- ====== 手動選號面板 ====== -->
      <div
        v-if="selectedStrategy === 'manual' && currentGame"
        class="manual-panel card"
      >
        <h2 class="manual-title">
          <i class="fas fa-hand-pointer"></i>
          手動選號
        </h2>

        <!-- 主號碼 -->
        <div class="manual-section">
          <div class="manual-counter">
            已選 {{ manualMainNumbers.size }} / {{ currentGame.main_pick_count }} 個主號碼
          </div>
          <div class="number-grid">
            <div
              v-for="n in currentGame.main_pool_size"
              :key="'main-' + n"
              class="number-grid__cell"
              :class="{
                'number-grid__cell--selected': manualMainNumbers.has(n),
                'number-grid__cell--disabled': !manualMainNumbers.has(n) && manualMainFull
              }"
              @click="toggleMainNumber(n)"
            >
              <LotteryBall
                :number="n"
                :type="manualMainNumbers.has(n) ? 'hot' : 'normal'"
                size="md"
              />
            </div>
          </div>
        </div>

        <!-- 特別號 -->
        <div
          v-if="currentGame.has_special && currentGame.special_pool_size"
          class="manual-section"
        >
          <div class="manual-counter">
            特別號：{{ manualSpecialNumber !== null ? '已選 1' : '未選' }} / 1 個
          </div>
          <div class="number-grid">
            <div
              v-for="n in currentGame.special_pool_size"
              :key="'sp-' + n"
              class="number-grid__cell"
              :class="{
                'number-grid__cell--selected': manualSpecialNumber === n
              }"
              @click="toggleSpecialNumber(n)"
            >
              <LotteryBall
                :number="n"
                :type="manualSpecialNumber === n ? 'special' : 'normal'"
                size="md"
              />
            </div>
          </div>
        </div>

        <button
          class="confirm-btn"
          :disabled="!manualComplete || isRolling"
          @click="confirmManual"
        >
          <i class="fas fa-check-circle"></i>
          確認選號
        </button>
      </div>

      <!-- ====== 搖獎動畫區 ====== -->
      <div class="prediction-area card">
        <!-- 未選彩種 -->
        <div v-if="!currentGame" class="empty-state">
          <i class="fas fa-hand-pointer fa-3x"></i>
          <p>請先選擇彩種開始搖獎</p>
        </div>

        <!-- 搖獎主區域 -->
        <div v-else class="rolling-zone">
          <div class="game-info">
            <span class="game-badge">{{ currentGame.name }}</span>
            <span class="game-rule">
              {{ currentGame.main_pick_count }} / {{ currentGame.main_pool_size }}
              <template v-if="currentGame.has_special">
                + 特別號 1 / {{ currentGame.special_pool_size }}
              </template>
            </span>
          </div>

          <!-- 號碼球顯示區 -->
          <div class="balls-display">
            <template v-if="drawnNumbers.length === 0 && !isRolling">
              <div class="placeholder-balls">
                <span
                  v-for="i in currentGame.main_pick_count"
                  :key="i"
                  class="placeholder-ball"
                >
                  ?
                </span>
                <template v-if="currentGame.has_special">
                  <span class="plus-sign">+</span>
                  <span class="placeholder-ball placeholder-ball--special">?</span>
                </template>
              </div>
            </template>

            <template v-else>
              <div class="drawn-balls">
                <TransitionGroup name="ball-pop">
                  <LotteryBall
                    v-for="(num, idx) in drawnNumbers"
                    :key="'main-' + num"
                    :number="num"
                    type="hot"
                    size="lg"
                    class="ball-animated"
                    :class="{ 'ball-visible': idx < visibleCount }"
                  />
                </TransitionGroup>

                <template v-if="currentGame.has_special && specialNumber !== null">
                  <span
                    class="plus-sign plus-sign--large"
                    :class="{ 'ball-visible': visibleCount > drawnNumbers.length }"
                  >+</span>
                  <LotteryBall
                    :number="specialNumber"
                    type="special"
                    size="lg"
                    class="ball-animated"
                    :class="{ 'ball-visible': visibleCount > drawnNumbers.length }"
                  />
                </template>
              </div>
            </template>
          </div>

          <!-- 搖獎按鈕 (非手動時顯示) -->
          <button
            v-if="selectedStrategy !== 'manual'"
            class="roll-btn"
            :class="{ 'roll-btn--rolling': isRolling }"
            :disabled="!canRoll"
            @click="startRolling"
          >
            <i :class="isRolling ? 'fas fa-spinner fa-spin' : 'fas fa-random'"></i>
            {{ isRolling ? '搖獎中...' : '開始搖獎' }}
          </button>
        </div>
      </div>

      <!-- ====== 歷史預測紀錄 ====== -->
      <div v-if="predictionHistory.length > 0" class="history-section">
        <h2>
          <i class="fas fa-history"></i>
          本次預測紀錄
        </h2>
        <div class="history-list">
          <div
            v-for="(record, idx) in predictionHistory"
            :key="idx"
            class="history-item card"
          >
            <div class="history-meta">
              <span class="history-time">
                <i class="fas fa-clock"></i>
                {{ formatTime(record.timestamp) }}
              </span>
              <span class="history-game">{{ record.gameName }}</span>
              <span class="history-strategy">
                <i class="fas fa-chess-knight"></i>
                {{ record.strategyLabel }}
              </span>
            </div>
            <div class="history-balls">
              <LotteryBall
                v-for="num in record.numbers"
                :key="'h-' + idx + '-' + num"
                :number="num"
                type="hot"
                size="sm"
              />
              <template v-if="record.special !== null">
                <span class="plus-sign">+</span>
                <LotteryBall
                  :number="record.special"
                  type="special"
                  size="sm"
                />
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.subtitle {
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-xl);
}
h1 i {
  color: var(--color-accent);
  margin-right: var(--spacing-sm);
}

/* ====== 設定面板 ====== */
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
  margin-right: var(--spacing-sm);
}
.settings-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-lg);
}
.setting-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
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
  min-width: 180px;
}
.setting-group select:focus,
.setting-group input[type="number"]:focus {
  outline: none;
  border-color: var(--color-primary);
}
.setting-group input[type="number"] {
  min-width: 100px;
  max-width: 120px;
}

.setting-group--strategy {
  flex-basis: 100%;
}

/* 策略 radio 組 */
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
  max-width: 260px;
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

/* 分析期數 */
.recent-input-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}
.recent-hint {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  white-space: nowrap;
}

/* ====== 手動選號面板 ====== */
.manual-panel {
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-lg);
}
.manual-title {
  font-size: 1.15rem;
  margin-bottom: var(--spacing-md);
}
.manual-title i {
  color: var(--color-accent);
  margin-right: var(--spacing-sm);
}
.manual-section {
  margin-bottom: var(--spacing-lg);
}
.manual-counter {
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-sm);
}

.number-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(48px, 1fr));
  gap: 8px;
  width: 100%;
}
.number-grid__cell {
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: var(--radius-md);
  padding: 2px;
  transition: transform 0.15s, opacity 0.15s;
}
.number-grid__cell:hover {
  transform: scale(1.15);
}
.number-grid__cell--selected {
  transform: scale(1.1);
}
.number-grid__cell--disabled {
  opacity: 0.35;
  cursor: not-allowed;
  pointer-events: none;
}

.confirm-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-lg);
  background: linear-gradient(135deg, var(--color-accent), var(--color-accent-dark));
  color: #fff;
  border: none;
  border-radius: var(--radius-full);
  font-size: 1rem;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s, opacity 0.2s;
  box-shadow: 0 4px 12px rgba(231, 111, 81, 0.3);
}
.confirm-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 6px 18px rgba(231, 111, 81, 0.45);
}
.confirm-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ====== 搖獎主區域 ====== */
.prediction-area {
  min-height: 360px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--color-surface) 0%, #faf8f0 100%);
  border-radius: var(--radius-xl);
  position: relative;
  overflow: hidden;
}

.empty-state {
  text-align: center;
  color: var(--color-text-muted);
}
.empty-state i {
  color: var(--color-primary);
  margin-bottom: var(--spacing-md);
}
.empty-state p {
  margin-top: var(--spacing-sm);
  font-size: 1.1rem;
}

.rolling-zone {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-xl) var(--spacing-lg);
  gap: var(--spacing-xl);
}

/* 彩種資訊 */
.game-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  flex-wrap: wrap;
  justify-content: center;
}
.game-badge {
  background: var(--color-primary);
  color: #fff;
  padding: var(--spacing-xs) var(--spacing-md);
  border-radius: var(--radius-full);
  font-weight: 700;
  font-size: 0.95rem;
}
.game-rule {
  color: var(--color-text-secondary);
  font-size: 0.9rem;
}

/* === 號碼球顯示 === */
.balls-display {
  min-height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-balls,
.drawn-balls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.placeholder-ball {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 50px;
  height: 50px;
  border-radius: var(--radius-full);
  border: 2px dashed var(--color-border);
  color: var(--color-text-muted);
  font-size: 1.25rem;
  font-weight: 700;
  font-family: var(--font-mono);
}
.placeholder-ball--special {
  border-color: var(--color-ball-special);
  color: var(--color-ball-special);
}

.plus-sign {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text-muted);
  margin: 0 var(--spacing-xs);
}
.plus-sign--large {
  font-size: 1.5rem;
  opacity: 0;
  transform: scale(0.5);
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.plus-sign--large.ball-visible {
  opacity: 1;
  transform: scale(1);
}

/* 號碼球動畫 */
.ball-animated {
  opacity: 0;
  transform: scale(0.3) rotateY(180deg);
  transition: opacity 0.4s cubic-bezier(0.34, 1.56, 0.64, 1),
              transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.ball-animated.ball-visible {
  opacity: 1;
  transform: scale(1) rotateY(0deg);
}

/* === 搖獎按鈕 === */
.roll-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-xl);
  background: linear-gradient(135deg, var(--color-accent), var(--color-accent-dark));
  color: #fff;
  border: none;
  border-radius: var(--radius-full);
  font-size: 1.15rem;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  box-shadow: 0 4px 15px rgba(231, 111, 81, 0.35);
}
.roll-btn:hover:not(:disabled) {
  transform: scale(1.08);
  box-shadow: 0 6px 20px rgba(231, 111, 81, 0.5);
}
.roll-btn:active:not(:disabled) {
  transform: scale(0.97);
}
.roll-btn:disabled {
  cursor: not-allowed;
  opacity: 0.8;
}
.roll-btn--rolling {
  background: linear-gradient(135deg, var(--color-text-muted), var(--color-text-secondary));
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
}

/* ====== 歷史紀錄 ====== */
.history-section {
  margin-top: var(--spacing-2xl);
}
.history-section h2 {
  margin-bottom: var(--spacing-lg);
  font-size: 1.25rem;
}
.history-section h2 i {
  color: var(--color-secondary);
  margin-right: var(--spacing-sm);
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg);
  gap: var(--spacing-md);
  flex-wrap: wrap;
}

.history-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  flex-shrink: 0;
}
.history-time {
  color: var(--color-text-secondary);
  font-size: 0.85rem;
  font-family: var(--font-mono);
}
.history-time i {
  margin-right: var(--spacing-xs);
  color: var(--color-text-muted);
}
.history-game {
  background: var(--color-primary-light);
  color: var(--color-text);
  padding: 2px var(--spacing-sm);
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  font-weight: 600;
}
.history-strategy {
  color: var(--color-text-secondary);
  font-size: 0.8rem;
}
.history-strategy i {
  margin-right: 4px;
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.history-balls {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  flex-wrap: wrap;
}

/* === TransitionGroup === */
.ball-pop-enter-active {
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.ball-pop-enter-from {
  opacity: 0;
  transform: scale(0.3);
}

/* ====== RWD ====== */
@media (max-width: 600px) {
  .settings-grid {
    flex-direction: column;
  }
  .strategy-options {
    flex-direction: column;
  }
  .strategy-radio {
    max-width: 100%;
  }
  .prediction-area {
    min-height: 280px;
  }
  .rolling-zone {
    padding: var(--spacing-lg) var(--spacing-md);
  }
  .history-item {
    flex-direction: column;
    align-items: flex-start;
  }
  .number-grid {
    grid-template-columns: repeat(auto-fill, minmax(32px, 1fr));
    gap: 4px;
  }
}
</style>
