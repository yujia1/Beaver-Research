<template>
    <div class="bond-section">
        <div class="category-tabs">
            <button 
                v-for="category in getBondCategories()" 
                :key="category.value"
                :class="{ active: activeBondCategory === category.value }"
                @click="activeBondCategory = category.value"
            >
                {{ category.label }}
            </button>
        </div>

        <div v-if="bondLoading" class="loading-state">
            <p>{{ t('dashboard.loading_states.bond') }}</p>
        </div>
        <div v-else-if="bondError" class="error-state">
            <p class="error-message">{{ bondError }}</p>
        </div>
        <div v-else class="bond-data">
            <div v-if="activeBondCategory" class="category-section">
                <h3 class="category-title">{{ getCategoryLabel(activeBondCategory) }}</h3>
                <div class="indicators-grid">
                    <div v-for="item in bondData[activeBondCategory]" :key="item.title" class="bond-card">
                        <h4>{{ item.title }}</h4>
                        <div class="card-content">
                            <p class="value">{{ item.current_value?.toFixed(3) }}%</p>
                            <p class="date">{{ item.current_date }}</p>
                            <p class="desc">
                                {{ item.description }}
                                <span v-if="getBondDailyChange(item)" :class="['daily-change', getBondDailyChange(item) > 0 ? 'positive' : 'negative']">
                                    {{ getBondDailyChange(item) > 0 ? '+' : '' }}{{ getBondDailyChange(item).toFixed(2) }}%
                                </span>
                            </p>
                            <div class="card-timeframe-selector">
                                <button 
                                    v-for="tf in getBondTimeframes()" 
                                    :key="tf.value"
                                    :class="{ active: item.selectedTimeframe === tf.value }"
                                    @click="updateBondItemTimeframe(item, tf.value)"
                                >
                                    {{ tf.label }}
                                </button>
                            </div>
                        </div>
                        <div class="chart-container" v-if="item.history && item.history.length > 0">
                            <div v-if="item.loading" class="chart-loading-overlay">
                                <span>Loading...</span>
                            </div>
                            <Line :data="getBondChartData(item)" :options="bondChartOptions" />
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
import { useI18n } from 'vue-i18n';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend
} from 'chart.js'
import { Line } from 'vue-chartjs'
import { getDailyCache, setDailyCache, clearCacheByKey } from '../../utils/dailyCache.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend
)

const { t } = useI18n();

// Bond cache configuration
const BOND_CACHE_EXPIRATION = 30 * 60 * 1000; // 30 minutes
const BOND_CACHE_KEY_PREFIX = 'bond_series_';

const getBondCacheKey = (seriesId, timeframe) => `${BOND_CACHE_KEY_PREFIX}${seriesId}_${timeframe}`;

const getBondCachedData = (seriesId, timeframe) => {
    try {
        const key = getBondCacheKey(seriesId, timeframe);
        const cached = localStorage.getItem(key);
        if (!cached) return null;
        
        const { data, timestamp } = JSON.parse(cached);
        if (Date.now() - timestamp < BOND_CACHE_EXPIRATION) {
            return data;
        }
        localStorage.removeItem(key);
        return null;
    } catch (e) {
        return null;
    }
};

const setBondCachedData = (seriesId, timeframe, data) => {
    try {
        const key = getBondCacheKey(seriesId, timeframe);
        localStorage.setItem(key, JSON.stringify({
            data,
            timestamp: Date.now()
        }));
    } catch (e) {
        console.error('Cache write error', e);
    }
};

// Bond Tab State
const bondData = ref({
  treasury_yields: [],
  yield_curve: [],
  tips_breakeven: [],
  central_bank_rates: [],
  credit_spreads: [],
  funding_stress: []
});
const bondLoading = ref(false);
const bondError = ref(null);
const activeBondCategory = ref('treasury_yields');

// We use a function or computed for timeframes/categories to ensure reactivity with language change
const getBondTimeframes = () => [
  { label: t('dashboard.timeframes.monthly'), value: 'daily' },
  { label: t('dashboard.timeframes.quarterly'), value: 'weekly' },
  { label: t('dashboard.timeframes.yearly'), value: 'monthly' },
  { label: t('dashboard.timeframes.5y'), value: 'yearly' },
  { label: t('dashboard.timeframes.max'), value: 'max' }
];

const getBondCategories = () => [
  { label: t('dashboard.bond_categories.treasury_yields'), value: 'treasury_yields' },
  { label: t('dashboard.bond_categories.yield_curve'), value: 'yield_curve' },
  { label: t('dashboard.bond_categories.tips_breakeven'), value: 'tips_breakeven' },
  { label: t('dashboard.bond_categories.central_bank_rates'), value: 'central_bank_rates' },
  { label: t('dashboard.bond_categories.credit_spreads'), value: 'credit_spreads' },
  { label: t('dashboard.bond_categories.funding_stress'), value: 'funding_stress' }
];

const getCategoryLabel = (value) => {
    const category = getBondCategories().find(c => c.value === value);
    return category ? category.label : '';
};

const bondChartOptions = {
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

const getBondChartData = (item) => {
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

const getBondDailyChange = (item) => {
    if (!item.history || item.history.length < 2) {
        return null;
    }
    
    const sortedHistory = [...item.history].sort((a, b) => new Date(a.date) - new Date(b.date));
    const currentPrice = sortedHistory[sortedHistory.length - 1]?.value;
    const previousPrice = sortedHistory[sortedHistory.length - 2]?.value;
    
    if (!currentPrice || !previousPrice || previousPrice === 0) {
        return null;
    }
    
    const change = ((currentPrice - previousPrice) / previousPrice) * 100;
    return change;
}

const fetchBondData = async () => {
  bondLoading.value = true;
  bondError.value = null;
  
  // Check daily cache first
  const cached = getDailyCache('bond_data_monthly');
  if (cached) {
    console.log('Using cached bond data');
    bondData.value = cached;
    bondLoading.value = false;
    return;
  }
  
  try {
    // Initial fetch of all data with default 'monthly' (1Y) timeframe
    const response = await fetch(`${API_BASE_URL}/api/market/bond/all?timeframe=monthly`);
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
    bondError.value = err.message;
  } finally {
    bondLoading.value = false;
  }
};

const updateBondItemTimeframe = async (item, timeframe) => {
    if (item.selectedTimeframe === timeframe) return;
    
    item.selectedTimeframe = timeframe;
    item.loading = true;
    
    // Check cache
    const cached = getBondCachedData(item.series_id, timeframe);
    if (cached) {
        Object.assign(item, cached);
        item.selectedTimeframe = timeframe; // Ensure this stays set
        item.loading = false;
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/market/bond/series/${item.series_id}?timeframe=${timeframe}`);
        if (!response.ok) throw new Error('Failed to fetch series');
        const data = await response.json();
        
        // Update item properties with new data
        Object.assign(item, data);
        item.selectedTimeframe = timeframe; // Ensure this stays set
        
        setBondCachedData(item.series_id, timeframe, data);
    } catch (err) {
        console.error(`Error fetching ${item.title}:`, err);
    } finally {
        item.loading = false;
    }
};

const refresh = async () => {
  clearCacheByKey('bond_data_monthly');
  await fetchBondData();
};

onMounted(() => {
    fetchBondData();
});

defineExpose({
    refresh
});
</script>

<style scoped>
.bond-section {
    width: 100%;
}

.category-tabs {
    display: flex;
    overflow-x: auto;
    border-bottom: 2px solid #e5e5e5;
    margin-bottom: 20px;
    padding-bottom: 0;
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
    white-space: nowrap;
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
    min-height: 400px;
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
    gap: 8px;
}

.daily-change {
    font-size: 0.95em;
    font-weight: 600;
    font-style: normal;
    padding: 2px 6px;
    border-radius: 4px;
}

.daily-change.positive {
    color: #27ae60;
    background: rgba(39, 174, 96, 0.1);
}

.daily-change.negative {
    color: #c0392b;
    background: rgba(192, 57, 43, 0.1);
}

.card-timeframe-selector {
    display: flex;
    justify-content: center;
    gap: 8px;
    margin-bottom: 16px;
    flex-wrap: wrap;
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
    height: 200px;
    width: 100%;
    position: relative;
}

.chart-loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.7);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 10;
}

.no-data {
    height: 200px;
    display: flex;
    justify-content: center;
    align-items: center;
    color: #666666;
    font-style: italic;
    background: #f8f9fa;
    border-radius: 8px;
}

.loading-state, .error-state {
    color: #000000;
    text-align: center;
    padding: 40px;
}

.error-message {
    color: #e74c3c;
}
</style>
