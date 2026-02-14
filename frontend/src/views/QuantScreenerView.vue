<template>
  <div class="quant-screener-view">
    <!-- Header -->
    <div class="header">
      <div class="back-link">
        <router-link to="/quant">← Back to Quant Dashboard</router-link>
      </div>
      <h1>Quantitative Stock Screener</h1>
      <p>Screen stocks using 4 fundamental analysis strategies</p>
    </div>
    
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
          {{ loading ? 'Screening...' : 'Screen Stock' }}
        </button>
      </div>
      
      <label class="peer-comparison-toggle">
        <input type="checkbox" v-model="enablePeerComparison" :disabled="loading" />
        <span>Enable Peer Comparison</span>
        <span class="warning-text">(slower, ~30-60s per stock)</span>
      </label>
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
        
        <ScreenerMetricsTable 
          :metrics="getMetricsByStrategy(activeTab)"
          :show-trend="true"
          @metric-click="onMetricClick"
        />
        
        <!-- Trend Charts -->
        <div class="trend-charts">
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
    
    <!-- Empty State -->
    <div v-else-if="!loading" class="empty-state">
      <!-- <div class="empty-icon">🔍</div> -->
      <h3>Ready to Screen</h3>
      <p>Enter a stock ticker above to analyze its fundamental metrics</p>
      <div class="example-tickers">
        <span>Try:</span>
        <button @click="ticker = 'PLTR'; screenStock()" class="example-button">PLTR</button>
        <button @click="ticker = 'AAPL'; screenStock()" class="example-button">AAPL</button>
        <button @click="ticker = 'MSFT'; screenStock()" class="example-button">MSFT</button>
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
import TrendChart from '@/components/quant/TrendChart.vue'
import RedFlagBadge from '@/components/quant/RedFlagBadge.vue'

export default {
  name: 'QuantScreenerView',
  components: {
    ScreenerMetricsTable,
    TrendChart,
    RedFlagBadge
  },
  data() {
    return {
      ticker: '',
      currentTicker: '',
      loading: false,
      enablePeerComparison: false,
      metrics: null,
      redFlags: null,
      activeTab: 'cash-flow',
      error: null,
      
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
          this.metrics = result.metrics
          this.redFlags = result.red_flag_summary
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

/* Header */
.header {
  text-align: center;
  margin-bottom: 2rem;
  position: relative;
}

.back-link {
  position: absolute;
  top: 0;
  left: 0;
}

.back-link a {
  color: #6b7280;
  text-decoration: none;
  font-weight: 500;
  font-size: 0.9rem;
  transition: color 0.2s;
}

.back-link a:hover {
  color: #667eea;
}

.header h1 {
  font-size: 2.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 0.5rem;
}

.header p {
  color: #6b7280;
  font-size: 1.125rem;
}

/* Input Section */
.input-section {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
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
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.2s;
}

.ticker-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.screen-button {
  padding: 0.75rem 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.screen-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.screen-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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
  color: #f59e0b;
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
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

.red-flags-summary.has-flags {
  border-left: 4px solid #ef4444;
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
}

.stat-value {
  font-size: 2.5rem;
  font-weight: 700;
  color: #10b981;
  margin-bottom: 0.5rem;
}

.stat-value.has-flags {
  color: #ef4444;
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
  color: #dc2626;
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
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.tab-button:hover {
  border-color: #667eea;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.tab-button.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
  background: #ef4444;
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
  background: #667eea;
  color: white;
  border-color: #667eea;
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
