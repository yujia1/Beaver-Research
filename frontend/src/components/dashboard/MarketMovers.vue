<template>
  <div class="market-movers">
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
          <tr v-for="stock in items" :key="stock.ticker">
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
import { ref, onMounted, watch } from 'vue'
import API_BASE_URL from '@/config/api'

const props = defineProps({
  moverType: {
    type: String,
    required: true
  }
})

const items = ref([])
const loading = ref(false)
const error = ref(null)

// Simple in-memory cache to prevent re-fetching if prop changes back and forth quickly in same session context (if kept alive)
const cache = new Map()

const fetchMarketMovers = async () => {
  const type = props.moverType
  
  if (cache.has(type)) {
    items.value = cache.get(type)
    return
  }
  
  loading.value = true
  error.value = null
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/alphatrade/market-movers/${type}`)
    if (!response.ok) throw new Error('Failed to fetch data')
    
    const result = await response.json()
    items.value = result.slice(0, 60) // Limit to top 50 to allow scrolling
    cache.set(type, items.value)
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

watch(() => props.moverType, () => {
  fetchMarketMovers()
})

onMounted(() => {
  fetchMarketMovers()
})
</script>

<style scoped>
.market-movers {
  background: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.movers-content {
  padding: 0;
  max-height: 400px; /* Fixed height for scroll area */
  overflow-y: auto;  /* Enable vertical scrolling */
  position: relative;
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
  
  /* Sticky Header */
  position: sticky;
  top: 0;
  z-index: 10;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
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

/* Custom scrollbar for webkit */
.movers-content::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.movers-content::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.movers-content::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 3px;
}

.movers-content::-webkit-scrollbar-thumb:hover {
  background: #999;
}
</style>
