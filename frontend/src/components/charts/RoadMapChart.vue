<script setup lang="ts">
import { computed, ref } from 'vue'

interface RoadMapDraw {
  draw_term: string
  draw_date: string
  numbers_sorted: number[]
  special_number: number | null
}

interface Props {
  draws: RoadMapDraw[]
  poolSize: number
  showSpecial: boolean
}

const props = defineProps<Props>()

const tooltipText = ref('')
const tooltipVisible = ref(false)
const tooltipX = ref(0)
const tooltipY = ref(0)
const hoveredRow = ref<number | null>(null)

// Reversed so newest draw is on the right
const orderedDraws = computed(() => [...props.draws].reverse())

const numbers = computed(() => {
  const arr: number[] = []
  for (let i = 1; i <= props.poolSize; i++) arr.push(i)
  return arr
})

function formatDate(dateStr: string): string {
  // dateStr format: "YYYY-MM-DD"
  const parts = dateStr.split('-')
  if (parts.length === 3) {
    return `${parts[1]}/${parts[2]}`
  }
  return dateStr
}

function hasNumber(draw: RoadMapDraw, num: number): boolean {
  return draw.numbers_sorted.includes(num)
}

function isSpecial(draw: RoadMapDraw, num: number): boolean {
  return props.showSpecial && draw.special_number === num
}

function showTooltip(event: MouseEvent, draw: RoadMapDraw, num: number) {
  tooltipText.value = `No.${num} - 第${draw.draw_term}期 ${draw.draw_date}`
  tooltipVisible.value = true
  tooltipX.value = event.clientX + 12
  tooltipY.value = event.clientY - 30
}

function hideTooltip() {
  tooltipVisible.value = false
}
</script>

<template>
  <div class="road-map">
    <div class="road-map__scroll">
      <table class="road-map__table">
        <thead>
          <tr>
            <th class="road-map__corner">No.</th>
            <th
              v-for="draw in orderedDraws"
              :key="draw.draw_term"
              class="road-map__date-header"
            >
              {{ formatDate(draw.draw_date) }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="num in numbers"
            :key="num"
            class="road-map__row"
            :class="{ 'road-map__row--hover': hoveredRow === num }"
            @mouseenter="hoveredRow = num"
            @mouseleave="hoveredRow = null"
          >
            <td class="road-map__number-label">{{ num }}</td>
            <td
              v-for="draw in orderedDraws"
              :key="draw.draw_term + '-' + num"
              class="road-map__cell"
            >
              <span
                v-if="isSpecial(draw, num)"
                class="road-map__dot road-map__dot--special"
                @mouseenter="showTooltip($event, draw, num)"
                @mouseleave="hideTooltip"
              ></span>
              <span
                v-else-if="hasNumber(draw, num)"
                class="road-map__dot road-map__dot--main"
                @mouseenter="showTooltip($event, draw, num)"
                @mouseleave="hideTooltip"
              ></span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Tooltip -->
    <Teleport to="body">
      <div
        v-if="tooltipVisible"
        class="road-map-tooltip"
        :style="{ left: tooltipX + 'px', top: tooltipY + 'px' }"
      >
        {{ tooltipText }}
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.road-map {
  position: relative;
  width: 100%;
}

.road-map__scroll {
  overflow-x: auto;
  overflow-y: visible;
  -webkit-overflow-scrolling: touch;
}

.road-map__table {
  border-collapse: collapse;
  font-size: 0.75rem;
  font-family: var(--font-mono);
}

.road-map__corner {
  position: sticky;
  left: 0;
  z-index: 2;
  background: var(--color-surface);
  padding: 4px 8px;
  text-align: center;
  font-weight: 700;
  color: var(--color-text-secondary);
  border-bottom: 2px solid var(--color-border);
  min-width: 40px;
}

.road-map__date-header {
  padding: 4px 2px;
  text-align: center;
  font-weight: 600;
  color: var(--color-text-secondary);
  border-bottom: 2px solid var(--color-border);
  white-space: nowrap;
  min-width: 28px;
  font-size: 0.65rem;
}

.road-map__row {
  transition: background-color 0.15s;
}

.road-map__row--hover {
  background-color: rgba(233, 196, 106, 0.12);
}

.road-map__number-label {
  position: sticky;
  left: 0;
  z-index: 1;
  background: var(--color-surface);
  padding: 2px 8px;
  text-align: center;
  font-weight: 700;
  color: var(--color-text);
  border-right: 1px solid var(--color-border);
  min-width: 40px;
}

.road-map__row--hover .road-map__number-label {
  background-color: rgba(233, 196, 106, 0.12);
}

.road-map__cell {
  padding: 2px;
  text-align: center;
  vertical-align: middle;
  min-width: 28px;
  height: 22px;
  border-bottom: 1px solid rgba(223, 230, 233, 0.4);
}

.road-map__dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  cursor: pointer;
  transition: transform 0.15s;
}

.road-map__dot:hover {
  transform: scale(1.5);
}

.road-map__dot--main {
  background-color: var(--color-primary);
  box-shadow: 0 0 3px rgba(233, 196, 106, 0.5);
}

.road-map__dot--special {
  background-color: var(--color-ball-special);
  box-shadow: 0 0 3px rgba(108, 92, 231, 0.5);
}

@media (max-width: 768px) {
  .road-map__date-header {
    font-size: 0.6rem;
    min-width: 24px;
    padding: 3px 1px;
  }

  .road-map__cell {
    min-width: 24px;
    height: 20px;
  }

  .road-map__dot {
    width: 8px;
    height: 8px;
  }
}
</style>

<style>
/* Global tooltip - not scoped so Teleport works */
.road-map-tooltip {
  position: fixed;
  z-index: 9999;
  background: var(--color-text, #2D3436);
  color: #fff;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-family: var(--font-mono, monospace);
  white-space: nowrap;
  pointer-events: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}
</style>
