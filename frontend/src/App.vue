<script setup>
import { RouterLink, RouterView } from 'vue-router'
import { ref } from 'vue'

const menuItems = [
  { 
    path: '/', 
    name: 'Market', 
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="20" x2="12" y2="10"></line><line x1="18" y1="20" x2="18" y2="4"></line><line x1="6" y1="20" x2="6" y2="16"></line></svg>' 
  },
  { 
    path: '/macro', 
    name: 'Macro', 
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>' 
  },
  { 
    path: '/micro', 
    name: 'Micro', 
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>' 
  },
  { 
    path: '/bond', 
    name: 'Bond', 
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>' 
  },
  { 
    path: '/productivity', 
    name: 'Productivity', 
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>' 
  },
  { 
    path: '/policy', 
    name: 'Policy/Regulation', 
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>' 
  },
  { 
    path: '/security', 
    name: 'Security', 
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>' 
  },
  { 
    path: '/energy', 
    name: 'Energy', 
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>' 
  },
  { 
    path: '/report', 
    name: 'Report', 
    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>' 
  }
]
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
}

.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  width: 60px; /* Minimized width */
  background-color: #1a1a1a;
  padding: 1rem 0;
  box-shadow: 2px 0 5px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  flex-shrink: 0;
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
  color: #fff;
  text-decoration: none;
  font-size: 1rem;
  font-weight: 500;
  border-left: 3px solid transparent;
  transition: all 0.2s ease;
  white-space: nowrap;
  height: 50px; /* Fixed height for consistency */
}

.nav-item:hover {
  background-color: rgba(255, 255, 255, 0.05);
  border-left-color: #42b983;
}

.nav-item.router-link-exact-active {
  color: #42b983;
  background-color: rgba(66, 185, 131, 0.1);
  border-left-color: #42b983;
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
  /* No margin-left needed because of flex layout */
}
</style>
