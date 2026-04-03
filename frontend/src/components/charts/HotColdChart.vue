<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import type { NumberFrequency } from '../../types/lottery'
import { getHotColdBarOptions } from '../../composables/useChartOptions'

interface Props {
  frequencies: NumberFrequency[]
  poolSize: number
}

const props = defineProps<Props>()

const chartRef = ref<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts | null = null

function initChart() {
  if (!chartRef.value) return
  chartInstance = echarts.init(chartRef.value)
  updateChart()
}

function updateChart() {
  if (!chartInstance) return
  const options = getHotColdBarOptions(props.frequencies, props.poolSize)
  chartInstance.setOption(options, true)
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

watch(() => [props.frequencies, props.poolSize], updateChart, { deep: true })
</script>

<template>
  <div class="chart-scroll-wrapper">
    <div ref="chartRef" class="hot-cold-chart" />
  </div>
</template>

<style scoped>
.chart-scroll-wrapper {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  max-width: 100%;
}

.hot-cold-chart {
  min-width: 600px;
  min-height: 320px;
  height: 100%;
}
</style>
