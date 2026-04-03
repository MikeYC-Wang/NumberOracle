<script setup lang="ts">
interface Props {
  modelValue: number
  options?: number[]
}

const props = withDefaults(defineProps<Props>(), {
  options: () => [30, 50, 100, 200],
})

const emit = defineEmits<{
  'update:modelValue': [value: number]
}>()

function select(value: number) {
  emit('update:modelValue', value)
}
</script>

<template>
  <div class="period-selector">
    <span class="period-label"><i class="fas fa-filter"></i> 近期期數:</span>
    <div class="period-btn-group">
      <button
        v-for="opt in props.options"
        :key="opt"
        class="period-btn"
        :class="{ active: modelValue === opt }"
        @click="select(opt)"
      >
        {{ opt }} 期
      </button>
    </div>
  </div>
</template>

<style scoped>
.period-selector {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
  flex-wrap: wrap;
}

.period-label {
  font-size: 0.9rem;
  color: var(--color-text-secondary, #636E72);
  white-space: nowrap;
}

.period-label i {
  margin-right: var(--spacing-xs);
}

.period-btn-group {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.period-btn {
  padding: 6px 16px;
  border: 1px solid var(--color-border, #DFE6E9);
  border-radius: var(--radius-md, 8px);
  background: var(--color-surface, #fff);
  color: var(--color-text, #2D3436);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.period-btn:hover {
  border-color: var(--color-primary, #E9C46A);
}

.period-btn.active {
  background: var(--color-primary, #E9C46A);
  border-color: var(--color-primary, #E9C46A);
  color: #fff;
  font-weight: 600;
}
</style>
