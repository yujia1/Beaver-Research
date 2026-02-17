<template>
  <div class="quant-container">
    <div class="quant-header">
      <h1>{{ t('quant.title') }}</h1>
      <p class="subtitle">{{ t('quant.subtitle') }}</p>
    </div>

    <!-- Tab Navigation -->
    <div class="tab-navigation">
      <button 
        :class="['tab-btn', { active: activeTab === 'screener' }]"
        @click="activeTab = 'screener'"
      >
        Stock Screener
      </button>
      <button 
        :class="['tab-btn', { active: activeTab === 'flagged' }]"
        @click="activeTab = 'flagged'"
      >
        Flagged Companies
      </button>
      <button 
        v-if="isAdmin"
        :class="['tab-btn', { active: activeTab === 'batch' }]"
        @click="activeTab = 'batch'"
      >
        Batch Screening
      </button>
    </div>

    <!-- Screener Tabs Content -->
    <div v-if="activeTab === 'screener'">
      <QuantScreenerView />
    </div>

    <div v-if="activeTab === 'flagged'">
      <FlaggedCompaniesView />
    </div>

    <div v-if="activeTab === 'batch' && isAdmin">
      <BatchScreeningView />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/stores/userStore'

// Import views for tabs
import QuantScreenerView from './QuantScreenerView.vue'
import FlaggedCompaniesView from './FlaggedCompaniesView.vue'
import BatchScreeningView from './BatchScreeningView.vue'

const { t } = useI18n()
const userStore = useUserStore()

const isAdmin = computed(() => userStore.user?.role === 'admin')

const activeTab = ref('screener')
</script>

<style scoped>
.quant-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.quant-header {
  margin-bottom: 2rem;
}

.quant-header h1 {
  font-size: 2rem;
  font-weight: 700;
  color: #000;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #666;
  font-size: 1rem;
}

.tab-navigation {
  display: flex;
  gap: 1rem;
  border-bottom: 2px solid #e0e0e0;
  margin-bottom: 2rem;
}

.tab-btn {
  padding: 0.75rem 1.5rem;
  background: none;
  border: none;
  border-bottom: 3px solid transparent;
  font-size: 1rem;
  font-weight: 600;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn.active {
  color: #000;
  border-bottom-color: #3498db;
  background: rgba(52, 152, 219, 0.1);
}

.tab-btn:hover:not(.active) {
  background: rgba(0,0,0,0.05);
}


</style>
