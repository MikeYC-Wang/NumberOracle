<script setup lang="ts">
// Spline 3D 搖獎預測區 - 後續整合 @splinetool/runtime
</script>

<template>
  <div class="page-content">
    <div class="container">
      <h1>
        <i class="fas fa-magic"></i>
        預測搖獎區
      </h1>
      <p class="subtitle">結合 3D 物理慣性特效的互動選號體驗</p>

      <div class="prediction-area card">
        <div class="spline-container">
          <i class="fas fa-cube fa-3x"></i>
          <p>Spline 3D 場景載入區</p>
          <p class="placeholder">整合開發中...</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.subtitle { color: var(--color-text-secondary); margin-bottom: var(--spacing-xl); }
h1 i { color: var(--color-accent); margin-right: var(--spacing-sm); }

.prediction-area {
  min-height: 500px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.spline-container {
  text-align: center;
  color: var(--color-text-muted);
}
.spline-container i {
  color: var(--color-primary);
  margin-bottom: var(--spacing-md);
}
.spline-container p {
  margin-top: var(--spacing-sm);
}
.placeholder {
  font-size: 0.875rem;
}
</style>
