<template>
  <div class="pricing-container">
    <div class="pricing-header">
      <h1>Upgrade to Pro</h1>
      <p class="subtitle">Unlock exclusive market research, advanced analysis, and premium reports.</p>
    </div>

    <div class="pricing-cards">
      <!-- Free Plan -->
      <div class="card basic">
        <h2>Basic</h2>
        <div class="price">Free</div>
        <ul class="features">
          <li><span class="check">✓</span> Market Dashboard</li>
          <li><span class="check">✓</span> Basic News Feed</li>
          <li><span class="check">✓</span> Delayed Data</li>
        </ul>
        <div class="current-plan" v-if="!userStore.user?.has_paid">Current Plan</div>
      </div>

      <!-- Pro Plan -->
      <div class="card pro">
        <div class="popular-tag">MOST POPULAR</div>
        <h2>Professional</h2>
        <div class="price">$19<span>/month</span></div>
        <ul class="features">
          <li><span class="check">✓</span> Unlimited AI Research Reports</li>
          <li><span class="check">✓</span> Real-time AlphaTrade Signals</li>
          <li><span class="check">✓</span> Deep Dive Fundamental Analysis</li>
          <li><span class="check">✓</span> Exclusive "Bear Cave" Research</li>
          <li><span class="check">✓</span> Priority Support</li>
        </ul>
        
        <button 
          v-if="!userStore.user?.has_paid" 
          @click="handleSubscribe" 
          class="subscribe-btn" 
          :disabled="loading"
        >
          {{ loading ? 'Processing...' : 'Subscribe Now' }}
        </button>
        <div v-else class="subscribed-badge">
          <span>✓ Active Subscription</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useUserStore } from '@/stores/userStore';
import API_BASE_URL from '@/config/api';

const userStore = useUserStore();
const loading = ref(false);

const handleSubscribe = async () => {
    if (!userStore.isAuthenticated) {
        alert("Please log in to subscribe.");
        return;
    }

    loading.value = true;
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_BASE_URL}/api/payment/create-checkout-session`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to initiate payment');
        }

        const data = await response.json();
        if (data.url) {
            // Redirect to Stripe Checkout
            window.location.href = data.url;
        } else {
            throw new Error("No checkout URL received");
        }
    } catch (e) {
        console.error("Payment error:", e);
        alert(`Payment initialization failed: ${e.message}`);
    } finally {
        loading.value = false;
    }
};
</script>

<style scoped>
.pricing-container {
    max-width: 1000px;
    margin: 4rem auto;
    padding: 0 2rem;
    font-family: 'Inter', sans-serif;
    color: #e5e7eb;
}

.pricing-header {
    text-align: center;
    margin-bottom: 4rem;
}

.pricing-header h1 {
    font-size: 3rem;
    font-weight: 800;
    background: linear-gradient(to right, #60a5fa, #a855f7);
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 1rem;
}

.subtitle {
    font-size: 1.2rem;
    color: #9ca3af;
}

.pricing-cards {
    display: flex;
    justify-content: center;
    gap: 2rem;
    flex-wrap: wrap;
}

.card {
    background: #1f2937;
    border-radius: 1rem;
    padding: 2.5rem;
    width: 350px;
    position: relative;
    border: 1px solid #374151;
    display: flex;
    flex-direction: column;
}

.card.pro {
    background: #111827;
    border: 2px solid #60a5fa;
    transform: scale(1.05);
    box-shadow: 0 0 30px rgba(96, 165, 250, 0.2);
}

.popular-tag {
    position: absolute;
    top: -12px;
    left: 50%;
    transform: translateX(-50%);
    background: #60a5fa;
    color: #000;
    padding: 0.25rem 1rem;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 700;
}

.card h2 {
    font-size: 1.5rem;
    margin-bottom: 1rem;
    color: #f3f4f6;
}

.price {
    font-size: 3rem;
    font-weight: 700;
    margin-bottom: 2rem;
    color: #f3f4f6;
}

.price span {
    font-size: 1rem;
    color: #9ca3af;
    font-weight: 400;
}

.features {
    list-style: none;
    padding: 0;
    margin: 0 0 2.5rem 0;
    flex-grow: 1;
}

.features li {
    margin-bottom: 1rem;
    color: #d1d5db;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.check {
    color: #10b981;
    font-weight: bold;
}

.subscribe-btn {
    background: linear-gradient(to right, #2563eb, #7c3aed);
    color: white;
    border: none;
    padding: 1rem;
    border-radius: 0.5rem;
    font-weight: 600;
    font-size: 1.1rem;
    cursor: pointer;
    transition: opacity 0.2s;
    width: 100%;
}

.subscribe-btn:hover {
    opacity: 0.9;
}

.subscribe-btn:disabled {
    background: #4b5563;
    cursor: not-allowed;
}

.current-plan, .subscribed-badge {
    text-align: center;
    padding: 1rem;
    background: #374151;
    border-radius: 0.5rem;
    color: #9ca3af;
    font-weight: 600;
}

.subscribed-badge {
    background: #064e3b;
    color: #34d399;
    border: 1px solid #059669;
}
</style>
