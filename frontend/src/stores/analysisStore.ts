import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { DrawResult, NumberFrequency, MissingValue, PaginatedResponse } from '../types/lottery'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'

export const useAnalysisStore = defineStore('analysis', () => {
  const draws = ref<DrawResult[]>([])
  const totalCount = ref(0)
  const frequencies = ref<NumberFrequency[]>([])
  const missingValues = ref<MissingValue[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchDraws(gameCode: string) {
    loading.value = true
    error.value = null
    try {
      const allResults: DrawResult[] = []
      let url: string | null = `${API_BASE}/draws/?game=${gameCode}&page_size=500`
      while (url) {
        const res = await fetch(url)
        if (!res.ok) throw new Error(`API 錯誤: ${res.status}`)
        const data: PaginatedResponse<DrawResult> = await res.json()
        allResults.push(...data.results)
        url = data.next
      }
      draws.value = allResults
      totalCount.value = allResults.length
    } catch (e) {
      error.value = e instanceof Error ? e.message : '載入失敗'
    } finally {
      loading.value = false
    }
  }

  async function fetchHotCold(gameCode: string, recent?: number) {
    loading.value = true
    error.value = null
    try {
      const params = new URLSearchParams({ game: gameCode })
      if (recent !== undefined) {
        params.set('recent', String(recent))
      }
      const res = await fetch(`${API_BASE}/draws/hot_cold/?${params}`)
      if (!res.ok) throw new Error(`API 錯誤: ${res.status}`)
      const data = await res.json()
      frequencies.value = data.frequencies as NumberFrequency[]
    } catch (e) {
      error.value = e instanceof Error ? e.message : '載入失敗'
    } finally {
      loading.value = false
    }
  }

  async function fetchMissingValues(gameCode: string) {
    loading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/draws/missing_values/?game=${gameCode}`)
      if (!res.ok) throw new Error(`API 錯誤: ${res.status}`)
      const data = await res.json()
      missingValues.value = data.missing_values as MissingValue[]
    } catch (e) {
      error.value = e instanceof Error ? e.message : '載入失敗'
    } finally {
      loading.value = false
    }
  }

  function clearDraws() {
    draws.value = []
    totalCount.value = 0
    frequencies.value = []
    missingValues.value = []
  }

  return {
    draws,
    totalCount,
    frequencies,
    missingValues,
    loading,
    error,
    fetchDraws,
    fetchHotCold,
    fetchMissingValues,
    clearDraws,
  }
})
