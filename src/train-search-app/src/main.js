import { createApp } from 'vue'
import App from './App.vue'
import axios from 'axios'

axios.defaults.baseURL = 'http://localhost:8899' // 換成你 API 的位址

createApp(App).mount('#app')
