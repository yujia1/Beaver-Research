<template>
  <div class="indices-section">
    <div class="index-card" v-for="index in indices" :key="index.name">
        <h3>{{ index.name }}</h3>
        <div class="index-value" :class="{ 'positive': index.change >= 0, 'negative': index.change < 0 }">
            <span class="value">{{ index.value.toLocaleString() }}</span>
            <span class="change">
                <span v-if="index.change > 0">+</span>
                {{ index.change }}%
            </span>
        </div>
        <div class="mini-chart">
            <Line :data="getIndexChartData(index)" :options="miniChartOptions" />
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

// Market indices data
const indices = ref([
    { name: 'Dow Jones', value: 0, change: 0, history: [] },
    { name: 'NASDAQ', value: 0, change: 0, history: [] },
    { name: 'S&P 500', value: 0, change: 0, history: [] },
    { name: 'Russell 2000', value: 0, change: 0, history: [] }
]);

const miniChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: { 
      enabled: true,
      mode: 'index',
      intersect: false
    }
  },
  scales: {
    x: { 
      display: true,
      grid: { color: 'rgba(0, 0, 0, 0.1)' },
      ticks: { 
        color: '#666666',
        font: { size: 9 },
        maxTicksLimit: 5
      }
    },
    y: { 
      display: true,
      grid: { color: 'rgba(0, 0, 0, 0.1)' },
      ticks: { 
        color: '#666666',
        font: { size: 9 },
        callback: function(value) {
          return value.toLocaleString();
        }
      }
    }
  },
  elements: {
    point: { radius: 0, hitRadius: 10, hoverRadius: 4 },
    line: { borderWidth: 2, tension: 0.3 }
  }
};

const getIndexChartData = (index) => {
    if (!index.history || index.history.length === 0) {
        return {
            labels: [],
            datasets: [{
                borderColor: index.change >= 0 ? '#42b983' : '#e74c3c',
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
            borderColor: index.change >= 0 ? '#42b983' : '#e74c3c',
            data: index.history.map(item => item.value),
            fill: false
        }]
    };
};

const fetchIndices = async () => {
    // Check cache first
    const cached = getDailyCache('indices_data');
    if (cached) {
        console.log('Using cached indices data');
        indices.value = cached;
        return;
    }
    
    // Fetch fresh data if no cache
    try {
        const response = await fetch('${API_BASE_URL}/api/internal/indices');
        if (!response.ok) throw new Error('Failed to fetch indices');
        const data = await response.json();
        indices.value = data;
        
        // Cache the data
        setDailyCache('indices_data', data);
    } catch (e) {
        console.error('Error fetching indices:', e);
    }
};

const refresh = async () => {
    clearCacheByKey('indices_data');
    await fetchIndices();
};

onMounted(() => {
    fetchIndices();
});

defineExpose({
    refresh
});
</script>

<style scoped>
.indices-section {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
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

.index-card h3 {
    margin: 0 0 10px 0;
    color: #2c3e50;
    font-size: 1.1em;
    font-weight: 600;
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
    font-size: 1.1em;
    font-weight: 600;
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
    height: 100px;
    width: 100%;
}
</style>
