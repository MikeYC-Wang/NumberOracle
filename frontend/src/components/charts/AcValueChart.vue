<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

interface DataItem {
  draw_term: string
  draw_date: string
  ac_value: number
}

interface Summary {
  avg: number
  max: number
  min: number
}

interface Props {
  data: DataItem[]
  summary: Summary
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
  if (!chartInstance || !props.data || props.data.length === 0) return

  const terms = props.data.map(d => d.draw_term)
  const values = props.data.map(d => d.ac_value)

  chartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      textStyle: { fontFamily: FONT_FAMILY },
    },
    grid: { left: 40, right: 16, top: 24, bottom: 40, containLabel: true },
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
      name: 'AC 值',
      nameTextStyle: { fontFamily: FONT_FAMILY, fontSize: 12, color: COLORS.textSecondary },
      axisLabel: { fontFamily: FONT_FAMILY, fontSize: 11, color: COLORS.textSecondary },
      splitLine: { lineStyle: { color: COLORS.border, type: 'dashed' } },
    },
    series: [{
      type: 'line',
      data: values,
      smooth: true,
      symbol: 'circle',
      symbolSize: 4,
      lineStyle: { color: COLORS.secondary, width: 2 },
      itemStyle: { color: COLORS.secondary },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(42, 157, 143, 0.3)' },
          { offset: 1, color: 'rgba(42, 157, 143, 0.02)' },
        ]),
      },
      markLine: {
        silent: true,
        data: [{
          yAxis: props.summary.avg,
          label: {
            formatter: `平均 ${props.summary.avg.toFixed(1)}`,
            fontFamily: FONT_FAMILY,
            fontSize: 11,
          },
          lineStyle: { color: COLORS.accent, type: 'dashed', width: 2 },
        }],
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

watch(() => [props.data, props.summary], updateChart, { deep: true })
</script>

<template>
  <div>
    <div class="ac-summary">
      <div class="ac-stat">
        <span class="ac-label">平均</span>
        <span class="ac-value">{{ summary.avg.toFixed(1) }}</span>
      </div>
      <div class="ac-stat">
        <span class="ac-label">最大</span>
        <span class="ac-value ac-max">{{ summary.max }}</span>
      </div>
      <div class="ac-stat">
        <span class="ac-label">最小</span>
        <span class="ac-value ac-min">{{ summary.min }}</span>
      </div>
    </div>
    <div class="chart-scroll-wrapper">
      <div ref="chartRef" class="ac-value-chart" />
    </div>
  </div>
</template>

<style scoped>
.ac-summary {
  display: flex;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-sm);
  flex-wrap: wrap;
}

.ac-stat {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.ac-label {
  font-size: 0.85rem;
  color: var(--color-text-secondary, #636E72);
}

.ac-value {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-text, #2D3436);
  font-family: var(--font-mono);
}

.ac-max {
  color: var(--color-accent, #E76F51);
}

.ac-min {
  color: var(--color-secondary, #2A9D8F);
}

.chart-scroll-wrapper {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  max-width: 100%;
}

.ac-value-chart {
  min-width: 600px;
  min-height: 300px;
  height: 300px;
}
</style>
