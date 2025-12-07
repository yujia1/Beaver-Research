<template>
  <div class="macro-view">
    <div class="page-header">
      <h2>Macro Economics</h2>
      <button @click="updateData" :disabled="loading" class="update-btn">
        {{ loading ? 'Updating...' : 'Update Data' }}
      </button>
    </div>
    
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>Loading Macro Economic Data...</p>
    </div>
    <div v-else-if="error" class="error-state">
      <p class="error-message">{{ error }}</p>
    </div>
    <div v-else class="indicators">
      <div v-for="item in indicators" :key="item.indicator" class="indicator-card">
        <div class="card-content">
          <h3>{{ item.indicator }}</h3>
          <p class="value">{{ item.value }}</p>
          <p class="date">{{ item.date }}</p>
          <p class="desc">{{ item.description || '&nbsp;' }}</p>
          
          <!-- Per-graph Timeframe Selector -->
          <div class="card-timeframe-selector">
            <button 
                v-for="tf in timeframes" 
                :key="tf.value" 
                :class="{ active: item.selectedTimeframe === tf.value }"
                @click="updateIndicatorTimeframe(item, tf.value)"
                :disabled="item.loading"
            >
                {{ tf.label }}
            </button>
          </div>
        </div>
        
        <!-- Interactive Chart.js Chart -->
        <div class="chart-container" v-if="item.history && item.history.length > 0">
           <div v-if="item.loading" class="chart-loading-overlay">
             <div class="spinner-small"></div>
           </div>
           <Bar v-if="item.chart_type === 'bar'" :data="getChartData(item)" :options="barChartOptions" />
           <Line v-else :data="getChartData(item)" :options="chartOptions" />
        </div>
        <div v-else class="no-data">
            <p>No history data available</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Line, Bar } from 'vue-chartjs'
import { getDailyCache, setDailyCache, clearCacheByKey } from '../utils/dailyCache.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
)

const indicators = ref([]);
const loading = ref(true);
const error = ref(null);

const timeframes = [
    { label: '1M', value: 'daily' }, // Using 'daily' for 1M view (approx 30 days)
    { label: '3M', value: 'weekly' }, // Using 'weekly' for 3M view
    { label: '1Y', value: 'monthly' }, // Using 'monthly' for 1Y view
    { label: '5Y', value: 'yearly' },   // Using 'yearly' for 5Y view
    { label: 'Max', value: 'max' }
];

// Cache configuration
const CACHE_EXPIRATION = 30 * 60 * 1000; // 30 minutes
const CACHE_KEY_PREFIX = 'macro_series_';

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
      borderColor: '#42b983',
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

const barChartOptions = {
  ...chartOptions,
  elements: {
      ...chartOptions.elements,
      bar: {
          borderRadius: 4
      }
  }
};

const getChartData = (item) => {
    if (item.chart_type === 'bar') {
        return {
            labels: item.history.map(h => h.date),
            datasets: [{
                label: item.indicator,
                backgroundColor: '#3498db',
                data: item.history.map(h => h.value)
            }]
        };
    }

    const sortedHistory = [...item.history].sort((a, b) => new Date(a.date) - new Date(b.date));
    
    return {
        labels: sortedHistory.map(h => h.date),
        datasets: [
            {
                label: item.indicator,
                backgroundColor: '#42b983',
                borderColor: '#42b983',
                data: sortedHistory.map(h => h.value),
                fill: false
            }
        ]
    }
}

const fetchMacroData = async () => {
  loading.value = true;
  error.value = null;
  
  // Check daily cache first
  const cached = getDailyCache('macro_data_monthly');
  if (cached) {
    console.log('Using cached macro data');
    indicators.value = cached;
    loading.value = false;
    return;
  }
  
  try {
    // Initial fetch of all data with default 'monthly' (1Y) timeframe
    const response = await fetch(`http://localhost:8000/api/internal/macro?timeframe=monthly`);
    if (!response.ok) throw new Error('Failed to fetch data');
    const data = await response.json();
    
    // Initialize with default timeframe state
    const processedData = data.map(item => ({
        ...item,
        selectedTimeframe: 'monthly',
        loading: false
    }));
    
    indicators.value = processedData;
    
    // Cache the data
    setDailyCache('macro_data_monthly', processedData);
    
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
};

const updateData = async () => {
  clearCacheByKey('macro_data_monthly');
  await fetchMacroData();
};


const updateIndicatorTimeframe = async (item, timeframe) => {
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
        const response = await fetch(`http://localhost:8000/api/internal/macro/series/${item.series_id}?timeframe=${timeframe}`);
        if (!response.ok) throw new Error('Failed to fetch series');
        const data = await response.json();
        
        // Update item properties with new data
        Object.assign(item, data);
        item.selectedTimeframe = timeframe; // Ensure this stays set
        
        setCachedData(item.series_id, timeframe, data);
    } catch (err) {
        console.error(`Error fetching ${item.indicator}:`, err);
    } finally {
        item.loading = false;
    }
};

onMounted(() => {
  fetchMacroData();
});
</script>

<style scoped>
.macro-view {
  padding: 30px 30px 30px 0;
  max-width: 1600px;
  margin: 0 auto;
  background: #ffffff;
  min-height: 100vh;
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

.macro-view h2 {
  margin: 0 0 24px 0;
  font-size: 2em;
  text-align: center;
  color: #000000;
  font-weight: 600;
}

.indicators {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  max-width: 1600px;
  margin: 0 auto;
}

@media (max-width: 1200px) {
  .indicators {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .indicators {
    grid-template-columns: 1fr;
  }
}

.indicator-card {
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

.indicator-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.indicator-card h3 {
  margin: 0 0 12px 0;
  font-size: 1.1em;
  font-weight: 600;
  color: #000000;
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
