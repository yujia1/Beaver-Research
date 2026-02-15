<template>
  <div class="quant-screener-view">

    
    <!-- Input Section -->
    <div class="input-section">
      <div class="input-group">
        <input 
          v-model="ticker" 
          type="text"
          placeholder="Enter ticker(s), e.g., PLTR, CRWV"
          @keyup.enter="screenStock"
          :disabled="loading"
          class="ticker-input"
        />
        <button 
          @click="screenStock" 
          :disabled="loading || !ticker.trim()"
          class="screen-button"
        >
          <span v-if="loading" class="loading-spinner"></span>
          {{ loading ? 'Screening...' : 'Screen' }}
        </button>
        <button 
          v-if="metrics && screenedTicker"
          @click="saveToFlaggedCompanies" 
          :disabled="saving"
          class="save-button"
        >
          <span v-if="saving" class="loading-spinner"></span>
          {{ saving ? 'Saving...' : 'Save' }}
        </button>
      </div>
      <div v-if="saveMessage" class="save-message" :class="{ success: saveSuccess, error: !saveSuccess }">
        {{ saveMessage }}
      </div>

    </div>
    
    <!-- Error Display -->
    <div v-if="error" class="error-alert">
      <span class="error-icon">Error</span>
      <span>{{ error }}</span>
      <button @click="error = null" class="close-button">×</button>
    </div>
    
    <!-- Results Section -->
    <div v-if="metrics" class="results-section">
      <!-- Red Flags Summary Card -->

      
      <!-- Strategy Tabs -->
      <div class="strategy-tabs">
        <button 
          v-for="tab in tabs" 
          :key="tab.key"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
          class="tab-button"
        >
          <!-- <span class="tab-icon">{{ tab.icon }}</span> -->
          <span class="tab-label">{{ tab.label }}</span>
          <span v-if="getTabRedFlagCount(tab.key) > 0" class="tab-badge">
            {{ getTabRedFlagCount(tab.key) }}
          </span>
        </button>
      </div>
      
      <!-- Metrics Display -->
      <div class="metrics-display">
        <h3 class="section-title">{{ activeTabLabel }} Metrics</h3>
        
        <!-- Cash Flow gets special yearly breakdown table -->
        <CashFlowYearlyTable 
          v-if="activeTab === 'cashflow' && cashFlowYearlyData.length > 0"
          :yearlyData="cashFlowYearlyData"
        />
        
        <!-- Other strategies use regular metrics table -->
        <ScreenerMetricsTable 
          v-else
          :metrics="getMetricsByStrategy(activeTab)"
          :show-trend="true"
          @metric-click="onMetricClick"
        />
        
        <!-- Trend Charts (not for cash flow) -->
        <div v-if="activeTab !== 'cashflow'" class="trend-charts">
          <h3 class="section-title">5-Year Trends</h3>
          <div class="charts-grid">
            <TrendChart 
              v-for="(metric, key) in getMetricsByStrategy(activeTab)"
              :key="key"
              :trend="metric.trend"
              :metric-name="metric.name"
              :is-percentage="isPercentageMetric(key)"
            />
          </div>
        </div>
      </div>
    </div>
    

  </div>
</template>

<script>
import axios from 'axios'
import API_BASE_URL from '@/config/api'

// Create axios instance with base URL
const api = axios.create({
  baseURL: API_BASE_URL
})
import ScreenerMetricsTable from '@/components/quant/ScreenerMetricsTable.vue'
import CashFlowYearlyTable from '@/components/quant/CashFlowYearlyTable.vue'
import TrendChart from '@/components/quant/TrendChart.vue'
import RedFlagBadge from '@/components/quant/RedFlagBadge.vue'

export default {
  name: 'QuantScreenerView',
  components: {
    ScreenerMetricsTable,
    CashFlowYearlyTable,
    TrendChart,
    RedFlagBadge
  },
  data() {
    return {
      ticker: '',
      currentTicker: '',
      screenedTicker: '', // Track the ticker that was screened
      loading: false,
      saving: false,
      enablePeerComparison: true,
      metrics: null,
      cashFlowYearlyData: [], // Yearly breakdown for cash flow table
      redFlags: null,
      activeTab: 'cashflow',
      error: null,
      saveMessage: null,
      saveSuccess: false,
      
      tabs: [
        { key: 'cash-flow', label: 'Cash Flow Sustainability', icon: '' },
        { key: 'balance-sheet', label: 'Balance Sheet Stress', icon: '' },
        { key: 'working-capital', label: 'Working Capital Anomalies', icon: '' },
        { key: 'valuation', label: 'Valuation Dislocation', icon: '' }
      ]
    }
  },
  computed: {
    activeTabLabel() {
      const tab = this.tabs.find(t => t.key === this.activeTab)
      return tab ? tab.label : ''
    }
  },
  methods: {
    async screenStock() {
      if (!this.ticker.trim()) return
      
      this.loading = true
      this.error = null
      
      try {
        const tickers = this.ticker.split(',').map(t => t.trim()).filter(t => t)
        
        const response = await api.post('/api/quant/screener/screen', {
          tickers,
          enable_peer_comparison: this.enablePeerComparison
        })
        
        if (response.data && response.data.length > 0) {
          const result = response.data[0]
          this.currentTicker = result.ticker
          this.screenedTicker = result.ticker // Track screened ticker
          this.metrics = result.metrics
          this.cashFlowYearlyData = result.cash_flow_yearly_breakdown || []
          this.redFlags = result.red_flag_summary
          // Clear any previous save messages
          this.saveMessage = null
        } else {
          this.error = 'No data returned for the specified ticker(s)'
        }
      } catch (err) {
        console.error('Screening error:', err)
        this.error = err.response?.data?.detail || err.message || 'Failed to screen stock'
      } finally {
        this.loading = false
      }
    },
    
    async saveToFlaggedCompanies() {
      if (!this.screenedTicker || !this.metrics) return
      
      this.saving = true
      this.saveMessage = null
      
      try {
        // Calculate total red flags
        const totalRedFlags = Object.values(this.metrics).filter(m => m.is_red_flag).length
        
        // Identify which strategies have red flags
        const redFlagStrategies = []
        const strategyMap = {
          'cash-flow': ['fcf_to_dividends_buybacks', 'fcf_to_revenue'],
          'balance-sheet': ['net_debt_to_ebitda', 'capitalized_costs_to_revenue'],
          'working-capital': ['days_sales_outstanding', 'channel_stuffing_risk'],
          'valuation': ['ev_to_revenue', 'ev_to_ebitda']
        }
        
        for (const [strategy, metricKeys] of Object.entries(strategyMap)) {
          const hasRedFlag = metricKeys.some(key => 
            this.metrics[key] && this.metrics[key].is_red_flag
          )
          if (hasRedFlag) {
            const strategyLabel = this.tabs.find(t => t.key === strategy)?.label || strategy
            redFlagStrategies.push(strategyLabel)
          }
        }
        
        // Prepare the data to save
        const flaggedData = {
          ticker: this.screenedTicker.toUpperCase(),
          red_flag_count: totalRedFlags,
          strategies: redFlagStrategies
        }
        
        // POST to backend to save
        await api.post('/api/quant/screener/flagged', flaggedData)
        
        this.saveMessage = `Successfully saved ${this.screenedTicker.toUpperCase()} to Flagged Companies!`
        this.saveSuccess = true
        
        // Clear message after 5 seconds
        setTimeout(() => {
          this.saveMessage = null
        }, 5000)
      } catch (err) {
        console.error('Save error:', err)
        this.saveMessage = err.response?.data?.detail || 'Failed to save to Flagged Companies'
        this.saveSuccess = false
        
        // Clear error message after 5 seconds
        setTimeout(() => {
          this.saveMessage = null
        }, 5000)
      } finally {
        this.saving = false
      }
    },
    
    getMetricsByStrategy(strategy) {
      if (!this.metrics) return {}
      
      const strategyMap = {
        'cash-flow': ['fcf_to_dividends_buybacks', 'fcf_to_revenue'],
        'balance-sheet': ['net_debt_to_ebitda', 'capitalized_costs_to_revenue'],
        'working-capital': ['days_sales_outstanding', 'channel_stuffing_risk'],
        'valuation': ['ev_to_revenue', 'ev_to_ebitda']
      }
      
      const metricKeys = strategyMap[strategy] || []
      return Object.fromEntries(
        metricKeys.map(key => [key, this.metrics[key]]).filter(([_, v]) => v)
      )
    },
    
    getTabRedFlagCount(tabKey) {
      const metrics = this.getMetricsByStrategy(tabKey)
      return Object.values(metrics).filter(m => m.is_red_flag).length
    },
    
    isPercentageMetric(key) {
      return ['fcf_to_revenue', 'fcf_to_dividends_buybacks'].includes(key)
    },
    
    onMetricClick(metricKey) {
      console.log('Metric clicked:', metricKey)
      // Could open a detailed modal here
    }
  }
}
</script>

<style scoped>
.quant-screener-view {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}



/* Input Section */
.input-section {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05); /* Reduced shadow */
  border: 1px solid #e0e0e0; /* Added border */
  margin-bottom: 2rem;
}

.input-group {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.ticker-input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 1px solid #cccccc; /* Standard border */
  border-radius: 6px; /* Standard radius */
  font-size: 1rem;
  transition: all 0.2s;
}

.ticker-input:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}

.screen-button {
  padding: 8px 24px;
  background: #000; /* Black */
  color: #fff; /* White text */
  border: none;
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: 700; /* Match framework */
  letter-spacing: 0.05em; /* Match framework */
  cursor: pointer;
  transition: background 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.screen-button:hover:not(:disabled) {
  background: #333; /* Dark gray on hover */
  transform: translateY(-1px);
}

.screen-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: #000;
}

.save-button {
  padding: 8px 24px;
  background: #000; /* Black */
  color: #fff; /* White text */
  border: none;
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: 700; /* Match framework */
  letter-spacing: 0.05em; /* Match framework */
  cursor: pointer;
  transition: background 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  white-space: nowrap;
}

.save-button:hover:not(:disabled) {
  background: #333; /* Dark gray on hover */
  transform: translateY(-1px);
}

.save-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.save-message {
  padding: 1rem;
  border-radius: 6px;
  font-size: 0.9375rem;
  font-weight: 500;
  margin-top: 1rem;
}

.save-message.success {
  background: #d1fae5;
  color: #065f46;
  border: 1px solid #a7f3d0;
}

.save-message.error {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.peer-comparison-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #374151;
  cursor: pointer;
}

.peer-comparison-toggle input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.warning-text {
  color: #f39c12; /* Standard warning orange */
  font-style: italic;
}

/* Error Alert */
.error-alert {
  background-color: #fef2f2;
  border-left: 4px solid #ef4444;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 2rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.error-icon {
  font-size: 1.5rem;
}

.close-button {
  margin-left: auto;
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #ef4444;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
}

/* Red Flags Summary */
.red-flags-summary {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
  border: 1px solid #e0e0e0;
}

.red-flags-summary.has-flags {
  border-left: 4px solid #e74c3c;
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.summary-header h3 {
  margin: 0;
  font-size: 1.5rem;
  color: #374151;
}

.ticker-badge {
  padding: 0.5rem 1rem;
  background: #3498db;
  color: white;
  border-radius: 9999px;
  font-weight: 600;
  font-size: 1rem;
}

.summary-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: #f9fafb;
  padding: 1.5rem;
  border-radius: 8px;
  text-align: center;
  border: 1px solid #eee;
}

.stat-value {
  font-size: 2.5rem;
  font-weight: 700;
  color: #42b983; /* Green */
  margin-bottom: 0.5rem;
}

.stat-value.has-flags {
  color: #e74c3c;
}

.stat-label {
  color: #6b7280;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.red-flags-list h4 {
  margin: 0 0 1rem 0;
  color: #374151;
}

.flag-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  background: #fef2f2;
  border-radius: 8px;
  margin-bottom: 0.5rem;
}

.flag-metric {
  font-weight: 500;
  color: #374151;
}

.no-flags {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 1.5rem;
  background: #f0fdf4;
  border-radius: 8px;
  color: #16a34a;
  font-weight: 500;
}

.check-icon {
  font-size: 1.5rem;
}

.strategies-flagged {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e5e7eb;
}

.strategy-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.strategy-chip {
  padding: 0.5rem 1rem;
  background: #fef2f2;
  color: #e74c3c;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
}

/* Strategy Tabs */
.strategy-tabs {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.tab-button {
  position: relative;
  padding: 1.5rem;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.tab-button:hover {
  border-color: #3498db;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.2);
}

.tab-button.active {
  background: #3498db;
  color: white;
  border-color: transparent;
}

.tab-icon {
  font-size: 2rem;
}

.tab-label {
  font-weight: 600;
  text-align: center;
}

.tab-badge {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  background: #e74c3c;
  color: white;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
}

/* Metrics Display */
.metrics-display {
  margin-bottom: 2rem;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 1rem;
}

.trend-charts {
  margin-top: 2rem;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-state h3 {
  font-size: 1.5rem;
  color: #374151;
  margin-bottom: 0.5rem;
}

.empty-state p {
  color: #6b7280;
  margin-bottom: 2rem;
}

.example-tickers {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
}

.example-button {
  padding: 0.5rem 1rem;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.example-button:hover {
  background: #3498db;
  color: white;
  border-color: #3498db;
}

/* Responsive */
@media (max-width: 768px) {
  .quant-screener-view {
    padding: 1rem;
  }
  
  .header h1 {
    font-size: 2rem;
  }
  
  .input-group {
    flex-direction: column;
  }
  
  .strategy-tabs {
    grid-template-columns: 1fr;
  }
  
  .charts-grid {
    grid-template-columns: 1fr;
  }
}
</style>
