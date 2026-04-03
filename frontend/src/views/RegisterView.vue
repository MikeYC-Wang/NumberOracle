<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/authStore'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const email = ref('')
const password = ref('')
const passwordConfirm = ref('')
const errorMsg = ref('')
const loading = ref(false)

const usernameError = computed(() => {
  if (!username.value) return ''
  if (!/^[a-zA-Z0-9_]+$/.test(username.value)) return '只能包含英文字母、數字和底線'
  if (username.value.length < 3) return '至少 3 個字元'
  return ''
})

const passwordStrength = computed(() => {
  const p = password.value
  if (!p) return { level: 0, text: '', color: '' }
  let score = 0
  if (p.length >= 8) score++
  if (/[A-Z]/.test(p)) score++
  if (/[a-z]/.test(p)) score++
  if (/[0-9]/.test(p)) score++
  if (/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?/~`]/.test(p)) score++

  if (score <= 2) return { level: 1, text: '弱', color: 'var(--color-accent)' }
  if (score <= 3) return { level: 2, text: '中', color: '#E9C46A' }
  if (score === 4) return { level: 3, text: '強', color: 'var(--color-secondary)' }
  return { level: 4, text: '極強', color: '#2A9D8F' }
})

const passwordErrors = computed(() => {
  const p = password.value
  if (!p) return []
  const errs: string[] = []
  if (p.length < 8) errs.push('至少 8 個字元')
  if (!/[A-Z]/.test(p)) errs.push('需包含大寫字母')
  if (!/[a-z]/.test(p)) errs.push('需包含小寫字母')
  if (!/[0-9]/.test(p)) errs.push('需包含數字')
  if (!/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?/~`]/.test(p)) errs.push('需包含特殊符號')
  return errs
})

const passwordMismatch = computed(() => {
  if (!passwordConfirm.value) return false
  return password.value !== passwordConfirm.value
})

const canSubmit = computed(() => {
  return username.value
    && !usernameError.value
    && password.value
    && passwordErrors.value.length === 0
    && passwordConfirm.value
    && !passwordMismatch.value
    && !loading.value
})

async function handleRegister() {
  errorMsg.value = ''

  if (!canSubmit.value) {
    errorMsg.value = '請修正上方的欄位錯誤'
    return
  }

  loading.value = true
  try {
    await authStore.register(
      username.value,
      password.value,
      passwordConfirm.value,
      email.value || undefined,
    )
    router.push('/')
  } catch (e) {
    errorMsg.value = e instanceof Error ? e.message : '註冊失敗'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card">
      <h1 class="auth-title">
        <i class="fas fa-user-plus"></i>
        註冊
      </h1>

      <form class="auth-form" @submit.prevent="handleRegister">
        <div class="form-group">
          <label for="reg-username">
            <i class="fas fa-user"></i> 帳號 <span class="required">*</span>
          </label>
          <input
            id="reg-username"
            v-model="username"
            type="text"
            placeholder="英文字母、數字、底線"
            autocomplete="username"
            :class="{ 'input-error': usernameError }"
          />
          <p v-if="usernameError" class="field-error">
            <i class="fas fa-exclamation-triangle"></i> {{ usernameError }}
          </p>
          <p v-else-if="username" class="field-hint">
            <i class="fas fa-check-circle"></i> 帳號格式正確
          </p>
        </div>

        <div class="form-group">
          <label for="reg-email">
            <i class="fas fa-envelope"></i> Email (選填)
          </label>
          <input
            id="reg-email"
            v-model="email"
            type="email"
            placeholder="yourname@example.com"
            autocomplete="email"
          />
        </div>

        <div class="form-group">
          <label for="reg-password">
            <i class="fas fa-lock"></i> 密碼 <span class="required">*</span>
          </label>
          <input
            id="reg-password"
            v-model="password"
            type="password"
            placeholder="至少 8 字元，含大小寫+數字+特殊符號"
            autocomplete="new-password"
            :class="{ 'input-error': password && passwordErrors.length > 0 }"
          />
          <div v-if="password" class="password-feedback">
            <div class="strength-bar">
              <div
                class="strength-bar__fill"
                :style="{ width: (passwordStrength.level / 4 * 100) + '%', background: passwordStrength.color }"
              ></div>
            </div>
            <span class="strength-label" :style="{ color: passwordStrength.color }">
              {{ passwordStrength.text }}
            </span>
          </div>
          <ul v-if="password && passwordErrors.length > 0" class="password-rules">
            <li v-for="err in passwordErrors" :key="err" class="rule-fail">
              <i class="fas fa-times-circle"></i> {{ err }}
            </li>
          </ul>
        </div>

        <div class="form-group">
          <label for="reg-password-confirm">
            <i class="fas fa-lock"></i> 確認密碼 <span class="required">*</span>
          </label>
          <input
            id="reg-password-confirm"
            v-model="passwordConfirm"
            type="password"
            placeholder="再次輸入密碼"
            autocomplete="new-password"
            :class="{ 'input-error': passwordMismatch }"
          />
          <p v-if="passwordMismatch" class="field-error">
            <i class="fas fa-exclamation-triangle"></i> 密碼不一致
          </p>
        </div>

        <p v-if="errorMsg" class="auth-error">
          <i class="fas fa-exclamation-circle"></i>
          {{ errorMsg }}
        </p>

        <button
          class="auth-btn"
          type="submit"
          :disabled="!canSubmit"
        >
          <i :class="loading ? 'fas fa-spinner fa-spin' : 'fas fa-user-plus'"></i>
          {{ loading ? '註冊中...' : '註冊' }}
        </button>
      </form>

      <p class="auth-switch">
        已有帳號？
        <router-link to="/login">立即登入</router-link>
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
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-xl);
  font-size: 1.5rem;
  color: var(--color-text);
}

.auth-title i {
  color: var(--color-primary);
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

.required {
  color: var(--color-accent);
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

.form-group input.input-error {
  border-color: var(--color-accent);
}

.field-error {
  color: var(--color-accent);
  font-size: 0.8rem;
}

.field-error i {
  margin-right: var(--spacing-xs);
}

.field-hint {
  color: var(--color-secondary);
  font-size: 0.8rem;
}
.field-hint i {
  margin-right: var(--spacing-xs);
}

.password-feedback {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.strength-bar {
  flex: 1;
  height: 6px;
  background: var(--color-border);
  border-radius: 3px;
  overflow: hidden;
}

.strength-bar__fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease, background 0.3s ease;
}

.strength-label {
  font-size: 0.8rem;
  font-weight: 700;
  min-width: 36px;
}

.password-rules {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs) var(--spacing-md);
}

.password-rules li {
  font-size: 0.75rem;
}

.rule-fail {
  color: var(--color-accent);
}
.rule-fail i {
  margin-right: 2px;
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
