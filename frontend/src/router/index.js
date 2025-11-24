import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../components/Dashboard.vue'
import MacroView from '../components/MacroView.vue'
import MicroView from '../components/MicroView.vue'
import BondView from '../components/BondView.vue'
import ProductivityView from '../components/ProductivityView.vue'
import PolicyView from '../components/PolicyView.vue'
import SecurityView from '../components/SecurityView.vue'
import ReportView from '../components/ReportView.vue'
import EnergyView from '../components/EnergyView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: Dashboard
    },
    {
      path: '/macro',
      name: 'macro',
      component: MacroView
    },
    {
      path: '/micro',
      name: 'micro',
      component: MicroView
    },
    {
      path: '/bond',
      name: 'bond',
      component: BondView
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
      path: '/energy',
      name: 'energy',
      component: EnergyView
    },
    {
      path: '/report',
      name: 'report',
      component: ReportView
    }
  ]
})

export default router
