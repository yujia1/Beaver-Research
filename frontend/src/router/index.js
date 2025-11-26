import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../components/Dashboard.vue'
import ProductivityView from '../components/ProductivityView.vue'
import PolicyView from '../components/PolicyView.vue'
import SecurityView from '../components/SecurityView.vue'
import TimelineView from '../components/TimelineView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: Dashboard
    },
    {
      path: '/productivity',
      name: 'productivity',
      component: ProductivityView
    },
    {
      path: '/policy',
      name: 'policy',
      component: PolicyView
    },
    {
      path: '/security',
      name: 'security',
      component: SecurityView
    },
    {
      path: '/timeline',
      name: 'timeline',
      component: TimelineView
    }
  ]
})

export default router
