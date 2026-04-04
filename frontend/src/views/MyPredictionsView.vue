<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/authStore'
import { useLotteryStore } from '../stores/lotteryStore'
import LotteryBall from '../components/common/LotteryBall.vue'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'
const authStore = useAuthStore()
const lotteryStore = useLotteryStore()

function getGameName(code: string): string {
  const game = lotteryStore.games.find(g => g.code === code)
  return game?.name ?? code
}

interface SavedPrediction {
  id: number
  game_code: string
  numbers: number[]
  special_number: number | null
  strategy: string
  created_at: string
  checked_term: string | null
  matched_count: number | null
  special_matched: boolean
  checked_at: string | null
}

const predictions = ref<SavedPrediction[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const checkingAll = ref(false)
const deletingId = ref<number | null>(null)

const strategyLabels: Record<string, string> = {
  random: '純隨機',
  hot_weighted: '熱門加權',
  cold_weighted: '冷門加權',
  balanced: '均衡策略',
  manual: '手動選號',
}

function getStrategyLabel(strategy: string): string {
  return strategyLabels[strategy] ?? strategy
}

async function fetchPredictions() {
  loading.value = true
  error.value = null
  try {
    const res = await fetch(`${API_BASE}/auth/predictions/`, {
      headers: { ...authStore.getAuthHeaders() },
    })
    if (!res.ok) throw new Error(`API 錯誤: ${res.status}`)
    const data = await res.json()
    predictions.value = data.results ?? data
  } catch (e) {
    error.value = e instanceof Error ? e.message : '載入失敗'
  } finally {
    loading.value = false
  }
}

async function checkAll() {
  if (checkingAll.value) return
  checkingAll.value = true
  try {
    const res = await fetch(`${API_BASE}/auth/predictions/check_all/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authStore.getAuthHeaders(),
      },
    })
    if (res.ok) {
      await fetchPredictions()
    } else {
      const data = await res.json().catch(() => ({}))
      alert(data.detail || '對獎失敗')
    }
  } catch {
    alert('網路錯誤')
  } finally {
    checkingAll.value = false
  }
}

async function deletePrediction(id: number) {
  if (deletingId.value === id) return
  if (!confirm('確定要刪除此收藏嗎？')) return

  deletingId.value = id
  try {
    const res = await fetch(`${API_BASE}/auth/predictions/${id}/`, {
      method: 'DELETE',
      headers: { ...authStore.getAuthHeaders() },
    })
    if (res.ok || res.status === 204) {
      predictions.value = predictions.value.filter(p => p.id !== id)
    } else {
      alert('刪除失敗')
    }
  } catch {
    alert('網路錯誤')
  } finally {
    deletingId.value = null
  }
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${day} ${h}:${min}`
}

onMounted(async () => {
  if (lotteryStore.games.length === 0) {
    await lotteryStore.fetchGames()
  }
  fetchPredictions()
})
</script>

<template>
  <div class="page-content">
    <div class="container">
      <h1>
        <i class="fas fa-bookmark"></i>
        我的收藏
      </h1>
      <p class="subtitle">管理你的預測號碼，一鍵全部對獎</p>

      <div class="top-actions">
        <button
          class="check-all-btn"
          :disabled="checkingAll || predictions.length === 0"
          @click="checkAll"
        >
          <i :class="checkingAll ? 'fas fa-spinner fa-spin' : 'fas fa-check-double'"></i>
          {{ checkingAll ? '對獎中...' : '全部對獎' }}
        </button>
      </div>

      <div v-if="loading" class="loading">
        <i class="fas fa-spinner fa-spin"></i> 載入中...
      </div>

      <div v-else-if="error" class="error-msg">
        <i class="fas fa-exclamation-triangle"></i> {{ error }}
      </div>

      <div v-else-if="predictions.length === 0" class="empty-state">
        <i class="fas fa-inbox fa-3x"></i>
        <p>尚無收藏的預測號碼</p>
        <p class="empty-hint">前往「預測搖獎」頁面搖出號碼後點擊收藏按鈕</p>
      </div>

      <div v-else class="predictions-list">
        <div
          v-for="pred in predictions"
          :key="pred.id"
          class="pred-card card"
          :class="{ 'pred-card--checked': pred.checked_term }"
        >
          <div class="pred-card__header">
            <span class="pred-card__game">{{ getGameName(pred.game_code) }}</span>
            <span class="pred-card__strategy">
              <i class="fas fa-chess-knight"></i>
              {{ getStrategyLabel(pred.strategy) }}
            </span>
            <span class="pred-card__time">
              <i class="fas fa-clock"></i>
              {{ formatDate(pred.created_at) }}
            </span>
          </div>

          <div class="pred-card__balls">
            <LotteryBall
              v-for="num in pred.numbers"
              :key="'n-' + pred.id + '-' + num"
              :number="num"
              type="normal"
              size="md"
            />
            <template v-if="pred.special_number !== null">
              <span class="plus-sign">+</span>
              <LotteryBall
                :number="pred.special_number"
                :type="pred.special_matched ? 'special' : 'normal'"
                size="md"
              />
            </template>
          </div>

          <!-- 對獎結果 -->
          <div v-if="pred.checked_term" class="pred-card__result">
            <div class="result-badge">
              <i class="fas fa-bullseye"></i>
              命中 {{ pred.matched_count }} 個號碼
            </div>
            <div v-if="pred.special_number !== null" class="result-special">
              特別號：{{ pred.special_matched ? '命中' : '未命中' }}
            </div>
            <div class="result-draw-info">
              對獎期別：第 {{ pred.checked_term }} 期
            </div>
          </div>

          <div class="pred-card__actions">
            <button
              class="delete-btn"
              :disabled="deletingId === pred.id"
              @click="deletePrediction(pred.id)"
            >
              <i :class="deletingId === pred.id ? 'fas fa-spinner fa-spin' : 'fas fa-trash'"></i>
            </button>
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

h1 {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}
h1 i {
  color: var(--color-accent);
}

.top-actions {
  margin-bottom: var(--spacing-lg);
}

.check-all-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-lg);
  background: linear-gradient(135deg, var(--color-secondary), var(--color-secondary-dark));
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-size: 1rem;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 2px 8px rgba(42, 157, 143, 0.3);
}
.check-all-btn:hover:not(:disabled) {
  transform: scale(1.03);
  box-shadow: 0 4px 14px rgba(42, 157, 143, 0.45);
}
.check-all-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading {
  text-align: center;
  padding: var(--spacing-2xl);
  color: var(--color-text-muted);
  font-size: 1.125rem;
}

.error-msg {
  text-align: center;
  padding: var(--spacing-2xl);
  color: var(--color-accent);
  font-size: 1rem;
}

.empty-state {
  text-align: center;
  padding: var(--spacing-2xl);
  color: var(--color-text-muted);
}
.empty-state i {
  margin-bottom: var(--spacing-md);
  color: var(--color-border);
}
.empty-state p {
  margin-top: var(--spacing-sm);
  font-size: 1.1rem;
}
.empty-hint {
  font-size: 0.9rem !important;
  color: var(--color-text-muted);
}

.predictions-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.pred-card {
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  position: relative;
}

.pred-card--checked {
  background: linear-gradient(135deg, var(--color-surface) 0%, #f0faf8 100%);
  border-left: 4px solid var(--color-secondary);
}

.pred-card__header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  flex-wrap: wrap;
}

.pred-card__game {
  background: var(--color-primary-light);
  color: var(--color-text);
  padding: 2px var(--spacing-sm);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-weight: 600;
}

.pred-card__strategy {
  color: var(--color-text-secondary);
  font-size: 0.8rem;
}
.pred-card__strategy i {
  margin-right: 4px;
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.pred-card__time {
  color: var(--color-text-muted);
  font-size: 0.8rem;
  font-family: var(--font-mono);
}
.pred-card__time i {
  margin-right: 4px;
}

.pred-card__balls {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  flex-wrap: wrap;
}

.plus-sign {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-text-muted);
  margin: 0 var(--spacing-xs);
}

.pred-card__result {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  flex-wrap: wrap;
  padding: var(--spacing-sm) var(--spacing-md);
  background: rgba(42, 157, 143, 0.08);
  border-radius: var(--radius-md);
  font-size: 0.85rem;
}

.result-badge {
  font-weight: 700;
  color: var(--color-secondary-dark);
}
.result-badge i {
  margin-right: var(--spacing-xs);
}

.result-special {
  color: var(--color-text-secondary);
}

.result-draw-info {
  color: var(--color-text-muted);
  font-family: var(--font-mono);
  font-size: 0.8rem;
}

.pred-card__actions {
  position: absolute;
  top: var(--spacing-md);
  right: var(--spacing-md);
}

.delete-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text-muted);
  cursor: pointer;
  font-size: 0.85rem;
  transition: color 0.2s, border-color 0.2s;
}
.delete-btn:hover:not(:disabled) {
  color: var(--color-accent);
  border-color: var(--color-accent);
}
.delete-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .pred-card__header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-xs);
  }

  .pred-card__result {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-xs);
  }
}
</style>
