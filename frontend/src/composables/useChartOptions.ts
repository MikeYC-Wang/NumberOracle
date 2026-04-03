import type { NumberFrequency, MissingValue } from '../types/lottery'
import type { EChartsOption } from 'echarts'

/** 統一字型設定 */
const FONT_FAMILY = "'Noto Sans TC', system-ui, -apple-system, sans-serif"

/** 色彩常數 (對應 variables.css) */
const COLORS = {
  hot: '#E76F51',
  cold: '#2A9D8F',
  normal: '#E9C46A',
  special: '#6C5CE7',
  text: '#2D3436',
  textSecondary: '#636E72',
  border: '#DFE6E9',
  bg: '#F4F1DE',
} as const

/**
 * 依照頻率值在冷(綠)與熱(紅)之間做線性內插
 */
function getHeatColor(value: number, min: number, max: number): string {
  if (max === min) return COLORS.normal
  const ratio = (value - min) / (max - min)
  // cold (#2A9D8F) -> normal (#E9C46A) -> hot (#E76F51)
  const r = Math.round(ratio < 0.5
    ? 0x2A + (0xE9 - 0x2A) * (ratio / 0.5)
    : 0xE9 + (0xE7 - 0xE9) * ((ratio - 0.5) / 0.5))
  const g = Math.round(ratio < 0.5
    ? 0x9D + (0xC4 - 0x9D) * (ratio / 0.5)
    : 0xC4 + (0x6F - 0xC4) * ((ratio - 0.5) / 0.5))
  const b = Math.round(ratio < 0.5
    ? 0x8F + (0x6A - 0x8F) * (ratio / 0.5)
    : 0x6A + (0x51 - 0x6A) * ((ratio - 0.5) / 0.5))
  return `rgb(${r}, ${g}, ${b})`
}

/** 共用的文字樣式 */
function textStyle(fontSize = 12) {
  return {
    fontFamily: FONT_FAMILY,
    fontSize,
    color: COLORS.textSecondary,
  }
}

/**
 * 冷熱門號碼長條圖 option
 */
export function getHotColdBarOptions(
  data: NumberFrequency[],
  poolSize: number,
): EChartsOption {
  // 建立 1~poolSize 的完整資料，缺少的補 0
  const freqMap = new Map(data.map((d) => [d.number, d.count]))
  const numbers = Array.from({ length: poolSize }, (_, i) => i + 1)
  const counts = numbers.map((n) => freqMap.get(n) ?? 0)

  const minCount = Math.min(...counts)
  const maxCount = Math.max(...counts)

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      textStyle: { fontFamily: FONT_FAMILY },
      formatter(params: unknown) {
        const p = Array.isArray(params) ? params[0] : params
        const item = p as { name: string; value: number }
        return `<b>No. ${item.name}</b><br/>出現次數: ${item.value}`
      },
    },
    grid: {
      left: 40,
      right: 16,
      top: 48,
      bottom: 40,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: numbers.map(String),
      axisLabel: {
        ...textStyle(11),
        interval: poolSize > 30 ? 'auto' : 0,
        rotate: poolSize > 30 ? 45 : 0,
      },
      axisTick: { alignWithLabel: true },
      axisLine: { lineStyle: { color: COLORS.border } },
    },
    yAxis: {
      type: 'value',
      name: '出現次數',
      nameTextStyle: textStyle(12),
      axisLabel: textStyle(11),
      splitLine: { lineStyle: { color: COLORS.border, type: 'dashed' } },
    },
    series: [
      {
        type: 'bar',
        data: counts.map((c) => ({
          value: c,
          itemStyle: {
            color: getHeatColor(c, minCount, maxCount),
            borderRadius: [3, 3, 0, 0],
          },
        })),
        barMaxWidth: 28,
        emphasis: {
          itemStyle: { shadowBlur: 8, shadowColor: 'rgba(0,0,0,0.15)' },
        },
      },
    ],
  }
}

/**
 * 遺漏值柱狀圖 option
 */
export function getMissingValueOptions(
  data: MissingValue[],
): EChartsOption {
  const numbers = data.map((d) => String(d.number))
  const values = data.map((d) => d.missing_draws)

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      textStyle: { fontFamily: FONT_FAMILY },
      formatter(params: unknown) {
        const p = Array.isArray(params) ? params[0] : params
        const item = p as { name: string; value: number }
        return `<b>No. ${item.name}</b><br/>遺漏期數: ${item.value}`
      },
    },
    grid: {
      left: 40,
      right: 16,
      top: 48,
      bottom: 40,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: numbers,
      axisLabel: {
        ...textStyle(11),
        interval: numbers.length > 30 ? 'auto' : 0,
        rotate: numbers.length > 30 ? 45 : 0,
      },
      axisTick: { alignWithLabel: true },
      axisLine: { lineStyle: { color: COLORS.border } },
    },
    yAxis: {
      type: 'value',
      name: '遺漏期數',
      nameTextStyle: textStyle(12),
      axisLabel: textStyle(11),
      splitLine: { lineStyle: { color: COLORS.border, type: 'dashed' } },
    },
    series: [
      {
        type: 'bar',
        data: values.map((v) => ({
          value: v,
          itemStyle: {
            color: COLORS.special,
            borderRadius: [3, 3, 0, 0],
          },
        })),
        barMaxWidth: 28,
        emphasis: {
          itemStyle: { shadowBlur: 8, shadowColor: 'rgba(0,0,0,0.15)' },
        },
      },
    ],
  }
}
