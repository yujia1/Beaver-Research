<template>
  <div class="payment-gate">
    <div class="payment-container">
      <div class="payment-header">
        <h1>{{ t('payment_gate.title') }}</h1>
        <p class="subtitle">{{ t('payment_gate.subtitle') }}</p>
      </div>
      
      <div class="payment-content">
        <div class="features-list">
          <h2>{{ t('payment_gate.features_title') }}</h2>
          <ul>
            <li>✓ {{ t('payment_gate.features.analysis') }}</li>
            <li>✓ {{ t('payment_gate.features.market_data') }}</li>
            <li>✓ {{ t('payment_gate.features.research_tools') }}</li>
            <li>✓ {{ t('payment_gate.features.data_vault') }}</li>
          </ul>
        </div>
        
        <!-- Plan Selection -->
        <div class="plan-selection">
          <h3>Choose Your Plan</h3>
          <div class="plan-options">
            <button 
              :class="['plan-option', { selected: selectedPlan === 'monthly' }]"
              @click="selectPlan('monthly')"
            >
              <div class="plan-header">
                <span class="plan-name">Monthly</span>
                <span class="plan-badge" v-if="selectedPlan === 'monthly'">✓</span>
              </div>
              <div class="plan-price">$29<span class="plan-period">/month</span></div>
              <div class="plan-description">Billed monthly</div>
            </button>
            
            <button 
              :class="['plan-option', { selected: selectedPlan === 'annual' }]"
              @click="selectPlan('annual')"
            >
              <div class="plan-header">
                <span class="plan-name">Annual</span>
                <span class="plan-badge popular">SAVE 14%</span>
              </div>
              <div class="plan-price">$300<span class="plan-period">/year</span></div>
              <div class="plan-description">$25/month, billed annually</div>
            </button>
          </div>
        </div>
        
        <!-- Stripe Embedded Checkout -->
        <div class="checkout-section">
          <div v-if="loading" class="loading-state">
            <div class="spinner"></div>
            <p>Loading payment form...</p>
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
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { loadStripe } from '@stripe/stripe-js'
import API_BASE_URL from '@/config/api.js'

const { t } = useI18n()
const router = useRouter()

const loading = ref(true)
const error = ref('')
const selectedPlan = ref('annual') // Default to annual (better value)

// Check if Stripe key is configured
const stripePublishableKey = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY

if (!stripePublishableKey) {
  error.value = 'Stripe is not configured. Please contact support.'
  loading.value = false
}

const stripePromise = stripePublishableKey ? loadStripe(stripePublishableKey) : null
let checkoutInstance = null

const selectPlan = (plan) => {
  selectedPlan.value = plan
  // Reinitialize checkout with new plan
  initializeCheckout()
}

const initializeCheckout = async () => {
  loading.value = true
  error.value = ''
  
  // Unmount previous checkout if exists
  if (checkoutInstance) {
    try {
      checkoutInstance.unmount()
    } catch (e) {
      console.log('Checkout already unmounted')
    }
    checkoutInstance = null
  }
  
  try {
    const token = localStorage.getItem('access_token')
    if (!token) {
      router.push('/login')
      return
    }

    // Create checkout session with selected plan
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
    console.log('Checkout session response:', data)
    
    const { clientSecret } = data
    
    if (!clientSecret) {
      throw new Error('No client secret returned from server')
    }
    
    // Initialize Stripe
    const stripe = await stripePromise
    
    if (!stripe) {
      throw new Error('Stripe failed to load. Please check your publishable key.')
    }
    
    // Stop loading to show the checkout container
    loading.value = false
    
    // Wait for next tick to ensure DOM is updated
    await new Promise(resolve => setTimeout(resolve, 100))
    
    // Verify the checkout element exists
    const checkoutElement = document.getElementById('checkout')
    if (!checkoutElement) {
      throw new Error('Checkout container not found in DOM')
    }
    
    console.log('Mounting Stripe checkout...')
    
    // Mount embedded checkout
    checkoutInstance = await stripe.initEmbeddedCheckout({
      clientSecret
    })
    
    checkoutInstance.mount('#checkout')
    console.log('Stripe checkout mounted successfully')
    
  } catch (err) {
    console.error('Checkout error:', err)
    error.value = err.message || 'Failed to load payment form. Please try again.'
    loading.value = false
  }
}

onMounted(() => {
  initializeCheckout()
})
</script>

<style scoped>
.payment-gate {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffffff;
  padding: 2rem;
}

.payment-container {
  max-width: 800px;
  width: 100%;
  background: #ffffff;
  border-radius: 16px;
  padding: 3rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.payment-header {
  text-align: center;
  margin-bottom: 2rem;
}

.payment-header h1 {
  font-size: 2rem;
  font-weight: 700;
  color: #000000;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #4b5563;
  font-size: 1rem;
}

.payment-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.features-list {
  background: #f9fafb;
  padding: 1.5rem;
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.features-list h2 {
  color: #000000;
  font-size: 1.25rem;
  margin-bottom: 1rem;
}

.features-list ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.features-list li {
  color: #1f2937;
  padding: 0.5rem 0;
  font-size: 1rem;
}

.plan-selection {
  background: #ffffff;
  padding: 1.5rem;
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.plan-selection h3 {
  color: #000000;
  font-size: 1.25rem;
  margin-bottom: 1rem;
  text-align: center;
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
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: left;
}

.plan-option:hover {
  border-color: #000000;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.plan-option.selected {
  border-color: #000000;
  background: #f9fafb;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.plan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.plan-name {
  font-weight: 700;
  font-size: 1.1rem;
  color: #000000;
}

.plan-badge {
  background: #000000;
  color: #ffffff;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.plan-badge.popular {
  background: #10b981;
}

.plan-price {
  font-size: 2rem;
  font-weight: 700;
  color: #000000;
  margin-bottom: 0.5rem;
}

.plan-period {
  font-size: 1rem;
  font-weight: 400;
  color: #6b7280;
}

.plan-description {
  color: #6b7280;
  font-size: 0.9rem;
}

.checkout-section {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-state,
.error-state {
  text-align: center;
  padding: 2rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f0f0f0;
  border-top-color: #000000;
  border-radius: 50%;
  animation: spin 1s linear infinite;
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
  background: #000000;
  color: #ffffff;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.retry-button:hover {
  background: #262626;
  transform: translateY(-2px);
}

#checkout {
  width: 100%;
}

@media (max-width: 640px) {
  .plan-options {
    grid-template-columns: 1fr;
  }
}
</style>

<style scoped>
.payment-gate {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffffff;
  padding: 2rem;
}

.payment-container {
  max-width: 800px;
  width: 100%;
  background: #ffffff;
  border-radius: 16px;
  padding: 3rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.payment-header {
  text-align: center;
  margin-bottom: 2rem;
}

.payment-header h1 {
  font-size: 2rem;
  font-weight: 700;
  color: #000000;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #4b5563;
  font-size: 1rem;
}

.payment-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.features-list {
  background: #f9fafb;
  padding: 1.5rem;
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.features-list h2 {
  color: #000000;
  font-size: 1.25rem;
  margin-bottom: 1rem;
}

.features-list ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.features-list li {
  color: #1f2937;
  padding: 0.5rem 0;
  font-size: 1rem;
}

.checkout-section {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-state,
.error-state {
  text-align: center;
  padding: 2rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f0f0f0;
  border-top-color: #000000;
  border-radius: 50%;
  animation: spin 1s linear infinite;
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
  background: #000000;
  color: #ffffff;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.retry-button:hover {
  background: #262626;
  transform: translateY(-2px);
}

#checkout {
  width: 100%;
}
</style>
