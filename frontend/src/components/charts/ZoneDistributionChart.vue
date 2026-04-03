<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

interface Props {
  zones: { zone: string; count: number }[]
}

const props = defineProps<Props>()

const FONT_FAMILY = "'Noto Sans TC', system-ui, -apple-system, sans-serif"
const COLORS = {
  textSecondary: '#636E72',
  border: '#DFE6E9',
  text: '#2D3436',
}

const ZONE_COLORS = [
  '#E76F51', '#F4A261', '#E9C46A', '#2A9D8F', '#264653',
  '#6C5CE7', '#A8DADC', '#457B9D', '#1D3557', '#D4A5A5',
]

const chartRef = ref<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts | null = null

function updateChart() {
  if (!chartInstance || !props.zones || props.zones.length === 0) return

  chartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      textStyle: { fontFamily: FONT_FAMILY },
    },
    grid: { left: 16, right: 40, top: 16, bottom: 16, containLabel: true },
    yAxis: {
      type: 'category',
      data: props.zones.map(z => z.zone),
      inverse: true,
      axisLabel: { fontFamily: FONT_FAMILY, fontSize: 12, color: COLORS.textSecondary },
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
      data: props.zones.map((z, i) => ({
        value: z.count,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: ZONE_COLORS[i % ZONE_COLORS.length] },
            { offset: 1, color: ZONE_COLORS[(i + 1) % ZONE_COLORS.length] },
          ]),
          borderRadius: [0, 4, 4, 0],
        },
      })),
      barMaxWidth: 28,
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

watch(() => props.zones, updateChart, { deep: true })
</script>

<template>
  <div class="chart-scroll-wrapper">
    <div ref="chartRef" class="zone-distribution-chart" />
  </div>
</template>

<style scoped>
.chart-scroll-wrapper {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  max-width: 100%;
}

.zone-distribution-chart {
  min-width: 400px;
  min-height: 320px;
  height: 320px;
}
</style>
