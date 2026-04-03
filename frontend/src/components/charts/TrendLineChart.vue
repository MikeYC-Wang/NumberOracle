<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'

export interface TrendItem {
  draw_term: string
  draw_date: string
  appeared: boolean
}

interface Props {
  trendData: TrendItem[]
  number: number
}

const props = defineProps<Props>()

const chartRef = ref<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts | null = null

const ACCENT = '#E76F51'
const GRAY = '#B2BEC3'
const FONT_FAMILY = "'Noto Sans TC', system-ui, -apple-system, sans-serif"

function buildOptions(): EChartsOption {
  const xLabels = props.trendData.map(d => d.draw_date)
  const yValues = props.trendData.map(d => (d.appeared ? 1 : 0))

  return {
    tooltip: {
      trigger: 'axis',
      formatter(params: unknown) {
        const p = Array.isArray(params) ? params[0] : params
        const item = p as { dataIndex: number; value: number }
        const d = props.trendData[item.dataIndex]
        return `${d.draw_date} (${d.draw_term})<br/>號碼 ${props.number}: ${d.appeared ? '<b style="color:' + ACCENT + '">出現</b>' : '未出現'}`
      },
    },
    grid: {
      left: 50,
      right: 20,
      top: 40,
      bottom: 60,
    },
    xAxis: {
      type: 'category',
      data: xLabels,
      axisLabel: {
        rotate: 45,
        fontSize: 11,
        fontFamily: FONT_FAMILY,
        color: '#636E72',
      },
      axisTick: { alignWithLabel: true },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 1,
      interval: 1,
      axisLabel: {
        formatter(val: number) {
          return val === 1 ? '出現' : '未出現'
        },
        fontFamily: FONT_FAMILY,
        color: '#636E72',
      },
      splitLine: {
        lineStyle: { type: 'dashed', color: '#DFE6E9' },
      },
    },
    series: [
      {
        name: `號碼 ${props.number}`,
        type: 'line',
        data: yValues,
        lineStyle: {
          type: 'dashed',
          color: GRAY,
          width: 1.5,
        },
        symbol: 'circle',
        symbolSize(value: number) {
          return value === 1 ? 12 : 6
        },
        itemStyle: {
          color(params: { value: number }) {
            return params.value === 1 ? ACCENT : GRAY
          },
        },
        emphasis: {
          itemStyle: {
            borderWidth: 2,
            borderColor: '#fff',
          },
        },
      },
    ],
  }
}

function initChart() {
  if (!chartRef.value) return
  chartInstance = echarts.init(chartRef.value)
  updateChart()
}

function updateChart() {
  if (!chartInstance) return
  chartInstance.setOption(buildOptions(), true)
}

function handleResize() {
  chartInstance?.resize()
}

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  chartInstance = null
})

watch(() => [props.trendData, props.number], updateChart, { deep: true })
</script>

<template>
  <div class="chart-scroll-wrapper">
    <div ref="chartRef" class="trend-line-chart" />
  </div>
</template>

<style scoped>
.chart-scroll-wrapper {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.trend-line-chart {
  min-width: 600px;
  min-height: 320px;
  height: 100%;
}
</style>
