<template>
  <div class="indices-container">
    <!-- Regional Tabs -->
    <div class="region-tabs">
        <button 
            v-for="region in regions" 
            :key="region"
            class="region-btn"
            :class="{ active: activeRegion === region }"
            @click="activeRegion = region"
        >
            {{ getRegionLabel(region) }}
        </button>
    </div>

    <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>{{ t('dashboard.loading') }}</p>
    </div>
    <div v-else-if="error" class="error-state">
        <p>{{ error }}</p>
    </div>

    <!-- Indices Cards -->
    <div v-else class="indices-grid">
      <div class="index-card" v-for="index in displayedIndices" :key="index.symbol">
          <div class="card-header">
              <div class="header-top">
                  <h3>{{ index.name }}</h3>
              </div>
              <div class="timeframe-selector">
                  <button 
                      v-for="tf in ['1M', '3M', '1Y', '5Y', 'Max']" 
                      :key="tf"
                      class="tf-btn"
                      :class="{ active: index.selectedTimeframe === tf }"
                      @click="updateIndexTimeframe(index, tf)"
                      :disabled="index.loading"
                  >
                      {{ tf }}
                  </button>
              </div>
          </div>
          
          <div class="index-value" :class="{ 'positive': index.change >= 0, 'negative': index.change < 0 }">
              <div v-if="index.loading" class="mini-spinner"></div>
              <template v-else>
                  <span class="value">{{ index.price.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) }}</span>
                  <span class="change">
                      <span v-if="index.change > 0">+</span>
                      {{ index.change }} ({{ index.changePercent }}%)
                  </span>
              </template>
          </div>
          <div class="mini-chart" :class="{ 'loading-chart': index.loading }">
              <Line :data="getIndexChartData(index)" :options="miniChartOptions" />
          </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import API_BASE_URL from '@/config/api.js'

import { ref, onMounted, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import { Line } from 'vue-chartjs'
import { getDailyCache, setDailyCache, clearCacheByKey } from '../../utils/dailyCache.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  Filler
)

const { t } = useI18n();

const regions = ['United States', 'Europe', 'Asia-Pacific'];
const activeRegion = ref('United States');
const loading = ref(false);
const error = ref(null);
const allRegionalIndices = ref({});

const getRegionLabel = (region) => {
    const key = region.toLowerCase().replace(/\s+/g, '_').replace(/-/g, '_');
    return t(`dashboard.regions.${key}`);
};

const displayedIndices = computed(() => {
    return allRegionalIndices.value[activeRegion.value] || [];
});

const miniChartOptions = {
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
      padding: 12,
      callbacks: {
          label: function(context) {
              let label = context.dataset.label || '';
              if (label) {
                  label += ': ';
              }
              if (context.parsed.y !== null) {
                  label += context.parsed.y.toLocaleString();
              }
              return label;
          }
      }
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
      position: 'right',
      ticks: { 
        color: '#666666', 
        font: { size: 10 },
        callback: function(value) {
            if (value >= 1000) return (value/1000).toFixed(1) + 'k';
            return value;
        }
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
  },
  interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false
  }
};

const getIndexChartData = (index) => {
    if (!index.history || index.history.length === 0) {
        return {
            labels: [],
            datasets: [{
                borderColor: '#ccc',
                data: [],
                fill: false
            }]
        };
    }
    
    return {
        labels: index.history.map(item => {
            const date = new Date(item.date);
            return `${date.getMonth() + 1}/${date.getDate()}`;
        }),
        datasets: [{
            label: 'Price',
            borderColor: index.change >= 0 ? '#42b983' : '#e74c3c',
            backgroundColor: index.change >= 0 ? '#42b983' : '#e74c3c',
            data: index.history.map(item => item.price),
            fill: false
        }]
    };
};

const fetchIndices = async () => {
    loading.value = true;
    error.value = null;
    
    // Check cache first
    const cached = getDailyCache('indices_regional_data');
    if (cached) {
        console.log('Using cached regional indices data');
        allRegionalIndices.value = cached;
        // Initialize default timeframe for each index if not present
        Object.values(allRegionalIndices.value).flat().forEach(idx => {
             if (!idx.selectedTimeframe) idx.selectedTimeframe = '1Y';
        });
        loading.value = false;
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/market/equity/indices/regional`);
        if (!response.ok) throw new Error('Failed to fetch regional indices');
        const data = await response.json();
        
        // Add default timeframe property
        Object.keys(data).forEach(region => {
            data[region] = data[region].map(idx => ({ ...idx, selectedTimeframe: '1Y' }));
        });
        
        allRegionalIndices.value = data;
        
        // Ensure active region has data, otherwise switch to first available
        if (!data[activeRegion.value] && Object.keys(data).length > 0) {
            activeRegion.value = Object.keys(data)[0];
        }
        
        // Cache the data
        setDailyCache('indices_regional_data', data);
    } catch (e) {
        console.error('Error fetching indices:', e);
        error.value = 'Failed to load market data';
    } finally {
        loading.value = false;
    }
};

const updateIndexTimeframe = async (index, timeframe) => {
    if (index.selectedTimeframe === timeframe) return;
    
    index.selectedTimeframe = timeframe;
    index.loading = true; // Add temporary loading state to the index object
    
    try {
        const encodedSymbol = encodeURIComponent(index.symbol);
        const response = await fetch(`${API_BASE_URL}/api/market/equity/indices/regional/series/${encodedSymbol}?timeframe=${timeframe}`);
        
        if (!response.ok) throw new Error('Failed to fetch index history');
        
        const data = await response.json();
        
        // Update index data with new history
        if (data.history && data.history.length > 0) {
            index.history = data.history;
            index.price = data.price;
            index.change = data.change;
            index.changePercent = data.changePercent;
        }
    } catch (e) {
        console.error(`Error updating timeframe for ${index.symbol}:`, e);
    } finally {
        index.loading = false;
    }
};

const refresh = async () => {
    clearCacheByKey('indices_regional_data');
    await fetchIndices();
};

onMounted(() => {
    fetchIndices();
});

const updateData = (newData) => {
    if (!newData) return;
    
    // Intelligent merge: Only update prices/stats, preserve history if timeframe differs
    Object.keys(newData).forEach(region => {
        // If region doesn't exist in current, simple add (though unlikely if static regions)
        if (!allRegionalIndices.value[region]) {
            // Initialize with default timeframe
             allRegionalIndices.value[region] = newData[region].map(idx => ({ 
                 ...idx, 
                 selectedTimeframe: '1Y' 
             }));
             return;
        }

        const currentIndices = allRegionalIndices.value[region];
        const newIndices = newData[region];
        
        newIndices.forEach(newIdx => {
            const currentIdx = currentIndices.find(c => c.symbol === newIdx.symbol);
            if (currentIdx) {
                // Update live stats
                currentIdx.price = newIdx.price;
                currentIdx.change = newIdx.change;
                currentIdx.changePercent = newIdx.changePercent;
                
                // Only update history if the user is viewing the default 1Y timeframe
                // The scheduled job fetches the default 1Y view.
                if (currentIdx.selectedTimeframe === '1Y') {
                    currentIdx.history = newIdx.history;
                }
            } else {
                // New index appeared in list
                currentIndices.push({ ...newIdx, selectedTimeframe: '1Y' });
            }
        });
    });
};

defineExpose({
    refresh,
    updateData
});
</script>

<style scoped>
.indices-container {
    display: flex;
    flex-direction: column;
    gap: 20px;
    margin-bottom: 30px;
}

.region-tabs {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    padding-bottom: 15px;
    border-bottom: 1px solid #eee;
}

.region-btn {
    padding: 8px 16px;
    background: #f5f7fa;
    border: 1px solid #e1e4e8;
    border-radius: 20px;
    cursor: pointer;
    font-size: 0.9rem;
    color: #5c6c7f;
    transition: all 0.2s;
}

.region-btn:hover {
    background: #e8eaed;
    color: #2c3e50;
}

.region-btn.active {
    background: #2c3e50;
    color: white;
    border-color: #2c3e50;
}

.indices-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
}

.index-card {
    background: white;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
    border: 1px solid rgba(0, 0, 0, 0.05);
    transition: transform 0.2s, box-shadow 0.2s;
}

.index-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 10px;
}

.index-card h3 {
    margin: 0;
    color: #2c3e50;
    font-size: 1.1em;
    font-weight: 600;
}

.symbol {
    font-size: 0.8em;
    color: #95a5a6;
    background: #f0f2f5;
    padding: 2px 6px;
    border-radius: 4px;
}

.index-value {
    display: flex;
    align-items: baseline;
    gap: 10px;
    margin-bottom: 15px;
}

.index-value .value {
    font-size: 1.8em;
    font-weight: 700;
    color: #2c3e50;
}

.index-value .change {
    font-size: 1em;
    font-weight: 500;
    padding: 4px 8px;
    border-radius: 6px;
}

.index-value.positive .change {
    color: #27ae60;
    background: rgba(39, 174, 96, 0.1);
}

.index-value.negative .change {
    color: #c0392b;
    background: rgba(192, 57, 43, 0.1);
}

.mini-chart {
    height: 200px;
    width: 100%;
}

.loading-state {
    text-align: center;
    padding: 40px;
    color: #95a5a6;
}

.error-state {
    text-align: center;
    padding: 40px;
    color: #e74c3c;
    background: #fdf0ef;
    border-radius: 8px;
}

.spinner {
    border: 3px solid #f3f3f3;
    border-radius: 50%;
    border-top: 3px solid #3498db;
    width: 24px;
    height: 24px;
    margin: 0 auto 15px;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.header-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
}

.card-header {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.timeframe-selector {
    display: flex;
    gap: 5px;
    background: #f8f9fa;
    padding: 3px;
    border-radius: 6px;
    align-self: flex-start;
}

.tf-btn {
    border: none;
    background: transparent;
    padding: 2px 8px;
    font-size: 0.75rem;
    color: #95a5a6;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
}

.tf-btn:hover:not(:disabled) {
    color: #2c3e50;
    background: rgba(0,0,0,0.05);
}

.tf-btn.active {
    background: white;
    color: #2c3e50;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    font-weight: 500;
}

.tf-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.mini-spinner {
    border: 2px solid #f3f3f3;
    border-top: 2px solid #3498db;
    border-radius: 50%;
    width: 16px;
    height: 16px;
    animation: spin 1s linear infinite;
    margin-right: 10px;
}

.loading-chart {
    opacity: 0.5;
    pointer-events: none;
    filter: grayscale(1);
}
</style>
