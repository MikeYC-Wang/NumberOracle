<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import type { MissingValue } from '@/types/lottery'
import { getMissingValueOptions } from '@/composables/useChartOptions'

interface Props {
  missingValues: MissingValue[]
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
  const options = getMissingValueOptions(props.missingValues)
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

watch(() => props.missingValues, updateChart, { deep: true })
</script>

<template>
  <div ref="chartRef" class="missing-value-chart" />
</template>

<style scoped>
.missing-value-chart {
  width: 100%;
  min-height: 320px;
  height: 100%;
}
</style>
