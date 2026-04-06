<script setup lang="ts">
import { onMounted } from 'vue'
import AppNavbar from './components/layout/AppNavbar.vue'
import AppFooter from './components/layout/AppFooter.vue'
import { useAuthStore } from './stores/authStore'

const authStore = useAuthStore()
onMounted(() => {
  authStore.initSession()
})
</script>

<template>
  <div class="app-layout">
    <AppNavbar />
    <main class="app-main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <AppFooter />
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-main {
  flex: 1;
  overflow-x: hidden;
}
</style>
