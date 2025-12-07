<template>
  <div class="energy-view">
    <div class="page-header">
      <h2>Energy Dashboard</h2>
      <button @click="updateData" :disabled="loading" class="update-btn">
        {{ loading ? 'Updating...' : 'Update Data' }}
      </button>
    </div>
    <div v-if="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="energy-layout">
      <!-- Main Content Area -->
      <div class="main-content">
        <!-- Energy Prices (Line) -->
        <div class="card full-width">
          <h3>Energy Prices</h3>
          
          <div class="timeframe-selector">
              <button 
                  v-for="tf in priceTimeframes" 
                  :key="tf.value" 
                  :class="{ active: selectedPriceTimeframe === tf.value }"
                  @click="changePriceTimeframe(tf.value)"
              >
                  {{ tf.label }}
              </button>
          </div>

          <div class="chart-container">
            <Line :data="priceData" :options="priceChartOptions" />
          </div>
        </div>

        <!-- Grid Status (Bar/Metrics) -->
        <div class="card grid-status">
          <h3>Grid Status</h3>
          <div class="metrics">
              <p><strong>Capacity:</strong> {{ gridData.capacity }} MW</p>
              <p><strong>Current Demand:</strong> {{ gridData.current_demand }} MW</p>
              <p><strong>Outages:</strong> {{ gridData.outages }}</p>
              <p><strong>Reliability:</strong> {{ gridData.reliability }}%</p>
          </div>
          
          <div class="timeframe-selector">
              <button 
                  v-for="tf in timeframes" 
                  :key="tf.value" 
                  :class="{ active: selectedTimeframe === tf.value }"
                  @click="changeTimeframe(tf.value)"
              >
                  {{ tf.label }}
              </button>
          </div>

          <div class="chart-container-small">
               <Line :data="demandCurveData" :options="lineOptions" />
          </div>
        </div>
      </div>

      <!-- Right Sidebar -->
      <div class="sidebar">
        <!-- Generation Mix (Doughnut) -->
        <div class="card">
          <h3>Generation by Fuel Type</h3>
          <div class="chart-container">
            <Doughnut :data="generationData" :options="pieOptions" />
          </div>
        </div>

        <!-- Consumption by Sector (Pie) -->
        <div class="card">
          <h3>Consumption by Sector</h3>
          <div class="chart-container">
            <Pie :data="consumptionData" :options="pieOptions" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title
} from 'chart.js'
import { Doughnut, Pie, Line } from 'vue-chartjs'
import { getDailyCache, setDailyCache, clearCacheByKey } from '../utils/dailyCache.js'

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, PointElement, LineElement, Title)

const loading = ref(true);
const error = ref(null);
const generation = ref([]);
const consumption = ref([]);
const gridData = ref({});
const prices = ref([]);

const selectedTimeframe = ref('realtime');
const timeframes = [
    { label: 'Real-time', value: 'realtime' },
    { label: 'Days', value: 'days' },
    { label: 'Monthly', value: 'monthly' },
    { label: 'Yearly', value: 'yearly' },
    { label: '5 Years', value: '5y' }
];

const selectedPriceTimeframe = ref('days');
const priceTimeframes = [
    { label: 'Days', value: 'days' },
    { label: 'Weekly', value: 'weekly' },
    { label: 'Monthly', value: 'monthly' },
    { label: 'Yearly', value: 'yearly' },
    { label: '5 Years', value: '5y' }
];

const pieOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
      legend: {
          position: 'right',
          labels: { color: 'white' }
      },
      tooltip: {
          callbacks: {
              label: function(context) {
                  const label = context.label || '';
                  const value = context.raw || 0;
                  const total = context.chart._metasets[context.datasetIndex].total;
                  const percentage = Math.round((value / total) * 100) + '%';
                  return `${label}: ${value} (${percentage})`;
              }
          }
      }
  }
};

const lineOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
      y: { ticks: { color: '#666666' }, grid: { color: 'rgba(0, 0, 0, 0.1)' } },
      x: { ticks: { color: '#666666' }, grid: { color: 'rgba(0, 0, 0, 0.1)' } }
  },
  plugins: {
      legend: { labels: { color: '#000000' } }
  }
};

const generationData = computed(() => ({
    labels: generation.value.map(i => i.type),
    datasets: [{
        data: generation.value.map(i => i.value),
        backgroundColor: generation.value.map(i => i.color)
    }]
}));

const consumptionData = computed(() => ({
    labels: consumption.value.map(i => i.sector),
    datasets: [{
        data: consumption.value.map(i => i.value),
        backgroundColor: consumption.value.map(i => i.color)
    }]
}));

const demandCurveData = computed(() => {
    if (!gridData.value.hourly_demand) return { labels: [], datasets: [] };
    return {
        labels: gridData.value.hourly_demand.map(i => i.time),
        datasets: [{
            label: 'Demand (MW)',
            data: gridData.value.hourly_demand.map(i => i.demand),
            borderColor: '#3498db',
            backgroundColor: '#3498db',
            fill: false,
            tension: 0.4
        }]
    };
});

const priceData = computed(() => ({
    labels: prices.value.map(i => i.date),
    datasets: [
        {
            label: 'Oil Price ($)',
            data: prices.value.map(i => i.oil),
            borderColor: '#e74c3c',
            backgroundColor: '#e74c3c',
            tension: 0.1,
            yAxisID: 'y'
        },
        {
            label: 'Natural Gas ($)',
            data: prices.value.map(i => i.gas),
            borderColor: '#f1c40f',
            backgroundColor: '#f1c40f',
            tension: 0.1,
            yAxisID: 'y1'
        }
    ]
}));

// Update lineOptions to support dual axis for prices
const priceChartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  scales: {
      y: { 
          type: 'linear',
          display: true,
          position: 'left',
          ticks: { color: '#e74c3c' }, 
          grid: { color: 'rgba(0, 0, 0, 0.1)' },
          title: { display: true, text: 'Oil ($)', color: '#e74c3c' }
      },
      y1: {
          type: 'linear',
          display: true,
          position: 'right',
          ticks: { color: '#f1c40f' },
          grid: { drawOnChartArea: false }, // only want the grid lines for one axis to show up
          title: { display: true, text: 'Gas ($)', color: '#f1c40f' }
      },
      x: { ticks: { color: '#666666' }, grid: { color: 'rgba(0, 0, 0, 0.1)' } }
  },
  plugins: {
      legend: { labels: { color: '#000000' } }
  }
}));


const fetchGridData = async (timeframe) => {
    try {
        const res = await fetch(`http://localhost:8000/api/energy/grid?timeframe=${timeframe}`);
        if (!res.ok) throw new Error("Failed to fetch grid data");
        gridData.value = await res.json();
    } catch (err) {
        console.error(err);
    }
};

const fetchPriceData = async (timeframe) => {
    try {
        const res = await fetch(`http://localhost:8000/api/energy/prices?timeframe=${timeframe}`);
        if (!res.ok) throw new Error("Failed to fetch price data");
        prices.value = await res.json();
    } catch (err) {
        console.error(err);
    }
};

const changeTimeframe = (timeframe) => {
    selectedTimeframe.value = timeframe;
    fetchGridData(timeframe);
};

const changePriceTimeframe = (timeframe) => {
    selectedPriceTimeframe.value = timeframe;
    fetchPriceData(timeframe);
};

const fetchData = async () => {
    // Check daily cache first
    const cachedGeneration = getDailyCache('energy_generation');
    const cachedConsumption = getDailyCache('energy_consumption');
    
    if (cachedGeneration && cachedConsumption) {
        console.log('Using cached energy data');
        generation.value = cachedGeneration;
        consumption.value = cachedConsumption;
        
        // Still fetch grid and price data with their timeframes
        await fetchGridData(selectedTimeframe.value);
        await fetchPriceData(selectedPriceTimeframe.value);
        
        loading.value = false;
        return;
    }
    
    try {
        const [genRes, conRes] = await Promise.all([
            fetch('http://localhost:8000/api/energy/generation'),
            fetch('http://localhost:8000/api/energy/consumption')
        ]);

        if (!genRes.ok || !conRes.ok) throw new Error("Failed to fetch energy data");

        const genData = await genRes.json();
        const conData = await conRes.json();
        
        generation.value = genData;
        consumption.value = conData;
        
        // Cache the data
        setDailyCache('energy_generation', genData);
        setDailyCache('energy_consumption', conData);
        
        // Fetch initial data
        await fetchGridData(selectedTimeframe.value);
        await fetchPriceData(selectedPriceTimeframe.value);

    } catch (err) {
        error.value = err.message;
    } finally {
        loading.value = false;
    }
};

const updateData = async () => {
    clearCacheByKey('energy_generation');
    clearCacheByKey('energy_consumption');
    await fetchData();
};


onMounted(() => {
    fetchData();
});
</script>

<style scoped>
.energy-view {
  padding: 20px 20px 20px 0;
  width: 100%;
  box-sizing: border-box;
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

.energy-layout {
  display: flex;
  gap: 15px;
  width: 100%;
  box-sizing: border-box;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 15px;
  min-width: 0;
}

.sidebar {
  flex: 0 0 25%;
  display: flex;
  flex-direction: column;
  gap: 15px;
  min-width: 300px;
}

@media (max-width: 1200px) {
  .energy-layout {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
    display: grid;
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .sidebar {
    grid-template-columns: 1fr;
  }
}

.card {
  background: #ffffff;
  color: #000000;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #cccccc;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.card h3 {
  color: #000000;
  font-weight: 600;
  margin: 0 0 15px 0;
}

.full-width {
  width: 100%;
}
.chart-container {
    height: 300px;
    position: relative;
}

.sidebar .chart-container {
    height: 250px;
}
.chart-container-small {
    height: 200px;
    margin-top: 20px;
}
.metrics p {
    margin: 5px 0;
    color: #000000;
}

.metrics strong {
    color: #000000;
}
.timeframe-selector {
    display: flex;
    gap: 10px;
    margin: 15px 0;
    justify-content: center;
}
.timeframe-selector button {
    background: #f8f9fa;
    border: 1px solid #cccccc;
    color: #000000;
    padding: 5px 10px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.8em;
    transition: all 0.2s;
}
.timeframe-selector button.active {
    background: #3498db;
    color: white;
    border-color: #3498db;
}
.timeframe-selector button:hover {
    background: #e9ecef;
}
.error {
    color: red;
}
</style>
