<template>
  <div class="research-view" :class="viewModeClass">
    <PaymentGate v-if="!hasPaid && !loading" />
    <div v-else-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Checking access...</p>
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
import { useRouter } from 'vue-router'
import ResearchEditView from './ResearchEditView.vue'
import PaymentGate from './PaymentGate.vue'

const router = useRouter()

// State Management - Lifted to parent
const viewMode = ref('COMPANY') // 'COMPANY' | 'MARKET'
const activeAgent = ref('FUNDAMENTAL_AGENT')
const ticker = ref('TSLA')

const hasPaid = ref(false)
const loading = ref(true)

const viewModeClass = computed(() => {
  return viewMode.value === 'COMPANY' ? 'company-mode' : 'market-mode'
})

const checkPaymentStatus = async () => {
  const token = localStorage.getItem('access_token')
  if (!token) {
    router.push('/login')
    return
  }
  
  try {
    const response = await fetch('http://localhost:8000/api/auth/payment-status', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (response.ok) {
      const status = await response.json()
      // Grant access if paid OR if user is admin/creator
      if (status.role === 'admin' || status.role === 'creator') {
        hasPaid.value = true
      } else {
        hasPaid.value = status.has_paid || false
      }
    } else if (response.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      router.push('/login')
    }
  } catch (error) {
    console.error('Error checking payment status:', error)
    // On error, allow access (fail open) - you can change this to fail closed
    hasPaid.value = true
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  checkPaymentStatus()
  
  // Listen for payment verification events
  window.addEventListener('payment-verified', () => {
    checkPaymentStatus()
  })
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
.research-view.company-mode {
  --accent-color: #000000;
  --accent-glow: rgba(0, 0, 0, 0.1);
}

.research-view.market-mode {
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
