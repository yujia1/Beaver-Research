<template>
  <div class="market-analysis">
    <!-- Sub Tabs -->
    <div class="sub-tabs">
      <button 
        :class="{ active: activeTab === 'sector' }"
        @click="activeTab = 'sector'"
      >
        Sector
      </button>
      <button 
        :class="{ active: activeTab === 'industry' }"
        @click="activeTab = 'industry'"
      >
        Industry
      </button>
    </div>

    <!-- Sector Tab Content -->
    <div v-if="activeTab === 'sector'" class="section-container">
      <div class="section-header">
        <h2>SECTOR PERFORMANCE & VALUATION</h2>
        <div class="exchanges">
          <template v-for="(ex, index) in exchanges" :key="ex">
            <button 
              class="exchange-btn" 
              :class="{ active: activeExchange === ex }"
              @click="activeExchange = ex"
            >
              {{ ex }}
            </button>
            <span v-if="index < exchanges.length - 1" class="divider">/</span>
          </template>
        </div>
      </div>
      
      <div class="charts-row">
        <!-- Chart 01: Relative Change -->
        <div class="chart-wrapper">
          <h3 class="chart-title">01. RELATIVE CHANGE (%)</h3>
          <div class="chart-content">
            <Bar :data="sectorPerformanceData" :options="horizontalBarOptions" />
          </div>
        </div>

        <!-- Chart 02: P/E Distribution -->
        <div class="chart-wrapper">
          <h3 class="chart-title">02. P/E DISTRIBUTION</h3>
          <div class="chart-content">
            <Bar :data="sectorPeData" :options="verticalBarOptions" />
          </div>
        </div>
      </div>
    </div>

    <!-- Industry Tab Content -->
    <!-- Industry Tab Content -->
    <div v-if="activeTab === 'industry'" class="section-container">
      <div class="section-header directory-header">
        <div class="header-left">
          <h2>Industry Matrix</h2>
          <div class="exchanges">
            <template v-for="(ex, index) in exchanges" :key="ex">
              <button 
                class="exchange-btn" 
                :class="{ active: activeExchange === ex }"
                @click="activeExchange = ex"
              >
                {{ ex }}
              </button>
              <span v-if="index < exchanges.length - 1" class="divider">/</span>
            </template>
          </div>
        </div>
        
        <div class="directory-controls">
          <input 
            type="text" 
            v-model="industrySearch" 
            placeholder="SEARCH INDUSTRIES..." 
            class="search-input"
          />
          <div class="sort-options">
            <button :class="{ active: industrySort === 'perf' }" @click="industrySort = 'perf'">PERF</button>
            <span class="divider">/</span>
            <button :class="{ active: industrySort === 'pe' }" @click="industrySort = 'pe'">P/E</button>
          </div>
        </div>
      </div>

      <div class="industry-grid-header">
        <span class="col-name">INDUSTRY</span>
        <span class="col-change">CHANGE</span>
        <span class="col-pe">P/E</span>
      </div>
      
      <div class="industry-grid">
        <div v-for="industry in filteredIndustries" :key="industry.name" class="industry-item">
          <div class="industry-info">
            <div class="industry-name">{{ industry.name }}</div>
            <div class="industry-sector">{{ industry.sector.toUpperCase() }}</div>
          </div>
          <div class="industry-metrics">
            <div class="metric-change" :class="industry.change >= 0 ? 'positive' : 'negative'">
              {{ formatChange(industry.change) }}
            </div>
            <div class="metric-pe">{{ industry.pe.toFixed(1) }}x</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted } from 'vue'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Bar } from 'vue-chartjs'
import API_BASE_URL from '@/config/api'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
)

// --- STATE ---
const activeTab = ref('sector')
const activeExchange = ref('NASDAQ')
const exchanges = ['NASDAQ', 'NYSE', 'AMEX']

// --- COLORS ---
const COLOR_POSITIVE = '#4ade80' // Greenish
const COLOR_NEGATIVE = '#f87171' // Reddish
const COLOR_NEUTRAL = '#000000'  // Black

// --- OPTIONS ---
const baseOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false }
  }
}

const horizontalBarOptions = {
  ...baseOptions,
  indexAxis: 'y',
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (context) => {
          const val = context.parsed.x
          return typeof val === 'number' ? val.toFixed(2) + '%' : val
        }
      }
    }
  },
  scales: {
    x: {
      grid: { display: true, color: '#f3f4f6' },
      ticks: { font: { size: 10 } }
    },
    y: {
      grid: { display: false },
      ticks: { font: { size: 11, weight: '500' }, color: '#374151' }
    }
  }
}

const verticalBarOptions = {
  ...baseOptions,
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (context) => {
          const val = context.parsed.y
          return typeof val === 'number' ? val.toFixed(1) + 'x' : val
        }
      }
    }
  },
  scales: {
    x: {
      grid: { display: false },
      ticks: { font: { size: 10 }, maxRotation: 45, minRotation: 45 }
    },
    y: {
      grid: { display: true, color: '#f3f4f6' }
    }
  }
}
// --- API DATA ---
const sectorData = ref([])
const loadingSectors = ref(false)

const sectorPeList = ref([])

const fetchSectorData = async () => {
  loadingSectors.value = true
  try {
    const today = new Date().toISOString().split('T')[0]
    
    // 1. Fetch Performance
    const perfRes = await fetch(`${API_BASE_URL}/api/alphatrade/sector-performance?exchange=${activeExchange.value}&date=${today}`)
    if (perfRes.ok) {
      sectorData.value = await perfRes.json()
    }

    // 2. Fetch P/E
    const peRes = await fetch(`${API_BASE_URL}/api/alphatrade/sector-pe?exchange=${activeExchange.value}&date=${today}`)
    if (peRes.ok) {
      sectorPeList.value = await peRes.json()
    }

  } catch (err) {
    console.error('Error fetching sector data:', err)
  } finally {
    loadingSectors.value = false
  }
}

// Watchers

watch([activeExchange, activeTab], ([newExchange, newTab]) => {
  if (newTab === 'sector') {
    fetchSectorData()
  }
})

onMounted(() => {
  if (activeTab.value === 'sector') {
    fetchSectorData()
  }
})


// 01. Sector Performance (Computed from API data)
const sectorPerformanceData = computed(() => {
  // Fallback to empty if no data yet
  if (!sectorData.value || sectorData.value.length === 0) {
    return {
      labels: [],
      datasets: [{ data: [], backgroundColor: [] }]
    }
  }

  // Sort by performance (averageChange) descending
  const sorted = [...sectorData.value].sort((a, b) => b.averageChange - a.averageChange)
  
  const labels = sorted.map(item => item.sector)
  const values = sorted.map(item => item.averageChange)

  return {
    labels,
    datasets: [{
      data: values,
      backgroundColor: values.map(v => v >= 0 ? COLOR_POSITIVE : COLOR_NEGATIVE),
      borderRadius: 2,
      barThickness: 12
    }]
  }
})

// 02. P/E Distribution
const sectorPeData = computed(() => {
   // Fallback to empty if no data yet
  if (!sectorPeList.value || sectorPeList.value.length === 0) {
    return {
      labels: [],
      datasets: [{ data: [], backgroundColor: [] }]
    }
  }

  // Sort by P/E descending
  const sorted = [...sectorPeList.value].sort((a, b) => b.pe - a.pe)

  const labels = sorted.map(item => item.sector)
  const values = sorted.map(item => item.pe)

  return {
    labels,
    datasets: [{
      data: values,
      backgroundColor: COLOR_NEUTRAL,
      borderRadius: 2,
      barThickness: 12
    }]
  }
})

// 03. Full Industry Directory
const industryList = ref([])
const loadingIndustries = ref(false)

const fetchIndustryData = async () => {
  loadingIndustries.value = true
  try {
    const today = new Date().toISOString().split('T')[0]
    
    const [perfRes, peRes] = await Promise.all([
      fetch(`${API_BASE_URL}/api/alphatrade/industry-performance?exchange=${activeExchange.value}&date=${today}`),
      fetch(`${API_BASE_URL}/api/alphatrade/industry-pe?exchange=${activeExchange.value}&date=${today}`)
    ])

    let perfData = []
    let peData = []

    if (perfRes.ok) perfData = await perfRes.json()
    if (peRes.ok) peData = await peRes.json()

    // Map by industry name for easy merging
    const industryMap = new Map()

    // Process Performance Data
    perfData.forEach(item => {
      industryMap.set(item.industry, {
        name: item.industry,
        sector: '', // FMP Snapshot doesn't give sector in this endpoint, but maybe we can infer or leave empty? 
                    // Wait, the user mock data had sectors. The endpoint response shown by user:
                    // { "date":..., "industry": "Advertising Agencies", "exchange": "NASDAQ", "averageChange": ... }
                    // It does NOT have sector.
                    // However, we need sector for display.
                    // If FMP doesn't return sector here, we might need another call or map it.
                    // For now, let's leave sector empty or use a fallback if not provided.
                    // Actually, the previous mock data was extensive. If FMP endpoint doesn't return sector, 
                    // we show empty or 'N/A' in the UI column.
        change: item.averageChange,
        pe: 0
      })
    })

    // Process P/E Data - Merge into map
    peData.forEach(item => {
      if (industryMap.has(item.industry)) {
        const existing = industryMap.get(item.industry)
        existing.pe = item.pe
      } else {
        // If it exists in PE but not Performance (unlikely but possible)
        industryMap.set(item.industry, {
          name: item.industry,
          sector: '',
          change: 0,
          pe: item.pe
        })
      }
    })

    industryList.value = Array.from(industryMap.values())

  } catch (err) {
    console.error('Error fetching industry data:', err)
  } finally {
    loadingIndustries.value = false
  }
}

watch([activeExchange, activeTab], ([newExchange, newTab]) => {
  if (newTab === 'industry') {
    fetchIndustryData()
  }
})

onMounted(() => {
  if (activeTab.value === 'industry') {
    fetchIndustryData()
  }
})

// Search and Sort State
const industrySearch = ref('')
const industrySort = ref('perf') // 'perf', 'pe', 'name'

const filteredIndustries = computed(() => {
  let result = [...industryList.value]
  
  // Search
  if (industrySearch.value) {
    const q = industrySearch.value.toLowerCase()
    result = result.filter(i => i.name.toLowerCase().includes(q) || i.sector.toLowerCase().includes(q))
  }
  
  // Sort
  if (industrySort.value === 'perf') {
    result.sort((a, b) => b.change - a.change)
  } else if (industrySort.value === 'pe') {
    result.sort((a, b) => b.pe - a.pe)
  } else if (industrySort.value === 'name') {
    result.sort((a, b) => a.name.localeCompare(b.name))
  }
  
  return result
})

const formatChange = (val) => {
  const sign = val > 0 ? '+' : ''
  return `${sign}${val.toFixed(2)}%`
}

</script>

<style scoped>
.market-analysis {
  padding: 1rem 0;
  display: flex;
  flex-direction: column;
  gap: 1.5rem; /* Reduced gap since sub-tabs take space */
}

.sub-tabs {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 0.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.sub-tabs button {
  background: none;
  border: none;
  padding: 0.5rem 0.25rem;
  font-size: 0.9rem;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  position: relative;
  transition: color 0.2s;
}

.sub-tabs button:hover {
  color: #111827;
}

.sub-tabs button.active {
  color: #000000;
  font-weight: 700;
}

.sub-tabs button.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  width: 100%;
  height: 2px;
  background-color: #000000;
}

.section-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 2px solid #000;
  padding-bottom: 0.5rem;
  margin-bottom: 1rem;
}

.section-header h2 {
  font-size: 0.9rem;
  font-weight: 700;
  letter-spacing: 1px;
  color: #9ca3af; /* Light gray to match "SECTOR PERFORMANCE & VALUATION" style */
  margin: 0;
  text-transform: uppercase;
}

.exchanges {
  font-size: 0.7rem;
  font-weight: 700;
  color: #9ca3af;
  display: flex;
  align-items: center;
}

.exchange-btn {
  background: none;
  border: none;
  padding: 0;
  font-size: 0.7rem;
  font-weight: 700;
  color: #9ca3af; /* Default gray */
  cursor: pointer;
  transition: all 0.2s ease;
}

.exchange-btn:hover {
  color: #4b5563;
}

.exchange-btn.active {
  color: #000000; /* Black for active */
  text-decoration: underline;
  text-underline-offset: 4px;
}

.divider {
  color: #e5e7eb;
  margin: 0 6px;
  font-weight: 400;
}

.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 3rem;
}

.chart-wrapper {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.chart-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: #6b7280; /* Neutral gray */
  margin: 0;
  font-style: italic;
}

.chart-content {
  height: 350px;
  position: relative;
}

@media (max-width: 1024px) {
  .charts-row {
    grid-template-columns: 1fr;
    gap: 2rem;
  }
}

.directory-header {
  display: block; /* Override flex */
  border-bottom: none;
  margin-bottom: 2rem;
  padding-bottom: 0;
}

.header-left {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  width: 100%;
}

.header-left h2 {
  font-size: 0.9rem;
  font-weight: 700;
  letter-spacing: 1px;
  color: #000000;
  margin: 0;
  text-transform: uppercase;
}

.directory-controls {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 3rem;
}

.search-input {
  border: none;
  border-bottom: 2px solid #000; /* Bold black underline */
  padding: 0.5rem 0;
  font-size: 0.9rem;
  color: #000;
  outline: none;
  width: 300px;
  font-family: inherit;
  font-weight: 700;
  text-transform: uppercase;
  background: transparent;
  letter-spacing: 1px;
}

.search-input::placeholder {
  color: #9ca3af;
  letter-spacing: 1px;
  font-weight: 700;
}

.sort-options {
  display: flex;
  align-items: center;
  font-size: 0.8rem;
  font-weight: 700;
  color: #e5e7eb; /* Light gray for dividers */
}

.sort-options button {
  background: none;
  border: none;
  padding: 0;
  font-size: 0.8rem;
  font-weight: 700;
  color: #d1d5db; /* Inactive color (light gray) */
  cursor: pointer;
  text-transform: uppercase;
  transition: color 0.2s;
}

.sort-options button.active {
  color: #000000; /* Active Black */
  background: none; /* Ensure no background */
}

.industry-grid-header {
  display: flex;
  justify-content: space-between;
  padding: 0 0.5rem;
  margin-bottom: 1.5rem; 
  font-size: 0.7rem;
  font-weight: 700;
  color: #2c2d30; 
  text-transform: uppercase;
  letter-spacing: 1px;
}

.col-right {
  display: flex;
  gap: 3rem;
}

.col-pe {
  text-align: right;
  width: 60px;
}

.industry-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem 4rem; /* Wider gap between columns */
}

.industry-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 0 0.5rem;
}

.industry-info {
  display: flex;
  flex-direction: column;
  gap: 4px; /* Slight spacing */
}

.industry-name {
  font-size: 0.75rem;
  font-weight: 800; /* Bolder */
  color: #111827;
  text-transform: uppercase;
  line-height: 1.2;
}

.industry-sector {
  font-size: 0.65rem;
  color: #9ca3af;
  text-transform: uppercase;
  font-weight: 500;
}

.industry-metrics {
  display: flex;
  gap: 2.5rem; /* Wider spacing */
  text-align: right;
  align-items: flex-start;
}

.metric-change {
  font-size: 0.8rem;
  font-weight: 700;
  min-width: 50px;
}

.metric-change.positive {
  color: #10b981;
}

.metric-change.negative {
  color: #ef4444;
}

.metric-pe {
  font-size: 0.8rem;
  color: #6b7280;
  min-width: 40px;
  font-weight: 500;
}

.industry-info {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.industry-name {
  font-size: 0.8rem;
  font-weight: 700;
  color: #111827;
  text-transform: uppercase;
}

.industry-sector {
  font-size: 0.65rem;
  color: #9ca3af;
  text-transform: uppercase;
}

.industry-metrics {
  display: flex;
  gap: 2rem; /* Spacing between change and P/E */
  text-align: right;
}

.metric-change {
  font-size: 0.8rem;
  font-weight: 600;
  min-width: 50px;
}

.metric-change.positive {
  color: #10b981;
}

.metric-change.negative {
  color: #ef4444;
}

.metric-pe {
  font-size: 0.8rem;
  color: #6b7280;
  min-width: 40px;
}

@media (max-width: 1280px) {
  .industry-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .industry-grid {
    grid-template-columns: 1fr;
  }
  
  .directory-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .directory-controls {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
