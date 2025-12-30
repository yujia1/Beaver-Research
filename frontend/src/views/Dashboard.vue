<template>
  <div class="dashboard">
    <div class="page-header">
      <h1>{{ t('dashboard.title') }}</h1>
    </div>
    
    <div v-if="loading" class="loading">{{ t('dashboard.loading') }}</div>
    <div v-else>
       <KeyLogsSection ref="keyLogsRef" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import KeyLogsSection from '@/components/dashboard/KeyLogsSection.vue';

const { t } = useI18n();
const loading = ref(false);
const keyLogsRef = ref(null);
</script>

<style scoped>
/* Page Layout - AlphaTrade Style */
.dashboard {
  font-family: 'Inter', sans-serif;
  max-width: 1600px;
  margin: 0 auto;
  padding: 2rem;
  background-color: #ffffff;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 2rem;
  border-bottom: 3px solid #000;
  padding-bottom: 1rem;
}

.page-header h1 {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
  color: #000000;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.loading {
  text-align: center;
  padding: 3rem;
  color: #666666;
  font-style: italic;
  font-size: 1rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}
</style>
