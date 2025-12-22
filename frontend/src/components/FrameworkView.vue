<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import API_BASE_URL from '@/config/api.js'

const { t } = useI18n()

// State
const ticker = ref('')
const activeTab = ref('income') // income, cash_flow, balance_sheet
const period = ref('annual') // annual or quarter
const loading = ref(false)
const error = ref(null)

// Data
const incomeData = ref([])
const cashFlowData = ref([])
const balanceSheetData = ref([])

// Fetch financial data
const fetchFinancialData = async () => {
  if (!ticker.value || ticker.value.trim() === '') {
    error.value = 'Please enter a ticker symbol'
    return
  }

  loading.value = true
  error.value = null

  try {
    const token = localStorage.getItem('access_token')
    const headers = token ? { 'Authorization': `Bearer ${token}` } : {}

    const response = await fetch(
      `${API_BASE_URL}/api/framework/all/${ticker.value.toUpperCase()}?period=${period.value}&limit=5`,
      { headers }
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch data' }))
      throw new Error(errorData.detail || 'Failed to fetch financial data')
    }

    const data = await response.json()
    incomeData.value = data.income_statement || []
    cashFlowData.value = data.cash_flow || []
    balanceSheetData.value = data.balance_sheet || []
  } catch (err) {
    error.value = err.message
    console.error('Error fetching financial data:', err)
  } finally {
    loading.value = false
  }
}

// Get current data based on active tab
const currentData = computed(() => {
  switch (activeTab.value) {
    case 'income':
      return incomeData.value
    case 'cash_flow':
      return cashFlowData.value
    case 'balance_sheet':
      return balanceSheetData.value
    default:
      return []
  }
})

// Get years/periods from data
const periods = computed(() => {
  if (!currentData.value || currentData.value.length === 0) return []
  return currentData.value.map(item => item.date || item.calendarYear)
})

// Format currency
const formatCurrency = (value) => {
  if (value === null || value === undefined) return '-'
  const num = parseFloat(value)
  if (isNaN(num)) return '-'
  
  // Format in billions/millions
  if (Math.abs(num) >= 1e9) {
    return `$${(num / 1e9).toFixed(2)}B`
  } else if (Math.abs(num) >= 1e6) {
    return `$${(num / 1e6).toFixed(2)}M`
  } else if (Math.abs(num) >= 1e3) {
    return `$${(num / 1e3).toFixed(2)}K`
  }
  return `$${num.toFixed(2)}`
}

// Get all line items for current statement type
const lineItems = computed(() => {
  if (!currentData.value || currentData.value.length === 0) return []
  
  const firstItem = currentData.value[0]
  const excludeKeys = ['date', 'symbol', 'reportedCurrency', 'cik', 'fillingDate', 'acceptedDate', 'calendarYear', 'period', 'link', 'finalLink']
  
  return Object.keys(firstItem).filter(key => !excludeKeys.includes(key))
})

// Handle search
const handleSearch = () => {
  fetchFinancialData()
}

// Handle period change
const changePeriod = (newPeriod) => {
  period.value = newPeriod
  if (ticker.value) {
    fetchFinancialData()
  }
}
</script>

<template>
  <div class="framework-container">
    <!-- Header -->
    <div class="header">
      <div>
        <h1 class="title">{{ t('framework.title') }}</h1>
        <p class="subtitle">{{ t('framework.subtitle') }}</p>
      </div>
    </div>

    <!-- Search Bar -->
    <div class="search-section">
      <input
        v-model="ticker"
        type="text"
        :placeholder="t('framework.ticker_placeholder')"
        class="ticker-input"
        @keyup.enter="handleSearch"
      />
      <button @click="handleSearch" class="search-btn" :disabled="loading">
        {{ loading ? t('framework.loading') : t('framework.search') }}
      </button>
    </div>

    <!-- Content -->
    <div v-if="ticker && !loading && !error" class="content">
      <!-- Company Header -->
      <div class="company-header">
        <h2>{{ ticker.toUpperCase() }}</h2>
        <p class="dataset-label">{{ period === 'annual' ? 'ANNUAL DATASET' : 'QUARTERLY DATASET' }}</p>
      </div>

      <!-- Tab Navigation -->
      <div class="tabs-section">
        <div class="tabs">
          <button
            :class="['tab', { active: activeTab === 'income' }]"
            @click="activeTab = 'income'"
          >
            {{ t('framework.tabs.income') }}
          </button>
          <button
            :class="['tab', { active: activeTab === 'cash_flow' }]"
            @click="activeTab = 'cash_flow'"
          >
            {{ t('framework.tabs.cash_flow') }}
          </button>
          <button
            :class="['tab', { active: activeTab === 'balance_sheet' }]"
            @click="activeTab = 'balance_sheet'"
          >
            {{ t('framework.tabs.balance_sheet') }}
          </button>
        </div>

        <!-- Period Toggle -->
        <div class="period-toggle">
          <button
            :class="['period-btn', { active: period === 'annual' }]"
            @click="changePeriod('annual')"
          >
            {{ t('framework.period.annual') }}
          </button>
          <button
            :class="['period-btn', { active: period === 'quarter' }]"
            @click="changePeriod('quarter')"
          >
            {{ t('framework.period.quarterly') }}
          </button>
        </div>
      </div>

      <!-- Financial Data Table -->
      <div v-if="currentData.length > 0" class="data-table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th class="line-item-header">{{ t('framework.line_item') }}</th>
              <th v-for="periodDate in periods" :key="periodDate" class="period-header">
                {{ periodDate }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in lineItems" :key="item">
              <td class="line-item-cell">{{ item }}</td>
              <td v-for="(data, index) in currentData" :key="index" class="data-cell">
                {{ formatCurrency(data[item]) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="no-data">
        {{ t('framework.no_data') }}
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>{{ t('framework.loading') }}</p>
    </div>

    <!-- Error State -->
    <div v-if="error && !loading" class="error-state">
      <p>{{ t('framework.error') }}: {{ error }}</p>
    </div>

    <!-- Empty State -->
    <div v-if="!ticker && !loading" class="empty-state">
      <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="7" height="7"></rect>
        <rect x="14" y="3" width="7" height="7"></rect>
        <rect x="14" y="14" width="7" height="7"></rect>
        <rect x="3" y="14" width="7" height="7"></rect>
      </svg>
      <p>{{ t('framework.ticker_placeholder') }}</p>
    </div>
  </div>
</template>

<style scoped>
.framework-container {
  padding: 2rem;
  max-width: 1600px;
  margin: 0 auto;
  min-height: calc(100vh - 4rem);
}

.header {
  margin-bottom: 2rem;
}

.title {
  font-size: 2rem;
  font-weight: 700;
  color: #000;
  margin: 0 0 0.5rem 0;
  letter-spacing: 0.5px;
}

.subtitle {
  font-size: 0.875rem;
  color: #666;
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.search-section {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  max-width: 600px;
}

.ticker-input {
  flex: 1;
  padding: 0.875rem 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
  font-family: inherit;
  transition: border-color 0.2s;
}

.ticker-input:focus {
  outline: none;
  border-color: #000;
}

.search-btn {
  padding: 0.875rem 2rem;
  background: #000;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.search-btn:hover:not(:disabled) {
  background: #333;
}

.search-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.content {
  background: #fff;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.company-header {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 2px solid #f0f0f0;
}

.company-header h2 {
  font-size: 1.75rem;
  font-weight: 700;
  color: #000;
  margin: 0 0 0.5rem 0;
}

.dataset-label {
  font-size: 0.875rem;
  color: #999;
  margin: 0;
  letter-spacing: 0.5px;
}

.tabs-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.tabs {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.tab {
  padding: 0.75rem 1.5rem;
  background: transparent;
  border: none;
  border-bottom: 3px solid transparent;
  font-size: 0.9375rem;
  font-weight: 600;
  color: #999;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.tab:hover {
  color: #000;
}

.tab.active {
  color: #000;
  border-bottom-color: #000;
}

.period-toggle {
  display: flex;
  gap: 0;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
}

.period-btn {
  padding: 0.75rem 1.5rem;
  background: #fff;
  border: none;
  font-size: 0.875rem;
  font-weight: 600;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.period-btn:first-child {
  border-right: 2px solid #e0e0e0;
}

.period-btn.active {
  background: #000;
  color: #fff;
}

.period-btn:hover:not(.active) {
  background: #f5f5f5;
}

.data-table-wrapper {
  overflow-x: auto;
  margin-top: 1.5rem;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9375rem;
}

.data-table thead {
  background: #f8f8f8;
  position: sticky;
  top: 0;
  z-index: 10;
}

.data-table th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  color: #000;
  border-bottom: 2px solid #e0e0e0;
  white-space: nowrap;
}

.line-item-header {
  position: sticky;
  left: 0;
  background: #f8f8f8;
  z-index: 11;
  min-width: 250px;
}

.period-header {
  text-align: right;
  min-width: 120px;
}

.data-table tbody tr {
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.2s;
}

.data-table tbody tr:hover {
  background: #fafafa;
}

.line-item-cell {
  padding: 1rem;
  font-weight: 500;
  color: #333;
  position: sticky;
  left: 0;
  background: #fff;
  border-right: 1px solid #f0f0f0;
}

.data-table tbody tr:hover .line-item-cell {
  background: #fafafa;
}

.data-cell {
  padding: 1rem;
  text-align: right;
  color: #666;
  font-family: 'Courier New', monospace;
}

.loading-state,
.error-state,
.empty-state,
.no-data {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  color: #999;
  text-align: center;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f0f0f0;
  border-top-color: #000;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-state {
  color: #ef4444;
}

.empty-state svg {
  color: #d0d0d0;
  margin-bottom: 1rem;
}

@media (max-width: 768px) {
  .framework-container {
    padding: 1rem;
  }

  .title {
    font-size: 1.5rem;
  }

  .search-section {
    flex-direction: column;
  }

  .tabs-section {
    flex-direction: column;
    align-items: stretch;
  }

  .tabs {
    justify-content: center;
  }

  .period-toggle {
    width: 100%;
  }

  .period-btn {
    flex: 1;
  }
}
</style>
