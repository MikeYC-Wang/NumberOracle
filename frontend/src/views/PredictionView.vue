<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useLotteryStore } from '../stores/lotteryStore'
import { useAnalysisStore } from '../stores/analysisStore'
import type { LotteryGame } from '../types/lottery'
import LotteryBall from '../components/common/LotteryBall.vue'

const lotteryStore = useLotteryStore()
const analysisStore = useAnalysisStore()

// --- 彩種選擇 ---
const selectedCode = ref<string>('')

const currentGame = computed<LotteryGame | null>(() => lotteryStore.currentGame)

function onGameChange() {
  lotteryStore.selectGame(selectedCode.value)
  if (selectedCode.value) {
    analysisStore.fetchHotCold(selectedCode.value)
  }
  // 切換彩種時清除目前搖獎結果
  drawnNumbers.value = []
  specialNumber.value = null
  visibleCount.value = 0
}

// --- 搖獎狀態 ---
const isRolling = ref(false)
const drawnNumbers = ref<number[]>([])
const specialNumber = ref<number | null>(null)
const visibleCount = ref(0)

// 總共要顯示的球數 (主號碼 + 可能的特別號)
const totalBalls = computed(() => {
  return drawnNumbers.value.length + (specialNumber.value !== null ? 1 : 0)
})

// --- 加權隨機選號 ---
function weightedRandomPick(poolSize: number, pickCount: number): number[] {
  const freqs = analysisStore.frequencies
  // 建立權重表：號碼 1 ~ poolSize
  const weights: number[] = []
  for (let i = 1; i <= poolSize; i++) {
    const freq = freqs.find(f => f.number === i)
    // 基礎權重 1，加上頻率作為額外權重 (熱門號碼權重更高)
    weights.push(1 + (freq ? freq.count : 0))
  }

  const picked: number[] = []
  const usedIndices = new Set<number>()

  while (picked.length < pickCount) {
    // 計算剩餘可選號碼的總權重
    let totalWeight = 0
    for (let i = 0; i < poolSize; i++) {
      if (!usedIndices.has(i)) totalWeight += weights[i]
    }

    let rand = Math.random() * totalWeight
    for (let i = 0; i < poolSize; i++) {
      if (usedIndices.has(i)) continue
      rand -= weights[i]
      if (rand <= 0) {
        picked.push(i + 1) // 號碼 = index + 1
        usedIndices.add(i)
        break
      }
    }
  }

  return picked.sort((a, b) => a - b)
}

function pickSpecialNumber(poolSize: number, excludeNumbers: number[]): number {
  // 特別號從獨立的號碼池中選取 (不排除主號碼，各彩種規則不同)
  // 威力彩特別號是獨立號碼池，其他可能從同池中選
  const candidates: number[] = []
  for (let i = 1; i <= poolSize; i++) {
    candidates.push(i)
  }
  return candidates[Math.floor(Math.random() * candidates.length)]
}

async function startRolling() {
  if (!currentGame.value || isRolling.value) return

  const game = currentGame.value
  isRolling.value = true
  drawnNumbers.value = []
  specialNumber.value = null
  visibleCount.value = 0

  // 產生號碼
  const mainNumbers = weightedRandomPick(game.main_pool_size, game.main_pick_count)
  let special: number | null = null
  if (game.has_special && game.special_pool_size) {
    special = pickSpecialNumber(game.special_pool_size, mainNumbers)
  }

  drawnNumbers.value = mainNumbers
  specialNumber.value = special

  // 依序顯示號碼球，每顆間隔 300ms
  for (let i = 1; i <= totalBalls.value; i++) {
    await delay(300)
    visibleCount.value = i
  }

  isRolling.value = false

  // 加入歷史紀錄
  predictionHistory.value.unshift({
    timestamp: new Date(),
    gameCode: game.code,
    gameName: game.name,
    numbers: [...mainNumbers],
    special,
  })
}

function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

// --- 歷史紀錄 ---
interface PredictionRecord {
  timestamp: Date
  gameCode: string
  gameName: string
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
  // 預設選第一個彩種
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
      <p class="subtitle">結合冷熱門加權的隨機選號體驗</p>

      <!-- 彩種選擇器 -->
      <div class="game-selector">
        <label for="game-select">
          <i class="fas fa-dice"></i>
          選擇彩種
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

      <!-- 搖獎動畫區 -->
      <div class="prediction-area card">
        <!-- 未選彩種時的提示 -->
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

          <!-- 搖獎按鈕 -->
          <button
            class="roll-btn"
            :class="{ 'roll-btn--rolling': isRolling }"
            :disabled="isRolling"
            @click="startRolling"
          >
            <i :class="isRolling ? 'fas fa-spinner fa-spin' : 'fas fa-random'"></i>
            {{ isRolling ? '搖獎中...' : '開始搖獎' }}
          </button>
        </div>
      </div>

      <!-- 歷史預測紀錄 -->
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

/* === 彩種選擇器 === */
.game-selector {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}
.game-selector label {
  font-weight: 600;
  color: var(--color-text);
  white-space: nowrap;
}
.game-selector label i {
  color: var(--color-primary-dark);
  margin-right: var(--spacing-xs);
}
.game-selector select {
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
.game-selector select:focus {
  outline: none;
  border-color: var(--color-primary);
}

/* === 搖獎主區域 === */
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

/* === 歷史紀錄 === */
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

/* === RWD === */
@media (max-width: 600px) {
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
}
</style>
