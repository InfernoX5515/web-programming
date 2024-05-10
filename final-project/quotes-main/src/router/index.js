import { createRouter, createWebHistory } from 'vue-router'
import Login from '../components/login.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: Login
    },
  ]
})

export default router