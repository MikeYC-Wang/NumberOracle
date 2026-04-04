<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '../../stores/authStore'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'

const authStore = useAuthStore()

const mobileMenuOpen = ref(false)
const refreshing = ref(false)
const refreshStatus = ref<'idle' | 'success' | 'error'>('idle')
const refreshMessage = ref('')

function toggleMenu() {
  mobileMenuOpen.value = !mobileMenuOpen.value
}

async function handleRefresh() {
  if (refreshing.value) return

  refreshing.value = true
  refreshStatus.value = 'idle'
  refreshMessage.value = ''

  try {
    const res = await fetch(`${API_BASE}/draws/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    })
    const data = await res.json()

    if (res.ok) {
      refreshStatus.value = 'success'
      refreshMessage.value = data.message || '資料更新完成'
    } else {
      refreshStatus.value = 'error'
      refreshMessage.value = data.message || `更新失敗 (${res.status})`
    }
  } catch (e) {
    refreshStatus.value = 'error'
    refreshMessage.value = '網路錯誤，無法連線後端'
  } finally {
    refreshing.value = false
    setTimeout(() => {
      refreshStatus.value = 'idle'
      refreshMessage.value = ''
    }, 2000)
  }
}

async function handleLogout() {
  await authStore.logout()
  mobileMenuOpen.value = false
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
        <li>
          <router-link to="/check" @click="mobileMenuOpen = false">
            <i class="fas fa-check-double"></i> 對獎
          </router-link>
        </li>
        <li>
          <router-link to="/backtest" @click="mobileMenuOpen = false">
            <i class="fas fa-flask"></i> 回測
          </router-link>
        </li>

        <!-- Auth -->
        <li v-if="!authStore.isLoggedIn">
          <router-link to="/login" @click="mobileMenuOpen = false">
            <i class="fas fa-sign-in-alt"></i> 登入
          </router-link>
        </li>
        <li v-if="authStore.isLoggedIn" class="navbar__user-wrapper">
          <span class="navbar__username">
            <i class="fas fa-user-circle"></i>
            {{ authStore.user?.username ?? '使用者' }}
          </span>
          <router-link
            to="/my-predictions"
            class="navbar__bookmark-link"
            @click="mobileMenuOpen = false"
          >
            <i class="fas fa-bookmark"></i> 我的收藏
          </router-link>
          <button class="navbar__logout-btn" @click="handleLogout">
            <i class="fas fa-sign-out-alt"></i> 登出
          </button>
        </li>

        <li class="navbar__refresh-wrapper">
          <button
            class="navbar__refresh-btn"
            :class="{
              'navbar__refresh-btn--success': refreshStatus === 'success',
              'navbar__refresh-btn--error': refreshStatus === 'error',
            }"
            :disabled="refreshing"
            @click="handleRefresh"
          >
            <i
              :class="
                refreshing
                  ? 'fas fa-spinner fa-spin'
                  : refreshStatus === 'success'
                    ? 'fas fa-check'
                    : refreshStatus === 'error'
                      ? 'fas fa-exclamation-triangle'
                      : 'fas fa-sync-alt'
              "
            ></i>
            <span v-if="refreshStatus === 'idle' && !refreshing">更新資料</span>
            <span v-else-if="refreshing">更新中...</span>
            <span v-else>{{ refreshMessage }}</span>
          </button>
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
  align-items: center;
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

/* User auth area */
.navbar__user-wrapper {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.navbar__username {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  color: var(--color-text);
  font-weight: 600;
  font-size: 0.9rem;
  white-space: nowrap;
}

.navbar__bookmark-link {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  font-weight: 500;
  font-size: 0.875rem;
  background-color: rgba(255, 255, 255, 0.15);
  color: var(--color-text);
  text-decoration: none;
  transition: background-color 0.2s ease;
}

.navbar__bookmark-link:hover {
  background-color: rgba(255, 255, 255, 0.25);
}

.navbar__logout-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  border: none;
  cursor: pointer;
  font-weight: 500;
  font-size: 0.875rem;
  font-family: inherit;
  background-color: rgba(255, 255, 255, 0.15);
  color: var(--color-text);
  transition: background-color 0.2s ease;
}

.navbar__logout-btn:hover {
  background-color: rgba(255, 255, 255, 0.25);
}

.navbar__refresh-wrapper {
  margin-left: var(--spacing-sm);
}

.navbar__refresh-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  border: none;
  cursor: pointer;
  font-weight: 500;
  font-size: 0.9375rem;
  font-family: inherit;
  background-color: rgba(255, 255, 255, 0.15);
  color: var(--color-text);
  transition: background-color 0.2s ease, opacity 0.2s ease;
}

.navbar__refresh-btn:hover:not(:disabled) {
  background-color: rgba(255, 255, 255, 0.25);
}

.navbar__refresh-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.navbar__refresh-btn--success {
  color: #4ade80;
}

.navbar__refresh-btn--error {
  color: #f87171;
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

  .navbar__user-wrapper {
    flex-direction: column;
    align-items: stretch;
  }

  .navbar__username {
    padding: var(--spacing-md);
  }

  .navbar__logout-btn {
    padding: var(--spacing-md);
    justify-content: flex-start;
  }
}
</style>
