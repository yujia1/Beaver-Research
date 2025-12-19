import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../components/Dashboard.vue'
import TimelineView from '../components/TimelineView.vue'
import LoginView from '../components/LoginView.vue'
import SignUpView from '../components/SignUpView.vue'
import ResearchView from '../components/ResearchView.vue'
import AdminView from '../components/AdminView.vue'
import ReportView from '../components/ReportView.vue'
import ShortInterestView from '../components/ShortInterestView.vue'
import AlphaTradeView from '../components/AlphaTradeView.vue'

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
      meta: { requiresAuth: true, requiresAdminOrCreator: true }
    },
    {
      path: '/short-interest',
      name: 'short-interest',
      component: ShortInterestView,
      meta: { requiresAuth: true, requiresAdminOrCreator: true }
    },
    {
      path: '/report',
      name: 'report',
      component: ReportView,
      meta: { requiresAuth: false, requiresPayment: true }
    },
    {
      path: '/admin',
      name: 'admin',
      component: AdminView,
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/alphatrade',
      name: 'alphatrade',
      component: AlphaTradeView,
      meta: { requiresAuth: false }
    }
  ]
})

// Navigation guard
router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('access_token')
  const requiresAuth = to.meta.requiresAuth !== false
  const requiresAdmin = to.meta.requiresAdmin === true
  const requiresAdminOrCreator = to.meta.requiresAdminOrCreator === true
  const requiresPayment = to.meta.requiresPayment === true

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

  // Check admin or creator requirement
  if (requiresAdminOrCreator && token) {
    try {
      const userStr = localStorage.getItem('user')
      let user = null
      if (userStr) {
        user = JSON.parse(userStr)
      } else {
        // Fetch user info if not in localStorage
        const response = await fetch('http://localhost:8000/api/auth/me', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        if (response.ok) {
          user = await response.json()
          localStorage.setItem('user', JSON.stringify(user))
        } else {
          next('/login')
          return
        }
      }

      // Check if user has admin or creator role
      if (user && user.role !== 'admin' && user.role !== 'creator') {
        next('/')
        return
      }
    } catch (error) {
      console.error('Error checking admin/creator status:', error)
      next('/')
      return
    }
  }

  // Check payment requirement - allow route but component will handle payment gate
  // This allows the component to show PaymentGate UI instead of redirecting
  if (requiresPayment && !token) {
    // If payment required but no token, redirect to login
    next('/login')
    return
  }

  if (!requiresAuth && token && (to.path === '/login' || to.path === '/signup')) {
    // Redirect to home if user is already logged in and tries to access login/signup
    next('/')
  } else {
    next()
  }
})

export default router
