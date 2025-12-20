<template>
  <div class="dashboard">
    <div class="page-header">
      <h1>Market Dashboard</h1>
      <button @click="refreshData" :disabled="loading" class="update-btn">
        {{ loading ? 'Refreshing...' : 'Refresh Data' }}
      </button>
    </div>
    
    <div v-if="loading" class="loading">Loading Market Data...</div>
    <div v-else>
       <KeyLogsSection ref="keyLogsRef" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import KeyLogsSection from './dashboard/KeyLogsSection.vue';

const loading = ref(false);
const keyLogsRef = ref(null);

const refreshData = async () => {
    loading.value = true;
    if (keyLogsRef.value) {
        await keyLogsRef.value.refresh();
    }
    loading.value = false;
};
</script>

<style scoped>
.dashboard {
  padding: 20px;
  max-width: 1600px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.page-header h1 {
  margin: 0;
  color: #2c3e50;
  font-size: 2rem;
}

.update-btn {
  padding: 0.5rem 1.5rem;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.2s;
}

.update-btn:disabled {
  background-color: #a8d5c2;
  cursor: not-allowed;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #666;
  font-size: 1.2rem;
}
</style>
