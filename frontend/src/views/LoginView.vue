<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/authStore'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const errorMsg = ref('')
const loading = ref(false)

async function handleLogin() {
  errorMsg.value = ''
  if (!username.value || !password.value) {
    errorMsg.value = '請輸入帳號與密碼'
    return
  }

  loading.value = true
  try {
    await authStore.login(username.value, password.value)
    router.push('/')
  } catch (e) {
    errorMsg.value = e instanceof Error ? e.message : '登入失敗'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card">
      <h1 class="auth-title">
        <i class="fas fa-sign-in-alt"></i>
        登入
      </h1>

      <form class="auth-form" @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="login-username">
            <i class="fas fa-user"></i> 帳號
          </label>
          <input
            id="login-username"
            v-model="username"
            type="text"
            placeholder="請輸入帳號"
            autocomplete="username"
          />
        </div>

        <div class="form-group">
          <label for="login-password">
            <i class="fas fa-lock"></i> 密碼
          </label>
          <input
            id="login-password"
            v-model="password"
            type="password"
            placeholder="請輸入密碼"
            autocomplete="current-password"
            @keyup.enter="handleLogin"
          />
        </div>

        <p v-if="errorMsg" class="auth-error">
          <i class="fas fa-exclamation-circle"></i>
          {{ errorMsg }}
        </p>

        <button
          class="auth-btn"
          type="submit"
          :disabled="loading"
        >
          <i :class="loading ? 'fas fa-spinner fa-spin' : 'fas fa-sign-in-alt'"></i>
          {{ loading ? '登入中...' : '登入' }}
        </button>
      </form>

      <p class="auth-switch">
        還沒有帳號？
        <router-link to="/register">立即註冊</router-link>
      </p>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - var(--navbar-height));
  padding: var(--spacing-lg);
}

.auth-card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  padding: var(--spacing-2xl) var(--spacing-xl);
  width: 100%;
  max-width: 420px;
}

.auth-title {
  text-align: center;
  margin-bottom: var(--spacing-xl);
  font-size: 1.5rem;
  color: var(--color-text);
}

.auth-title i {
  color: var(--color-primary);
  margin-right: var(--spacing-sm);
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.form-group label {
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

.form-group label i {
  margin-right: var(--spacing-xs);
  color: var(--color-primary-dark);
}

.form-group input {
  padding: var(--spacing-sm) var(--spacing-md);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 1rem;
  font-family: inherit;
  background: var(--color-surface);
  color: var(--color-text);
  transition: border-color 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(233, 196, 106, 0.25);
}

.auth-error {
  color: var(--color-accent);
  font-size: 0.875rem;
  text-align: center;
}

.auth-error i {
  margin-right: var(--spacing-xs);
}

.auth-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-lg);
  background: var(--color-primary);
  color: var(--color-text);
  border: none;
  border-radius: var(--radius-md);
  font-size: 1rem;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.2s, opacity 0.2s;
  margin-top: var(--spacing-sm);
}

.auth-btn:hover:not(:disabled) {
  background: var(--color-primary-dark);
}

.auth-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.auth-switch {
  text-align: center;
  margin-top: var(--spacing-lg);
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

.auth-switch a {
  color: var(--color-secondary);
  font-weight: 600;
  text-decoration: none;
}

.auth-switch a:hover {
  text-decoration: underline;
}

@media (max-width: 480px) {
  .auth-card {
    padding: var(--spacing-xl) var(--spacing-md);
  }
}
</style>
