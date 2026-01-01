<template>
  <div class="payment-gate">
    <div class="payment-container">
      
      <!-- Left Panel: Info & Features -->
      <div class="left-panel">
        <div class="payment-header">
          <h1>{{ t('payment_gate.title') }}</h1>
          <p class="subtitle">{{ t('payment_gate.subtitle') }}</p>
        </div>
        
        <div class="features-list">
          <h2>{{ t('payment_gate.features_title') }}</h2>
          <ul>
            <li>
              <span class="check-icon">✓</span>
              <span>{{ t('payment_gate.features.analysis') }}</span>
            </li>
            <li>
              <span class="check-icon">✓</span>
              <span>{{ t('payment_gate.features.market_data') }}</span>
            </li>
            <li>
              <span class="check-icon">✓</span>
              <span>{{ t('payment_gate.features.research_tools') }}</span>
            </li>
            <li>
              <span class="check-icon">✓</span>
              <span>{{ t('payment_gate.features.data_vault') }}</span>
            </li>
          </ul>
        </div>
        
        <div class="trust-badges">
          <!-- Optional: Add trust badges or secure payment text here if needed -->
          <p class="secure-text">
            <span class="lock-icon">🔒</span> Secure Payment via Stripe
          </p>
        </div>
      </div>
      
      <!-- Right Panel: Action -->
      <div class="right-panel">
        <!-- Plan Selection -->
        <div class="plan-selection">
          <h3>Choose Your Plan</h3>
          <div class="plan-options">
            <button 
              :class="['plan-option', { selected: selectedPlan === 'monthly' }]"
              :disabled="isProcessing"
              @click="selectPlan('monthly')"
            >
              <div class="plan-header-row">
                <span class="plan-name">Monthly</span>
                <span class="plan-badge" v-if="selectedPlan === 'monthly'">✓</span>
              </div>
              <div class="plan-price">$29<span class="plan-period">/mo</span></div>
            </button>
            
            <button 
              :class="['plan-option', { selected: selectedPlan === 'annual' }]"
              :disabled="isProcessing"
              @click="selectPlan('annual')"
            >
              <div class="plan-header-row">
                <span class="plan-name">Annual</span>
                <span class="plan-badge popular">SAVE 14%</span>
              </div>
              <div class="plan-price">$300<span class="plan-period">/yr</span></div>
            </button>
          </div>
        </div>
        
        <!-- Stripe Embedded Checkout -->
        <div class="checkout-wrapper">
          <div class="checkout-section">
            <div v-if="loading" class="loading-state">
              <div class="spinner"></div>
              <p>Loading secure payment...</p>
            </div>
            
            <div v-else-if="error" class="error-state">
              <p class="error-message">{{ error }}</p>
              <button @click="initializeCheckout" class="retry-button">Try Again</button>
            </div>
            
            <div v-else id="checkout"></div>
          </div>
        </div>
      </div>
      
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { loadStripe } from '@stripe/stripe-js'
import API_BASE_URL from '@/config/api.js'

const { t } = useI18n()
const router = useRouter()

const loading = ref(true)
const error = ref('')
const selectedPlan = ref('annual') // Default to annual (better value)
const isProcessing = ref(false) // Prevent double-clicks

// Check if Stripe key is configured
const stripePublishableKey = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY

// Initialize Stripe Promise globally
const stripePromise = stripePublishableKey ? loadStripe(stripePublishableKey) : null
let checkoutInstance = null

const selectPlan = async (plan) => {
  if (selectedPlan.value === plan || isProcessing.value) return // Don't reinitialize if same plan or processing
  
  isProcessing.value = true
  selectedPlan.value = plan
  
  // Cleanup previous instance
  if (checkoutInstance) {
    try {
      await checkoutInstance.destroy()
    } catch (e) {
      // Ignore cleanup errors
    }
    checkoutInstance = null
  }
  
  // Reinitialize
  await initializeCheckout()
  isProcessing.value = false
}

const initializeCheckout = async () => {
  loading.value = true
  error.value = ''
  
  // Cleanup safety check
  if (checkoutInstance) {
    try {
      await checkoutInstance.destroy()
    } catch (e) {
      // Ignore
    }
    checkoutInstance = null
  }
  
  try {
    if (!stripePublishableKey) {
      throw new Error('Stripe is not configured. Please contact support.')
    }

    const token = localStorage.getItem('access_token')
    if (!token) {
      router.push('/login')
      return
    }

    // Create checkout session
    const response = await fetch(`${API_BASE_URL}/api/payment/create-checkout-session`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        plan: selectedPlan.value
      })
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Failed to create checkout session')
    }

    const data = await response.json()
    const { clientSecret } = data
    
    if (!clientSecret) {
      throw new Error('No client secret returned from server')
    }
    
    // Load Stripe
    const stripe = await stripePromise
    if (!stripe) {
      throw new Error('Stripe failed to initialize')
    }
    
    // Reveal container
    loading.value = false
    await nextTick()
    
    // Verify DOM
    const checkoutElement = document.getElementById('checkout')
    if (!checkoutElement) {
      throw new Error('Checkout container not found in DOM')
    }
    
    // Mount
    checkoutInstance = await stripe.initEmbeddedCheckout({
      clientSecret
    })
    
    checkoutInstance.mount('#checkout')
    
  } catch (err) {
    console.error('Payment initialization error:', err)
    error.value = err.message || 'Failed to request payment session.'
    loading.value = false
  }
}

onMounted(() => {
  initializeCheckout()
})

onUnmounted(async () => {
  if (checkoutInstance) {
    try {
      await checkoutInstance.destroy()
    } catch (e) {
      // Ignore
    }
    checkoutInstance = null
  }
})
</script>

<style scoped>
.payment-gate {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8fafc;
  padding: 2rem;
}

.payment-container {
  display: grid;
  grid-template-columns: 1fr 1.2fr; /* Right side slightly wider for checkout */
  gap: 3rem;
  max-width: 1100px;
  width: 100%;
  background: #ffffff;
  border-radius: 20px;
  padding: 3rem;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.08); /* Softer, more modern shadow */
  border: 1px solid rgba(0, 0, 0, 0.03);
  align-items: start;
}

/* --- Left Panel --- */
.left-panel {
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  height: 100%;
  padding-top: 1rem;
}

.payment-header {
  text-align: left;
  margin-bottom: 2.5rem;
}

.payment-header h1 {
  font-size: 2.25rem;
  font-weight: 800;
  color: #111827;
  margin-bottom: 0.75rem;
  line-height: 1.2;
}

.subtitle {
  color: #6b7280;
  font-size: 1.1rem;
  line-height: 1.5;
}

.features-list {
  background: #f9fafb;
  padding: 2rem;
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, 0.04);
}

.features-list h2 {
  color: #111827;
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
}

.features-list ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.features-list li {
  color: #374151;
  font-size: 1.05rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.check-icon {
  color: #10b981;
  font-weight: 800;
  font-size: 1.1rem;
  background: rgba(16, 185, 129, 0.1);
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  flex-shrink: 0;
}

.trust-badges {
  margin-top: auto;
  padding-top: 2rem;
}

.secure-text {
  color: #6b7280;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* --- Right Panel --- */
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding-left: 1rem;
  border-left: 1px solid #f3f4f6;
}

.plan-selection h3 {
  color: #111827;
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 1rem;
  text-align: left;
}

.plan-options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.plan-option {
  background: #ffffff;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 1rem 1.25rem;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.plan-option:not(:disabled):hover {
  border-color: #9ca3af;
  transform: translateY(-2px);
}

.plan-option.selected {
  border-color: #111827;
  background: #f9fafb;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.plan-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.plan-name {
  font-weight: 700;
  font-size: 1rem;
  color: #111827;
}

.plan-badge {
  background: #111827;
  color: #ffffff;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
}

.plan-badge.popular {
  background: #10b981;
}

.plan-price {
  font-size: 1.5rem;
  font-weight: 800;
  color: #111827;
  line-height: 1;
}

.plan-period {
  font-size: 0.9rem;
  font-weight: 500;
  color: #6b7280;
  margin-left: 2px;
}

/* --- Checkout Section --- */
.checkout-wrapper {
  background: #ffffff;
  min-height: 400px; /* Reduced min-height to reduce scrolling */
}

.checkout-section {
  width: 100%;
}

.loading-state,
.error-state {
  text-align: center;
  padding: 4rem 2rem;
  background: #f9fafb;
  border-radius: 12px;
}

.spinner {
  width: 36px;
  height: 36px;
  border: 3px solid #e5e7eb;
  border-top-color: #111827;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-message {
  color: #ef4444;
  margin-bottom: 1rem;
}

.retry-button {
  background: #111827;
  color: #ffffff;
  padding: 0.6rem 1.2rem;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}

#checkout {
  width: 100%;
}

/* --- Responsive --- */
@media (max-width: 900px) {
  .payment-container {
    grid-template-columns: 1fr;
    max-width: 600px;
    padding: 2rem;
    gap: 2rem;
  }
  
  .right-panel {
    border-left: none;
    padding-left: 0;
    border-top: 1px solid #f3f4f6;
    padding-top: 2rem;
  }
  
  .payment-gate {
    padding: 1rem;
    align-items: flex-start; /* Allow scrolling on mobile */
  }
}
</style>
