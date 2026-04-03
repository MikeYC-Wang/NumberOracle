<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

interface DataItem {
  draw_term: string
  draw_date: string
  odd: number
  even: number
  small: number
  large: number
}

interface Props {
  data: DataItem[]
}

const props = defineProps<Props>()

const FONT_FAMILY = "'Noto Sans TC', system-ui, -apple-system, sans-serif"
const COLORS = {
  accent: '#E76F51',
  secondary: '#2A9D8F',
  primary: '#E9C46A',
  special: '#6C5CE7',
  textSecondary: '#636E72',
  border: '#DFE6E9',
  text: '#2D3436',
}

const oddEvenRef = ref<HTMLDivElement | null>(null)
const sizeRef = ref<HTMLDivElement | null>(null)
let oddEvenInstance: echarts.ECharts | null = null
let sizeInstance: echarts.ECharts | null = null

function makeLineOption(
  title: string,
  terms: string[],
  series1: { name: string; data: number[]; color: string },
  series2: { name: string; data: number[]; color: string },
): echarts.EChartsOption {
  return {
    title: {
      text: title,
      left: 'center',
      textStyle: { fontFamily: FONT_FAMILY, fontSize: 14, color: COLORS.text },
    },
    tooltip: {
      trigger: 'axis',
      textStyle: { fontFamily: FONT_FAMILY },
    },
    legend: {
      bottom: 0,
      textStyle: { fontFamily: FONT_FAMILY, fontSize: 11, color: COLORS.textSecondary },
    },
    grid: { left: 40, right: 16, top: 48, bottom: 40, containLabel: true },
    xAxis: {
      type: 'category',
      data: terms,
      axisLabel: {
        fontFamily: FONT_FAMILY, fontSize: 10, color: COLORS.textSecondary,
        rotate: 45, interval: 'auto',
      },
      axisLine: { lineStyle: { color: COLORS.border } },
    },
    yAxis: {
      type: 'value',
      name: '個數',
      nameTextStyle: { fontFamily: FONT_FAMILY, fontSize: 12, color: COLORS.textSecondary },
      axisLabel: { fontFamily: FONT_FAMILY, fontSize: 11, color: COLORS.textSecondary },
      splitLine: { lineStyle: { color: COLORS.border, type: 'dashed' } },
    },
    series: [
      {
        name: series1.name,
        type: 'line',
        data: series1.data,
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { color: series1.color, width: 2 },
        itemStyle: { color: series1.color },
      },
      {
        name: series2.name,
        type: 'line',
        data: series2.data,
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { color: series2.color, width: 2 },
        itemStyle: { color: series2.color },
      },
    ],
  }
}

function updateCharts() {
  if (!props.data || props.data.length === 0) return
  const terms = props.data.map(d => d.draw_term)

  if (oddEvenInstance) {
    oddEvenInstance.setOption(makeLineOption(
      '奇偶走勢',
      terms,
      { name: '奇數', data: props.data.map(d => d.odd), color: COLORS.accent },
      { name: '偶數', data: props.data.map(d => d.even), color: COLORS.secondary },
    ), true)
  }

  if (sizeInstance) {
    sizeInstance.setOption(makeLineOption(
      '大小走勢',
      terms,
      { name: '小號', data: props.data.map(d => d.small), color: COLORS.primary },
      { name: '大號', data: props.data.map(d => d.large), color: COLORS.special },
    ), true)
  }
}

function handleResize() {
  oddEvenInstance?.resize()
  sizeInstance?.resize()
}

onMounted(() => {
  if (oddEvenRef.value) {
    oddEvenInstance = echarts.init(oddEvenRef.value)
  }
  if (sizeRef.value) {
    sizeInstance = echarts.init(sizeRef.value)
  }
  updateCharts()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  oddEvenInstance?.dispose()
  sizeInstance?.dispose()
  oddEvenInstance = null
  sizeInstance = null
})

watch(() => props.data, updateCharts, { deep: true })
</script>

<template>
  <div class="odd-even-size-chart">
    <div class="chart-scroll-wrapper">
      <div ref="oddEvenRef" class="chart-row" />
    </div>
    <div class="chart-scroll-wrapper">
      <div ref="sizeRef" class="chart-row" />
    </div>
  </div>
</template>

<style scoped>
.odd-even-size-chart {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.chart-scroll-wrapper {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  max-width: 100%;
}

.chart-row {
  min-width: 600px;
  min-height: 280px;
  height: 280px;
}
</style>
