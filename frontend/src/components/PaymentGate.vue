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
        
        <div class="payment-section">
          <div class="paypal-button-container">
            <a 
              href="https://www.paypal.com/paypalme/beaverinvest/19.99" 
              target="_blank"
              rel="noopener noreferrer"
              class="paypal-button"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 12c0 1.66-1.34 3-3 3H6c-1.66 0-3-1.34-3-3s1.34-3 3-3h12c1.66 0 3 1.34 3 3z"></path>
                <path d="M6 9h12"></path>
                <path d="M6 15h12"></path>
              </svg>
              {{ t('payment_gate.pay_button') }}
            </a>
          </div>
          
          <div class="verification-section">
            <div class="pending-status">
              <div class="pending-badge">
                <span class="pending-icon">⏳</span>
                <span>{{ t('payment_gate.verification_pending') }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
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
  max-width: 600px;
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

.payment-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.paypal-button-container {
  display: flex;
  justify-content: center;
}

.paypal-button {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  background: linear-gradient(135deg, #0070ba 0%, #003087 100%);
  color: #ffffff;
  padding: 1rem 2rem;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 600;
  font-size: 1rem;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 112, 186, 0.3);
}

.paypal-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 112, 186, 0.4);
}

.paypal-button svg {
  width: 20px;
  height: 20px;
}

.verification-section {
  text-align: center;
}

.pending-status {
  display: flex;
  justify-content: center;
  align-items: center;
}

.pending-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: rgba(245, 158, 11, 0.15);
  border: 1px solid rgba(245, 158, 11, 0.3);
  border-radius: 8px;
  color: #d97706;
  font-weight: 600;
  font-size: 0.9rem;
}

.pending-icon {
  font-size: 1.2rem;
}
</style>

