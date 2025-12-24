<template>
  <div class="research-view" :class="viewModeClass">
    <PaymentGate v-if="!hasPaid && !loading" />
    <div v-else-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>{{ t('research.loading.checking_access') }}</p>
    </div>
    <ResearchEditView
      v-else
      :view-mode="viewMode"
      :active-agent="activeAgent"
      :ticker="ticker"
      @update:view-mode="viewMode = $event"
      @update:active-agent="activeAgent = $event"
      @update:ticker="ticker = $event"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import ResearchEditView from './ResearchEditView.vue'
import PaymentGate from '@/components/PaymentGate.vue'
import { usePayment } from '@/composables/usePayment.js'

const { t } = useI18n()
const { hasPaid, loading, checkPaymentStatus, setupPaymentListeners } = usePayment()

// State Management - Lifted to parent
const viewMode = ref('EDIT') // 'EDIT' | 'PREVIEW'
const activeAgent = ref('MANAGEMENT_AGENT')
const ticker = ref('TSLA')

const viewModeClass = computed(() => {
  return viewMode.value === 'EDIT' ? 'edit-mode' : 'preview-mode'
})

onMounted(() => {
  checkPaymentStatus()
  setupPaymentListeners()
})
</script>

<style scoped>
.research-view {
  min-height: 100vh;
  width: 100%;
  position: relative;
  overflow: hidden;
  background-color: #ffffff;
  font-family: 'Inter', sans-serif;
  color: #000000;
}

/* Theme Colors - Adjusted for light mode financial terminal look */
.research-view.edit-mode {
  --accent-color: #000000;
  --accent-glow: rgba(0, 0, 0, 0.1);
}

.research-view.preview-mode {
  --accent-color: #3498db;
  --accent-glow: rgba(52, 152, 219, 0.1);
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  gap: 1rem;
  background: #ffffff;
}

.loading-container p {
  color: #666666;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f0f0f0;
  border-top-color: #000000;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
