<template>
  <div class="payment-return">
    <div class="return-container">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Verifying your payment...</p>
      </div>
      
      <div v-else-if="status === 'complete'" class="success-state">
        <div class="success-icon">✓</div>
        <h1>Payment Successful!</h1>
        <p>Your subscription has been activated.</p>
        <button @click="goToDashboard" class="action-button">Go to Dashboard</button>
      </div>
      
      <div v-else-if="status === 'open'" class="pending-state">
        <div class="pending-icon">⏳</div>
        <h1>Payment Pending</h1>
        <p>Your payment is being processed. Please check back shortly.</p>
        <button @click="checkStatus" class="action-button">Check Status</button>
      </div>
      
      <div v-else class="error-state">
        <div class="error-icon">✗</div>
        <h1>Payment Failed</h1>
        <p>{{ errorMessage || 'Something went wrong with your payment.' }}</p>
        <button @click="goToPayment" class="action-button">Try Again</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import API_BASE_URL from '@/config/api.js'

const router = useRouter()
const route = useRoute()

const loading = ref(true)
const status = ref('')
const errorMessage = ref('')

const checkStatus = async () => {
  loading.value = true
  
  try {
    const sessionId = route.query.session_id
    if (!sessionId) {
      throw new Error('No session ID found')
    }

    const token = localStorage.getItem('access_token')
    if (!token) {
      router.push('/login')
      return
    }

    const response = await fetch(`${API_BASE_URL}/api/payment/session-status?session_id=${sessionId}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
      throw new Error('Failed to check payment status')
    }

    const data = await response.json()
    status.value = data.status
    
    if (data.status === 'complete') {
      // Emit event to refresh user data
      window.dispatchEvent(new Event('payment-verified'))
      
      // Redirect after a short delay
      setTimeout(() => {
        router.push('/')
      }, 2000)
    }
    
  } catch (err) {
    console.error('Status check error:', err)
    errorMessage.value = err.message
    status.value = 'error'
  } finally {
    loading.value = false
  }
}

const goToDashboard = () => {
  router.push('/')
}

const goToPayment = () => {
  router.push('/pricing')
}

onMounted(() => {
  checkStatus()
})
</script>

<style scoped>
.payment-return {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffffff;
  padding: 2rem;
}

.return-container {
  max-width: 500px;
  width: 100%;
  background: #ffffff;
  border-radius: 16px;
  padding: 3rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(0, 0, 0, 0.1);
  text-align: center;
}

.loading-state,
.success-state,
.pending-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f0f0f0;
  border-top-color: #000000;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.success-icon {
  width: 80px;
  height: 80px;
  background: #10b981;
  color: #ffffff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 3rem;
  font-weight: bold;
}

.pending-icon {
  font-size: 4rem;
}

.error-icon {
  width: 80px;
  height: 80px;
  background: #ef4444;
  color: #ffffff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 3rem;
  font-weight: bold;
}

h1 {
  font-size: 2rem;
  font-weight: 700;
  color: #000000;
  margin: 0;
}

p {
  color: #4b5563;
  font-size: 1rem;
  margin: 0;
}

.action-button {
  background: #000000;
  color: #ffffff;
  padding: 0.75rem 2rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 1rem;
}

.action-button:hover {
  background: #262626;
  transform: translateY(-2px);
}
</style>
