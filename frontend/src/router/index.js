import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../components/Dashboard.vue'
import TimelineView from '../components/TimelineView.vue'
import LoginView from '../components/LoginView.vue'
import SignUpView from '../components/SignUpView.vue'
import ResearchView from '../components/ResearchView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { requiresAuth: false }
    },
    {
      path: '/signup',
      name: 'signup',
      component: SignUpView,
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      name: 'dashboard',
      component: Dashboard,
      meta: { requiresAuth: false }
    },
    {
      path: '/investment',
      name: 'investment',
      component: TimelineView,
      meta: { requiresAuth: false }
    },
    {
      path: '/research',
      name: 'research',
      component: ResearchView,
      meta: { requiresAuth: false }
    }
  ]
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  const requiresAuth = to.meta.requiresAuth !== false
  
  if (requiresAuth && !token) {
    // Redirect to login if route requires auth and user is not authenticated
    next('/login')
  } else if (!requiresAuth && token && (to.path === '/login' || to.path === '/signup')) {
    // Redirect to home if user is already logged in and tries to access login/signup
    next('/')
  } else {
    next()
  }
})

export default router
