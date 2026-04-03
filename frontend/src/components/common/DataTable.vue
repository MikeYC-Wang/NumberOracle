<script setup lang="ts">
import { ref, computed } from 'vue'
import type { DrawResult } from '../../types/lottery'
import LotteryBall from './LotteryBall.vue'

interface Props {
  draws: DrawResult[]
  showSpecial?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showSpecial: false,
})

const PAGE_SIZE = 20
const currentPage = ref(1)

const totalPages = computed(() =>
  Math.max(1, Math.ceil(props.draws.length / PAGE_SIZE)),
)

const pagedDraws = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return props.draws.slice(start, start + PAGE_SIZE)
})

function goTo(page: number) {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}

/** 滑動視窗分頁：固定顯示 3 個頁碼 */
const visiblePages = computed(() => {
  const total = totalPages.value
  const current = currentPage.value

  if (total <= 3) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }

  let start = current
  if (start + 2 > total) {
    start = total - 2
  }
  if (start < 1) {
    start = 1
  }

  return [start, start + 1, start + 2]
})
</script>

<template>
  <div class="data-table-wrapper">
    <table class="data-table">
      <thead>
        <tr>
          <th>期數</th>
          <th>開獎日期</th>
          <th>開獎號碼</th>
          <th v-if="showSpecial">特別號</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="draw in pagedDraws" :key="draw.id">
          <td class="data-table__term">{{ draw.draw_term }}</td>
          <td class="data-table__date">{{ draw.draw_date }}</td>
          <td class="data-table__numbers">
            <LotteryBall
              v-for="num in draw.numbers_sorted"
              :key="num"
              :number="num"
              type="normal"
              size="sm"
            />
          </td>
          <td v-if="showSpecial" class="data-table__special">
            <LotteryBall
              v-if="draw.special_number !== null"
              :number="draw.special_number"
              type="special"
              size="sm"
            />
            <span v-else class="data-table__na">--</span>
          </td>
        </tr>
        <tr v-if="draws.length === 0">
          <td :colspan="showSpecial ? 4 : 3" class="data-table__empty">
            <i class="fas fa-inbox" /> 暫無資料
          </td>
        </tr>
      </tbody>
    </table>

    <!-- 分頁 -->
    <nav v-if="totalPages > 1" class="data-table-pager">
      <button
        class="pager-btn"
        :disabled="currentPage === 1"
        @click="goTo(currentPage - 1)"
      >
        <i class="fas fa-chevron-left" />
      </button>
      <button
        v-for="p in visiblePages"
        :key="p"
        class="pager-btn"
        :class="{ 'pager-btn--active': p === currentPage }"
        @click="goTo(p)"
      >
        {{ p }}
      </button>
      <button
        class="pager-btn"
        :disabled="currentPage === totalPages"
        @click="goTo(currentPage + 1)"
      >
        <i class="fas fa-chevron-right" />
      </button>
    </nav>
  </div>
</template>

<style scoped>
.data-table-wrapper {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--font-sans);
  font-size: 14px;
}

.data-table th {
  background: var(--color-bg);
  color: var(--color-text-secondary);
  font-weight: 600;
  text-align: left;
  padding: var(--spacing-md) var(--spacing-md);
  border-bottom: 2px solid var(--color-border);
  white-space: nowrap;
}

.data-table thead {
  margin-top: var(--spacing-md);
}

.data-table-wrapper h2 + & {
  margin-top: var(--spacing-md);
}

.data-table td {
  padding: var(--spacing-sm) var(--spacing-md);
  border-bottom: 1px solid var(--color-border);
  vertical-align: middle;
}

.data-table tbody tr {
  transition: background-color 0.15s ease;
}

.data-table tbody tr:hover {
  background-color: var(--color-surface-hover);
}

.data-table__term {
  font-family: var(--font-mono);
  font-weight: 600;
  white-space: nowrap;
}

.data-table__date {
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.data-table__numbers {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

.data-table__special {
  text-align: center;
}

.data-table__na {
  color: var(--color-text-muted);
}

.data-table__empty {
  text-align: center;
  padding: var(--spacing-xl) var(--spacing-md);
  color: var(--color-text-muted);
}

.data-table__empty i {
  margin-right: var(--spacing-xs);
}

/* 分頁 */
.data-table-pager {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-md) 0;
}

.pager-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  height: 32px;
  padding: 0 var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  font-family: var(--font-mono);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.pager-btn:hover:not(:disabled) {
  border-color: var(--color-primary);
  color: var(--color-primary-dark);
}

.pager-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.pager-btn--active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
  font-weight: 700;
}
</style>
