import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { DrawResult, NumberFrequency, MissingValue, PaginatedResponse } from '../types/lottery'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'

export interface TrendItem {
  draw_term: string
  draw_date: string
  appeared: boolean
}

export const useAnalysisStore = defineStore('analysis', () => {
  const draws = ref<DrawResult[]>([])
  const totalCount = ref(0)
  const frequencies = ref<NumberFrequency[]>([])
  const missingValues = ref<MissingValue[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const trendNumber = ref<number | null>(null)
  const trendData = ref<TrendItem[]>([])

  // 進階分析
  const selectedRecent = ref<number>(50)
  const consecutiveTail = ref<any>(null)
  const zoneDistribution = ref<any>(null)
  const oddEvenSize = ref<any>(null)
  const acValue = ref<any>(null)
  const pairFrequency = ref<any>(null)

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

  async function fetchTrend(gameCode: string, number: number, recent?: number) {
    loading.value = true
    error.value = null
    try {
      const params = new URLSearchParams({ game: gameCode, number: String(number) })
      if (recent !== undefined) {
        params.set('recent', String(recent))
      }
      const res = await fetch(`${API_BASE}/draws/trend/?${params}`)
      if (!res.ok) throw new Error(`API 錯誤: ${res.status}`)
      const data = await res.json()
      trendNumber.value = number
      trendData.value = data.trend as TrendItem[]
    } catch (e) {
      error.value = e instanceof Error ? e.message : '載入失敗'
    } finally {
      loading.value = false
    }
  }

  async function fetchConsecutiveTail(gameCode: string, recent: number) {
    try {
      const res = await fetch(`${API_BASE}/draws/consecutive_tail/?game=${gameCode}&recent=${recent}`)
      if (!res.ok) throw new Error(`API 錯誤: ${res.status}`)
      consecutiveTail.value = await res.json()
    } catch (e) {
      error.value = e instanceof Error ? e.message : '載入失敗'
    }
  }

  async function fetchZoneDistribution(gameCode: string, recent: number) {
    try {
      const res = await fetch(`${API_BASE}/draws/zone_distribution/?game=${gameCode}&recent=${recent}`)
      if (!res.ok) throw new Error(`API 錯誤: ${res.status}`)
      zoneDistribution.value = await res.json()
    } catch (e) {
      error.value = e instanceof Error ? e.message : '載入失敗'
    }
  }

  async function fetchOddEvenSize(gameCode: string, recent: number) {
    try {
      const res = await fetch(`${API_BASE}/draws/odd_even_size/?game=${gameCode}&recent=${recent}`)
      if (!res.ok) throw new Error(`API 錯誤: ${res.status}`)
      oddEvenSize.value = await res.json()
    } catch (e) {
      error.value = e instanceof Error ? e.message : '載入失敗'
    }
  }

  async function fetchAcValue(gameCode: string, recent: number) {
    try {
      const res = await fetch(`${API_BASE}/draws/ac_value/?game=${gameCode}&recent=${recent}`)
      if (!res.ok) throw new Error(`API 錯誤: ${res.status}`)
      acValue.value = await res.json()
    } catch (e) {
      error.value = e instanceof Error ? e.message : '載入失敗'
    }
  }

  async function fetchPairFrequency(gameCode: string, recent: number, top?: number) {
    try {
      const params = new URLSearchParams({ game: gameCode, recent: String(recent) })
      if (top !== undefined) {
        params.set('top', String(top))
      }
      const res = await fetch(`${API_BASE}/draws/pair_frequency/?${params}`)
      if (!res.ok) throw new Error(`API 錯誤: ${res.status}`)
      pairFrequency.value = await res.json()
    } catch (e) {
      error.value = e instanceof Error ? e.message : '載入失敗'
    }
  }

  function clearDraws() {
    draws.value = []
    totalCount.value = 0
    frequencies.value = []
    missingValues.value = []
    trendNumber.value = null
    trendData.value = []
    consecutiveTail.value = null
    zoneDistribution.value = null
    oddEvenSize.value = null
    acValue.value = null
    pairFrequency.value = null
  }

  return {
    draws,
    totalCount,
    frequencies,
    missingValues,
    trendNumber,
    trendData,
    loading,
    error,
    selectedRecent,
    consecutiveTail,
    zoneDistribution,
    oddEvenSize,
    acValue,
    pairFrequency,
    fetchDraws,
    fetchHotCold,
    fetchMissingValues,
    fetchTrend,
    fetchConsecutiveTail,
    fetchZoneDistribution,
    fetchOddEvenSize,
    fetchAcValue,
    fetchPairFrequency,
    clearDraws,
  }
})
