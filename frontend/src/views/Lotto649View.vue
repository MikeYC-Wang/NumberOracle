<script setup lang="ts">
import { onMounted } from 'vue'
import { useLotteryStore } from '../stores/lotteryStore'
import { useAnalysisStore } from '../stores/analysisStore'

const lotteryStore = useLotteryStore()
const analysisStore = useAnalysisStore()

onMounted(() => {
  lotteryStore.selectGame('lotto649')
  analysisStore.fetchDraws('lotto649')
})
</script>

<template>
  <div class="page-content">
    <div class="container">
      <h1>
        <i class="fas fa-trophy"></i>
        大樂透 分析
      </h1>
      <p class="subtitle">6/49 + 特別號 -- 每週二、五開獎</p>

      <div v-if="analysisStore.loading" class="loading">
        <i class="fas fa-spinner fa-spin"></i> 載入中...
      </div>

      <div v-else class="analysis-grid">
        <section class="card">
          <h2><i class="fas fa-fire"></i> 冷熱門號碼</h2>
          <p class="placeholder">圖表開發中...</p>
        </section>

        <section class="card">
          <h2><i class="fas fa-search"></i> 遺漏值分析</h2>
          <p class="placeholder">圖表開發中...</p>
        </section>

        <section class="card full-width">
          <h2><i class="fas fa-history"></i> 歷史開獎紀錄</h2>
          <p class="placeholder">
            共 {{ analysisStore.totalCount }} 筆紀錄
          </p>
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
.subtitle { color: var(--color-text-secondary); margin-bottom: var(--spacing-xl); }
h1 i { color: var(--color-primary); margin-right: var(--spacing-sm); }
h2 i { margin-right: var(--spacing-sm); }
.loading { text-align: center; padding: var(--spacing-2xl); color: var(--color-text-muted); }
.analysis-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: var(--spacing-lg); }
.full-width { grid-column: 1 / -1; }
.placeholder { color: var(--color-text-muted); padding: var(--spacing-xl); text-align: center; }
@media (max-width: 768px) { .analysis-grid { grid-template-columns: 1fr; } }
</style>
