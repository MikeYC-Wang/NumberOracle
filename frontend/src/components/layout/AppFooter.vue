<template>
  <footer class="footer">
    <div class="footer__inner container">
      <span>&copy; {{ new Date().getFullYear() }} NumberOracle.</span>
      <span class="footer__sep">|</span>
      <span>本站僅提供歷史數據統計分析，不構成任何投注建議。</span>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  background-color: var(--color-primary);
  padding: var(--spacing-sm) 0;
  margin-top: auto;
}

.footer__inner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  font-size: 0.8125rem;
  color: var(--color-text);
}

.footer__sep {
  color: var(--color-primary-dark);
}

@media (max-width: 768px) {
  .footer__inner {
    font-size: 0.75rem;
  }
}
</style>
