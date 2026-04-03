import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'

import '@fortawesome/fontawesome-free/css/all.min.css'
import './assets/styles/base.css'
import './assets/styles/transitions.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
