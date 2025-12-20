<template>
  <div class="bond-view">
    <div class="page-header">
      <h2>Bond Market Data</h2>
      <button @click="updateData" :disabled="loading" class="update-btn">
        {{ loading ? 'Updating...' : 'Update Data' }}
      </button>
    </div>
    
    
    
    <div class="category-tabs">
      <button 
        v-for="category in categories" 
        :key="category.value" 
        :class="{ active: activeCategory === category.value }"
        @click="activeCategory = category.value"
      >
        {{ category.label }}
      </button>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>Loading Bond Market Data...</p>
    </div>
    <div v-else-if="error" class="error-state">
      <p class="error-message">{{ error }}</p>
    </div>
    <div v-else class="bond-data">
      <!-- Treasury Yields -->
      <div v-if="activeCategory === 'treasury_yields'" class="category-section">
        <h3 class="category-title">Government Bond Market Data - Treasury Yields</h3>
        <div class="indicators-grid">
          <div v-for="item in bondData.treasury_yields" :key="item.title" class="bond-card">
            <h4>{{ item.title }}</h4>
            <div class="card-content">
              <p class="value">{{ item.current_value?.toFixed(3) }}%</p>
              <p class="date">{{ item.current_date }}</p>
              <p class="desc">{{ item.description || '&nbsp;' }}</p>
              
              <!-- Per-graph Timeframe Selector -->
              <div class="card-timeframe-selector">
                <button 
                    v-for="tf in timeframes" 
                    :key="tf.value" 
                    :class="{ active: item.selectedTimeframe === tf.value }"
                    @click="updateBondItemTimeframe(item, tf.value)"
                    :disabled="item.loading"
                >
                    {{ tf.label }}
                </button>
              </div>
            </div>
            <div class="chart-container" v-if="item.history && item.history.length > 0">
               <div v-if="item.loading" class="chart-loading-overlay">
                 <div class="spinner-small"></div>
               </div>
              <Line :data="getChartData(item)" :options="chartOptions" />
            </div>
            <div v-else class="no-data">
                <p>No history data available</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Yield Curve Spreads -->
      <div v-if="activeCategory === 'yield_curve'" class="category-section">
        <h3 class="category-title">Yield Curve Spreads</h3>
        <div class="indicators-grid">
          <div v-for="item in bondData.yield_curve" :key="item.title" class="bond-card">
            <h4>{{ item.title }}</h4>
            <div class="card-content">
              <p class="value">{{ item.current_value?.toFixed(3) }} bps</p>
              <p class="date">{{ item.current_date }}</p>
              <p class="desc">{{ item.description || '&nbsp;' }}</p>
              
              <div class="card-timeframe-selector">
                <button 
                    v-for="tf in timeframes" 
                    :key="tf.value" 
                    :class="{ active: item.selectedTimeframe === tf.value }"
                    @click="updateBondItemTimeframe(item, tf.value)"
                    :disabled="item.loading"
                >
                    {{ tf.label }}
                </button>
              </div>
            </div>
            <div class="chart-container" v-if="item.history && item.history.length > 0">
               <div v-if="item.loading" class="chart-loading-overlay">
                 <div class="spinner-small"></div>
               </div>
              <Line :data="getChartData(item)" :options="chartOptions" />
            </div>
             <div v-else class="no-data">
                <p>No history data available</p>
            </div>
          </div>
        </div>
      </div>

      <!-- TIPS & Breakeven -->
      <div v-if="activeCategory === 'tips_breakeven'" class="category-section">
        <h3 class="category-title">Inflation-Linked Bonds (TIPS) & Breakeven Rates</h3>
        <div class="indicators-grid">
          <div v-for="item in bondData.tips_breakeven" :key="item.title" class="bond-card">
            <h4>{{ item.title }}</h4>
            <div class="card-content">
              <p class="value">{{ item.current_value?.toFixed(3) }}%</p>
              <p class="date">{{ item.current_date }}</p>
              <p class="desc">{{ item.description || '&nbsp;' }}</p>
              
              <div class="card-timeframe-selector">
                <button 
                    v-for="tf in timeframes" 
                    :key="tf.value" 
                    :class="{ active: item.selectedTimeframe === tf.value }"
                    @click="updateBondItemTimeframe(item, tf.value)"
                    :disabled="item.loading"
                >
                    {{ tf.label }}
                </button>
              </div>
            </div>
            <div class="chart-container" v-if="item.history && item.history.length > 0">
               <div v-if="item.loading" class="chart-loading-overlay">
                 <div class="spinner-small"></div>
               </div>
              <Line :data="getChartData(item)" :options="chartOptions" />
            </div>
             <div v-else class="no-data">
                <p>No history data available</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Central Bank Rates -->
      <div v-if="activeCategory === 'central_bank_rates'" class="category-section">
        <h3 class="category-title">Central Bank & Money Market Rates</h3>
        <div class="indicators-grid">
          <div v-for="item in bondData.central_bank_rates" :key="item.title" class="bond-card">
            <h4>{{ item.title }}</h4>
            <div class="card-content">
              <p class="value">{{ item.current_value?.toFixed(3) }}%</p>
              <p class="date">{{ item.current_date }}</p>
              <p class="desc">{{ item.description || '&nbsp;' }}</p>
              
              <div class="card-timeframe-selector">
                <button 
                    v-for="tf in timeframes" 
                    :key="tf.value" 
                    :class="{ active: item.selectedTimeframe === tf.value }"
                    @click="updateBondItemTimeframe(item, tf.value)"
                    :disabled="item.loading"
                >
                    {{ tf.label }}
                </button>
              </div>
            </div>
            <div class="chart-container" v-if="item.history && item.history.length > 0">
               <div v-if="item.loading" class="chart-loading-overlay">
                 <div class="spinner-small"></div>
               </div>
              <Line :data="getChartData(item)" :options="chartOptions" />
            </div>
             <div v-else class="no-data">
                <p>No history data available</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Credit Spreads -->
      <div v-if="activeCategory === 'credit_spreads'" class="category-section">
        <h3 class="category-title">Credit Market Data - Corporate Bond Spreads</h3>
        <div class="indicators-grid">
          <div v-for="item in bondData.credit_spreads" :key="item.title" class="bond-card">
            <h4>{{ item.title }}</h4>
            <div class="card-content">
              <p class="value">{{ item.current_value?.toFixed(2) }} bps</p>
              <p class="date">{{ item.current_date }}</p>
              <p class="desc">{{ item.description || '&nbsp;' }}</p>
              
              <div class="card-timeframe-selector">
                <button 
                    v-for="tf in timeframes" 
                    :key="tf.value" 
                    :class="{ active: item.selectedTimeframe === tf.value }"
                    @click="updateBondItemTimeframe(item, tf.value)"
                    :disabled="item.loading"
                >
                    {{ tf.label }}
                </button>
              </div>
            </div>
            <div class="chart-container large-chart" v-if="item.history && item.history.length > 0">
               <div v-if="item.loading" class="chart-loading-overlay">
                 <div class="spinner-small"></div>
               </div>
              <Line :data="getChartData(item)" :options="chartOptions" />
            </div>
             <div v-else class="no-data">
                <p>No history data available</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Funding Stress -->
      <div v-if="activeCategory === 'funding_stress'" class="category-section">
        <h3 class="category-title">Funding Stress Metrics</h3>
        <div class="indicators-grid">
          <div v-for="item in bondData.funding_stress" :key="item.title" class="bond-card">
            <h4>{{ item.title }}</h4>
            <div class="card-content">
              <p class="value">{{ item.current_value?.toFixed(3) }}%</p>
              <p class="date">{{ item.current_date }}</p>
              <p class="desc">{{ item.description || '&nbsp;' }}</p>
              
              <div class="card-timeframe-selector">
                <button 
                    v-for="tf in timeframes" 
                    :key="tf.value" 
                    :class="{ active: item.selectedTimeframe === tf.value }"
                    @click="updateBondItemTimeframe(item, tf.value)"
                    :disabled="item.loading"
                >
                    {{ tf.label }}
                </button>
              </div>
            </div>
            <div class="chart-container" v-if="item.history && item.history.length > 0">
               <div v-if="item.loading" class="chart-loading-overlay">
                 <div class="spinner-small"></div>
               </div>
              <Line :data="getChartData(item)" :options="chartOptions" />
            </div>
             <div v-else class="no-data">
                <p>No history data available</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import API_BASE_URL from '@/config/api.js'

import { ref, onMounted } from 'vue';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Line } from 'vue-chartjs'
import { getDailyCache, setDailyCache, clearCacheByKey } from '../utils/dailyCache.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

const bondData = ref({
  treasury_yields: [],
  yield_curve: [],
  tips_breakeven: [],
  central_bank_rates: [],
  credit_spreads: [],
  funding_stress: []
});

const loading = ref(true);
const error = ref(null);
const activeCategory = ref('treasury_yields');

const timeframes = [
  { label: '1M', value: 'daily' },
  { label: '3M', value: 'weekly' },
  { label: '1Y', value: 'monthly' },
  { label: '5Y', value: 'yearly' },
  { label: 'Max', value: 'max' }
];

const categories = [
  { label: 'Treasury Yields', value: 'treasury_yields' },
  { label: 'Yield Curve', value: 'yield_curve' },
  { label: 'TIPS & Breakeven', value: 'tips_breakeven' },
  { label: 'Central Bank Rates', value: 'central_bank_rates' },
  { label: 'Credit Spreads', value: 'credit_spreads' },
  { label: 'Funding Stress', value: 'funding_stress' }
];

// Cache configuration
const CACHE_EXPIRATION = 30 * 60 * 1000; // 30 minutes
const CACHE_KEY_PREFIX = 'bond_series_';

const getCacheKey = (seriesId, timeframe) => `${CACHE_KEY_PREFIX}${seriesId}_${timeframe}`;

const getCachedData = (seriesId, timeframe) => {
    try {
        const key = getCacheKey(seriesId, timeframe);
        const cached = localStorage.getItem(key);
        if (!cached) return null;
        
        const { data, timestamp } = JSON.parse(cached);
        if (Date.now() - timestamp < CACHE_EXPIRATION) {
            return data;
        }
        localStorage.removeItem(key);
        return null;
    } catch (e) {
        return null;
    }
};

const setCachedData = (seriesId, timeframe, data) => {
    try {
        const key = getCacheKey(seriesId, timeframe);
        localStorage.setItem(key, JSON.stringify({
            data,
            timestamp: Date.now()
        }));
    } catch (e) {
        console.error('Cache write error', e);
    }
};

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: { 
      mode: 'index', 
      intersect: false,
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      titleColor: '#000000',
      bodyColor: '#000000',
      borderColor: '#cccccc',
      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
      borderWidth: 1,
      padding: 12
    }
  },
  scales: {
    x: { 
      display: true,
      ticks: { 
        color: '#666666', 
        font: { size: 10 },
        maxRotation: 45,
        minRotation: 45
      },
      grid: { 
        display: true,
        color: 'rgba(0, 0, 0, 0.1)'
      }
    },
    y: { 
      display: true,
      ticks: { 
        color: '#666666', 
        font: { size: 10 }
      },
      grid: { 
        display: true,
        color: 'rgba(0, 0, 0, 0.1)'
      }
    }
  },
  elements: {
    point: { 
      radius: 0, 
      hitRadius: 10, 
      hoverRadius: 4
    },
    line: { 
      borderWidth: 2, 
      tension: 0.2 
    }
  }
};

const getChartData = (item) => {
  const sortedHistory = [...(item.history || [])].sort((a, b) => new Date(a.date) - new Date(b.date));
  
  return {
    labels: sortedHistory.map(h => h.date),
    datasets: [
      {
        label: item.title,
        backgroundColor: '#42b983',
        borderColor: '#42b983',
        data: sortedHistory.map(h => h.value),
        fill: false
      }
    ]
  }
}

const fetchBondData = async () => {
  loading.value = true;
  error.value = null;
  
  // Check daily cache first
  const cached = getDailyCache('bond_data_monthly');
  if (cached) {
    console.log('Using cached bond data');
    bondData.value = cached;
    loading.value = false;
    return;
  }
  
  try {
    // Initial fetch of all data with default 'monthly' (1Y) timeframe
    const response = await fetch(`${API_BASE_URL}/api/bond/all?timeframe=monthly`);
    if (!response.ok) throw new Error('Failed to fetch bond data');
    const data = await response.json();
    
    // Initialize with default timeframe state for each item in each category
    Object.keys(data).forEach(category => {
        data[category] = data[category].map(item => ({
            ...item,
            selectedTimeframe: 'monthly',
            loading: false
        }));
    });
    
    bondData.value = data;
    
    // Cache the data
    setDailyCache('bond_data_monthly', data);
    
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
};

const updateData = async () => {
  clearCacheByKey('bond_data_monthly');
  await fetchBondData();
};

const updateBondItemTimeframe = async (item, timeframe) => {
    if (item.selectedTimeframe === timeframe) return;
    
    item.selectedTimeframe = timeframe;
    item.loading = true;
    
    // Check cache
    const cached = getCachedData(item.series_id, timeframe);
    if (cached) {
        Object.assign(item, cached);
        item.selectedTimeframe = timeframe; // Ensure this stays set
        item.loading = false;
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/bond/series/${item.series_id}?timeframe=${timeframe}`);
        if (!response.ok) throw new Error('Failed to fetch series');
        const data = await response.json();
        
        // Update item properties with new data
        Object.assign(item, data);
        item.selectedTimeframe = timeframe; // Ensure this stays set
        
        setCachedData(item.series_id, timeframe, data);
    } catch (err) {
        console.error(`Error fetching ${item.title}:`, err);
    } finally {
        item.loading = false;
    }
};

onMounted(() => {
  fetchBondData();
});
</script>

<style scoped>
.bond-view {
  padding: 30px 30px 30px 0;
  max-width: 1800px;
  margin: 0 auto;
  background: #ffffff;
  min-height: 100vh;
}

.bond-view h2 {
  margin: 0 0 24px 0;
  font-size: 2em;
  text-align: center;
  color: #000000;
  font-weight: 600;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #000000;
  font-weight: 600;
}

.update-btn {
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

.update-btn:hover:not(:disabled) {
  background: #2980b9;
  transform: translateY(-1px);
}

.update-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}


.category-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 30px;
  justify-content: center;
  flex-wrap: nowrap;
  border-bottom: 2px solid #cccccc;
  padding-bottom: 12px;
  overflow-x: auto;
}

.category-tabs button {
  background: transparent;
  border: none;
  color: #666666;
  padding: 12px 20px;
  border-radius: 6px 6px 0 0;
  cursor: pointer;
  font-size: 0.95em;
  font-weight: 500;
  transition: all 0.2s;
  border-bottom: 3px solid transparent;
}

.category-tabs button.active {
  color: #000000;
  border-bottom-color: #3498db;
  background: rgba(52, 152, 219, 0.1);
  font-weight: 600;
}

.category-tabs button:hover {
  color: #000000;
  background: rgba(0, 0, 0, 0.05);
}

.category-section {
  margin-top: 20px;
}

.category-title {
  font-size: 1.5em;
  color: #000000;
  margin-bottom: 24px;
  text-align: center;
  font-weight: 600;
}

.indicators-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

@media (max-width: 1200px) {
  .indicators-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .indicators-grid {
    grid-template-columns: 1fr;
  }
}

.bond-card {
  border: 1px solid #cccccc;
  padding: 20px;
  border-radius: 12px;
  text-align: center;
  background: #ffffff;
  color: #000000;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
  position: relative;
}

.bond-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.bond-card h4 {
  margin: 0 0 12px 0;
  font-size: 1.1em;
  font-weight: 600;
  color: #000000;
}

.card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.value {
  font-size: 2em;
  font-weight: bold;
  color: #42b983;
  margin: 8px 0;
}

.date {
  font-size: 0.85em;
  color: #666666;
  margin: 4px 0;
}

.desc {
  font-size: 0.9em;
  font-style: italic;
  margin: 8px 0 16px 0;
  color: #666666;
  min-height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-timeframe-selector {
    display: flex;
    justify-content: center;
    gap: 8px;
    margin-bottom: 16px;
}

.card-timeframe-selector button {
    background: #f8f9fa;
    border: 1px solid #cccccc;
    color: #000000;
    padding: 4px 8px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.75em;
    transition: all 0.2s;
}

.card-timeframe-selector button.active {
    background: #3498db;
    color: white;
    border-color: #3498db;
}

.card-timeframe-selector button:hover:not(.active) {
    background: #e9ecef;
}

.chart-container {
  height: 250px;
  width: 100%;
  margin-top: auto;
  padding-top: 16px;
  position: relative;
}

.chart-container.large-chart {
  height: 350px;
}

.chart-loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10;
}

.spinner-small {
    width: 24px;
    height: 24px;
    border: 2px solid rgba(0, 0, 0, 0.1);
    border-top-color: #42b983;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #000000;
}

.loading-state p {
  color: #666666;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #cccccc;
  border-top-color: #42b983;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
}

.error-message {
  color: #e74c3c;
  font-size: 1.1em;
  background: rgba(231, 76, 60, 0.1);
  padding: 16px 24px;
  border-radius: 8px;
  border: 1px solid #e74c3c;
}

.no-data {
    height: 250px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #666666;
    font-style: italic;
}
</style>

