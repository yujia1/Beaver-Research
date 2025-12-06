import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../components/Dashboard.vue'
import TimelineView from '../components/TimelineView.vue'
import LoginView from '../components/LoginView.vue'
import SignUpView from '../components/SignUpView.vue'
import ResearchView from '../components/ResearchView.vue'
import AdminView from '../components/AdminView.vue'
import ReportView from '../components/ReportView.vue'

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
    },
    {
      path: '/report',
      name: 'report',
      component: ReportView,
      meta: { requiresAuth: false }
    },
    {
      path: '/admin',
      name: 'admin',
      component: AdminView,
      meta: { requiresAuth: true, requiresAdmin: true }
    }
  ]
})

// Navigation guard
router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('access_token')
  const requiresAuth = to.meta.requiresAuth !== false
  const requiresAdmin = to.meta.requiresAdmin === true
  
  if (requiresAuth && !token) {
    // Redirect to login if route requires auth and user is not authenticated
    next('/login')
    return
  }
  
  // Check admin requirement
  if (requiresAdmin && token) {
    try {
      const userStr = localStorage.getItem('user')
      if (userStr) {
        const user = JSON.parse(userStr)
        if (user.role !== 'admin') {
          next('/')
          return
        }
      } else {
        // Fetch user info if not in localStorage
        const response = await fetch('http://localhost:8000/api/auth/me', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        if (response.ok) {
          const user = await response.json()
          localStorage.setItem('user', JSON.stringify(user))
          if (user.role !== 'admin') {
            next('/')
            return
          }
        } else {
          next('/login')
          return
        }
      }
    } catch (error) {
      console.error('Error checking admin status:', error)
      next('/')
      return
    }
  }
  
  if (!requiresAuth && token && (to.path === '/login' || to.path === '/signup')) {
    // Redirect to home if user is already logged in and tries to access login/signup
    next('/')
  } else {
    next()
  }
})

export default router
