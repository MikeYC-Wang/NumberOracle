<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useLotteryStore } from '../stores/lotteryStore'
import type { LotteryGame, DrawResult } from '../types/lottery'
import LotteryBall from '../components/common/LotteryBall.vue'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'

const lotteryStore = useLotteryStore()

// --- game selection ---
const selectedCode = ref('')
const currentGame = computed<LotteryGame | null>(() =>
  lotteryStore.games.find(g => g.code === selectedCode.value) ?? null,
)

// --- draws for period selection ---
const recentDraws = ref<DrawResult[]>([])
const selectedTerm = ref<string>('latest')
const loadingDraws = ref(false)

async function fetchRecentDraws(gameCode: string) {
  loadingDraws.value = true
  try {
    const res = await fetch(`${API_BASE}/draws/?game=${gameCode}&page_size=10`)
    if (!res.ok) throw new Error('載入失敗')
    const data = await res.json()
    recentDraws.value = data.results ?? data
  } catch {
    recentDraws.value = []
  } finally {
    loadingDraws.value = false
  }
}

function onGameChange() {
  lotteryStore.selectGame(selectedCode.value)
  mainNumbers.value = new Set()
  specialNumber.value = null
  result.value = null
  showResult.value = false
  recentDraws.value = []
  selectedTerm.value = 'latest'
  if (selectedCode.value) {
    fetchRecentDraws(selectedCode.value)
  }
}

watch(selectedCode, () => {
  if (selectedCode.value) onGameChange()
})

// --- number selection ---
const mainNumbers = ref<Set<number>>(new Set())
const specialNumber = ref<number | null>(null)

const mainFull = computed(() => {
  if (!currentGame.value) return false
  return mainNumbers.value.size >= currentGame.value.main_pick_count
})

const selectionComplete = computed(() => {
  if (!currentGame.value) return false
  const mainOk = mainNumbers.value.size === currentGame.value.main_pick_count
  if (currentGame.value.has_special) {
    return mainOk && specialNumber.value !== null
  }
  return mainOk
})

function toggleMainNumber(num: number) {
  const next = new Set(mainNumbers.value)
  if (next.has(num)) {
    next.delete(num)
  } else {
    if (currentGame.value && next.size >= currentGame.value.main_pick_count) return
    next.add(num)
  }
  mainNumbers.value = next
}

function toggleSpecialNumber(num: number) {
  specialNumber.value = specialNumber.value === num ? null : num
}

// --- check result ---
interface CheckResult {
  draw_term: string
  draw_date: string
  draw_numbers: number[]
  special_number: number | null
  your_numbers: number[]
  your_special: number | null
  matched_numbers: number[]
  matched_special: boolean
  match_count: number
  result_description: string
}

const result = ref<CheckResult | null>(null)
const showResult = ref(false)
const checking = ref(false)
const checkError = ref('')

async function checkNumbers() {
  if (!currentGame.value || !selectionComplete.value) return

  checkError.value = ''
  checking.value = true
  showResult.value = false
  result.value = null

  try {
    const body: Record<string, any> = {
      game: selectedCode.value,
      numbers: Array.from(mainNumbers.value).sort((a, b) => a - b),
    }
    if (currentGame.value.has_special && specialNumber.value !== null) {
      body.special_number = specialNumber.value
    }
    if (selectedTerm.value !== 'latest') {
      body.draw_term = selectedTerm.value
    }

    const res = await fetch(`${API_BASE}/draws/check_numbers/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    const data = await res.json()
    if (!res.ok) {
      checkError.value = data.detail || data.message || JSON.stringify(data)
      return
    }

    result.value = data
    // trigger slide-up after a tick
    setTimeout(() => {
      showResult.value = true
    }, 50)
  } catch {
    checkError.value = '網路錯誤，無法連線後端'
  } finally {
    checking.value = false
  }
}

// --- init ---
onMounted(async () => {
  if (lotteryStore.games.length === 0) {
    await lotteryStore.fetchGames()
  }
  if (lotteryStore.games.length > 0 && !selectedCode.value) {
    selectedCode.value = lotteryStore.games[0].code
  }
})
</script>

<template>
  <div class="page-content">
    <div class="container">
      <h1>
        <i class="fas fa-check-double"></i>
        對獎
      </h1>
      <p class="subtitle">選擇彩種與期數，輸入您的號碼來對獎</p>

      <!-- Settings -->
      <div class="check-settings card">
        <div class="settings-row">
          <div class="setting-group">
            <label for="check-game">
              <i class="fas fa-dice"></i> 彩種
            </label>
            <select id="check-game" v-model="selectedCode">
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

          <div class="setting-group">
            <label for="check-term">
              <i class="fas fa-calendar-alt"></i> 期數
            </label>
            <select id="check-term" v-model="selectedTerm" :disabled="!selectedCode">
              <option value="latest">最新一期</option>
              <option
                v-for="draw in recentDraws"
                :key="draw.draw_term"
                :value="draw.draw_term"
              >
                {{ draw.draw_term }} ({{ draw.draw_date }})
              </option>
            </select>
          </div>
        </div>
      </div>

      <!-- Number Selection -->
      <div v-if="currentGame" class="number-selection card">
        <h2>
          <i class="fas fa-hand-pointer"></i>
          選擇號碼
        </h2>

        <!-- Main Numbers -->
        <div class="selection-section">
          <div class="selection-counter">
            已選 {{ mainNumbers.size }} / {{ currentGame.main_pick_count }} 個主號碼
          </div>
          <div class="number-grid">
            <div
              v-for="n in currentGame.main_pool_size"
              :key="'main-' + n"
              class="number-grid__cell"
              :class="{
                'number-grid__cell--selected': mainNumbers.has(n),
                'number-grid__cell--disabled': !mainNumbers.has(n) && mainFull,
              }"
              @click="toggleMainNumber(n)"
            >
              <LotteryBall
                :number="n"
                :type="mainNumbers.has(n) ? 'hot' : 'normal'"
                size="md"
              />
            </div>
          </div>
        </div>

        <!-- Special Number -->
        <div
          v-if="currentGame.has_special && currentGame.special_pool_size"
          class="selection-section"
        >
          <div class="selection-counter">
            特別號：{{ specialNumber !== null ? '已選 1' : '未選' }} / 1 個
          </div>
          <div class="number-grid">
            <div
              v-for="n in currentGame.special_pool_size"
              :key="'sp-' + n"
              class="number-grid__cell"
              :class="{ 'number-grid__cell--selected': specialNumber === n }"
              @click="toggleSpecialNumber(n)"
            >
              <LotteryBall
                :number="n"
                :type="specialNumber === n ? 'special' : 'normal'"
                size="md"
              />
            </div>
          </div>
        </div>

        <button
          class="check-btn"
          :disabled="!selectionComplete || checking"
          @click="checkNumbers"
        >
          <i :class="checking ? 'fas fa-spinner fa-spin' : 'fas fa-search'"></i>
          {{ checking ? '對獎中...' : '開始對獎' }}
        </button>

        <p v-if="checkError" class="check-error">
          <i class="fas fa-exclamation-circle"></i> {{ checkError }}
        </p>
      </div>

      <!-- Result -->
      <Transition name="slide-up">
        <div v-if="result && showResult" class="result-card card">
          <h2>
            <i class="fas fa-trophy"></i>
            對獎結果
          </h2>

          <div class="result-term">
            第 {{ result.draw_term }} 期 ({{ result.draw_date }})
          </div>

          <!-- Draw numbers -->
          <div class="result-section">
            <h3>開獎號碼</h3>
            <div class="result-balls">
              <LotteryBall
                v-for="num in result.draw_numbers"
                :key="'draw-' + num"
                :number="num"
                :type="result.matched_numbers.includes(num) ? 'hot' : 'normal'"
                size="lg"
              />
              <template v-if="result.special_number !== null">
                <span class="plus-sign">+</span>
                <LotteryBall
                  :number="result.special_number"
                  :type="result.matched_special ? 'special' : 'normal'"
                  size="lg"
                />
              </template>
            </div>
          </div>

          <!-- Your numbers -->
          <div class="result-section">
            <h3>您的號碼</h3>
            <div class="result-balls">
              <LotteryBall
                v-for="num in result.your_numbers"
                :key="'your-' + num"
                :number="num"
                :type="result.matched_numbers.includes(num) ? 'hot' : 'normal'"
                size="md"
              />
              <template v-if="result.your_special !== null">
                <span class="plus-sign">+</span>
                <LotteryBall
                  :number="result.your_special"
                  :type="result.matched_special ? 'special' : 'normal'"
                  size="md"
                />
              </template>
            </div>
          </div>

          <!-- Match summary -->
          <div class="result-summary">
            <div class="match-count">
              中 {{ result.match_count }} 個號碼
              <span v-if="result.matched_special" class="match-special">
                + 特別號
              </span>
            </div>
            <div class="result-description">
              {{ result.result_description }}
            </div>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
.subtitle {
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-xl);
}

h1 i {
  color: var(--color-primary);
  margin-right: var(--spacing-sm);
}

/* Settings */
.check-settings {
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.settings-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-lg);
}

.setting-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.setting-group label {
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

.setting-group label i {
  margin-right: var(--spacing-xs);
  color: var(--color-primary-dark);
}

.setting-group select {
  padding: var(--spacing-sm) var(--spacing-md);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: 1rem;
  font-family: inherit;
  cursor: pointer;
  transition: border-color 0.2s;
  min-width: 200px;
}

.setting-group select:focus {
  outline: none;
  border-color: var(--color-primary);
}

/* Number Selection */
.number-selection {
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.number-selection h2 {
  margin-bottom: var(--spacing-md);
}

.number-selection h2 i {
  color: var(--color-accent);
  margin-right: var(--spacing-sm);
}

.selection-section {
  margin-bottom: var(--spacing-lg);
}

.selection-counter {
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

.check-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-xl);
  background: linear-gradient(135deg, var(--color-secondary), var(--color-secondary-dark));
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-size: 1.05rem;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s, opacity 0.2s;
  box-shadow: 0 4px 12px rgba(42, 157, 143, 0.3);
}

.check-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 6px 18px rgba(42, 157, 143, 0.45);
}

.check-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.check-error {
  color: var(--color-accent);
  font-size: 0.875rem;
  margin-top: var(--spacing-sm);
}

.check-error i {
  margin-right: var(--spacing-xs);
}

/* Result */
.result-card {
  padding: var(--spacing-xl);
  text-align: center;
}

.result-card h2 {
  margin-bottom: var(--spacing-md);
}

.result-card h2 i {
  color: var(--color-primary);
  margin-right: var(--spacing-sm);
}

.result-term {
  color: var(--color-text-secondary);
  font-size: 0.95rem;
  margin-bottom: var(--spacing-lg);
}

.result-section {
  margin-bottom: var(--spacing-lg);
}

.result-section h3 {
  margin-bottom: var(--spacing-sm);
  font-size: 0.95rem;
  color: var(--color-text-secondary);
}

.result-balls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.plus-sign {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text-muted);
  margin: 0 var(--spacing-xs);
}

.result-summary {
  padding: var(--spacing-lg);
  background: var(--color-surface-hover);
  border-radius: var(--radius-md);
  margin-top: var(--spacing-md);
}

.match-count {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: var(--spacing-sm);
}

.match-special {
  color: var(--color-ball-special);
}

.result-description {
  font-size: 1.1rem;
  color: var(--color-secondary);
  font-weight: 600;
}

/* Slide-up transition */
.slide-up-enter-active {
  transition: all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from {
  opacity: 0;
  transform: translateY(40px);
}

.slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

@media (max-width: 768px) {
  .settings-row {
    flex-direction: column;
  }

  .setting-group select {
    min-width: 100%;
  }

  .number-grid {
    grid-template-columns: repeat(auto-fill, minmax(40px, 1fr));
    gap: 4px;
  }
}
</style>
