<script setup lang="ts">
import { ref } from 'vue'

const mobileMenuOpen = ref(false)

function toggleMenu() {
  mobileMenuOpen.value = !mobileMenuOpen.value
}
</script>

<template>
  <nav class="navbar">
    <div class="navbar__inner container">
      <router-link to="/" class="navbar__brand">
        <span class="navbar__title">NumberOracle</span>
      </router-link>

      <button class="navbar__toggle" @click="toggleMenu" aria-label="切換選單">
        <i :class="mobileMenuOpen ? 'fas fa-times' : 'fas fa-bars'"></i>
      </button>

      <ul class="navbar__links" :class="{ 'navbar__links--open': mobileMenuOpen }">
        <li>
          <router-link to="/" @click="mobileMenuOpen = false">
            <i class="fas fa-chart-line"></i> 總覽
          </router-link>
        </li>
        <li>
          <router-link to="/daily-cash" @click="mobileMenuOpen = false">
            <i class="fas fa-star"></i> 今彩539
          </router-link>
        </li>
        <li>
          <router-link to="/lotto649" @click="mobileMenuOpen = false">
            <i class="fas fa-trophy"></i> 大樂透
          </router-link>
        </li>
        <li>
          <router-link to="/super-lotto" @click="mobileMenuOpen = false">
            <i class="fas fa-bolt"></i> 威力彩
          </router-link>
        </li>
        <li>
          <router-link to="/prediction" @click="mobileMenuOpen = false">
            <i class="fas fa-magic"></i> 預測搖獎
          </router-link>
        </li>
      </ul>
    </div>
  </nav>
</template>

<style scoped>
.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
  height: var(--navbar-height);
  background-color: var(--color-primary);
  box-shadow: var(--shadow-sm);
}

.navbar__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
}

.navbar__brand {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  color: var(--color-text);
  font-weight: 700;
  font-size: 1.25rem;
  text-decoration: none;
}

.navbar__logo {
  height: 44px;
  width: auto;
}

.navbar__toggle {
  display: none;
  background: none;
  color: var(--color-text);
  font-size: 1.25rem;
  padding: var(--spacing-sm);
}

.navbar__links {
  display: flex;
  gap: var(--spacing-xs);
}

.navbar__links a {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  color: var(--color-text);
  font-weight: 500;
  font-size: 0.9375rem;
  transition: background-color 0.2s ease;
}

.navbar__links a:hover,
.navbar__links a.router-link-active {
  background-color: var(--color-primary-dark);
  color: var(--color-surface);
}

@media (max-width: 768px) {
  .navbar__toggle {
    display: block;
  }

  .navbar__links {
    display: none;
    position: absolute;
    top: var(--navbar-height);
    left: 0;
    right: 0;
    flex-direction: column;
    background-color: var(--color-primary);
    padding: var(--spacing-md);
    box-shadow: var(--shadow-md);
  }

  .navbar__links--open {
    display: flex;
  }

  .navbar__links a {
    padding: var(--spacing-md);
  }
}
</style>
