<template>
  <div class="payment-gate">
    <div class="payment-container">
      
      <!-- LEFT COLUMN: Plan Selection & Summary -->
      <div class="left-column">
        
        <!-- Header -->
        <div class="brand-header">
          <div class="logo-circle">B</div>
          <h1>Beaver Research</h1>
        </div>

        <!-- 1. Choose Your Plan -->
        <section class="selection-section">
          <h2 class="section-title">Choose your plan</h2>
          
          <div class="plan-radios">
            <!-- Monthly Plan -->
            <div 
              class="plan-radio" 
              :class="{ selected: selectedPlan === 'monthly' }"
              @click="selectPlan('monthly')"
            >
              <div class="radio-indicator">
                <div class="radio-dot" v-if="selectedPlan === 'monthly'"></div>
              </div>
              <div class="radio-content">
                <span class="radio-label">Monthly subscription</span>
                <span class="radio-price">$29/mo</span>
              </div>
            </div>

            <!-- Annual Plan -->
            <div 
              class="plan-radio" 
              :class="{ selected: selectedPlan === 'annual' }"
              @click="selectPlan('annual')"
            >
              <div class="radio-indicator">
                <div class="radio-dot" v-if="selectedPlan === 'annual'"></div>
              </div>
              <div class="radio-content">
                <span class="radio-label">Annual subscription</span>
                <div class="radio-right">
                  <span class="save-badge">Save 14%</span>
                  <span class="radio-price">$300/yr</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- 2. Plan Details (Summary) -->
        <section class="summary-section">
          <div class="summary-card">
            <h2 class="summary-title">Plan details</h2>
            
            <div class="selected-plan-info">
              <h3 class="plan-name">{{ selectedPlan === 'annual' ? 'Professional Annual' : 'Professional Monthly' }}</h3>
              <p class="plan-desc">Premium market intelligence access</p>
              
              <div class="big-price">
                {{ selectedPlan === 'annual' ? '$300' : '$29' }} 
                <span class="period">/ {{ selectedPlan === 'annual' ? 'year' : 'month' }}</span>
              </div>
            </div>

            <div class="feature-divider"></div>

            <p class="includes-label">This includes:</p>
            <ul class="summary-features">
              <li>
                <span class="check-icon">✓</span>
                <span>Real-time market analysis & insights</span>
              </li>
              <li>
                <span class="check-icon">✓</span>
                <span>Advanced AI Research Reports</span>
              </li>
              <li>
                <span class="check-icon">✓</span>
                <span>Exclusive Data Vault access</span>
              </li>
              <li>
                <span class="check-icon">✓</span>
                <span>Full institutional-grade toolkit</span>
              </li>
            </ul>

            <div class="total-line">
              <span>Total due today</span>
              <span class="total-amount">{{ selectedPlan === 'annual' ? '$300.00' : '$29.00' }}</span>
            </div>
          </div>
        </section>

      </div>

      <!-- RIGHT COLUMN: Payment Form (Embedded Checkout) -->
      <div class="right-column">
        <section class="payment-section">
          <h2 class="section-title">Pay with</h2>
          
          <div class="checkout-wrapper">
             <div v-if="error" class="error-banner">
              <p>{{ error }}</p>
              <button @click="initializeCheckout" class="retry-link">Try again</button>
            </div>
            
            <div id="checkout"></div>
          </div>
        </section>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import API_BASE_URL from '@/config/api.js'
import { StripeCheckoutService } from '@/services/stripeService'

const { t } = useI18n()
const router = useRouter()

const error = ref('')
const selectedPlan = ref('annual') // Default to annual
const isProcessing = ref(false)

// Function to fetch client secret, passed to Stripe
const fetchClientSecret = async () => {
  const token = localStorage.getItem('access_token')
  if (!token) {
    router.push('/login')
    throw new Error('User not authenticated')
  }

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
  return data.clientSecret
}

const selectPlan = async (plan) => {
  if (selectedPlan.value === plan) return 
  selectedPlan.value = plan
  // Trigger re-initialization
  await initializeCheckout()
}

const initializeCheckout = async () => {
  error.value = ''
  try {
    // Delegate to Global Service
    await StripeCheckoutService.mount('#checkout', fetchClientSecret)
  } catch (err) {
    console.error(err)
    error.value = err.message || 'Failed to load payment form.'
  }
}

onMounted(() => {
  initializeCheckout()
})

onUnmounted(async () => {
  await StripeCheckoutService.destroy()
})
</script>

<style scoped>
/* Main Layout */
.payment-gate {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f7f9fc; /* Light blue-grey background */
  padding: 2rem;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

.payment-container {
  display: grid;
  grid-template-columns: 1fr 1fr; /* Equivalent columns */
  gap: 4rem;
  max-width: 1200px;
  width: 100%;
  align-items: start;
}

/* --- Left Column: Selection + Summary --- */
.left-column {
  display: flex;
  flex-direction: column;
  gap: 3rem;
}

.brand-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.logo-circle {
  width: 32px;
  height: 32px;
  background: #635bff; /* Stripe Blurple */
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}

.brand-header h1 {
  font-size: 1.2rem;
  font-weight: 600;
  color: #1a1f36;
  margin: 0;
}

.section-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1a1f36;
  margin-bottom: 1rem;
}

/* Plan Radios */
.plan-radios {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.plan-radio {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: white;
  border: 1px solid #e6e6e6; /* Default border */
  border-radius: 8px;
  padding: 1.25rem;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.plan-radio:hover {
  border-color: #bfaaff;
}

.plan-radio.selected {
  border: 2px solid #635bff; /* Selected Purple */
  background: #fcfbff; /* Very light purple tint */
  padding: 1.18rem; /* Adjust padding to separate border width change */
  box-shadow: 0 0 0 1px #635bff; /* Extra glow */
}

.radio-indicator {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid #d9d9d9;
  display: flex;
  align-items: center;
  justify-content: center;
}

.plan-radio.selected .radio-indicator {
  border-color: #635bff;
  background: #635bff;
}

.radio-dot {
  width: 8px;
  height: 8px;
  background: white;
  border-radius: 50%;
}

.radio-content {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.radio-label {
  font-weight: 500;
  color: #1a1f36;
}

.radio-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.save-badge {
  background: #ece8ff;
  color: #635bff;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 12px;
}

.radio-price {
  color: #4f566b;
  font-weight: 500;
}

/* Summary Card */
.summary-card {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 24px rgba(0,0,0,0.06);
}

.summary-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1a1f36;
  margin-bottom: 2rem;
}

.selected-plan-info {
  margin-bottom: 2rem;
}

.plan-name {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1a1f36;
  margin-bottom: 0.25rem;
}

.plan-desc {
  color: #697386;
  font-size: 0.95rem;
  margin-bottom: 1.5rem;
}

.big-price {
  font-size: 2.5rem;
  font-weight: 700;
  color: #1a1f36;
}

.big-price .period {
  font-size: 1rem;
  color: #697386;
  font-weight: 400;
}

.feature-divider {
  height: 1px;
  background: #e6ebf1;
  margin-bottom: 1.5rem;
}

.includes-label {
  font-weight: 600;
  color: #1a1f36;
  margin-bottom: 1rem;
}

.summary-features {
  list-style: none;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2rem;
}

.summary-features li {
  display: flex;
  gap: 0.75rem;
  color: #4f566b;
  font-size: 0.95rem;
  line-height: 1.4;
}

.check-icon {
  color: #635bff;
  background: #ece8ff;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  flex-shrink: 0;
}

.total-line {
  border-top: 1px solid #e6ebf1;
  padding-top: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: #1a1f36;
}

.total-amount {
  font-size: 1.25rem;
}

/* Payment Section */
.right-column .checkout-wrapper {
  background: white;
  border-radius: 12px;
  padding: 1.5rem; /* Optional wrapper padding */
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.error-banner {
  background: #fef2f2;
  color: #ef4444;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  display: flex;
  gap: 1rem;
  align-items: center;
}

.retry-link {
  background: none;
  border: none;
  text-decoration: underline;
  color: #ef4444;
  cursor: pointer;
  font-weight: 600;
}

/* Responsive */
@media (max-width: 900px) {
  .payment-container {
    grid-template-columns: 1fr;
    gap: 2rem;
    padding: 1rem;
  }
  
  .right-column {
    order: 1; /* Keep payment last on mobile? */
  }
}
</style>
