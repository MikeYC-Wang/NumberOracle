import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { LotteryGame } from '../types/lottery'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'

export const useLotteryStore = defineStore('lottery', () => {
  const games = ref<LotteryGame[]>([])
  const currentGame = ref<LotteryGame | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchGames() {
    loading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/games/`)
      if (!res.ok) throw new Error(`API 錯誤: ${res.status}`)
      const data = await res.json()
      games.value = data.results ?? data
    } catch (e) {
      error.value = e instanceof Error ? e.message : '載入失敗'
    } finally {
      loading.value = false
    }
  }

  function selectGame(code: string) {
    currentGame.value = games.value.find(g => g.code === code) ?? null
  }

  return { games, currentGame, loading, error, fetchGames, selectGame }
})
