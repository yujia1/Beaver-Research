<template>
  <div class="timeline-view">
    <div class="page-header">
      <div>
        <h1>{{ t('investment.title') }}</h1>
        <p class="subtitle">{{ t('investment.subtitle') }}</p>
      </div>
      <div class="price-info" v-if="selectedStock">
        <div class="current-price-wrapper">
          <span v-if="todayChangePercent !== 0" class="today-change" :class="todayChangePercent >= 0 ? 'positive' : 'negative'">
            {{ todayChangePercent >= 0 ? '+' : '' }}{{ todayChangePercent.toFixed(2) }}%
          </span>
          <span class="current-price">${{ currentPrice.toFixed(2) }}</span>
        </div>
        <div class="price-change" :class="priceChange >= 0 ? 'positive' : 'negative'">
          {{ priceChange >= 0 ? '+' : '' }}{{ priceChange.toFixed(2) }} ({{ priceChangePercent >= 0 ? '+' : '' }}{{ priceChangePercent.toFixed(2) }}%) since {{ referenceDate }}
        </div>
      </div>
      <div v-else class="price-info">
        <div class="current-price" style="color: #999999;">{{ t('investment.no_stock') }}</div>
      </div>
    </div>

    <!-- Stock Selection -->
    <div class="stock-selector">
      <label for="stock-search">{{ t('investment.search_label') }}</label>
      <input 
        id="stock-search" 
        v-model="stockSearchInput" 
        type="text" 
        :placeholder="t('investment.search_placeholder')"
        @keyup.enter="searchStock"
      />
      <button @click="searchStock" :disabled="loadingStock">{{ t('investment.search_button') }}</button>
      <div v-if="loadingStock" class="loading-indicator">{{ t('investment.loading') }}</div>
      <div v-if="stockError" class="stock-error">{{ stockError }}</div>
    </div>

    <!-- Chart Section -->
    <!-- Chart Section -->
    <PriceTimeline 
      v-if="stockData.length > 0 || selectedStock"
      :stock-data="stockData"
      v-model:selected-time-period="selectedTimePeriod"
      :title="`${selectedStock || t('investment.no_stock')} - ${timelineYear} ${t('investment.price_timeline')}`"
    />
    <div v-else class="chart-card empty-state">
       <div class="chart-container" style="display: flex; justify-content: center; align-items: center; height: 400px; color: #999;">
          {{ t('investment.no_stock_selected') || 'Select a stock to view price timeline' }}
       </div>
    </div>

    <!-- Key Events Section Removed -->
    <div class="events-card">
      <div class="events-header">
        <h2>{{ t('investment.tabs.polymarket') }}</h2>
      </div>

      <!-- Tab Selector -->
      <div class="tab-selector">
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'productivity' }"
          @click="activeTab = 'productivity'"
        >
          {{ t('investment.tabs.polymarket') }}
        </button>
      </div>
      <div v-if="activeTab === 'productivity'" class="tab-content productivity-tab-content">
         <PolyMarketSection 
            v-if="selectedStock"
            :ticker="selectedStock" 
         />
         <div v-else class="empty-deck">
           <p>{{ t('investment.polymarket.placeholder') || 'Select a stock to view PolyMarket data' }}</p>
         </div>
      </div>

    </div>

    <!-- Add Event Modal -->
    <div v-if="showAddEventForm" class="modal-overlay" @click.self="closeAddEventForm">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Add New Event</h3>
          <button class="close-btn" @click="closeAddEventForm">&times;</button>
        </div>
        <form @submit.prevent="addEvent" class="event-form">
          <div class="form-group">
            <label for="event-date">Date *</label>
            <input 
              type="date" 
              id="event-date" 
              v-model="newEvent.date" 
              required
              :max="maxDate"
            />
          </div>
          <div class="form-group">
            <label for="event-title">Title *</label>
            <input 
              type="text" 
              id="event-title" 
              v-model="newEvent.title" 
              required
              placeholder="e.g., Q4 2023 Earnings Miss"
            />
          </div>
          <div class="form-group">
            <label for="event-description">Description *</label>
            <textarea 
              id="event-description" 
              v-model="newEvent.description" 
              required
              rows="3"
              placeholder="e.g., Tesla reported lower-than-expected Q4 earnings, causing stock decline."
            ></textarea>
          </div>
          <div class="form-group">
            <label for="event-type">Event Type *</label>
            <select id="event-type" v-model="newEvent.type" required>
              <option value="positive">Positive Event</option>
              <option value="negative">Negative Event</option>
              <option value="neutral">Neutral Event</option>
            </select>
          </div>
          <div class="form-group">
            <label for="event-category">Category *</label>
            <select id="event-category" v-model="newEvent.category" required>
              <option value="macro">Macro - FED decisions, policy changes, economic indicators</option>
              <option value="micro">Micro - Company-specific internal events</option>
              <option value="market">Market - Trading and financial events</option>
              <option value="industry">Industry - Sector-wide events</option>
              <option value="product">Product - Product-related announcements</option>
            </select>
          </div>
          <div class="form-group">
            <label class="checkbox-label">
              <input 
                type="checkbox" 
                v-model="newEvent.isForecast"
              />
              <span>Mark as Forecast Event (for upcoming expected events)</span>
            </label>
            <p class="form-hint">Forecast events are for scheduled future events like earnings reports, product launches, or regulatory decisions.</p>
          </div>
          <div class="form-actions">
            <button type="button" class="cancel-btn" @click="closeAddEventForm">Cancel</button>
            <button type="submit" class="submit-btn">Add Event</button>
          </div>
        </form>
      </div>
    </div>

  </div>
</template>

<script setup>
import API_BASE_URL from '@/config/api.js'
import PriceTimeline from '@/components/investment/PriceTimeline.vue'

import PolyMarketSection from '@/components/investment/PolyMarketSection.vue'

import { usePayment } from '@/composables/usePayment'
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
// ChartJS imports removed as chart logic is moved to sub-components

const { checkPaymentStatus } = usePayment()


// Stock data
const selectedStock = ref('')
const stockSearchInput = ref('')
const timelineYear = ref('2024')
const referenceDate = ref('')
const currentPrice = ref(0)
const priceChange = ref(0)
const priceChangePercent = ref(0)
const todayChangePercent = ref(0) // Today's percentage change
const loadingStock = ref(false)
const stockError = ref(null)

const { t } = useI18n()

// Time period selector
const selectedTimePeriod = ref('daily')
const timePeriods = computed(() => [
  { label: t('investment.timeframes.daily'), value: 'daily' },
  { label: t('investment.timeframes.weekly'), value: 'weekly' },
  { label: t('investment.timeframes.monthly'), value: 'monthly' },
  { label: t('investment.timeframes.yearly'), value: 'yearly' },
  { label: t('investment.timeframes.max'), value: 'max' }
])

// User info and role check
const user = ref(null)
const isCreator = computed(() => {
  if (!user.value) {
    console.log('isCreator: user.value is null')
    return false
  }
  const role = user.value.role
  const isCreatorRole = role === 'creator' || role === 'admin'
  console.log('isCreator check:', { username: user.value.username, role, isCreatorRole })
  return isCreatorRole
})

// Creator selector
const creators = ref([])
const selectedCreatorId = ref(null)
const loadingCreators = ref(false)

// Events - now loaded from API
const events = ref([])
const loadingEvents = ref(false)

// Filtered events based on selected creator (for chart display)
const filteredEventsForChart = computed(() => {
  // Always filter by selected creator's user_id
  if (selectedCreatorId.value === null) {
    return [] // No creator selected, show no events
  }
  return events.value.filter(event => event.user_id === selectedCreatorId.value)
})

const showAddEventForm = ref(false)
const highlightedEventId = ref(null)

// Active tab state
const activeTab = ref('productivity')

// Company Basic / Micro Economics data
const companyData = ref(null)
const loadingCompany = ref(false)
// Micro Economics tab state managed by CompanyAnalysis.vue


// Computed properties
const currentCard = computed({
  get: () => {
    if (linkedCards.value.length === 0) {
      return { id: null, content: '', sentenceId: null }
    }
    const card = linkedCards.value.find(c => c.id === selectedSentenceId.value)
    return card || { id: null, content: '', sentenceId: null }
  },
  set: (value) => {
    if (selectedSentenceId.value) {
      const card = linkedCards.value.find(c => c.id === selectedSentenceId.value)
      if (card) {
        card.content = value.content
        saveReportData()
      }
    }
  }
})





// Category filters
const categoryFilters = ref({
  macro: true,
  micro: true,
  market: true,
  industry: true,
  product: true
})



// Events state removed

const stockData = ref([]) // Populated with real data from API

// Filter stock data based on selected time period
// Filter logic moved to PriceTimeline.vue

// Chart data
// Chart Data & Options moved to PriceTimeline.vue



const maxDate = computed(() => {
  return new Date().toISOString().split('T')[0]
})

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric', 
    year: 'numeric' 
  })
}

const loadStockData = async () => {
  if (!selectedStock.value) return
  
  loadingStock.value = true
  stockError.value = null
  
  try {
    // Determine period based on selected time period
    const periodMap = {
      'daily': '1mo',
      'weekly': '3mo',
      'monthly': '1y',
      'yearly': '2y',
      'max': 'max'
    }
    const period = periodMap[selectedTimePeriod.value] || '2y'
    
    const response = await fetch(`${API_BASE_URL}/api/internal/stock/${selectedStock.value.toUpperCase()}/history?period=${period}`)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch stock data' }))
      throw new Error(errorData.detail || 'Failed to fetch stock data')
    }
    
    const data = await response.json()
    
    // Convert API response to chart data format
    stockData.value = data.history.map(item => ({
      date: new Date(item.date + 'T00:00:00'),
      price: item.price
    }))
    
    // Update price info
    currentPrice.value = data.current_price
    priceChange.value = data.price_change
    priceChangePercent.value = data.price_change_percent
    referenceDate.value = data.reference_date
    timelineYear.value = new Date().getFullYear().toString()
    
    // Get today's percentage change from API response
    todayChangePercent.value = data.today_change_percent || 0
    
  } catch (err) {
    stockError.value = err.message || 'Error loading stock data'
    console.error('Error loading stock data:', err)
    // Fallback to empty data
    stockData.value = []
  } finally {
    loadingStock.value = false
  }
}

const searchStock = () => {
  const ticker = stockSearchInput.value.trim().toUpperCase()
  if (!ticker) {
    stockError.value = 'Please enter a ticker symbol'
    return
  }
  
  selectedStock.value = ticker
  loadStockData()
  
  // Also fetch PolyMarket data if on PolyMarket tab
  if (selectedStock.value && activeTab.value === 'productivity') {
    fetchPolyMarketData()
  }
}

// Company Data fetching logic moved to CompanyAnalysis.vue


// Watch selectedStock to auto-fetch company data
watch(selectedStock, (newStock, oldStock) => {
  // Clear price info when stock is cleared
  if (!newStock) {
    currentPrice.value = 0
    priceChange.value = 0
    priceChangePercent.value = 0
    todayChangePercent.value = 0
    referenceDate.value = ''
    stockData.value = []
    return
  }
  
  // Fetch events for the new ticker
// Events logic removed
  
  // Always fetch company data if on company tab when stock changes
  // This ensures Key Logs (Company Basic) always uses the same ticker as Stock Price Timeline
  if (activeTab.value === 'company' && selectedStock.value) {
    fetchCompanyData()
  }
  
  
  // Fetch PolyMarket data if on PolyMarket tab
  if (selectedStock.value && activeTab.value === 'productivity') {
    fetchPolyMarketData()
  }
  
  // Reload stock data for the new ticker
  if (selectedStock.value) {
    loadStockData()
  }
})

// Watchers for company data moved to CompanyAnalysis.vue

// Formatting functions for timeline events
const formatNumber = (value) => {
  if (!value && value !== 0) return 'N/A'
  if (value >= 1e12) return (value / 1e12).toFixed(2) + 'T'
  if (value >= 1e9) return (value / 1e9).toFixed(2) + 'B'
  if (value >= 1e6) return (value / 1e6).toFixed(2) + 'M'
  if (value >= 1e3) return (value / 1e3).toFixed(2) + 'K'
  return value.toFixed(2)
}

const formatRatio = (value) => {
  if (!value && value !== 0) return 'N/A'
  return value.toFixed(2)
}

const formatPercent = (value) => {
  if (!value && value !== 0) return 'N/A'
  return (value * 100).toFixed(2) + '%'
}

// Holders / Filings / Options / Financials logic moved to CompanyAnalysis.vue
const getActionClass = (action) => {
  if (!action) return ''
  
  // Handle action strings (BUY, SELL, HOLD, NEW)
  if (typeof action === 'string') {
    const actionUpper = action.toUpperCase()
    if (actionUpper === 'BUY' || actionUpper === 'NEW') return 'action-buy'
    if (actionUpper === 'SELL') return 'action-sell'
    if (actionUpper === 'HOLD') return 'action-hold'
    // Legacy text parsing
    if (actionUpper.includes('SALE') || actionUpper.includes('SELL')) return 'action-sell'
    if (actionUpper.includes('PURCHASE') || actionUpper.includes('BUY')) return 'action-buy'
    if (actionUpper.includes('GIFT')) return 'action-gift'
    if (actionUpper.includes('NO CHANGE')) return 'action-no-change'
    if (actionUpper.includes('OPTION')) return 'action-option'
  }
  
  // Handle numeric pctChange (legacy support)
  if (typeof action === 'number') {
    if (action > 0) return 'action-buy'
    if (action < 0) return 'action-sell'
    return 'action-hold'
  }
  
  return 'action-other'
}

const getChangeClass = (pctChange) => {
  if (!pctChange && pctChange !== 0) return ''
  if (pctChange > 0) return 'action-purchase'
  if (pctChange < 0) return 'action-sell'
  return ''
}

const formatPercentChange = (value) => {
  if (value === null || value === undefined) return '-'
  const sign = value >= 0 ? '+' : ''
  return sign + (value * 100).toFixed(2) + '%'
}

// Report functions removed - reports are now handled in /report route

// Fetch user info from API
const fetchUserInfo = async () => {
  const token = localStorage.getItem('access_token')
  if (!token) {
    user.value = null
    return
  }
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    if (response.ok) {
      user.value = await response.json()
      localStorage.setItem('user', JSON.stringify(user.value))
    } else {
      // Token invalid, clear storage
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      user.value = null
    }
  } catch (err) {
    console.error('Failed to fetch user info:', err)
    // Fallback to localStorage
    const storedUser = localStorage.getItem('user')
    if (storedUser) {
      user.value = JSON.parse(storedUser)
    }
  }
}

onMounted(() => {
  // Load user info from localStorage first (for immediate display)
  const storedUser = localStorage.getItem('user')
  if (storedUser) {
    user.value = JSON.parse(storedUser)
  }
  
  // Fetch fresh user info from API to ensure role is correct
  fetchUserInfo()
  
  // Check payment status
  checkPaymentStatus()
  
  // Listen for login events to update user info
  const handleLoginEvent = () => {
    fetchUserInfo()
    checkPaymentStatus()
  }
  window.addEventListener('user-logged-in', handleLoginEvent)
  
  // Listen for payment verification events
  window.addEventListener('payment-verified', () => {
    checkPaymentStatus()
  })
  

  // Only load data if a stock is selected
  if (selectedStock.value) {
    loadStockData()
    fetchCompanyData()
  }
})

// Watch selectedTimePeriod to reload data when period changes
watch(selectedTimePeriod, () => {
  if (selectedStock.value) {
    loadStockData()
  }
})



</script>

<style scoped>
/* Page Layout - AlphaTrade Style */
.timeline-view {
  font-family: 'Inter', sans-serif;
  max-width: 1600px;
  margin: 0 auto;
  padding: 2rem;
  background-color: #ffffff;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 2rem;
  border-bottom: 3px solid #000;
  padding-bottom: 1rem;
}

.page-header h1 {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
  color: #000000;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.subtitle {
  color: #666666;
  margin: 0;
  font-size: 0.875rem;
  font-style: italic;
}

.price-info {
  text-align: right;
}

.current-price-wrapper {
  display: flex;
  align-items: center;
  gap: 1rem;
  justify-content: flex-end;
}

.current-price {
  font-size: 2.5rem;
  font-weight: 700;
  color: #000000;
  line-height: 1;
}

.today-change {
  font-size: 1.125rem;
  font-weight: 600;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.today-change.positive {
  color: #10b981;
  background: rgba(16, 185, 129, 0.1);
}

.today-change.negative {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.price-change {
  font-size: 0.875rem;
  color: #666666;
  margin-top: 0.5rem;
  font-weight: 500;
}

/* Stock Selector */
.stock-selector {
  display: flex;
  gap: 1rem;
  align-items: center;
  margin-bottom: 2rem;
  background: #fafafa;
  padding: 1.5rem;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
}

.stock-selector label {
  font-weight: 600;
  color: #000000;
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.5px;
}

.stock-selector input {
  padding: 0.75rem;
  border: 1px solid #d0d0d0;
  border-radius: 4px;
  font-size: 1rem;
  width: 300px;
  font-weight: 500;
  color: #000000;
}

.stock-selector input:focus {
  outline: none;
  border-color: #000000;
}

.stock-selector button {
  padding: 0.75rem 1.5rem;
  background-color: #000000;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  transition: background 0.2s;
}

.stock-selector button:hover {
  background-color: #333333;
}

.stock-selector button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

/* Chart Card */
.chart-card {
  background: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e0e0e0;
}

.chart-header h2 {
  font-size: 1.125rem;
  font-weight: 700;
  color: #000000;
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Updated Timeframe Selector */
.timeframe-selector {
  display: flex;
  background: #f5f5f5;
  border-radius: 4px;
  padding: 2px;
}

.timeframe-selector button {
  padding: 0.5rem 1rem;
  border: none;
  background: transparent;
  color: #666666;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 2px;
  transition: all 0.2s;
}

.timeframe-selector button.active {
  background: #ffffff;
  color: #000000;
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

/* Events Card */
.events-card {
  background: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 0; 
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.events-header {
  padding: 1.5rem;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fafafa;
}

.events-header h2 {
  font-size: 1.125rem;
  font-weight: 700;
  color: #000000;
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Tab Selector - AlphaTrade Style */
.tab-selector {
  display: flex;
  background: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
  padding: 0 1.5rem;
}

.tab-btn {
  padding: 1rem 1.5rem;
  background: none;
  border: none;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  cursor: pointer;
  color: #666;
  transition: all 0.2s;
  border-bottom: 3px solid transparent;
}

.tab-btn:hover {
  background: #ebebeb;
  color: #000;
}

.tab-btn.active {
  background: #fff;
  color: #000;
  border-bottom-color: #000;
  margin-bottom: -1px; /* Overlap border */
  border-left: 1px solid #e0e0e0;
  border-right: 1px solid #e0e0e0;
  border-top: 3px solid transparent; 
}

.tab-content {
  padding: 2rem;
}

.chart-container {
  height: 400px;
  position: relative;
}

.events-card {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.events-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

.events-header-controls {
  display: flex;
  align-items: center;
  gap: 15px;
  flex-wrap: wrap;
}

.creator-selector {
  display: flex;
  align-items: center;
  gap: 10px;
}

.creator-selector label {
  font-size: 0.9em;
  color: #666666;
  font-weight: 500;
  white-space: nowrap;
}

.creator-select {
  padding: 8px 12px;
  border: 1px solid #cccccc;
  border-radius: 6px;
  background: #ffffff;
  color: #000000;
  font-size: 0.9em;
  cursor: pointer;
  min-width: 180px;
  transition: all 0.2s;
}

.creator-select:hover {
  border-color: #3498db;
}

.creator-select:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.1);
}

.tab-selector {
  display: flex;
  gap: 0;
  margin-bottom: 20px;
  border-bottom: 2px solid #e0e0e0;
}

.tab-btn {
  padding: 12px 24px;
  border: none;
  background: transparent;
  color: #666666;
  font-size: 1em;
  font-weight: 500;
  cursor: pointer;
  border-bottom: 3px solid transparent;
  transition: all 0.2s;
  position: relative;
  top: 2px;
}

.tab-btn:hover {
  color: #000000;
  background: #f8f9fa;
}

.tab-btn.active {
  color: #000000;
  border-bottom-color: #3498db;
  font-weight: 600;
}

.tab-content {
  min-height: 200px;
}

.company-basic-content,
.report-content {
  padding: 20px 0;
}

.company-basic-content h3,
.report-content h3 {
  margin: 0 0 15px 0;
  color: #000000;
  font-size: 1.3em;
  font-weight: 600;
}

.company-basic-content p {
  color: #666666;
  margin: 0;
}

.analysis-section .report-content,
.analysis-section .report-content p,
.analysis-section .report-content li,
.analysis-section .report-content span,
.analysis-section .report-content div,
.analysis-section .report-content strong,
.analysis-section .report-content em,
.analysis-section .report-content a,
.analysis-section .report-content h1,
.analysis-section .report-content h2,
.analysis-section .report-content h3,
.analysis-section .report-content h4,
.analysis-section .report-content h5,
.analysis-section .report-content h6 {
  color: #000000;
}

/* Black text for report content in Notes, Operating Drivers, and Capital Structure tabs */
.micro-tab-pane .report-content,
.micro-tab-pane .report-content p,
.micro-tab-pane .report-content li,
.micro-tab-pane .report-content span,
.micro-tab-pane .report-content div,
.micro-tab-pane .report-content strong,
.micro-tab-pane .report-content em,
.micro-tab-pane .report-content a,
.micro-tab-pane .report-content h1,
.micro-tab-pane .report-content h2,
.micro-tab-pane .report-content h3,
.micro-tab-pane .report-content h4,
.micro-tab-pane .report-content h5,
.micro-tab-pane .report-content h6 {
  color: #000000;
}

/* Report with Linked Cards Styles */
.report-tab-content {
  padding: 20px;
  min-height: 500px;
}

.report-container {
  width: 100%;
  margin: 0 auto;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e0e0e0;
}

.report-header h2 {
  margin: 0;
  color: #000000;
  font-size: 1.8em;
  font-weight: 600;
}

.report-section-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 20px;
  border-bottom: 2px solid #e0e0e0;
}

.section-tab-btn {
  padding: 12px 24px;
  border: none;
  background: transparent;
  color: #666666;
  font-size: 1em;
  font-weight: 500;
  cursor: pointer;
  border-bottom: 3px solid transparent;
  transition: all 0.2s;
  position: relative;
  top: 2px;
}

.section-tab-btn:hover {
  color: #000000;
  background: #f8f9fa;
}

.section-tab-btn.active {
  color: #000000;
  border-bottom-color: #3498db;
  font-weight: 600;
}

.report-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.position-selector {
  display: flex;
  gap: 10px;
  align-items: center;
}

.position-selector label {
  font-weight: 500;
  color: #000000;
}

.position-select {
  padding: 6px 12px;
  border: 1px solid #cccccc;
  border-radius: 4px;
  background: white;
  color: #000000;
  font-size: 0.9em;
  cursor: pointer;
}

.position-select:focus {
  outline: none;
  border-color: #3498db;
}

.btn-save-report {
  padding: 8px 16px;
  background: #42b983;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9em;
  font-weight: 500;
  transition: background 0.2s;
}

.btn-save-report:hover:not(:disabled) {
  background: #35a372;
}

.btn-save-report:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.selection-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 8px 16px;
  background: #e3f2fd;
  border-radius: 6px;
  border: 2px solid #3498db;
}

.btn-link-card {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  background: #3498db;
  color: white;
  font-size: 0.9em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-link-card:hover {
  background: #2980b9;
  transform: translateY(-1px);
}

.btn-cancel {
  padding: 8px 16px;
  border: 2px solid #cccccc;
  border-radius: 6px;
  background: transparent;
  color: #666666;
  font-size: 0.9em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel:hover {
  background: #f0f0f0;
}

.report-main-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
  position: relative;
}

.report-editor-area {
  flex: 1;
  min-width: 0;
  position: relative;
}

.report-editor-wrapper {
  position: relative;
}

.connector-lines {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
  overflow: visible;
}

.connector-line {
  stroke: #3498db;
  stroke-width: 2;
  stroke-dasharray: 5, 5;
  opacity: 0.4;
  transition: opacity 0.3s;
}

.connector-line.active {
  stroke: #2980b9;
  stroke-width: 3;
  opacity: 0.8;
  stroke-dasharray: none;
}

.report-editor-header {
  margin-bottom: 15px;
}

.report-editor-header h3 {
  margin: 0 0 5px 0;
  color: #000000;
  font-size: 1.2em;
  font-weight: 600;
}

.editor-hint {
  margin: 0;
  color: #666666;
  font-size: 0.85em;
  font-style: italic;
}

.report-editor {
  min-height: 500px;
  padding: 20px;
  border: 2px solid #cccccc;
  border-radius: 8px;
  background: #ffffff;
  color: #000000;
  font-size: 1em;
  line-height: 1.8;
  outline: none;
  white-space: pre-wrap;
  word-wrap: break-word;
  position: relative;
  z-index: 2;
  direction: ltr;
  text-align: left;
}

.report-editor:focus {
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}

.report-editor :deep(.linked-sentence) {
  background-color: #e3f2fd;
  padding: 2px 4px;
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  display: inline;
}

.report-editor :deep(.linked-sentence:hover) {
  background-color: #bbdefb;
  box-shadow: 0 0 0 1px #3498db;
}

.report-editor :deep(.linked-sentence.active) {
  background-color: #90caf9;
  box-shadow: 0 0 0 2px #3498db;
  animation: pulse-highlight 1s ease-in-out;
}

@keyframes pulse-highlight {
  0%, 100% {
    box-shadow: 0 0 0 2px #3498db;
  }
  50% {
    box-shadow: 0 0 0 4px rgba(52, 152, 219, 0.5);
  }
}

.flashcard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e0e0e0;
}

.flashcard-header h2 {
  margin: 0;
  color: #000000;
  font-size: 1.8em;
  font-weight: 600;
}

.flashcard-actions {
  display: flex;
  gap: 10px;
}

.btn-add-card,
.btn-complete {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 0.95em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-add-card {
  background: #3498db;
  color: white;
}

.btn-add-card:hover {
  background: #2980b9;
  transform: translateY(-1px);
}

.btn-complete {
  background: #42b983;
  color: white;
}

.btn-complete:hover {
  background: #35a372;
  transform: translateY(-1px);
}

.empty-deck {
  text-align: center;
  padding: 60px 20px;
  color: #666666;
  font-size: 1.1em;
}

.flashcard-viewer {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.card-counter {
  font-size: 0.9em;
  color: #666666;
  font-weight: 500;
}

.flashcard-wrapper {
  width: 100%;
  max-width: 600px;
  height: 400px;
  perspective: 1000px;
}

.flashcard {
  position: relative;
  width: 100%;
  height: 100%;
  transform-style: preserve-3d;
}

.flashcard-side {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 2px solid #cccccc;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  backface-visibility: hidden;
  transform: rotateY(0deg);
}


.card-label {
  padding: 12px 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
  font-weight: 600;
  color: #666666;
  font-size: 0.85em;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.card-textarea {
  flex: 1;
  padding: 20px;
  border: none;
  outline: none;
  resize: none;
  font-size: 1.1em;
  line-height: 1.6;
  color: #000000;
  font-family: inherit;
  background: transparent;
}

.card-textarea::placeholder {
  color: #999999;
}

.flashcard-controls {
  display: flex;
  gap: 15px;
  align-items: center;
  margin-top: 20px;
}

.nav-btn {
  padding: 12px 24px;
  border: 2px solid #cccccc;
  border-radius: 6px;
  background: #ffffff;
  color: #000000;
  font-size: 0.95em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-btn:hover:not(:disabled) {
  border-color: #3498db;
  background: #e3f2fd;
  color: #1976d2;
}

.nav-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.card-actions {
  margin-top: 20px;
  display: flex;
  gap: 10px;
  justify-content: center;
}

.btn-add-card {
  padding: 10px 20px;
  border: 2px solid #3498db;
  border-radius: 6px;
  background: #3498db;
  color: white;
  font-size: 0.95em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-add-card:hover {
  background: #2980b9;
  border-color: #2980b9;
  transform: translateY(-1px);
}

.btn-delete-card {
  padding: 10px 20px;
  border: 2px solid #e74c3c;
  border-radius: 6px;
  background: transparent;
  color: #e74c3c;
  font-size: 0.95em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-delete-card:hover {
  background: #e74c3c;
  color: white;
}

/* Linked Cards Sidebar Styles */
.linked-cards-sidebar {
  width: 350px;
  background: #f8f9fa;
  border-left: 1px solid #cccccc;
  padding: 20px;
  border-radius: 8px;
  max-height: calc(100vh - 200px);
  overflow-y: auto;
  flex-shrink: 0;
  position: relative;
}

.linked-cards-sidebar h3 {
  margin: 0 0 15px 0;
  color: #000000;
  font-size: 1.1em;
  font-weight: 600;
  padding-bottom: 10px;
  border-bottom: 2px solid #e0e0e0;
}

.no-cards {
  text-align: center;
  padding: 40px 20px;
  color: #666666;
  font-size: 0.9em;
}

.cards-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.linked-card-item {
  padding: 12px;
  background: #ffffff;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.linked-card-item:hover {
  border-color: #3498db;
  box-shadow: 0 2px 8px rgba(52, 152, 219, 0.2);
}

.linked-card-item.active {
  background: #e3f2fd;
  border-color: #3498db;
  border-width: 2px;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 10px;
}

.card-sentence-preview {
  font-size: 0.85em;
  color: #666666;
  font-style: italic;
  line-height: 1.4;
  flex: 1;
}

.btn-delete-small {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: #e74c3c;
  font-size: 1.2em;
  font-weight: bold;
  cursor: pointer;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.btn-delete-small:hover {
  background: #fee;
  color: #c0392b;
}

.card-content-editor {
  margin-top: 8px;
}

.card-textarea-small {
  width: 100%;
  min-height: 80px;
  padding: 10px;
  border: 1px solid #cccccc;
  border-radius: 4px;
  font-size: 0.9em;
  line-height: 1.5;
  color: #000000;
  font-family: inherit;
  resize: vertical;
  outline: none;
}

.card-textarea-small:focus {
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.1);
}

.card-textarea-small::placeholder {
  color: #999999;
}

/* Report History Styles */
.report-upload-section {
  padding: 20px 0;
}

.upload-header {
  margin-bottom: 30px;
}

.upload-header h3 {
  margin: 0 0 10px 0;
  color: #000000;
  font-size: 1.3em;
  font-weight: 600;
}

.upload-hint {
  color: #666666;
  font-size: 0.9em;
  margin: 0;
}

.upload-area {
  border: 2px dashed #cccccc;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  background: #fafafa;
  transition: all 0.3s;
  position: relative;
}

.upload-area:hover {
  border-color: #3498db;
  background: #f0f7ff;
}

.file-input {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
  overflow: hidden;
}

.file-upload-label {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 20px;
}

.upload-icon {
  font-size: 3em;
  margin-bottom: 15px;
}

.upload-text {
  color: #000000;
  font-size: 1em;
}

.upload-text strong {
  color: #3498db;
  font-weight: 600;
}

.upload-formats {
  color: #666666;
  font-size: 0.85em;
  margin-top: 5px;
  display: block;
}

.upload-progress {
  margin-top: 20px;
  padding: 15px;
  background: #e3f2fd;
  border-radius: 6px;
}

.upload-progress p {
  margin: 0 0 10px 0;
  color: #1976d2;
  font-weight: 500;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #3498db;
  transition: width 0.3s;
  border-radius: 4px;
}

.upload-error {
  margin-top: 20px;
  padding: 15px;
  background: #ffebee;
  border: 1px solid #e74c3c;
  border-radius: 6px;
  color: #c62828;
}

.upload-success {
  margin-top: 20px;
  padding: 15px;
  background: #e8f5e9;
  border: 1px solid #42b983;
  border-radius: 6px;
  color: #2e7d32;
}

.upload-success p {
  margin: 5px 0;
}

.upload-filename {
  font-weight: 600;
  color: #1b5e20;
}

.report-history-section {
  padding: 20px 0;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e0e0e0;
}

.history-header h3 {
  margin: 0;
  color: #000000;
  font-size: 1.3em;
  font-weight: 600;
}

.btn-refresh {
  padding: 8px 16px;
  border: 2px solid #3498db;
  border-radius: 6px;
  background: transparent;
  color: #3498db;
  font-size: 0.9em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-refresh:hover {
  background: #3498db;
  color: white;
}

.loading-state {
  text-align: center;
  padding: 40px 20px;
  color: #666666;
}

.empty-history {
  text-align: center;
  padding: 60px 20px;
  color: #666666;
}

.hint-text {
  font-size: 0.9em;
  color: #999999;
  margin-top: 10px;
}

/* Upload Section Styles */
.report-upload-section {
  padding: 20px 0;
}

.upload-header {
  margin-bottom: 30px;
}

.upload-header h3 {
  margin: 0 0 10px 0;
  color: #000000;
  font-size: 1.3em;
  font-weight: 600;
}

.upload-hint {
  color: #666666;
  font-size: 0.9em;
  margin: 0;
}

.upload-area {
  border: 2px dashed #cccccc;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  background: #fafafa;
  transition: all 0.3s;
  position: relative;
}

.upload-area:hover {
  border-color: #3498db;
  background: #f0f7ff;
}

.file-input {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
  overflow: hidden;
}

.file-upload-label {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 20px;
}

.upload-icon {
  font-size: 3em;
  margin-bottom: 15px;
}

.upload-text {
  color: #000000;
  font-size: 1em;
}

.upload-text strong {
  color: #3498db;
  font-weight: 600;
}

.upload-formats {
  color: #666666;
  font-size: 0.85em;
  margin-top: 5px;
  display: block;
}

.upload-progress {
  margin-top: 20px;
  padding: 15px;
  background: #e3f2fd;
  border-radius: 6px;
}

.upload-progress p {
  margin: 0 0 10px 0;
  color: #1976d2;
  font-weight: 500;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #3498db;
  transition: width 0.3s;
  border-radius: 4px;
}

.upload-error {
  margin-top: 20px;
  padding: 15px;
  background: #ffebee;
  border: 1px solid #e74c3c;
  border-radius: 6px;
  color: #c62828;
}

.upload-success {
  margin-top: 20px;
  padding: 15px;
  background: #e8f5e9;
  border: 1px solid #42b983;
  border-radius: 6px;
  color: #2e7d32;
}

.upload-success p {
  margin: 5px 0;
}

.upload-filename {
  font-weight: 600;
  color: #1b5e20;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.history-item {
  padding: 20px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  background: #ffffff;
  transition: all 0.2s;
  cursor: pointer;
}

.history-item:hover {
  border-color: #3498db;
  box-shadow: 0 2px 8px rgba(52, 152, 219, 0.1);
  transform: translateY(-2px);
}

.history-item-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.history-item-info h4 {
  margin: 0 0 5px 0;
  color: #000000;
  font-size: 1.1em;
  font-weight: 600;
}

.history-date {
  margin: 0;
  color: #666666;
  font-size: 0.85em;
}

.history-item-actions {
  display: flex;
  gap: 10px;
}

.btn-load-report {
  padding: 8px 16px;
  border: 2px solid #3498db;
  border-radius: 6px;
  background: #3498db;
  color: white;
  font-size: 0.9em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-load-report:hover {
  background: #2980b9;
  border-color: #2980b9;
}

.btn-delete-history {
  padding: 8px 16px;
  border: 2px solid #e74c3c;
  border-radius: 6px;
  background: transparent;
  color: #e74c3c;
  font-size: 0.9em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-delete-history:hover {
  background: #e74c3c;
  color: white;
}

.history-item-preview {
  padding-top: 15px;
  border-top: 1px solid #e0e0e0;
}

.history-item-preview p {
  margin: 0;
  color: #666666;
  font-size: 0.9em;
  line-height: 1.6;
}

.upload-section {
  margin-bottom: 20px;
  padding: 40px;
  border: 2px dashed #cccccc;
  border-radius: 8px;
  text-align: center;
  background: #fafafa;
}

.upload-section h3 {
  color: #000000;
  font-weight: 600;
  margin: 0 0 15px 0;
}

.upload-section input[type="file"] {
  padding: 10px;
  border: 1px solid #cccccc;
  border-radius: 6px;
  background: #ffffff;
  color: #000000;
  cursor: pointer;
}

.loading-small {
  text-align: center;
  margin: 20px 0;
  color: #666666;
  font-size: 0.9em;
}

.report-body {
  line-height: 1.6;
  color: #000000;
}

.report-body :deep(h1), .report-body :deep(h2), .report-body :deep(h3) {
  color: #000000;
  margin-top: 1.5em;
  font-weight: 600;
}

.report-body :deep(ul), .report-body :deep(ol) {
  padding-left: 20px;
}

.report-body :deep(p) {
  margin-bottom: 1em;
  color: #000000;
}

.no-reports {
  color: #666666;
  font-style: italic;
  text-align: center;
  margin-top: 20px;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 20px;
  border-radius: 8px;
  width: 80%;
  max-width: 900px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 10px;
}

.modal-header h3 {
  margin: 0;
  color: #000000;
  font-weight: 600;
}

.modal-body {
  overflow-y: auto;
  flex: 1;
}

.close-btn {
  padding: 6px 12px;
  background: #95a5a6;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.close-btn:hover {
  background: #7f8c8d;
}

.search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.search-bar input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1em;
}

.search-bar input:focus {
  outline: none;
  border-color: #3498db;
}

.search-bar button {
  padding: 10px 20px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1em;
  font-weight: 500;
  transition: all 0.2s;
}

.search-bar button:hover:not(:disabled) {
  background: #2980b9;
}

.search-bar button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666666;
}

.error {
  padding: 15px;
  background: #fee;
  color: #c33;
  border-radius: 6px;
  margin-bottom: 20px;
}

.company-info {
  margin-top: 20px;
}

.company-header {
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e0e0e0;
}

.company-header h3 {
  margin: 0 0 10px 0;
  color: #000000;
  font-size: 1.5em;
  font-weight: 600;
}

.company-price-info {
  display: flex;
  align-items: center;
  gap: 15px;
  flex-wrap: wrap;
}

.company-price {
  font-size: 1.8em;
  font-weight: bold;
  color: #000000;
}

.company-sector {
  color: #666666;
  font-size: 1em;
}

.company-section {
  margin-bottom: 30px;
}

.company-section h4 {
  margin: 0 0 15px 0;
  color: #000000;
  font-size: 1.2em;
  font-weight: 600;
}

.company-details {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.detail-label {
  color: #666666;
  font-weight: 500;
}

.detail-value {
  color: #000000;
  font-weight: 600;
}

.ratios-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 15px;
}

.ratio-card {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  text-align: center;
}

.ratio-label {
  color: #666666;
  font-size: 0.9em;
  margin-bottom: 8px;
}

.ratio-value {
  color: #000000;
  font-size: 1.3em;
  font-weight: 600;
}

.financial-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.financial-metric {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
}

.metric-label {
  color: #666666;
  font-size: 0.9em;
  margin-bottom: 8px;
}

.metric-value {
  color: #000000;
  font-size: 1.2em;
  font-weight: 600;
}

.no-company-data {
  text-align: center;
  padding: 40px;
  color: #666666;
}

.event-filters {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.filter-section {
  display: flex;
  align-items: center;
  gap: 15px;
  flex-wrap: wrap;
}

.filter-label {
  color: #000000;
  font-weight: 500;
  font-size: 0.95em;
}

.filter-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.filter-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 2px solid #cccccc;
  background: #ffffff;
  color: #000000;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9em;
  font-weight: 500;
  transition: all 0.2s;
}

.filter-btn:hover {
  border-color: #3498db;
  background: #f0f8ff;
}

.filter-btn.active {
  border-color: #3498db;
  background: #e3f2fd;
  color: #1976d2;
}

.filter-btn.clear-all {
  border-color: #cccccc;
  color: #666666;
}

.filter-btn.clear-all:hover {
  border-color: #999999;
  background: #f8f9fa;
}

.filter-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.filter-dot.positive {
  background-color: #42b983;
}

.filter-dot.negative {
  background-color: #e74c3c;
}

.filter-dot.neutral {
  background-color: #95a5a6;
}

.category-btn {
  border-color: #7f8c8d;
}

.category-btn.active {
  border-color: #3498db;
  background: #e3f2fd;
  color: #1976d2;
}

.event-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 5px;
  flex-wrap: wrap;
}

.event-header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.event-category-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.75em;
  font-weight: 600;
  text-transform: uppercase;
  white-space: nowrap;
}

.event-category-badge.macro {
  background-color: #e8f5e9;
  color: #2e7d32;
}

.event-category-badge.micro {
  background-color: #fff3e0;
  color: #e65100;
}

.event-category-badge.market {
  background-color: #e3f2fd;
  color: #1565c0;
}

.event-category-badge.industry {
  background-color: #f3e5f5;
  color: #6a1b9a;
}

.event-category-badge.product {
  background-color: #fce4ec;
  color: #c2185b;
}

.delete-event-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 1.2em;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s ease;
  opacity: 0.6;
}

.delete-event-btn:hover {
  opacity: 1;
  background: #fee;
  transform: scale(1.1);
}

.event-item.forecast {
  border-left: 3px dashed #7f8c8d;
}

.event-content.forecast {
  opacity: 0.9;
}

.event-dot.forecast {
  border: 2px dashed #fff;
  box-sizing: border-box;
}

.forecast-badge {
  display: inline-block;
  margin-left: 8px;
  padding: 2px 8px;
  background-color: #fff3cd;
  color: #856404;
  border-radius: 10px;
  font-size: 0.7em;
  font-weight: 600;
  text-transform: uppercase;
}

.status-btn {
  border-color: #7f8c8d;
}

.status-btn.active {
  border-color: #3498db;
  background: #e3f2fd;
  color: #1976d2;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #000000;
  font-weight: 500;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.form-hint {
  margin: 5px 0 0 0;
  font-size: 0.85em;
  color: #666666;
  font-style: italic;
}

.legend {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #000000;
  font-size: 0.9em;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  display: inline-block;
}

.legend-dot.positive {
  background-color: #42b983;
}

.legend-dot.negative {
  background-color: #e74c3c;
}

.legend-dot.neutral {
  background-color: #95a5a6;
}

.events-header h2 {
  margin: 0;
  color: #000000;
  font-size: 1.5em;
  font-weight: 600;
  flex: 1;
}

.add-event-btn {
  background: #3498db;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.95em;
  font-weight: 500;
  transition: all 0.2s;
}

.add-event-btn:hover {
  background: #2980b9;
  transform: translateY(-1px);
}

.events-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.event-item {
  display: flex;
  align-items: flex-start;
  gap: 15px;
  padding: 15px;
  border-radius: 6px;
  background: #f8f9fa;
  transition: all 0.2s;
  cursor: pointer;
}

.event-item:hover {
  background: #e9ecef;
  transform: translateX(5px);
}

.event-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-top: 6px;
  flex-shrink: 0;
}

.event-dot.positive {
  background-color: #42b983;
}

.event-dot.negative {
  background-color: #e74c3c;
}

.event-dot.neutral {
  background-color: #95a5a6;
}

.event-content {
  flex: 1;
}

.event-title {
  margin: 0 0 5px 0;
  color: #000000;
  font-size: 1.1em;
  font-weight: 600;
}

.event-date {
  margin: 0 0 8px 0;
  color: #666666;
  font-size: 0.9em;
}

.event-description {
  margin: 0;
  color: #333333;
  font-size: 0.95em;
  line-height: 1.5;
}

.no-events {
  text-align: center;
  padding: 40px;
  color: #666666;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #fff;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h3 {
  margin: 0;
  color: #000000;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 2em;
  color: #666666;
  cursor: pointer;
  line-height: 1;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #000000;
}

.event-form {
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #000000;
  font-weight: 500;
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1em;
  font-family: inherit;
  box-sizing: border-box;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: #3498db;
}

.form-group textarea {
  resize: vertical;
  min-height: 80px;
}

.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 30px;
}

.cancel-btn,
.submit-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1em;
  font-weight: 500;
  transition: all 0.2s;
}

.cancel-btn {
  background: #95a5a6;
  color: white;
}

.cancel-btn:hover {
  background: #7f8c8d;
}

.submit-btn {
  background: #42b983;
  color: white;
}

.submit-btn:hover {
  background: #35a372;
}

/* Micro Economics Styles */
.company-data {
  margin-top: 20px;
}

.micro-tabs {
  display: flex;
  gap: 5px;
  margin-bottom: 20px;
  border-bottom: 2px solid #cccccc;
  flex-wrap: nowrap;
  overflow-x: auto;
  white-space: nowrap;
  scrollbar-width: none;
}

.micro-tabs::-webkit-scrollbar {
  display: none;
}

.micro-tabs button {
  padding: 10px 15px;
  border: none;
  background: #f8f9fa;
  color: #000000;
  cursor: pointer;
  font-size: 0.9em;
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  border-bottom: 3px solid transparent;
  transition: all 0.2s;
}

.micro-tabs button:hover {
  background: #e9ecef;
}

.micro-tabs button.active {
  background: #ffffff;
  color: #000000;
  font-weight: 600;
  border-bottom-color: #3498db;
}

.micro-tab-content {
  padding: 10px 0;
}

.overview-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.tenk-section {
  flex: 1;
  min-width: 0;
  background: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  max-height: calc(100vh - 300px);
  overflow-y: auto;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e0e0e0;
}

.section-header h4 {
  margin: 0;
  color: #000000;
  font-size: 1.3em;
  font-weight: 600;
}

.refresh-btn {
  padding: 8px 16px;
  border: 2px solid #3498db;
  border-radius: 6px;
  background: transparent;
  color: #3498db;
  font-size: 0.9em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: #3498db;
  color: white;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.button-group {
  display: flex;
  gap: 10px;
  align-items: center;
}

.download-btn {
  padding: 8px 16px;
  border: 2px solid #27ae60;
  border-radius: 6px;
  background: transparent;
  color: #27ae60;
  font-size: 0.9em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.download-btn:hover:not(:disabled) {
  background: #27ae60;
  color: white;
}

.download-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.download-btn svg {
  width: 16px;
  height: 16px;
}


.analysis-section-wrapper {
  flex: 1;
  min-width: 0;
}

.micro-tab-pane {
  padding: 10px 0;
}

.ai-section {
  margin-bottom: 30px;
}

.ai-btn {
  background: #8e44ad;
  color: white;
  padding: 12px 24px;
  border: none;
  border-radius: 4px;
  font-size: 1.1em;
  cursor: pointer;
  margin-bottom: 20px;
}

.ai-btn:disabled {
  opacity: 0.7;
  cursor: wait;
}

.progress-indicator {
  background: #e8f5e9;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 20px;
  font-weight: bold;
  color: #2e7d32;
}

.analysis-section {
  margin-bottom: 40px;
  padding-bottom: 30px;
  border-bottom: 2px solid #eee;
}

.analysis-section h4 {
  color: #000000;
  margin-bottom: 15px;
  font-weight: 600;
}

.report-content {
  background: #f9f9f9;
  padding: 20px;
  border-radius: 8px;
  line-height: 1.6;
  margin-bottom: 20px;
}

.info-message {
  background: #fff3cd;
  padding: 15px;
  border-radius: 4px;
  color: #856404;
  margin-top: 10px;
}

.metrics-viz,
.capital-viz {
  margin-top: 20px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  border: 1px solid #ddd;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
}

.metric-card {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  border-left: 4px solid #42b983;
  position: relative;
}

.metric-card.highlight {
  border-left-color: #8e44ad;
  background: #f3e5f5;
}

.metric-label {
  font-size: 0.85em;
  color: #666;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 1.5em;
  font-weight: bold;
  color: #000000;
}

.metric-trend {
  position: absolute;
  top: 10px;
  right: 10px;
  font-size: 1.5em;
}

.metric-trend.positive {
  color: #42b983;
}

.metric-trend.negative {
  color: #e74c3c;
}

.financials-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.financials-header h4 {
  margin: 0;
}

.period-selector {
  display: flex;
  gap: 0;
  border: 2px solid #42b983;
  border-radius: 6px;
  overflow: hidden;
}

.period-selector button {
  padding: 8px 20px;
  border: none;
  background: white;
  color: #42b983;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
}

.period-selector button:hover {
  background: #e8f5e9;
}

.period-selector button.active {
  background: #42b983;
  color: white;
}

.financial-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 15px;
  margin-bottom: 30px;
}

.summary-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.summary-label {
  font-size: 0.85em;
  opacity: 0.9;
  margin-bottom: 8px;
}

.summary-value {
  font-size: 1.8em;
  font-weight: bold;
  margin-bottom: 5px;
}

.summary-change {
  font-size: 0.9em;
  font-weight: 600;
}

.summary-change.positive {
  color: #a8e6cf;
}

.summary-change.negative {
  color: #ffaaa5;
}

.charts-row {
  display: flex;
  gap: 20px;
  margin-bottom: 40px;
  flex-wrap: wrap;
}

.chart-section {
  flex: 1;
  background: white;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #ddd;
  min-width: 300px;
}

.chart-section h5 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #2c3e50;
}

.chart-container {
  height: 300px;
  position: relative;
}

.balance-composition {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.composition-chart {
  flex: 1;
  min-width: 200px;
  text-align: center;
}

.composition-chart h6 {
  margin-bottom: 15px;
  color: #2c3e50;
}

.composition-chart canvas {
  max-height: 250px;
}

.detailed-tables {
  margin-top: 40px;
}

.detailed-tables details {
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  margin-bottom: 15px;
  padding: 15px;
}

.detailed-tables summary {
  cursor: pointer;
  font-size: 1.1em;
  padding: 10px;
  user-select: none;
  color: #2c3e50;
}

.detailed-tables summary:hover {
  background: #f8f9fa;
  border-radius: 4px;
}

.detailed-tables details[open] summary {
  margin-bottom: 20px;
  border-bottom: 2px solid #42b983;
  padding-bottom: 10px;
}

.detailed-tables .table-container {
  overflow-x: auto;
}

.detailed-tables table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
  font-size: 0.85em;
}

.detailed-tables th,
.detailed-tables td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: right;
  white-space: nowrap;
  color: #2c3e50;
}

.detailed-tables th:first-child,
.detailed-tables td:first-child {
  text-align: left;
  font-weight: bold;
  position: sticky;
  left: 0;
  background: white;
  z-index: 2;
  min-width: 200px;
  max-width: 300px;
}

.detailed-tables .item-name {
  font-size: 0.9em;
  color: #2c3e50;
}

.detailed-tables .category-header {
  background-color: #f8f9fa;
  cursor: pointer;
  transition: background-color 0.2s;
}

.detailed-tables .category-header:hover {
  background-color: #e9ecef;
}

.detailed-tables .category-name {
  font-weight: 600;
  color: #000000;
  padding: 10px 20px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.detailed-tables .expand-icon {
  display: inline-block;
  width: 16px;
  text-align: center;
  color: #3498db;
  font-size: 0.9em;
}

.detailed-tables .category-item {
  background-color: #ffffff;
}

.detailed-tables .category-item .item-name {
  padding-left: 40px;
  font-weight: 400;
}

.detailed-tables th {
  background: #f2f2f2;
  position: sticky;
  top: 0;
  z-index: 1;
  font-weight: bold;
}

.detailed-tables .ltm-header {
  background: #d4edda !important;
  color: #155724;
  font-weight: bold;
}

.detailed-tables .ltm-col {
  background: #e8f5e9;
  font-weight: bold;
  color: #2e7d32;
}

.ratios-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.ratio-card {
  background: #fff;
  border: 1px solid #ddd;
  padding: 15px;
  border-radius: 8px;
  color: #2c3e50;
}

.ratio-card h5 {
  margin-top: 0;
  color: #42b983;
}

.ratio-card p {
  margin: 8px 0;
}

.filings-container {
  margin-top: 20px;
}

.filings-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  overflow: hidden;
}

.filings-table thead {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.filings-table th {
  padding: 15px;
  text-align: left;
  font-weight: 600;
  font-size: 0.95em;
  color: white;
}

.filings-table th.sortable {
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.filings-table th.sortable:hover {
  background: rgba(255, 255, 255, 0.1);
}

.filings-table .sort-icon {
  margin-left: 8px;
  font-size: 0.9em;
  opacity: 0.8;
}

.filings-table tbody tr {
  border-bottom: 1px solid #e0e0e0;
  transition: background 0.2s;
}

.filings-table tbody tr:hover {
  background: #f8f9fa;
}

.filings-table tbody tr:last-child {
  border-bottom: none;
}

.filings-table td {
  padding: 12px 15px;
  font-size: 0.9em;
  color: #000;
}

.filing-type {
  font-weight: 600;
  color: #000;
}

.filing-date {
  color: #000;
}

.filing-title {
  color: #000;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.no-link {
  color: #999;
  font-style: italic;
}

.filing-link a {
  color: #42b983;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
}

.filing-link a:hover {
  color: #35a372;
  text-decoration: underline;
}

.trade-log-tabs {
  display: flex;
  gap: 10px;
  margin: 20px 0;
}

.trade-log-tabs button {
  padding: 8px 20px;
  background: #2c3e50;
  color: white;
  border: 1px solid #34495e;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.trade-log-tabs button:hover {
  background: #34495e;
}

.trade-log-tabs button.active {
  background: #3498db;
  border-color: #3498db;
}

.trade-log-container {
  margin-top: 20px;
}

.section-heading {
  color: #000000;
  margin: 30px 0 15px 0;
  font-size: 1.2em;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  border-bottom: 2px solid #3498db;
  padding-bottom: 8px;
}

.trade-log-table {
  width: 100%;
  border-collapse: collapse;
  background: #ffffff;
  color: #000000;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #cccccc;
}

.trade-log-table thead {
  background: #f8f9fa;
}

.trade-log-table th {
  padding: 12px 15px;
  text-align: left;
  font-weight: 600;
  font-size: 0.85em;
  color: #000000;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  background: #f8f9fa;
  border-bottom: 2px solid #cccccc;
}

.trade-log-table tbody tr {
  border-bottom: 1px solid #e0e0e0;
  transition: background 0.2s;
}

.trade-log-table tbody tr:hover {
  background: #f8f9fa;
}

.trade-log-table tbody tr:last-child {
  border-bottom: none;
}

.trade-log-table td {
  padding: 12px 15px;
  font-size: 0.9em;
  background: #ffffff;
  color: #000000;
}

.trade-log-table tbody tr:hover td {
  background: #f8f9fa;
}

.trade-date {
  color: #666666;
  font-size: 0.85em;
}

.trade-action.action-buy {
  color: #10b981;
  font-weight: 600;
}

.trade-action.action-sell {
  color: #ef4444;
  font-weight: 600;
}

.trade-action.action-hold {
  color: #6b7280;
}

.trade-action {
  font-weight: 600;
  text-transform: uppercase;
}

.trade-action.action-buy {
  color: #10b981;
  font-weight: 600;
}

.trade-action.action-purchase {
  color: #3498db;
}

.trade-action.action-sell {
  color: #e74c3c;
}

.trade-action.action-hold {
  color: #6b7280;
}

.trade-shares,
.trade-value,
.trade-holdings {
  text-align: right;
  font-family: 'Courier New', monospace;
}

.trade-party {
  color: #666666;
  font-size: 0.85em;
}

.trade-insider {
  color: #000000;
  font-weight: 500;
}

.options-charts-container {
  margin-top: 30px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 20px;
}

.options-chart-section {
  background: white;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #ddd;
}

.options-chart-section h5 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #000000;
  font-weight: 600;
}

.options-chart-section .chart-container {
  height: 400px;
  position: relative;
}

.no-company-data {
  text-align: center;
  padding: 40px;
  color: #999;
  font-style: italic;
}

/* Productivity Tab Styles */
.productivity-tab-content {
    padding: 20px 0;
}

.content-section {
    display: flex;
    flex-direction: column;
    gap: 24px;
}

.info-card {
    border: 1px solid #cccccc;
    padding: 30px;
    border-radius: 12px;
    background: #ffffff;
    color: #000000;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.info-card h3 {
    margin: 0 0 16px 0;
    font-size: 1.5em;
    color: #000000;
    font-weight: 600;
}

.info-card p {
    margin: 12px 0;
    line-height: 1.6;
    color: #666666;
}

.coming-soon {
    font-style: italic;
    color: #999999;
    margin-top: 20px;
}

/* PolyMarket Styles */
.polymarket-content {
    display: flex;
    flex-direction: column;
    gap: 24px;
}

.polymarket-warning {
    background: #fff3cd;
    border: 2px solid #ffc107;
    border-radius: 8px;
    padding: 15px 20px;
    color: #856404;
    font-size: 0.95em;
    line-height: 1.6;
}

.polymarket-warning strong {
    color: #856404;
    font-weight: 600;
}

.polymarket-header {
    background: #ffffff;
    padding: 20px;
    border-radius: 8px;
    border: 1px solid #cccccc;
}

.polymarket-header h3 {
    margin: 0 0 10px 0;
    color: #000000;
    font-size: 1.5em;
    font-weight: 600;
}

.polymarket-question {
    margin: 0;
    color: #666666;
    font-size: 1em;
}

.polymarket-chart-container {
    background: #ffffff;
    padding: 20px;
    border-radius: 8px;
    border: 1px solid #cccccc;
    height: 400px;
    position: relative;
}

.polymarket-table {
    background: #ffffff;
    padding: 20px;
    border-radius: 8px;
    border: 1px solid #cccccc;
    overflow-x: auto;
}

.polymarket-table table {
    width: 100%;
    border-collapse: collapse;
}

.polymarket-table thead {
    background: #f8f9fa;
}

.polymarket-table th {
    padding: 12px 15px;
    text-align: left;
    font-weight: 600;
    color: #000000;
    border-bottom: 2px solid #cccccc;
}

.polymarket-table td {
    padding: 12px 15px;
    color: #000000;
    border-bottom: 1px solid #e0e0e0;
}

.polymarket-table tbody tr:hover {
    background: #f8f9fa;
}

.odds-value {
    font-weight: 600;
    font-size: 1.1em;
    color: #3498db;
}

.loading-state {
    text-align: center;
    padding: 40px;
    color: #666666;
}

.error-message {
    background: #ffe6e6;
    border: 1px solid #ff9999;
    padding: 20px;
    border-radius: 8px;
    color: #cc0000;
}

/* Overview Layout Styles */
.overview-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.tenk-section {
  flex: 1;
  min-width: 0;
  background: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  max-height: calc(100vh - 300px);
  overflow-y: auto;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e0e0e0;
}

.section-header h4 {
  margin: 0;
  color: #000000;
  font-size: 1.3em;
  font-weight: 600;
}

.refresh-btn {
  padding: 8px 16px;
  border: 2px solid #3498db;
  border-radius: 6px;
  background: transparent;
  color: #3498db;
  font-size: 0.9em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: #3498db;
  color: white;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.refresh-btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #cccccc !important;
  color: #666666 !important;
  border-color: #cccccc !important;
}

.payment-notice {
  margin-top: 10px;
  padding: 12px;
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 6px;
  color: #856404;
  font-size: 0.9em;
}

.tenk-content {
  display: flex;
  flex-direction: column;
}

.tenk-full-html {
  color: #000000;
  font-size: 0.95em;
  line-height: 1.8;
  padding: 20px;
  background: #ffffff;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
  max-width: 100%;
  overflow-x: auto;
}

.tenk-full-html :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 15px 0;
  font-size: 0.9em;
}

.tenk-full-html :deep(table th),
.tenk-full-html :deep(table td) {
  border: 1px solid #ddd;
  padding: 8px 12px;
  text-align: left;
}

.tenk-full-html :deep(table th) {
  background-color: #f8f9fa;
  font-weight: 600;
}

.tenk-full-html :deep(p) {
  margin: 10px 0;
  line-height: 1.6;
}

.tenk-full-html :deep(h1),
.tenk-full-html :deep(h2),
.tenk-full-html :deep(h3),
.tenk-full-html :deep(h4),
.tenk-full-html :deep(h5),
.tenk-full-html :deep(h6) {
  margin: 20px 0 10px 0;
  font-weight: 600;
  color: #000000;
}

.tenk-full-html :deep(ul),
.tenk-full-html :deep(ol) {
  margin: 10px 0;
  padding-left: 30px;
}

.tenk-full-html :deep(li) {
  margin: 5px 0;
  line-height: 1.6;
}

.tenk-full-html :deep(strong),
.tenk-full-html :deep(b) {
  font-weight: 600;
  color: #000000;
}

.tenk-full-html :deep(em),
.tenk-full-html :deep(i) {
  font-style: italic;
}

.analysis-section-wrapper {
  flex: 1;
  min-width: 0;
}

.analysis-report-section {
  flex: 1;
  min-width: 0;
  background: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  max-height: calc(100vh - 300px);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.analysis-report-content {
  flex: 1;
  overflow-y: auto;
  margin-top: 10px;
}

.analysis-report-section .progress-indicator {
  background: #e8f5e9;
  padding: 15px;
  border-radius: 6px;
  margin: 15px 0;
  font-weight: 500;
  color: #2e7d32;
  text-align: center;
}

.analysis-html-content {
  color: #000000;
  font-size: 0.95em;
  line-height: 1.8;
  padding: 0;
  background: transparent;
}

.analysis-html-content :deep(h1),
.analysis-html-content :deep(h2),
.analysis-html-content :deep(h3),
.analysis-html-content :deep(h4),
.analysis-html-content :deep(h5),
.analysis-html-content :deep(h6) {
  margin: 20px 0 10px 0;
  font-weight: 600;
  color: #000000;
}

.analysis-html-content :deep(h1) {
  font-size: 1.8em;
  border-bottom: 2px solid #e0e0e0;
  padding-bottom: 10px;
}

.analysis-html-content :deep(h2) {
  font-size: 1.5em;
  margin-top: 30px;
}

.analysis-html-content :deep(h3) {
  font-size: 1.3em;
}

.analysis-html-content :deep(p) {
  margin: 10px 0;
  line-height: 1.8;
  color: #000000;
}

.analysis-html-content :deep(ul),
.analysis-html-content :deep(ol) {
  margin: 15px 0;
  padding-left: 30px;
}

.analysis-html-content :deep(li) {
  margin: 8px 0;
  line-height: 1.8;
  color: #000000;
}

.analysis-html-content :deep(strong),
.analysis-html-content :deep(b) {
  font-weight: 600;
  color: #000000;
}

.analysis-html-content :deep(em),
.analysis-html-content :deep(i) {
  font-style: italic;
}

.analysis-html-content :deep(blockquote) {
  border-left: 4px solid #3498db;
  padding-left: 15px;
  margin: 15px 0;
  color: #666666;
  font-style: italic;
}

.analysis-html-content :deep(code) {
  background: #f8f9fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

.analysis-html-content :deep(pre) {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 15px 0;
}

.analysis-html-content :deep(pre code) {
  background: transparent;
  padding: 0;
}

.analysis-html-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 15px 0;
  font-size: 0.9em;
}

.analysis-html-content :deep(table th),
.analysis-html-content :deep(table td) {
  border: 1px solid #ddd;
  padding: 8px 12px;
  text-align: left;
}

.analysis-html-content :deep(table th) {
  background-color: #f8f9fa;
  font-weight: 600;
}

.analysis-html-content :deep(a) {
  color: #3498db;
  text-decoration: none;
}

.analysis-html-content :deep(a:hover) {
  text-decoration: underline;
}

.no-data {
  text-align: center;
  padding: 40px 20px;
  color: #666666;
  font-style: italic;
}

</style>


