<script setup lang="ts">
interface Props {
  number: number
  type?: 'hot' | 'cold' | 'normal' | 'special'
  size?: 'sm' | 'md' | 'lg'
}

withDefaults(defineProps<Props>(), {
  type: 'normal',
  size: 'md',
})
</script>

<template>
  <span
    class="lottery-ball"
    :class="[`lottery-ball--${type}`, `lottery-ball--${size}`]"
  >
    {{ number }}
  </span>
</template>

<style scoped>
.lottery-ball {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-full);
  font-family: var(--font-mono);
  font-weight: 700;
  color: #fff;
  user-select: none;
  flex-shrink: 0;
}

/* --- 尺寸 --- */
.lottery-ball--sm {
  width: 28px;
  height: 28px;
  font-size: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
}

.lottery-ball--md {
  width: 38px;
  height: 38px;
  font-size: 15px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.18);
}

.lottery-ball--lg {
  width: 50px;
  height: 50px;
  font-size: 20px;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
}

/* --- 色彩與漸層 --- */
.lottery-ball--hot {
  background: linear-gradient(135deg, var(--color-accent-light), var(--color-ball-hot));
}

.lottery-ball--cold {
  background: linear-gradient(135deg, var(--color-secondary-light), var(--color-ball-cold));
}

.lottery-ball--normal {
  background: linear-gradient(135deg, var(--color-primary-light), var(--color-ball-normal));
  color: var(--color-text);
}

.lottery-ball--special {
  background: linear-gradient(135deg, #a29bfe, var(--color-ball-special));
}
</style>
