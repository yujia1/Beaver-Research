<template>
  <div class="quant-container">
    <div class="quant-header">
      <h1>{{ t('quant.title') }}</h1>
      <p class="subtitle">{{ t('quant.subtitle') }}</p>
    </div>

    <!-- Tab Navigation -->
    <div class="tab-navigation">
      <button 
        :class="['tab-btn', { active: activeTab === 'fibonacci' }]"
        @click="activeTab = 'fibonacci'"
      >
        {{ t('quant.fibonacci.title') }}
      </button>
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

    <!-- Fibonacci Tab Content -->
    <div v-if="activeTab === 'fibonacci'" class="tab-content">
      <div class="analysis-controls">
        <div class="input-group">
          <label>{{ t('quant.fibonacci.ticker_label') }}</label>
          <input 
            v-model="ticker"
            type="text"
            :placeholder="t('quant.fibonacci.ticker_placeholder')"
            @keyup.enter="analyzeFibonacci"
            class="ticker-input"
          />
        </div>

        <div class="input-group">
          <label>{{ t('quant.fibonacci.days_label') }}</label>
          <select v-model="days" class="select-input">
            <option :value="90">90 {{ t('quant.fibonacci.days') }}</option>
            <option :value="180">180 {{ t('quant.fibonacci.days') }}</option>
            <option :value="365">1 {{ t('quant.fibonacci.year') }}</option>
            <option :value="730">2 {{ t('quant.fibonacci.years') }}</option>
            <option :value="1825">5 {{ t('quant.fibonacci.years') }}</option>
          </select>
        </div>

        <div class="input-group">
          <label>{{ t('quant.fibonacci.lookback_label') }}</label>
          <select v-model="lookback" class="select-input">
            <option :value="30">30 {{ t('quant.fibonacci.days') }}</option>
            <option :value="60">60 {{ t('quant.fibonacci.days') }}</option>
            <option :value="90">90 {{ t('quant.fibonacci.days') }}</option>
            <option :value="180">180 {{ t('quant.fibonacci.days') }}</option>
          </select>
        </div>

        <button 
          @click="analyzeFibonacci"
          :disabled="loading || !ticker"
          class="analyze-btn"
        >
          {{ loading ? t('quant.fibonacci.analyzing') : t('quant.fibonacci.analyze') }}
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>{{ t('quant.fibonacci.loading') }}</p>
      </div>

      <!-- Error State -->
      <div v-if="error" class="error-state">
        <p>{{ error }}</p>
      </div>

      <!-- Results Display -->
      <div v-if="results && !loading" class="results-container">
        <!-- Current Price & Trend -->
        <div class="results-header">
          <div class="price-card">
            <h3>{{ results.ticker }}</h3>
            <div class="current-price">${{ results.current_price }}</div>
          </div>

          <div class="trend-card" :class="getTrendClass(results.trend_analysis.status)">
            <h4>{{ t('quant.fibonacci.trend') }}</h4>
            <div class="trend-status">{{ results.trend_analysis.status }}</div>
            <div class="sma-values">
              <div v-if="results.trend_analysis.sma_50">
                SMA(50): ${{ results.trend_analysis.sma_50 }}
              </div>
              <div v-if="results.trend_analysis.sma_200">
                SMA(200): ${{ results.trend_analysis.sma_200 }}
              </div>
            </div>
          </div>
        </div>

        <!-- Setup Info -->
        <div class="setup-card">
          <h4>{{ t('quant.fibonacci.setup') }}: {{ results.setup.type }}</h4>
          <div class="swing-points">
            <div class="swing-point">
              <span class="label">{{ t('quant.fibonacci.swing_low') }}:</span>
              <span class="value">${{ results.setup.swing_low }}</span>
            </div>
            <div class="swing-point">
              <span class="label">{{ t('quant.fibonacci.swing_high') }}:</span>
              <span class="value">${{ results.setup.swing_high }}</span>
            </div>
          </div>
        </div>

        <!-- Fibonacci Levels -->
        <div class="levels-section">
          <div class="entry-zones">
            <h4>{{ t('quant.fibonacci.entry_zones') }}</h4>
            <div class="level-item">
              <span class="level-label">0.382:</span>
              <span class="level-value">${{ results.levels['entry_zone_0.382'] }}</span>
            </div>
            <div class="level-item">
              <span class="level-label">0.5:</span>
              <span class="level-value">${{ results.levels['entry_zone_0.5'] }}</span>
            </div>
            <div class="level-item">
              <span class="level-label">0.618:</span>
              <span class="level-value">${{ results.levels['entry_zone_0.618'] }}</span>
            </div>
          </div>

          <div class="price-targets">
            <h4>{{ t('quant.fibonacci.price_targets') }}</h4>
            <div class="level-item target">
              <span class="level-label">1.272:</span>
              <span class="level-value">${{ results.levels['take_profit_1.272'] }}</span>
            </div>
            <div class="level-item target">
              <span class="level-label">1.618:</span>
              <span class="level-value">${{ results.levels['take_profit_1.618'] }}</span>
            </div>
          </div>
        </div>
      </div>
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
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/userStore'
import API_BASE_URL from '@/config/api.js'

// Import views for tabs
import QuantScreenerView from './QuantScreenerView.vue'
import FlaggedCompaniesView from './FlaggedCompaniesView.vue'
import BatchScreeningView from './BatchScreeningView.vue'

const { t } = useI18n()
const router = useRouter()
const userStore = useUserStore()

const isAdmin = computed(() => userStore.user?.role === 'admin')

const activeTab = ref('fibonacci')
const ticker = ref('')
const days = ref(365)
const lookback = ref(90)
const loading = ref(false)
const error = ref(null)
const results = ref(null)

const analyzeFibonacci = async () => {
  if (!ticker.value) return

  loading.value = true
  error.value = null
  results.value = null

  try {
    const token = localStorage.getItem('access_token')
    const response = await fetch(
      `${API_BASE_URL}/api/quant/fibonacci/${ticker.value.toUpperCase()}?days=${days.value}&lookback=${lookback.value}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    )

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Failed to fetch analysis')
    }

    results.value = await response.json()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

const getTrendClass = (status) => {
  if (status === 'Uptrend') return 'trend-bullish'
  if (status === 'Downtrend') return 'trend-bearish'
  return 'trend-neutral'
}
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

.tab-content {
  background: #fff;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.analysis-controls {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  align-items: flex-end;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.input-group label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #333;
}

.ticker-input,
.select-input {
  padding: 0.75rem;
  border: 1px solid #cccccc;
  border-radius: 6px;
  font-size: 1rem;
  min-width: 150px;
  transition: border-color 0.2s;
}

.ticker-input:focus,
.select-input:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}

.analyze-btn {
  padding: 0.75rem 2rem;
  background: #3498db;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.analyze-btn:hover:not(:disabled) {
  background: #2980b9;
}

.analyze-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: #3498db;
}

.loading-state,
.error-state {
  text-align: center;
  padding: 3rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #000;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-state {
  color: #e74c3c;
  font-weight: 500;
}

.results-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.results-header {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.price-card,
.trend-card,
.setup-card {
  background: #ffffff;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid #cccccc;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.price-card h3 {
  font-size: 1.25rem;
  font-weight: 700;
  color: #000;
  margin-bottom: 0.5rem;
}

.current-price {
  font-size: 2rem;
  font-weight: 700;
  color: #42b983;
}

.trend-card h4 {
  font-size: 0.875rem;
  font-weight: 600;
  color: #000;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
}

.trend-status {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.75rem;
}

.trend-bullish .trend-status {
  color: #42b983;
}

.trend-bearish .trend-status {
  color: #e74c3c;
}

.trend-neutral .trend-status {
  color: #f39c12;
}

.sma-values {
  font-size: 0.875rem;
  color: #666;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.setup-card h4 {
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: 1rem;
  color: #000;
}

.swing-points {
  display: flex;
  gap: 2rem;
}

.swing-point {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.swing-point .label {
  font-size: 0.875rem;
  color: #666;
}

.swing-point .value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #000;
}

.levels-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.entry-zones,
.price-targets {
  background: #ffffff;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid #cccccc;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.entry-zones h4,
.price-targets h4 {
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: 1rem;
  text-transform: uppercase;
  color: #000;
}

.level-item {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
  margin-bottom: 0.5rem;
  border: 1px solid #eee;
}

.level-item.target {
  background: #e8f5e9;
  border-color: #c8e6c9;
}

.level-label {
  font-weight: 600;
  color: #666;
}

.level-value {
  font-weight: 700;
  color: #000;
  font-size: 1.125rem;
}

@media (max-width: 768px) {
  .results-header,
  .levels-section {
    grid-template-columns: 1fr;
  }

  .analysis-controls {
    flex-direction: column;
    align-items: stretch;
  }

  .analyze-btn {
    width: 100%;
  }
}

</style>
