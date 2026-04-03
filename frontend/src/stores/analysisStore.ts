import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { DrawResult, PaginatedResponse } from '../types/lottery'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'

export const useAnalysisStore = defineStore('analysis', () => {
  const draws = ref<DrawResult[]>([])
  const totalCount = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchDraws(gameCode: string, page = 1) {
    loading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/draws/?game=${gameCode}&page=${page}`)
      if (!res.ok) throw new Error(`API 錯誤: ${res.status}`)
      const data: PaginatedResponse<DrawResult> = await res.json()
      draws.value = data.results
      totalCount.value = data.count
    } catch (e) {
      error.value = e instanceof Error ? e.message : '載入失敗'
    } finally {
      loading.value = false
    }
  }

  function clearDraws() {
    draws.value = []
    totalCount.value = 0
  }

  return { draws, totalCount, loading, error, fetchDraws, clearDraws }
})
