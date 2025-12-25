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
        <span class="col-name">INDUSTRY NAME</span>
        <span class="col-change">Daily CHANGE</span>
        <span class="col-pe">P/E RATIO</span>
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
const exchanges = ['NASDAQ', 'NYSE', 'AMEX', 'CBOE']

// --- COLORS ---
const COLOR_POSITIVE = '#4ade80' // Greenish
const COLOR_NEGATIVE = '#f87171' // Reddish
const COLOR_NEUTRAL = '#000000'  // Black

// --- OPTIONS ---
const commonOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    },
    tooltip: {
      callbacks: {
        label: (context) => `${context.parsed.y !== null ? context.parsed.y : context.parsed.x}`
      }
    }
  }
}

const horizontalBarOptions = {
  ...commonOptions,
  indexAxis: 'y',
  scales: {
    x: {
      grid: {
        display: true,
        color: '#f3f4f6'
      },
      ticks: {
        font: { size: 10 }
      }
    },
    y: {
      grid: {
        display: false
      },
      ticks: {
        font: { size: 11, weight: '500' },
        color: '#374151'
      }
    }
  }
}

const verticalBarOptions = {
  ...commonOptions,
  scales: {
    x: {
      grid: {
        display: false
      },
      ticks: {
        font: { size: 10 },
        maxRotation: 45,
        minRotation: 45
      }
    },
    y: {
      grid: {
        display: true,
        color: '#f3f4f6'
      }
    }
  }
}

// --- MOCK DATA ---

// --- API DATA ---
const sectorData = ref([])
const loadingSectors = ref(false)

const sectorPeList = ref([])

const fetchSectorData = async () => {
  loadingSectors.value = true
  try {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
    const today = new Date().toISOString().split('T')[0]
    
    // 1. Fetch Performance
    const perfRes = await fetch(`${baseUrl}/api/alphatrade/sector-performance?exchange=${activeExchange.value}&date=${today}`)
    if (perfRes.ok) {
      sectorData.value = await perfRes.json()
    }

    // 2. Fetch P/E
    const peRes = await fetch(`${baseUrl}/api/alphatrade/sector-pe?exchange=${activeExchange.value}&date=${today}`)
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
const industryList = [
  { name: 'Advertising Agencies', sector: 'Communication Services', change: 1.25, pe: 15.4 },
  { name: 'Aerospace & Defense', sector: 'Industrials', change: 2.10, pe: 21.0 },
  { name: 'Agricultural Farm Products', sector: 'Consumer Defensive', change: -0.50, pe: 18.2 },
  { name: 'Agricultural Inputs', sector: 'Basic Materials', change: 0.80, pe: 12.5 },
  { name: 'Agricultural - Machinery', sector: 'Industrials', change: 1.45, pe: 14.8 },
  { name: 'Airlines, Airports & Air Services', sector: 'Industrials', change: 3.20, pe: 9.5 },
  { name: 'Apparel - Footwear & Accessories', sector: 'Consumer Cyclical', change: 1.10, pe: 22.1 },
  { name: 'Apparel - Manufacturers', sector: 'Consumer Cyclical', change: 0.90, pe: 19.8 },
  { name: 'Apparel - Retail', sector: 'Consumer Cyclical', change: 1.50, pe: 24.5 },
  { name: 'Auto - Dealerships', sector: 'Consumer Cyclical', change: 2.22, pe: 6.0 },
  { name: 'Auto - Manufacturers', sector: 'Consumer Cyclical', change: 4.50, pe: 15.0 },
  { name: 'Auto - Parts', sector: 'Consumer Cyclical', change: 1.80, pe: 11.2 },
  { name: 'Auto - Recreational Vehicles', sector: 'Consumer Cyclical', change: 0.70, pe: 10.5 },
  { name: 'Banks', sector: 'Financial Services', change: 1.15, pe: 11.0 },
  { name: 'Banks - Regional', sector: 'Financial Services', change: 2.34, pe: 25.0 },
  { name: 'Beverages - Alcoholic', sector: 'Consumer Defensive', change: -0.20, pe: 19.5 },
  { name: 'Beverages - Non-Alcoholic', sector: 'Consumer Defensive', change: 0.50, pe: 23.4 },
  { name: 'Beverages - Wineries & Distilleries', sector: 'Consumer Defensive', change: 0.10, pe: 21.0 },
  { name: 'Biotechnology', sector: 'Healthcare', change: 2.80, pe: 30.0 },
  { name: 'Broadcasting', sector: 'Communication Services', change: 0.60, pe: 14.2 },
  { name: 'Chemicals', sector: 'Basic Materials', change: 2.53, pe: 38.7 },
  { name: 'Chemicals - Specialty', sector: 'Basic Materials', change: 1.90, pe: 28.5 },
  { name: 'Coal', sector: 'Energy', change: -1.50, pe: 5.4 },
  { name: 'Communication Equipment', sector: 'Technology', change: 1.20, pe: 18.9 },
  { name: 'Computer Hardware', sector: 'Technology', change: 2.69, pe: 16.2 },
  { name: 'Conglomerates', sector: 'Industrials', change: 0.40, pe: 15.6 },
  { name: 'Construction', sector: 'Industrials', change: 1.70, pe: 13.8 },
  { name: 'Construction Materials', sector: 'Basic Materials', change: 1.50, pe: 14.5 },
  { name: 'Consulting Services', sector: 'Industrials', change: 2.11, pe: 41.8 },
  { name: 'Consumer Electronics', sector: 'Technology', change: 1.80, pe: 20.5 },
  { name: 'Discount Stores', sector: 'Consumer Defensive', change: 0.30, pe: 22.0 },
  { name: 'Diversified Utilities', sector: 'Utilities', change: 2.58, pe: 35.7 },
  { name: 'Drug Manufacturers - General', sector: 'Healthcare', change: 1.10, pe: 16.5 },
  { name: 'Drug Manufacturers - Specialty & Generic', sector: 'Healthcare', change: 1.90, pe: 21.5 },
  { name: 'Education & Training Services', sector: 'Consumer Defensive', change: 2.61, pe: 16.2 },
  { name: 'Electrical Equipment & Parts', sector: 'Industrials', change: 1.30, pe: 18.0 },
  { name: 'Electronic Gaming & Multimedia', sector: 'Communication Services', change: 3.10, pe: 28.5 },
  { name: 'Engineering & Construction', sector: 'Industrials', change: 2.71, pe: 22.1 },
  { name: 'Entertainment', sector: 'Communication Services', change: 2.02, pe: 21.3 },
  { name: 'Financial - Capital Markets', sector: 'Financial Services', change: 1.60, pe: 14.5 },
  { name: 'Financial - Conglomerates', sector: 'Financial Services', change: 0.90, pe: 12.8 },
  { name: 'Financial - Credit Services', sector: 'Financial Services', change: 2.69, pe: 41.1 },
  { name: 'Financial - Data & Stock Exchanges', sector: 'Financial Services', change: 1.40, pe: 25.0 },
  { name: 'Financial - Mortgages', sector: 'Financial Services', change: 0.80, pe: 9.5 },
  { name: 'Food Distribution', sector: 'Consumer Defensive', change: 2.46, pe: 15.9 },
  { name: 'Furnishings, Fixtures & Appliances', sector: 'Consumer Cyclical', change: 1.00, pe: 13.5 },
  { name: 'Gambling, Resorts & Casinos', sector: 'Consumer Cyclical', change: 1.80, pe: 28.0 },
  { name: 'Gold', sector: 'Basic Materials', change: 2.99, pe: 12.6 },
  { name: 'Grocery Stores', sector: 'Consumer Defensive', change: 2.20, pe: 8.0 },
  { name: 'Hardware, Equipment & Parts', sector: 'Technology', change: 1.50, pe: 17.5 },
  { name: 'Home Improvement', sector: 'Consumer Cyclical', change: 1.20, pe: 19.8 },
  { name: 'Household & Personal Products', sector: 'Consumer Defensive', change: 0.60, pe: 24.5 },
  { name: 'Industrial - Distribution', sector: 'Industrials', change: 1.10, pe: 16.0 },
  { name: 'Industrial - Machinery', sector: 'Industrials', change: 1.40, pe: 18.5 },
  { name: 'Industrial Materials', sector: 'Basic Materials', change: 1.00, pe: 14.0 },
  { name: 'Industrial - Pollution & Treatment Controls', sector: 'Industrials', change: 1.70, pe: 22.0 },
  { name: 'Information Technology Services', sector: 'Technology', change: 2.23, pe: 35.9 },
  { name: 'Insurance - Brokers', sector: 'Financial Services', change: 1.30, pe: 19.0 },
  { name: 'Insurance - Diversified', sector: 'Financial Services', change: 1.50, pe: 13.0 },
  { name: 'Insurance - Life', sector: 'Financial Services', change: 0.80, pe: 10.5 },
  { name: 'Insurance - Property & Casualty', sector: 'Financial Services', change: 1.10, pe: 14.0 },
  { name: 'Insurance - Reinsurance', sector: 'Financial Services', change: 1.20, pe: 12.5 },
  { name: 'Insurance - Specialty', sector: 'Financial Services', change: 1.40, pe: 15.5 },
  { name: 'Integrated Freight & Logistics', sector: 'Industrials', change: 0.90, pe: 16.8 },
  { name: 'Internet Content & Information', sector: 'Technology', change: 3.50, pe: 52.0 },
  { name: 'Investment - Banking & Investment Services', sector: 'Financial Services', change: 1.60, pe: 13.5 },
  { name: 'Leisure', sector: 'Consumer Cyclical', change: 1.80, pe: 24.0 },
  { name: 'Luxury Goods', sector: 'Consumer Cyclical', change: 2.45, pe: 23.7 },
  { name: 'Manufacturing - Metal Fabrication', sector: 'Industrials', change: 1.20, pe: 15.0 },
  { name: 'Manufacturing - Tools & Accessories', sector: 'Industrials', change: 1.40, pe: 17.5 },
  { name: 'Marine Shipping', sector: 'Industrials', change: -0.50, pe: 8.5 },
  { name: 'Medical - Care Facilities', sector: 'Healthcare', change: 0.70, pe: 20.0 },
  { name: 'Medical - Devices', sector: 'Healthcare', change: 2.10, pe: 32.0 },
  { name: 'Medical - Diagnostics & Research', sector: 'Healthcare', change: 1.90, pe: 28.5 },
  { name: 'Medical - Distribution', sector: 'Healthcare', change: 1.10, pe: 16.0 },
  { name: 'Medical - Equipment & Services', sector: 'Healthcare', change: 1.50, pe: 25.0 },
  { name: 'Medical - Healthcare Information Services', sector: 'Healthcare', change: 2.00, pe: 45.0 },
  { name: 'Medical - Healthcare Plans', sector: 'Healthcare', change: 1.30, pe: 18.0 },
  { name: 'Medical - Instruments & Supplies', sector: 'Healthcare', change: 1.80, pe: 29.0 },
  { name: 'Medical - Pharmaceuticals', sector: 'Healthcare', change: 0.50, pe: 18.0 },
  { name: 'Oil & Gas Energy', sector: 'Energy', change: -0.80, pe: 9.5 },
  { name: 'Oil & Gas Equipment & Services', sector: 'Energy', change: -0.50, pe: 12.0 },
  { name: 'Oil & Gas Exploration & Production', sector: 'Energy', change: -1.20, pe: 8.5 },
  { name: 'Oil & Gas Integrated', sector: 'Energy', change: -0.60, pe: 9.0 },
  { name: 'Oil & Gas Midstream', sector: 'Energy', change: 0.20, pe: 11.5 },
  { name: 'Oil & Gas Refining & Marketing', sector: 'Energy', change: -0.30, pe: 8.0 },
  { name: 'Other Precious Metals', sector: 'Basic Materials', change: 2.10, pe: 14.5 },
  { name: 'Packaged Foods', sector: 'Consumer Defensive', change: 0.40, pe: 20.0 },
  { name: 'Packaging & Containers', sector: 'Consumer Cyclical', change: 1.10, pe: 15.5 },
  { name: 'Paper, Lumber & Forest Products', sector: 'Basic Materials', change: 0.90, pe: 13.0 },
  { name: 'Personal Products & Services', sector: 'Consumer Defensive', change: 0.70, pe: 22.5 },
  { name: 'Publishing', sector: 'Communication Services', change: 0.80, pe: 16.0 },
  { name: 'Railroads', sector: 'Industrials', change: 2.47, pe: 42.5 },
  { name: 'Real Estate - Development', sector: 'Real Estate', change: 0.30, pe: 18.0 },
  { name: 'Real Estate - General', sector: 'Real Estate', change: 0.50, pe: 19.5 },
  { name: 'Real Estate - Services', sector: 'Real Estate', change: 0.90, pe: 21.0 },
  { name: 'Regulated Electric', sector: 'Utilities', change: 0.60, pe: 18.5 },
  { name: 'Regulated Water', sector: 'Utilities', change: 0.70, pe: 22.0 },
  { name: 'REIT - Diversified', sector: 'Real Estate', change: 1.20, pe: 32.0 },
  { name: 'REIT - Healthcare Facilities', sector: 'Real Estate', change: 1.50, pe: 28.0 },
  { name: 'REIT - Industrial', sector: 'Real Estate', change: 1.80, pe: 35.0 },
  { name: 'REIT - Mortgage', sector: 'Real Estate', change: -0.30, pe: 11.0 },
  { name: 'REIT - Retail', sector: 'Real Estate', change: 1.10, pe: 25.0 },
  { name: 'REIT - Specialty', sector: 'Real Estate', change: 2.46, pe: 34.8 },
  { name: 'Renewable Utilities', sector: 'Utilities', change: 2.80, pe: 40.0 },
  { name: 'Rental & Leasing Services', sector: 'Industrials', change: 1.40, pe: 15.0 },
  { name: 'Residential Construction', sector: 'Consumer Cyclical', change: 1.90, pe: 12.0 },
  { name: 'Restaurants', sector: 'Consumer Cyclical', change: 1.60, pe: 26.0 },
  { name: 'Security & Protection Services', sector: 'Industrials', change: 2.45, pe: 33.6 },
  { name: 'Semiconductors', sector: 'Technology', change: 4.20, pe: 45.0 },
  { name: 'Shell Companies', sector: 'Real Estate', change: 2.50, pe: 16.0 },
  { name: 'Software - Application', sector: 'Technology', change: 3.80, pe: 48.0 },
  { name: 'Software - Infrastructure', sector: 'Technology', change: 3.20, pe: 38.0 },
  { name: 'Software - Services', sector: 'Technology', change: 2.50, pe: 35.0 },
  { name: 'Solar', sector: 'Technology', change: -1.50, pe: 55.0 },
  { name: 'Specialty Business Services', sector: 'Industrials', change: 1.30, pe: 21.0 },
  { name: 'Specialty Retail', sector: 'Consumer Cyclical', change: 1.70, pe: 24.0 },
  { name: 'Staffing & Employment Services', sector: 'Industrials', change: 0.90, pe: 16.5 },
  { name: 'Steel', sector: 'Basic Materials', change: 1.50, pe: 10.0 },
  { name: 'Technology Distributors', sector: 'Technology', change: 2.10, pe: 18.0 },
  { name: 'Telecommunications Services', sector: 'Communication Services', change: 2.42, pe: 13.9 },
  { name: 'Tobacco', sector: 'Consumer Defensive', change: 0.30, pe: 12.5 },
  { name: 'Travel Lodging', sector: 'Consumer Cyclical', change: 1.80, pe: 22.0 },
  { name: 'Travel Services', sector: 'Consumer Cyclical', change: 2.42, pe: 18.1 },
  { name: 'Trucking', sector: 'Industrials', change: 1.10, pe: 19.5 },
  { name: 'Waste Management', sector: 'Industrials', change: 1.40, pe: 28.0 },
]

// Search and Sort State
const industrySearch = ref('')
const industrySort = ref('perf') // 'perf', 'pe', 'name'

const filteredIndustries = computed(() => {
  let result = [...industryList]
  
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
