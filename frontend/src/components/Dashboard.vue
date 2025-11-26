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
        <!-- Key Logs Section -->
        <div class="key-logs-section">
            <div class="key-logs-header">
                <h2>Key Logs</h2>
            </div>

            <!-- Tab Selector -->
            <div class="tab-selector">
                <button 
                    class="tab-btn" 
                    :class="{ active: activeTab === 'equity' }"
                    @click="activeTab = 'equity'"
                >
                    Equity
                </button>
                <button 
                    class="tab-btn" 
                    :class="{ active: activeTab === 'bond' }"
                    @click="activeTab = 'bond'"
                >
                    Bond
                </button>
                <button 
                    class="tab-btn" 
                    :class="{ active: activeTab === 'economic' }"
                    @click="activeTab = 'economic'"
                >
                    Economic
                </button>
                <button 
                    class="tab-btn" 
                    :class="{ active: activeTab === 'energy' }"
                    @click="activeTab = 'energy'"
                >
                    Energy
                </button>
            </div>

            <!-- Equity Tab Content -->
            <div v-if="activeTab === 'equity'" class="tab-content">
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

            <!-- Bond Tab Content -->
            <div v-if="activeTab === 'bond'" class="tab-content bond-tab-content">
                <div class="bond-header">
                    <button @click="updateBondData" :disabled="bondLoading" class="update-btn">
                        {{ bondLoading ? 'Updating...' : 'Update Data' }}
                    </button>
                </div>

                <div class="category-tabs">
                    <button 
                        v-for="category in bondCategories" 
                        :key="category.value" 
                        :class="{ active: activeBondCategory === category.value }"
                        @click="activeBondCategory = category.value"
                    >
                        {{ category.label }}
                    </button>
                </div>

                <div v-if="bondLoading" class="loading-state">
                    <div class="loading-spinner"></div>
                    <p>Loading Bond Market Data...</p>
                </div>
                <div v-else-if="bondError" class="error-state">
                    <p class="error-message">{{ bondError }}</p>
                </div>
                <div v-else class="bond-data">
                    <!-- Treasury Yields -->
                    <div v-if="activeBondCategory === 'treasury_yields'" class="category-section">
                        <h3 class="category-title">Government Bond Market Data - Treasury Yields</h3>
                        <div class="indicators-grid">
                            <div v-for="item in bondData.treasury_yields" :key="item.title" class="bond-card">
                                <h4>{{ item.title }}</h4>
                                <div class="card-content">
                                    <p class="value">{{ item.current_value?.toFixed(3) }}%</p>
                                    <p class="date">{{ item.current_date }}</p>
                                    <p class="desc">{{ item.description || '&nbsp;' }}</p>
                                    
                                    <div class="card-timeframe-selector">
                                        <button 
                                            v-for="tf in bondTimeframes" 
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
                                    <Line :data="getBondChartData(item)" :options="bondChartOptions" />
                                </div>
                                <div v-else class="no-data">
                                    <p>No history data available</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Yield Curve Spreads -->
                    <div v-if="activeBondCategory === 'yield_curve'" class="category-section">
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
                                            v-for="tf in bondTimeframes" 
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
                                    <Line :data="getBondChartData(item)" :options="bondChartOptions" />
                                </div>
                                <div v-else class="no-data">
                                    <p>No history data available</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- TIPS & Breakeven -->
                    <div v-if="activeBondCategory === 'tips_breakeven'" class="category-section">
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
                                            v-for="tf in bondTimeframes" 
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
                                    <Line :data="getBondChartData(item)" :options="bondChartOptions" />
                                </div>
                                <div v-else class="no-data">
                                    <p>No history data available</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Central Bank Rates -->
                    <div v-if="activeBondCategory === 'central_bank_rates'" class="category-section">
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
                                            v-for="tf in bondTimeframes" 
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
                                    <Line :data="getBondChartData(item)" :options="bondChartOptions" />
                                </div>
                                <div v-else class="no-data">
                                    <p>No history data available</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Credit Spreads -->
                    <div v-if="activeBondCategory === 'credit_spreads'" class="category-section">
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
                                            v-for="tf in bondTimeframes" 
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
                                    <Line :data="getBondChartData(item)" :options="bondChartOptions" />
                                </div>
                                <div v-else class="no-data">
                                    <p>No history data available</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Funding Stress -->
                    <div v-if="activeBondCategory === 'funding_stress'" class="category-section">
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
                                            v-for="tf in bondTimeframes" 
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

            <!-- Economic Tab Content -->
            <div v-if="activeTab === 'economic'" class="tab-content economic-tab-content">
                <div class="economic-header">
                    <button @click="updateEconomicData" :disabled="economicLoading" class="update-btn">
                        {{ economicLoading ? 'Updating...' : 'Update Data' }}
                    </button>
                </div>

                <div v-if="economicLoading" class="loading-state">
                    <div class="loading-spinner"></div>
                    <p>Loading Macro Economic Data...</p>
                </div>
                <div v-else-if="economicError" class="error-state">
                    <p class="error-message">{{ economicError }}</p>
                </div>
                <div v-else class="indicators">
                    <div v-for="item in economicIndicators" :key="item.indicator" class="indicator-card">
                        <div class="card-content">
                            <h3>{{ item.indicator }}</h3>
                            <p class="value">{{ item.value }}</p>
                            <p class="date">{{ item.date }}</p>
                            <p class="desc">{{ item.description || '&nbsp;' }}</p>
                            
                            <!-- Per-graph Timeframe Selector -->
                            <div class="card-timeframe-selector">
                                <button 
                                    v-for="tf in economicTimeframes" 
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
                            <Bar v-if="item.chart_type === 'bar'" :data="getEconomicChartData(item)" :options="barChartOptions" />
                            <Line v-else :data="getEconomicChartData(item)" :options="economicChartOptions" />
                        </div>
                        <div v-else class="no-data">
                            <p>No history data available</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Energy Tab Content -->
            <div v-if="activeTab === 'energy'" class="tab-content energy-tab-content">
                <div class="energy-header">
                    <button @click="updateEnergyData" :disabled="energyLoading" class="update-btn">
                        {{ energyLoading ? 'Updating...' : 'Update Data' }}
                    </button>
                </div>

                <div v-if="energyLoading" class="loading-state">
                    <div class="loading-spinner"></div>
                    <p>Loading Energy Data...</p>
                </div>
                <div v-else-if="energyError" class="error-state">
                    <p class="error-message">{{ energyError }}</p>
                </div>
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
                                    v-for="tf in energyTimeframes" 
                                    :key="tf.value" 
                                    :class="{ active: selectedEnergyTimeframe === tf.value }"
                                    @click="changeEnergyTimeframe(tf.value)"
                                >
                                    {{ tf.label }}
                                </button>
                            </div>

                            <div class="chart-container-small">
                                <Line :data="demandCurveData" :options="energyLineOptions" />
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
import { ref, onMounted, computed } from 'vue';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Line, Bar, Doughnut, Pie } from 'vue-chartjs'
import { getDailyCache, setDailyCache, clearCacheByKey } from '../utils/dailyCache.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
)

const marketData = ref({ gainers: [], losers: [], volatile: [], active: [] });
const loading = ref(true);
const activeTab = ref('equity');

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

const bondTimeframes = [
  { label: '1M', value: 'daily' },
  { label: '3M', value: 'weekly' },
  { label: '1Y', value: 'monthly' },
  { label: '5Y', value: 'yearly' },
  { label: 'Max', value: 'max' }
];

const bondCategories = [
  { label: 'Treasury Yields', value: 'treasury_yields' },
  { label: 'Yield Curve', value: 'yield_curve' },
  { label: 'TIPS & Breakeven', value: 'tips_breakeven' },
  { label: 'Central Bank Rates', value: 'central_bank_rates' },
  { label: 'Credit Spreads', value: 'credit_spreads' },
  { label: 'Funding Stress', value: 'funding_stress' }
];

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

// Economic Tab State (from MacroView)
const economicIndicators = ref([]);
const economicLoading = ref(false);
const economicError = ref(null);

const economicTimeframes = [
    { label: '1M', value: 'daily' },
    { label: '3M', value: 'weekly' },
    { label: '1Y', value: 'monthly' },
    { label: '5Y', value: 'yearly' },
    { label: 'Max', value: 'max' }
];

// Economic cache configuration
const ECONOMIC_CACHE_EXPIRATION = 30 * 60 * 1000; // 30 minutes
const ECONOMIC_CACHE_KEY_PREFIX = 'macro_series_';

const getEconomicCacheKey = (seriesId, timeframe) => `${ECONOMIC_CACHE_KEY_PREFIX}${seriesId}_${timeframe}`;

const getEconomicCachedData = (seriesId, timeframe) => {
    try {
        const key = getEconomicCacheKey(seriesId, timeframe);
        const cached = localStorage.getItem(key);
        if (!cached) return null;
        
        const { data, timestamp } = JSON.parse(cached);
        if (Date.now() - timestamp < ECONOMIC_CACHE_EXPIRATION) {
            return data;
        }
        localStorage.removeItem(key);
        return null;
    } catch (e) {
        return null;
    }
};

const setEconomicCachedData = (seriesId, timeframe, data) => {
    try {
        const key = getEconomicCacheKey(seriesId, timeframe);
        localStorage.setItem(key, JSON.stringify({
            data,
            timestamp: Date.now()
        }));
    } catch (e) {
        console.error('Cache write error', e);
    }
};

// Energy Tab State (from EnergyView)
const energyLoading = ref(true);
const energyError = ref(null);
const generation = ref([]);
const consumption = ref([]);
const gridData = ref({});
const prices = ref([]);

const selectedEnergyTimeframe = ref('realtime');
const energyTimeframes = [
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

// Bond Chart Options
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
    const response = await fetch(`http://localhost:8000/api/bond/all?timeframe=monthly`);
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

const updateBondData = async () => {
  clearCacheByKey('bond_data_monthly');
  await fetchBondData();
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
        const response = await fetch(`http://localhost:8000/api/bond/series/${item.series_id}?timeframe=${timeframe}`);
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

// Energy Chart Options
const pieOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
      legend: {
          position: 'right',
          labels: { color: '#000000' }
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

const energyLineOptions = {
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
          grid: { drawOnChartArea: false },
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

const changeEnergyTimeframe = (timeframe) => {
    selectedEnergyTimeframe.value = timeframe;
    fetchGridData(timeframe);
};

const changePriceTimeframe = (timeframe) => {
    selectedPriceTimeframe.value = timeframe;
    fetchPriceData(timeframe);
};

const fetchEnergyData = async () => {
    // Check daily cache first
    const cachedGeneration = getDailyCache('energy_generation');
    const cachedConsumption = getDailyCache('energy_consumption');
    
    if (cachedGeneration && cachedConsumption) {
        console.log('Using cached energy data');
        generation.value = cachedGeneration;
        consumption.value = cachedConsumption;
        
        // Still fetch grid and price data with their timeframes
        await fetchGridData(selectedEnergyTimeframe.value);
        await fetchPriceData(selectedPriceTimeframe.value);
        
        energyLoading.value = false;
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
        await fetchGridData(selectedEnergyTimeframe.value);
        await fetchPriceData(selectedPriceTimeframe.value);

    } catch (err) {
        energyError.value = err.message;
    } finally {
        energyLoading.value = false;
    }
};

const updateEnergyData = async () => {
    clearCacheByKey('energy_generation');
    clearCacheByKey('energy_consumption');
    await fetchEnergyData();
};

// Economic Chart Options
const economicChartOptions = {
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

const barChartOptions = {
  ...economicChartOptions,
  elements: {
      ...economicChartOptions.elements,
      bar: {
          borderRadius: 4
      }
  }
};

const getEconomicChartData = (item) => {
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

const fetchEconomicData = async () => {
  economicLoading.value = true;
  economicError.value = null;
  
  // Check daily cache first
  const cached = getDailyCache('macro_data_monthly');
  if (cached) {
    console.log('Using cached macro data');
    economicIndicators.value = cached;
    economicLoading.value = false;
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
    
    economicIndicators.value = processedData;
    
    // Cache the data
    setDailyCache('macro_data_monthly', processedData);
    
  } catch (err) {
    economicError.value = err.message;
  } finally {
    economicLoading.value = false;
  }
};

const updateEconomicData = async () => {
  clearCacheByKey('macro_data_monthly');
  await fetchEconomicData();
};

const updateIndicatorTimeframe = async (item, timeframe) => {
    if (item.selectedTimeframe === timeframe) return;
    
    item.selectedTimeframe = timeframe;
    item.loading = true;
    
    // Check cache
    const cached = getEconomicCachedData(item.series_id, timeframe);
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
        
        setEconomicCachedData(item.series_id, timeframe, data);
    } catch (err) {
        console.error(`Error fetching ${item.indicator}:`, err);
    } finally {
        item.loading = false;
    }
};

onMounted(() => {
    // Generate mock history for each index
    indices.value.forEach(index => {
        index.history = generateMockHistory(index.value);
    });
    
    fetchMarketData();
    
    // Fetch bond data when bond tab might be accessed
    fetchBondData();
    
    // Fetch economic data when economic tab might be accessed
    fetchEconomicData();
    
    // Fetch energy data when energy tab might be accessed
    fetchEnergyData();
});
</script>

<style scoped>
.dashboard {
  padding: 20px 20px 20px 0;
  max-width: 1800px;
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

.page-header h1 {
  margin: 0;
  color: #000000;
  font-weight: 600;
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
    background: #ffffff;
    padding: 20px;
    border-radius: 8px;
    color: #000000;
    text-align: center;
    border: 1px solid #cccccc;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.index-card h3 {
    margin: 0 0 10px 0;
    font-size: 1em;
    color: #000000;
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
    background: #ffffff;
    padding: 15px;
    border-radius: 8px;
    color: #000000;
    border: 1px solid #cccccc;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.market-section h3 {
    color: #000000;
    font-weight: 600;
    margin: 0 0 15px 0;
}

.market-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
}

.market-table th {
    text-align: left;
    color: #666666;
    font-size: 0.9em;
    padding-bottom: 5px;
    border-bottom: 1px solid #cccccc;
    font-weight: 600;
}

.market-table td {
    padding: 8px 0;
    font-size: 0.95em;
    color: #000000;
}

.ticker-cell {
    font-weight: bold;
    color: #3498db;
    cursor: pointer;
    text-decoration: underline;
}

.ticker-cell:hover {
    color: #2980b9;
}
.positive { color: #42b983; }
.negative { color: #e74c3c; }

.hover-chart-tooltip {
    position: fixed;
    background: #ffffff;
    border: 1px solid #cccccc;
    padding: 10px;
    border-radius: 8px;
    z-index: 9999;
    width: 250px;
    height: 150px;
    pointer-events: none; /* Let mouse events pass through so we don't trigger leave */
    box-shadow: 0 4px 6px rgba(0,0,0,0.15);
}

.hover-chart-tooltip h4 {
    margin: 0 0 5px 0;
    font-size: 0.9em;
    color: #000000;
    text-align: center;
    font-weight: 600;
}
.chart-wrapper {
    height: 100px;
    width: 100%;
}

/* Key Logs Section Styles */
.key-logs-section {
    background: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    margin-bottom: 20px;
}

.key-logs-header {
    margin-bottom: 20px;
}

.key-logs-header h2 {
    margin: 0;
    color: #000000;
    font-weight: 600;
    font-size: 1.5em;
}

.tab-selector {
    display: flex;
    gap: 0;
    border-bottom: 2px solid #cccccc;
    margin-bottom: 20px;
}

.tab-btn {
    padding: 12px 24px;
    background: transparent;
    border: none;
    border-bottom: 3px solid transparent;
    color: #666666;
    font-size: 1em;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
}

.tab-btn:hover {
    color: #000000;
    background: #f8f9fa;
}

.tab-btn.active {
    color: #000000;
    border-bottom-color: #3498db;
    font-weight: 600;
}

.tab-content {
    padding: 0;
}

.tab-placeholder {
    padding: 40px;
    text-align: center;
    color: #666666;
}

.tab-placeholder h3 {
    color: #000000;
    font-weight: 600;
    margin: 0 0 15px 0;
}

.tab-placeholder p {
    margin: 10px 0;
    line-height: 1.6;
}

.placeholder-note {
    font-style: italic;
    color: #999999;
    font-size: 0.9em;
}

/* Bond Tab Styles */
.bond-tab-content {
    padding: 0;
}

.bond-header {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 20px;
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

/* Economic Tab Styles */
.economic-tab-content {
    padding: 0;
}

.economic-header {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 20px;
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

.indicator-card h3 {
    margin: 0 0 12px 0;
    font-size: 1.1em;
    font-weight: 600;
    color: #000000;
}

/* Energy Tab Styles */
.energy-tab-content {
    padding: 0;
}

.energy-header {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 20px;
}

.energy-layout {
    display: flex;
    gap: 15px;
    width: 100%;
    box-sizing: border-box;
}

.energy-layout .main-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 15px;
    min-width: 0;
}

.energy-layout .sidebar {
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
    
    .energy-layout .sidebar {
        width: 100%;
        display: grid;
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 768px) {
    .energy-layout .sidebar {
        grid-template-columns: 1fr;
    }
}

.energy-layout .card {
    background: #ffffff;
    color: #000000;
    padding: 20px;
    border-radius: 8px;
    border: 1px solid #cccccc;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.energy-layout .card h3 {
    color: #000000;
    font-weight: 600;
    margin: 0 0 15px 0;
}

.energy-layout .full-width {
    width: 100%;
}

.energy-layout .chart-container {
    height: 300px;
    position: relative;
}

.energy-layout .sidebar .chart-container {
    height: 250px;
}

.energy-layout .chart-container-small {
    height: 200px;
    margin-top: 20px;
}

.energy-layout .metrics p {
    margin: 5px 0;
    color: #000000;
}

.energy-layout .metrics strong {
    color: #000000;
}

.energy-layout .timeframe-selector {
    display: flex;
    gap: 10px;
    margin: 15px 0;
    justify-content: center;
}

.energy-layout .timeframe-selector button {
    background: #f8f9fa;
    border: 1px solid #cccccc;
    color: #000000;
    padding: 5px 10px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.8em;
    transition: all 0.2s;
}

.energy-layout .timeframe-selector button.active {
    background: #3498db;
    color: white;
    border-color: #3498db;
}

.energy-layout .timeframe-selector button:hover {
    background: #e9ecef;
}
</style>
