<template>
  <div class="market-movers">
    <div class="movers-tabs">
      <button 
        :class="{ active: activeTab === 'most-actives' }" 
        @click="activeTab = 'most-actives'"
      >
        {{ t('dashboard.market_movers.most_actives') || 'Top Trade' }}
      </button>
      <button 
        :class="{ active: activeTab === 'gainers' }" 
        @click="activeTab = 'gainers'"
      >
        {{ t('dashboard.market_movers.top_gainers') || 'Top Gainers' }}
      </button>
      <button 
        :class="{ active: activeTab === 'losers' }" 
        @click="activeTab = 'losers'"
      >
        {{ t('dashboard.market_movers.top_losers') || 'Top Losers' }}
      </button>
    </div>

    <div class="movers-content">
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
      </div>
      <div v-else-if="error" class="error-state">
        {{ error }}
      </div>
      <table v-else class="movers-table">
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Name</th>
            <th class="text-right">Price</th>
            <th class="text-right">% Change</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="stock in displayedData" :key="stock.ticker">
            <td class="symbol">{{ stock.ticker }}</td>
            <td class="name" :title="stock.name">{{ stock.name }}</td>
            <td class="text-right">${{ formatNumber(stock.price) }}</td>
            <td 
              class="text-right" 
              :class="stock.changesPercentage >= 0 ? 'positive' : 'negative'"
            >
              {{ stock.changesPercentage >= 0 ? '+' : '' }}{{ formatNumber(stock.changesPercentage) }}%
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import API_BASE_URL from '@/config/api'

const { t } = useI18n()

const activeTab = ref('most-actives')
const data = ref({
  'most-actives': [],
  'gainers': [],
  'losers': []
})
const loading = ref(false)
const error = ref(null)

const displayedData = computed(() => {
  return data.value[activeTab.value] || []
})

const fetchMarketMovers = async (type) => {
  if (data.value[type].length > 0) return // Return if already cached
  
  loading.value = true
  error.value = null
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/alphatrade/market-movers/${type}`)
    if (!response.ok) throw new Error('Failed to fetch data')
    
    const result = await response.json()
    data.value[type] = result.slice(0, 10) // Limit to top 10
  } catch (err) {
    console.error(`Error fetching ${type}:`, err)
    error.value = "Failed to load market data"
  } finally {
    loading.value = false
  }
}

const formatNumber = (num) => {
  return num ? num.toFixed(2) : '0.00'
}

watch(activeTab, (newTab) => {
  fetchMarketMovers(newTab)
})

onMounted(() => {
  fetchMarketMovers(activeTab.value)
})
</script>

<style scoped>
.market-movers {
  margin-top: 2rem;
  background: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.movers-tabs {
  display: flex;
  background: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
}

.movers-tabs button {
  flex: 1;
  padding: 1rem;
  border: none;
  background: none;
  font-weight: 600;
  color: #666;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
  font-family: 'Inter', sans-serif;
  text-transform: uppercase;
  font-size: 0.8rem;
  letter-spacing: 0.5px;
}

.movers-tabs button.active {
  color: #000;
  border-bottom-color: #000;
  background: #ffffff;
}

.movers-tabs button:hover:not(.active) {
  background: #eeeeee;
  color: #333;
}

.movers-content {
  padding: 0;
  min-height: 200px;
}

.movers-table {
  width: 100%;
  border-collapse: collapse;
}

.movers-table th {
  text-align: left;
  padding: 0.75rem 1rem;
  background: #fafafa;
  color: #666;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  border-bottom: 1px solid #e0e0e0;
}

.movers-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #f0f0f0;
  font-size: 0.875rem;
  color: #333;
}

.movers-table tr:last-child td {
  border-bottom: none;
}

.movers-table tr:hover {
  background-color: #f9f9f9;
}

.symbol {
  font-weight: 700;
  color: #000;
}

.name {
  color: #666;
  max-width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.text-right {
  text-align: right;
}

.positive {
  color: #10b981;
  font-weight: 600;
}

.negative {
  color: #ef4444;
  font-weight: 600;
}

.loading-state, .error-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  color: #999;
}

.loading-spinner {
  border: 2px solid #f3f3f3;
  border-top: 2px solid #000;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
