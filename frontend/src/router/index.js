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
      meta: { requiresAuth: false } // Controlled dynamically
    },
    {
      path: '/research',
      name: 'research',
      component: ResearchView,
      meta: { requiresAuth: true } // Controlled dynamically
    },
    {
      path: '/short-interest',
      name: 'short-interest',
      component: ShortInterestView,
      meta: { requiresAuth: true } // Controlled dynamically
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
      meta: { requiresAuth: false } // Controlled dynamically
    }
  ]
})

// Helper to check permission
async function checkPermission(user, resource) {
  // Admin always has access
  if (user.role === 'admin') return true

  try {
    const token = localStorage.getItem('access_token')
    const response = await fetch('${API_BASE_URL}/api/auth/my-permissions', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (response.ok) {
      const allowedResources = await response.json()
      return allowedResources.includes(resource)
    }
    return false
  } catch (e) {
    console.error('Error checking permission:', e)
    return false
  }
}

// Navigation guard
router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('access_token')
  const requiresAuth = to.meta.requiresAuth !== false
  const requiresAdmin = to.meta.requiresAdmin === true
  const requiresPayment = to.meta.requiresPayment === true

  // Public routes that don't need permission checks specific to roles (login, signup, dashboard)
  // Note: dashboard (/) is always public
  const publicRoutes = ['/login', '/signup', '/']
  if (publicRoutes.includes(to.path)) {
    if (to.path !== '/' && token && !requiresAuth) {
      next('/')
    } else {
      next()
    }
    return
  }

  if (requiresAuth && !token) {
    next('/login')
    return
  }

  // Get user info
  let user = null
  if (token) {
    try {
      const userStr = localStorage.getItem('user')
      if (userStr) {
        user = JSON.parse(userStr)
      } else {
        const response = await fetch('${API_BASE_URL}/api/auth/me', {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        if (response.ok) {
          user = await response.json()
          localStorage.setItem('user', JSON.stringify(user))
        }
      }
    } catch (e) {
      console.error('Error getting user:', e)
    }
  }

  // Check admin requirement
  if (requiresAdmin) {
    if (!user || user.role !== 'admin') {
      next('/')
      return
    }
  }

  // Check dynamic permissions for protected resources
  // Only check for specific routes that are managed
  const managedRoutes = ['/research', '/alphatrade', '/report', '/investment', '/short-interest']
  if (managedRoutes.includes(to.path)) {
    // If user is not logged in but route is managed (some might be public-facing but restricted)
    // For now, if it requiresAuth, we handled it above.

    // If we have a user, check permission
    if (user) {
      const hasAccess = await checkPermission(user, to.path)
      if (!hasAccess) {
        // Creating a smoother UX: if access denied, redirect home with a query param?
        // or just redirect home
        console.warn(`Access denied to ${to.path} for role ${user.role}`)
        next('/')
        return
      }
    } else {
      // No user, but trying to access managed route.
      // If the route strictly requires auth, we already redirected.
      // If it doesn't strictly require auth (like Report/Investment might not in some configs),
      // we might need to check if "public" access is allowed?
      // For now, simpler approach: if it is a managed route, we enforce the check via backend.
      // Since the backend returns permissions for a USER, unauthenticated users have no permissions.
      // EXCEPTION: If the business logic says "User" role means "Public" too? 
      // Current implementation assumes logic applies to Logged In users or specific roles.
      // Unauthenticated users -> treat as no role?

      // Let's assume managed routes require at least being logged in to check permissions properly,
      // OR if they are public, we explicitly allow them in the backend logic?
      // The current requirement says "grant different user type to different access".
      // Implies logged in users.

      if (to.meta.requiresAuth === false) {
        // It's technically public, but we want to restrict it? 
        // If we really want to restrict /alphatrade which calls itself public metadata currently...
        // We should probably default to enforcing auth for these if we want to manage them.
        // OR we just redirect to login if we can't verify permission.
        next('/login')
        return
      }
    }
  }

  // Check payment requirement
  if (requiresPayment && !token) {
    next('/login')
    return
  }

  next()
})

export default router
