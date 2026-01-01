<script setup>
import { RouterLink, RouterView, useRouter, useRoute } from 'vue-router'
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import LanguageSwitcher from './components/LanguageSwitcher.vue'
import { usePermissionStore } from '@/stores/permissionStore'
import { useUserStore } from '@/stores/userStore'

import API_BASE_URL from './config/api.js'


const router = useRouter()
const route = useRoute()
const { t } = useI18n()
const permissionStore = usePermissionStore()
const userStore = useUserStore()

// State from stores
const user = computed(() => userStore.user)
const isAuthenticated = computed(() => userStore.isAuthenticated)
const allowedResources = computed(() => permissionStore.permissions)

// Helper methods
const hasAccess = (resource) => permissionStore.hasAccess(resource)

const logout = (e) => {
  if (e) e.preventDefault()
  userStore.logout()
}

const getRoleBadgeColor = (role) => {
  const colors = {
    admin: '#000000',
    creator: '#262626',
    contributor: '#525252',
    user: '#737373'
  }
  return colors[role] || colors.user
}

// Menu Items
const menuItems = computed(() => {
  const items = [
    { 
      path: '/', 
      name: t('nav.dashboard'), 
      icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="20" x2="12" y2="10"></line><line x1="18" y1="20" x2="18" y2="4"></line><line x1="6" y1="20" x2="6" y2="16"></line></svg>' 
    }
  ]
  
  // Base items that might be restricted

  const reportItem = { 
    path: '/report', 
    name: t('nav.report'), 
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>' 
  }
  
  const portfolioItem = { 
    path: '/portfolio', 
    name: t('nav.portfolio'), 
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>' 
  }
  
  const frameworkItem = {
    path: '/framework',
    name: t('nav.framework'),
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>'
  }
  
  const academyItem = {
    path: '/academy',
    name: t('nav.academy'),
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>'
  }
  
  const researchItem = {
    path: '/research',
    name: t('nav.research'),
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><path d="m21 21-4.35-4.35"></path></svg>'
  }



  // Check if user is logged in
  if (user.value) {
    // User is logged in - check permissions
    if (user.value.role === 'admin') {
      // Admin gets everything
      items.push(frameworkItem)
      items.push(reportItem)
      items.push(portfolioItem)
      items.push(academyItem)
      items.push(researchItem)
    } else {
      // Check specific permissions for logged-in non-admin users
      if (hasAccess('/framework')) items.push(frameworkItem)
      if (hasAccess('/report')) items.push(reportItem)
      if (hasAccess('/portfolio')) items.push(portfolioItem)
      if (hasAccess('/academy')) items.push(academyItem)
      if (hasAccess('/research')) items.push(researchItem)
    }
  } else {
    // User is NOT logged in - show all items except admin
    items.push(frameworkItem)
    items.push(reportItem)
    items.push(portfolioItem)
    items.push(academyItem)
    items.push(researchItem)
  }

  // Upgrade to Pro (if not paid and not admin)
  if (user.value && !user.value.has_paid && user.value.role !== 'admin') {
      items.push({
          path: '/pricing',
          name: 'Upgrade', // Could use t('nav.upgrade') if available
          icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>'
      })
  }

  
  // Add Admin link only for admin users
  if (user.value && user.value.role === 'admin') {
    items.push({
      path: '/admin',
      name: t('nav.admin'),
      icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>'
    })
  }
  
  return items
})

// Update stores on mount
onMounted(() => {
  // Check if we have token
  // Check if we have token
  if (userStore.isAuthenticated) {
    // Always fetch fresh user data (for has_paid status) and permissions
    userStore.fetchUser(API_BASE_URL)
    permissionStore.fetch(API_BASE_URL)
  }
})
</script>

<template>
  <div class="app-container">
    <aside class="sidebar">
      <nav>
        <RouterLink 
          v-for="item in menuItems" 
          :key="item.path" 
          :to="item.path"
          class="nav-item"
        >
          <div class="icon-wrapper" v-html="item.icon"></div>
          <span class="link-text">{{ item.name }}</span>
        </RouterLink>
      </nav>
      
      <div v-if="isAuthenticated" class="user-section">
        <div v-if="user" class="user-info">
          <div class="user-avatar">{{ user.username.charAt(0).toUpperCase() }}</div>
          <div class="user-details">
            <!-- <div class="username">{{ user.username }}</div> -->
          </div>
        </div>
        <div v-else class="user-info">
          <div class="user-avatar">?</div>
          <div class="user-details">
            <div class="username">{{ t('common.loading') }}</div>
          </div>
        </div>
        <button @click="logout" class="logout-btn">
          <span class="logout-text">{{ t('nav.logout') }}</span>
        </button>
      </div>
      
      <div v-else class="auth-section">
        <RouterLink to="/login" class="auth-link">
          <span class="auth-text">{{ t('nav.login') }}</span>
        </RouterLink>
        <RouterLink to="/signup" class="auth-link">
          <span class="auth-text">{{ t('auth.signup') }}</span>
        </RouterLink>
      </div>

      <div class="lang-switch-container">
        <LanguageSwitcher />
      </div>
    </aside>
    
    <div class="main-content">
      <router-view v-slot="{ Component }">
        <keep-alive>
          <component :is="Component" />
        </keep-alive>
      </router-view>
    </div>
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  min-height: 100vh;
  width: 100%;
  background-color: #ffffff;
}

.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  width: 60px; /* Minimized width */
  background-color: #ffffff;
  padding: 1rem 0;
  box-shadow: 2px 0 5px rgba(0, 0, 0, 0.1);
  border-right: 1px solid #cccccc;
  z-index: 1000;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
}

.sidebar:hover {
  width: 240px; /* Expanded width */
}

nav {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 0.8rem 0; /* Vertical padding only, horizontal handled by children */
  color: #666666; /* Default text color gray */
  text-decoration: none;
  font-size: 1rem;
  font-weight: 600; /* Bolder text */
  border-left: 3px solid transparent;
  transition: all 0.2s ease;
  white-space: nowrap;
  height: 50px; /* Fixed height for consistency */
  text-transform: uppercase; /* Uppercase for AlphaTrade style */
  letter-spacing: 0.5px;
}

.nav-item:hover {
  background-color: #f5f5f5;
  border-left-color: #000000;
  color: #000000;
}

.nav-item.router-link-exact-active {
  color: #000000;
  background-color: #f0f0f0;
  border-left-color: #000000;
  font-weight: 700;
}

.icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 60px; /* Matches sidebar minimized width */
  height: 100%;
}

/* Target SVG within v-html */
:deep(.icon-wrapper svg) {
  width: 24px;
  height: 24px;
  stroke: currentColor;
  color: inherit;
}

.link-text {
  opacity: 0;
  transform: translateX(-10px);
  transition: opacity 0.2s ease, transform 0.2s ease;
  margin-left: 10px;
}

.sidebar:hover .link-text {
  opacity: 1;
  transform: translateX(0);
  transition-delay: 0.1s; /* Wait for sidebar to start expanding */
}

.main-content {
  flex: 1;
  min-width: 0; /* Prevent flex item from overflowing */
  min-height: 100vh;
  padding-left: 2rem;
  background-color: #ffffff;
  /* No margin-left needed because of flex layout */
}

.sidebar {
  display: flex;
  flex-direction: column;
}

.user-section {
  margin-top: auto;
  padding: 1rem 0;
  border-top: 1px solid #e0e0e0;
}

.user-info {
  display: flex;
  align-items: center;
  padding: 0.5rem 0;
  margin-bottom: 0.5rem;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: #000000; /* Black background */
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.9em;
  margin-left: 14px;
  flex-shrink: 0;
}

.user-details {
  margin-left: 1rem;
  opacity: 0;
  transition: opacity 0.2s ease;
  flex: 1;
  min-width: 0;
}

.sidebar:hover .user-details {
  opacity: 1;
}

.username {
  font-weight: 500;
  color: #000000;
  font-size: 0.9em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-role {
  font-size: 0.75em;
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-block;
  margin-top: 4px;
  text-transform: capitalize;
  font-weight: 500;
}

.logout-btn {
  width: calc(100% - 28px);
  margin: 0 14px;
  padding: 8px 12px;
  background-color: #000000; /* Black background */
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9em;
  font-weight: 600; /* Bolder */
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  text-transform: uppercase; /* Uppercase */
  letter-spacing: 0.5px;
}

.logout-btn:hover {
  background-color: #333333; /* Dark gray hover */
}

.logout-icon {
  opacity: 1;
  font-size: 1em;
}

.logout-text {
  opacity: 0;
  transition: opacity 0.2s ease;
}

.sidebar:hover .logout-text {
  opacity: 1;
}

.auth-section {
  margin-top: auto;
  padding: 1rem 0;
  border-top: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.auth-link {
  padding: 8px 14px;
  color: #000000;
  text-decoration: none;
  font-size: 0.9em;
  font-weight: 600;
  transition: background-color 0.2s;
  border-radius: 4px;
  margin: 0 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  text-transform: uppercase;
}

.auth-link:hover {
  background-color: #f5f5f5;
}

.auth-icon {
  opacity: 1;
  font-size: 1em;
}

.auth-text {
  opacity: 0;
  transition: opacity 0.2s ease;
}

.sidebar:hover .auth-text {
  opacity: 1;
}

.lang-switch-container {
  margin-top: 1rem;
  padding: 0 1rem;
  display: flex;
  justify-content: center;
}
</style>
