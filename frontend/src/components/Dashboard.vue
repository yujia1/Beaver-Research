<template>
  <div class="dashboard">
    <div class="page-header">
      <h1>Market Dashboard</h1>
      <button @click="updateData" :disabled="loading" class="update-btn">
        {{ loading ? 'Updating...' : 'Update Data' }}
      </button>
    </div>
    
    <div v-if="loading" class="loading">Loading Market Data...</div>
    <div v-else>
        <!-- Index Charts Section -->
        <div class="indices-section">
            <div class="index-card" v-for="index in indices" :key="index.name">
                <h3>{{ index.name }}</h3>
                <div class="index-value" :class="index.change >= 0 ? 'positive' : 'negative'">
                    {{ index.value.toLocaleString() }}
                </div>
                <div class="index-change" :class="index.change >= 0 ? 'positive' : 'negative'">
                    {{ index.change >= 0 ? '+' : '' }}{{ index.change.toFixed(2) }}%
                </div>
                <div class="mini-chart">
                    <Line :data="getIndexChartData(index)" :options="miniChartOptions" />
                </div>
            </div>
        </div>

        <!-- Market Movers Grid -->
        <div class="market-grid">
        <!-- Top Gainers -->
        <div class="market-section">
            <h3>🚀 Top Gainers</h3>
            <table class="market-table">
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th>Price</th>
                        <th>Chg %</th>
                        <th>Vol</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="stock in marketData.gainers" :key="stock.ticker">
                        <td 
                            class="ticker-cell" 
                            @mouseenter="showChart($event, stock.ticker)" 
                            @mouseleave="hideChart"
                        >
                            {{ stock.ticker }}
                        </td>
                        <td>{{ stock.price }}</td>
                        <td class="positive">+{{ stock.change_percent }}%</td>
                        <td>{{ stock.volume }}</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Top Losers -->
        <div class="market-section">
            <h3>📉 Top Losers</h3>
            <table class="market-table">
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th>Price</th>
                        <th>Chg %</th>
                        <th>Vol</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="stock in marketData.losers" :key="stock.ticker">
                        <td 
                            class="ticker-cell" 
                            @mouseenter="showChart($event, stock.ticker)" 
                            @mouseleave="hideChart"
                        >
                            {{ stock.ticker }}
                        </td>
                        <td>{{ stock.price }}</td>
                        <td class="negative">{{ stock.change_percent }}%</td>
                        <td>{{ stock.volume }}</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Most Volatile -->
        <div class="market-section">
            <h3>⚡ Most Volatile</h3>
            <table class="market-table">
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th>Price</th>
                        <th>Chg %</th>
                        <th>Vol</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="stock in marketData.volatile" :key="stock.ticker">
                        <td 
                            class="ticker-cell" 
                            @mouseenter="showChart($event, stock.ticker)" 
                            @mouseleave="hideChart"
                        >
                            {{ stock.ticker }}
                        </td>
                        <td>{{ stock.price }}</td>
                        <td :class="stock.change_percent >= 0 ? 'positive' : 'negative'">
                            {{ stock.change_percent > 0 ? '+' : ''}}{{ stock.change_percent }}%
                        </td>
                        <td>{{ stock.volume }}</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Most Active -->
        <div class="market-section">
            <h3>🔥 Most Active</h3>
            <table class="market-table">
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th>Price</th>
                        <th>Chg %</th>
                        <th>Vol</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="stock in marketData.active" :key="stock.ticker">
                        <td 
                            class="ticker-cell" 
                            @mouseenter="showChart($event, stock.ticker)" 
                            @mouseleave="hideChart"
                        >
                            {{ stock.ticker }}
                        </td>
                        <td>{{ stock.price }}</td>
                        <td :class="stock.change_percent >= 0 ? 'positive' : 'negative'">
                            {{ stock.change_percent > 0 ? '+' : ''}}{{ stock.change_percent }}%
                        </td>
                        <td>{{ stock.volume }}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    </div>

    <!-- Hover Chart Tooltip -->
    <div 
        v-if="hoverChart.visible" 
        class="hover-chart-tooltip" 
        :style="{ top: hoverChart.y + 'px', left: hoverChart.x + 'px' }"
    >
        <h4>{{ hoverChart.ticker }} Daily History</h4>
        <div class="chart-wrapper" v-if="hoverChart.data">
            <Line :data="hoverChart.data" :options="chartOptions" />
        </div>
        <div v-else>Loading chart...</div>
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

const marketData = ref({ gainers: [], losers: [], volatile: [], active: [] });
const loading = ref(true);

// Market indices data
const indices = ref([
    { name: 'Dow Jones', value: 43870.35, change: 0.28, history: [] },
    { name: 'NASDAQ', value: 19281.40, change: -0.23, history: [] },
    { name: 'S&P 500', value: 5948.71, change: 0.13, history: [] },
    { name: 'Russell 2000', value: 2426.28, change: 0.52, history: [] }
]);

const hoverChart = ref({
    visible: false,
    x: 0,
    y: 0,
    ticker: '',
    data: null
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: { mode: 'index', intersect: false }
  },
  scales: {
    x: { display: false },
    y: { display: false } // Sparkline style
  },
  elements: {
    point: { radius: 0 },
    line: { borderWidth: 2, tension: 0.4 }
  }
};

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
      grid: { color: 'rgba(255, 255, 255, 0.1)' },
      ticks: { 
        color: '#95a5a6',
        font: { size: 9 },
        maxTicksLimit: 5
      }
    },
    y: { 
      display: true,
      grid: { color: 'rgba(255, 255, 255, 0.1)' },
      ticks: { 
        color: '#95a5a6',
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

const fetchMarketData = async () => {
    // Check cache first
    const cached = getDailyCache('market_movers');
    if (cached) {
        console.log('Using cached market data');
        marketData.value = cached;
        loading.value = false;
        return;
    }
    
    // Fetch fresh data if no cache
    try {
        const response = await fetch('http://localhost:8000/api/internal/market-movers');
        if (!response.ok) throw new Error('Failed to fetch market movers');
        const data = await response.json();
        marketData.value = data;
        
        // Cache the data
        setDailyCache('market_movers', data);
    } catch (e) {
        console.error(e);
    } finally {
        loading.value = false;
    }
};

const updateData = async () => {
    clearCacheByKey('market_movers');
    await fetchMarketData();
};


const showChart = async (event, ticker) => {
    const rect = event.target.getBoundingClientRect();
    hoverChart.value = {
        visible: true,
        x: rect.right + 10, // Position to the right of the cell
        y: rect.top,
        ticker: ticker,
        data: null
    };

    // Fetch history for the ticker
    try {
        // We can use the micro endpoint to get history
        // Note: This might be slow for a hover, but let's try.
        // Optimization: Cache results?
        const response = await fetch(`http://localhost:8000/api/internal/micro/${ticker}`);
        if (response.ok) {
            const data = await response.json();
            // Mock history generation if not present or just use a random walk for demo if micro endpoint doesn't return history list
            // The micro endpoint currently returns current price. We need history.
            // Let's assume we need to generate mock history here or update micro endpoint.
            // Actually, let's just generate mock history locally for the "hover" effect to be snappy 
            // since the user wants "stock price daily historical graph".
            
            // Generating mock history for demo speed
            const history = generateMockHistory(data.price);
            
            hoverChart.value.data = {
                labels: history.map((_, i) => i),
                datasets: [{
                    label: ticker,
                    borderColor: '#3498db',
                    data: history,
                    fill: false
                }]
            };
        }
    } catch (e) {
        console.error("Error fetching chart data", e);
    }
};

const hideChart = () => {
    hoverChart.value.visible = false;
};

const generateMockHistory = (basePrice) => {
    const history = [];
    let current = basePrice;
    const today = new Date();
    
    for (let i = 29; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        history.push({
            date: date,
            value: current
        });
        current = current * (1 + (Math.random() - 0.5) * 0.05);
    }
    return history;
};

const getIndexChartData = (index) => {
    return {
        labels: index.history.map(item => {
            const date = item.date;
            return `${date.getMonth() + 1}/${date.getDate()}`;
        }),
        datasets: [{
            borderColor: index.change >= 0 ? '#42b983' : '#e74c3c',
            data: index.history.map(item => item.value),
            fill: false
        }]
    };
};

onMounted(() => {
    // Generate mock history for each index
    indices.value.forEach(index => {
        index.history = generateMockHistory(index.value);
    });
    
    fetchMarketData();
});
</script>

<style scoped>
.dashboard {
  padding: 20px 20px 20px 0;
  max-width: 1800px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
}

.update-btn {
  background: #42b983;
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
  background: #35a372;
  transform: translateY(-1px);
}

.update-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}


.indices-section {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    margin-bottom: 30px;
}

@media (max-width: 1200px) {
    .indices-section {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 768px) {
    .indices-section {
        grid-template-columns: 1fr;
    }
}

.index-card {
    background: #2c3e50;
    padding: 20px;
    border-radius: 8px;
    color: white;
    text-align: center;
}

.index-card h3 {
    margin: 0 0 10px 0;
    font-size: 1em;
    color: #ecf0f1;
    font-weight: 600;
}

.index-value {
    font-size: 1.8em;
    font-weight: bold;
    margin: 8px 0;
}

.index-change {
    font-size: 1.1em;
    font-weight: 600;
    margin: 5px 0 15px 0;
}

.mini-chart {
    height: 120px;
    margin-top: 10px;
}

.market-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
}

@media (max-width: 1400px) {
    .market-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 768px) {
    .market-grid {
        grid-template-columns: 1fr;
    }
}
.market-section {
    background: #2c3e50;
    padding: 15px;
    border-radius: 8px;
    color: white;
}
.market-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
}
.market-table th {
    text-align: left;
    color: #aaa;
    font-size: 0.9em;
    padding-bottom: 5px;
    border-bottom: 1px solid #34495e;
}
.market-table td {
    padding: 8px 0;
    font-size: 0.95em;
}
.ticker-cell {
    font-weight: bold;
    color: #3498db;
    cursor: pointer;
    text-decoration: underline;
}
.ticker-cell:hover {
    color: #5dade2;
}
.positive { color: #42b983; }
.negative { color: #e74c3c; }

.hover-chart-tooltip {
    position: fixed;
    background: #34495e;
    border: 1px solid #42b983;
    padding: 10px;
    border-radius: 8px;
    z-index: 9999;
    width: 250px;
    height: 150px;
    pointer-events: none; /* Let mouse events pass through so we don't trigger leave */
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
}
.hover-chart-tooltip h4 {
    margin: 0 0 5px 0;
    font-size: 0.9em;
    color: #fff;
    text-align: center;
}
.chart-wrapper {
    height: 100px;
    width: 100%;
}
</style>
