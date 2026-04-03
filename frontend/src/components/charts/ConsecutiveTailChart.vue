<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

interface Props {
  data: {
    consecutive: Record<string, number>
    tail_frequency: { tail: number; count: number }[]
  }
}

const props = defineProps<Props>()

const FONT_FAMILY = "'Noto Sans TC', system-ui, -apple-system, sans-serif"
const COLORS = {
  primary: '#E9C46A',
  secondary: '#2A9D8F',
  accent: '#E76F51',
  special: '#6C5CE7',
  text: '#2D3436',
  textSecondary: '#636E72',
  border: '#DFE6E9',
}

const TAIL_COLORS = [
  '#E76F51', '#2A9D8F', '#E9C46A', '#6C5CE7', '#264653',
  '#F4A261', '#A8DADC', '#457B9D', '#1D3557', '#D4A5A5',
]

const pieRef = ref<HTMLDivElement | null>(null)
const barRef = ref<HTMLDivElement | null>(null)
let pieInstance: echarts.ECharts | null = null
let barInstance: echarts.ECharts | null = null

function updatePie() {
  if (!pieInstance || !props.data) return
  const entries = Object.entries(props.data.consecutive)
  const pieData = entries.map(([name, value]) => ({ name, value }))

  pieInstance.setOption({
    title: {
      text: '連號分布',
      left: 'center',
      textStyle: { fontFamily: FONT_FAMILY, fontSize: 14, color: COLORS.text },
    },
    tooltip: {
      trigger: 'item',
      textStyle: { fontFamily: FONT_FAMILY },
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      bottom: 0,
      textStyle: { fontFamily: FONT_FAMILY, fontSize: 11, color: COLORS.textSecondary },
    },
    series: [{
      type: 'pie',
      radius: ['35%', '65%'],
      center: ['50%', '45%'],
      data: pieData,
      label: { formatter: '{b}\n{d}%', fontFamily: FONT_FAMILY, fontSize: 11 },
      itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
      color: [COLORS.accent, COLORS.secondary, COLORS.primary, COLORS.special, '#264653'],
    }],
  }, true)
}

function updateBar() {
  if (!barInstance || !props.data) return
  const tails = props.data.tail_frequency

  barInstance.setOption({
    title: {
      text: '尾數頻率',
      left: 'center',
      textStyle: { fontFamily: FONT_FAMILY, fontSize: 14, color: COLORS.text },
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      textStyle: { fontFamily: FONT_FAMILY },
    },
    grid: { left: 40, right: 16, top: 48, bottom: 24, containLabel: true },
    xAxis: {
      type: 'category',
      data: tails.map(t => String(t.tail)),
      axisLabel: { fontFamily: FONT_FAMILY, fontSize: 11, color: COLORS.textSecondary },
      axisLine: { lineStyle: { color: COLORS.border } },
    },
    yAxis: {
      type: 'value',
      name: '次數',
      nameTextStyle: { fontFamily: FONT_FAMILY, fontSize: 12, color: COLORS.textSecondary },
      axisLabel: { fontFamily: FONT_FAMILY, fontSize: 11, color: COLORS.textSecondary },
      splitLine: { lineStyle: { color: COLORS.border, type: 'dashed' } },
    },
    series: [{
      type: 'bar',
      data: tails.map((t, i) => ({
        value: t.count,
        itemStyle: { color: TAIL_COLORS[i % TAIL_COLORS.length], borderRadius: [3, 3, 0, 0] },
      })),
      barMaxWidth: 32,
    }],
  }, true)
}

function handleResize() {
  pieInstance?.resize()
  barInstance?.resize()
}

onMounted(() => {
  if (pieRef.value) {
    pieInstance = echarts.init(pieRef.value)
    updatePie()
  }
  if (barRef.value) {
    barInstance = echarts.init(barRef.value)
    updateBar()
  }
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  pieInstance?.dispose()
  barInstance?.dispose()
  pieInstance = null
  barInstance = null
})

watch(() => props.data, () => { updatePie(); updateBar() }, { deep: true })
</script>

<template>
  <div class="consecutive-tail-chart">
    <div class="chart-scroll-wrapper">
      <div ref="pieRef" class="chart-half" />
    </div>
    <div class="chart-scroll-wrapper">
      <div ref="barRef" class="chart-half" />
    </div>
  </div>
</template>

<style scoped>
.consecutive-tail-chart {
  display: flex;
  gap: var(--spacing-md);
}

.chart-scroll-wrapper {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  max-width: 100%;
  flex: 1;
  min-width: 0;
}

.chart-half {
  min-width: 300px;
  min-height: 320px;
  height: 320px;
}

@media (max-width: 768px) {
  .consecutive-tail-chart {
    flex-direction: column;
  }
}
</style>
