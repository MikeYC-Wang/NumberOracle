<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

interface PairItem {
  pair: number[]
  count: number
}

interface Props {
  pairs: PairItem[]
}

const props = defineProps<Props>()

const FONT_FAMILY = "'Noto Sans TC', system-ui, -apple-system, sans-serif"
const COLORS = {
  secondary: '#2A9D8F',
  accent: '#E76F51',
  textSecondary: '#636E72',
  border: '#DFE6E9',
  text: '#2D3436',
}

const chartRef = ref<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts | null = null

function updateChart() {
  if (!chartInstance || !props.pairs || props.pairs.length === 0) return

  const sorted = [...props.pairs].sort((a, b) => a.count - b.count)
  const labels = sorted.map(p => `${p.pair[0]} & ${p.pair[1]}`)
  const values = sorted.map(p => p.count)
  const maxVal = Math.max(...values)

  const chartHeight = Math.max(320, sorted.length * 24)
  if (chartRef.value) {
    chartRef.value.style.height = `${chartHeight}px`
  }
  chartInstance.resize()

  chartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      textStyle: { fontFamily: FONT_FAMILY },
    },
    grid: { left: 16, right: 40, top: 16, bottom: 16, containLabel: true },
    yAxis: {
      type: 'category',
      data: labels,
      axisLabel: {
        fontFamily: FONT_FAMILY, fontSize: 11, color: COLORS.textSecondary,
      },
      axisLine: { lineStyle: { color: COLORS.border } },
    },
    xAxis: {
      type: 'value',
      name: '次數',
      nameTextStyle: { fontFamily: FONT_FAMILY, fontSize: 12, color: COLORS.textSecondary },
      axisLabel: { fontFamily: FONT_FAMILY, fontSize: 11, color: COLORS.textSecondary },
      splitLine: { lineStyle: { color: COLORS.border, type: 'dashed' } },
    },
    series: [{
      type: 'bar',
      data: values.map(v => ({
        value: v,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: COLORS.secondary },
            { offset: 1, color: maxVal > 0 ? `rgba(231, 111, 81, ${0.3 + 0.7 * (v / maxVal)})` : COLORS.accent },
          ]),
          borderRadius: [0, 4, 4, 0],
        },
      })),
      barMaxWidth: 20,
      label: {
        show: true,
        position: 'right',
        fontFamily: FONT_FAMILY,
        fontSize: 11,
        color: COLORS.text,
      },
    }],
  }, true)
}

function handleResize() {
  chartInstance?.resize()
}

onMounted(() => {
  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value)
    updateChart()
  }
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  chartInstance = null
})

watch(() => props.pairs, updateChart, { deep: true })
</script>

<template>
  <div class="chart-scroll-wrapper">
    <div ref="chartRef" class="pair-frequency-chart" />
  </div>
</template>

<style scoped>
.chart-scroll-wrapper {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  max-width: 100%;
}

.pair-frequency-chart {
  min-width: 500px;
  min-height: 320px;
  height: 320px;
}
</style>
