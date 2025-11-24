<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div class="app-container">
    <aside class="sidebar">
      <nav>
        <RouterLink to="/">Market</RouterLink>
        <RouterLink to="/macro">Macro</RouterLink>
        <RouterLink to="/micro">Micro</RouterLink>
        <RouterLink to="/bond">Bond</RouterLink>
        <RouterLink to="/productivity">Productivity</RouterLink>
        <RouterLink to="/policy">Policy/Regulation</RouterLink>
        <RouterLink to="/security">Security</RouterLink>
        <RouterLink to="/energy">Energy</RouterLink>
        <RouterLink to="/report">Report</RouterLink>
      </nav>
    </aside>
    
    <div class="content">
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
  position: fixed;
  left: 0;
  top: 0;
  width: 200px;
  height: 100vh;
  background-color: #1a1a1a;
  padding: 2rem 0;
  box-shadow: 2px 0 5px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

nav {
  display: flex;
  flex-direction: column;
  gap: 0;
}

nav a {
  display: block;
  padding: 1rem 1.5rem;
  color: #fff;
  text-decoration: none;
  font-size: 1rem;
  font-weight: 500;
  border-left: 3px solid transparent;
  transition: all 0.3s ease;
}

nav a:hover {
  background-color: rgba(255, 255, 255, 0.05);
  border-left-color: #42b983;
}

nav a.router-link-exact-active {
  color: #42b983;
  background-color: rgba(66, 185, 131, 0.1);
  border-left-color: #42b983;
}

.main-content {
  flex: 1;
  margin-left: 60px;
  width: calc(100% - 200px);
  min-height: 100vh;
}
</style>
