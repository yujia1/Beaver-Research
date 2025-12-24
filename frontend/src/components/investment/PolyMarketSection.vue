<template>
  <div class="productivity-tab-content">
    <div v-if="!ticker" class="empty-deck">
      <p>{{ t('investment.polymarket.placeholder') || 'Select a stock to view PolyMarket data' }}</p>
    </div>
    <div v-else class="content-section">
      <div v-if="loadingPolyMarket" class="loading-state">
        <p>{{ t('investment.polymarket.loading') || 'Loading PolyMarket data...' }}</p>
      </div>
      <div v-else-if="polyMarketError" class="error-message">
        <p>{{ polyMarketError }}</p>
      </div>
      <div v-else-if="polyMarketData" class="polymarket-content">
        <div v-if="polyMarketData.is_real_data === false" class="polymarket-warning">
          <strong>{{ t('investment.polymarket.note') }}</strong> {{ t('investment.polymarket.warning', { stock: ticker }) }}
        </div>
        <div class="polymarket-header">
          <h3>📊 {{ t('investment.polymarket.title') }} - {{ ticker }}</h3>
          <p class="polymarket-question">{{ polyMarketData.question }}</p>
        </div>
        <div class="polymarket-chart-container">
          <canvas ref="polyMarketChart"></canvas>
        </div>
        <div class="polymarket-table">
          <table>
            <thead>
              <tr>
                <th>{{ t('investment.polymarket.price_target') }}</th>
                <th>{{ t('investment.polymarket.odds') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="target in polyMarketData.targets" :key="target.target">
                <td>{{ target.target }}</td>
                <td class="odds-value">{{ target.odds }}%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div v-else class="no-data">
        <p>No PolyMarket data available for {{ ticker }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import API_BASE_URL from '@/config/api.js'
import { Chart as ChartJS, BarElement, BarController, CategoryScale, LinearScale, Tooltip, Legend } from 'chart.js'

ChartJS.register(BarElement, BarController, CategoryScale, LinearScale, Tooltip, Legend)

const props = defineProps({
  ticker: { type: String, default: '' }
})

const { t } = useI18n()

const polyMarketData = ref(null)
const loadingPolyMarket = ref(false)
const polyMarketError = ref(null)
const polyMarketChart = ref(null)
let polyMarketChartInstance = null

const fetchPolyMarketData = async () => {
  if (!props.ticker) {
    polyMarketData.value = null
    return
  }
  
  loadingPolyMarket.value = true
  polyMarketError.value = null
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/internal/polymarket/${props.ticker.toUpperCase()}`)
    if (!response.ok) {
      throw new Error('Failed to fetch PolyMarket data')
    }
    polyMarketData.value = await response.json()
    
    await nextTick()
    renderPolyMarketChart()
  } catch (err) {
    polyMarketError.value = err.message || 'Error loading PolyMarket data'
    console.error('Error fetching PolyMarket data:', err)
  } finally {
    loadingPolyMarket.value = false
  }
}

const renderPolyMarketChart = () => {
  if (!polyMarketChart.value || !polyMarketData.value) return
  
  if (polyMarketChartInstance) {
    polyMarketChartInstance.destroy()
  }
  
  const labels = polyMarketData.value.targets.map(t => t.target)
  const odds = polyMarketData.value.targets.map(t => t.odds)
  
  polyMarketChartInstance = new ChartJS(polyMarketChart.value, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Odds (%)',
        data: odds,
        backgroundColor: odds.map(o => {
          if (o >= 40) return '#42b983'
          if (o >= 25) return '#95a5a6'
          if (o >= 15) return '#f39c12'
          return '#e74c3c'
        }),
        borderColor: '#000000',
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (context) => `Odds: ${context.parsed.y}%`
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          ticks: { callback: (value) => value + '%' },
          grid: { color: 'rgba(0, 0, 0, 0.1)' }
        },
        x: {
          grid: { display: false },
          ticks: { color: '#000000' }
        }
      }
    }
  })
}

watch(() => props.ticker, (newTicker) => {
  if (newTicker) {
    fetchPolyMarketData()
  } else {
    polyMarketData.value = null
  }
})

onMounted(() => {
  if (props.ticker) fetchPolyMarketData()
})

onUnmounted(() => {
  if (polyMarketChartInstance) {
    polyMarketChartInstance.destroy()
  }
})
</script>

<style scoped>
.polymarket-content {
  padding: 1rem;
}
.polymarket-warning {
  background: #fff3cd;
  color: #856404;
  padding: 0.75rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}
.polymarket-header {
  margin-bottom: 1rem;
}
.polymarket-question {
  font-size: 1.1rem;
  color: #555;
  margin-top: 0.5rem;
}
.polymarket-chart-container {
  height: 300px;
  margin-bottom: 1rem;
}
.polymarket-table table {
  width: 100%;
  border-collapse: collapse;
}
.polymarket-table th, .polymarket-table td {
  padding: 0.75rem;
  border-bottom: 1px solid #eee;
  text-align: left;
}
.odds-value {
  font-weight: bold;
}
.error-message {
  color: red;
  padding: 1rem;
}
.loading-state, .empty-deck, .no-data {
  text-align: center;
  padding: 2rem;
  color: #666;
}
</style>
