<template>
  <div class="market-analysis">
    <!-- Row 1: Sector Performance & Valuation -->
    <div class="section-container">
      <div class="section-header">
        <h2>SECTOR PERFORMANCE & VALUATION</h2>
        <div class="exchanges">NASDAQ <span class="divider">/</span> NYSE <span class="divider">/</span> AMEX <span class="divider">/</span> CBOE</div>
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

    <!-- Row 2: Industry Performance & Valuation -->
    <div class="section-container">
      <div class="section-header">
        <h2>INDUSTRY PERFORMANCE & VALUATION</h2>
        <div class="exchanges">NASDAQ <span class="divider">/</span> NYSE <span class="divider">/</span> AMEX <span class="divider">/</span> CBOE</div>
      </div>
      
      <div class="charts-row">
        <!-- Chart 03: Key Industry Performance -->
        <div class="chart-wrapper">
          <h3 class="chart-title">03. KEY INDUSTRY PERFORMANCE</h3>
          <div class="chart-content">
            <Bar :data="industryPerformanceData" :options="horizontalBarOptions" />
          </div>
        </div>

        <!-- Chart 04: Industry Valuation Ratios -->
        <div class="chart-wrapper">
          <h3 class="chart-title">04. INDUSTRY VALUATION RATIOS</h3>
          <div class="chart-content">
            <Bar :data="industryPeData" :options="verticalBarOptions" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
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

// 01. Sector Performance
const sectors = [
  'Technology', 'Comm. Services', 'Consumer Disc.', 'Materials', 
  'Financials', 'Health Care', 'Consumer Staples', 'Industrials', 
  'Utilities', 'Real Estate', 'Energy'
]
const sectorValues = [14.5, 12.2, 7.8, 4.2, 3.1, 2.0, 0.5, -2.1, -4.5, -8.2, -12.5]

const sectorPerformanceData = computed(() => ({
  labels: sectors,
  datasets: [{
    data: sectorValues,
    backgroundColor: sectorValues.map(v => v >= 0 ? COLOR_POSITIVE : COLOR_NEGATIVE),
    borderRadius: 2,
    barThickness: 12
  }]
}))

// 02. P/E Distribution
const sectorPeMap = [
  { label: 'Real Estate', value: 36 },
  { label: 'Technology', value: 33 },
  { label: 'Consumer Disc.', value: 28 },
  { label: 'Health Care', value: 24 },
  { label: 'Consumer Staples', value: 22 },
  { label: 'Comm. Services', value: 21 },
  { label: 'Industrials', value: 19 },
  { label: 'Utilities', value: 17.5 },
  { label: 'Materials', value: 16 },
  { label: 'Financials', value: 14 },
  { label: 'Energy', value: 11 }
]
const sectorPeData = computed(() => ({
  labels: sectorPeMap.map(i => i.label),
  datasets: [{
    data: sectorPeMap.map(i => i.value),
    backgroundColor: COLOR_NEUTRAL,
    borderRadius: 2,
    barThickness: 12
  }]
}))

// 03. Industry Performance
const industries = [
  'Semiconductors', 'Software', 'Internet Retail', 'Auto Manufacturers',
  'Major Banks', 'Aerospace/Defense', 'Insurance', 'Biotechnology',
  'Telecomm', 'Retail', 'Pharmaceuticals', 'Oil & Gas'
]
const industryValues = [8.5, 7.2, 5.1, 4.5, 3.8, 3.0, 2.5, 2.1, 1.5, 0.8, -0.5, -5.2]

const industryPerformanceData = computed(() => ({
  labels: industries,
  datasets: [{
    data: industryValues,
    backgroundColor: industryValues.map(v => v >= 0 ? COLOR_POSITIVE : COLOR_NEGATIVE),
    borderRadius: 2,
    barThickness: 10
  }]
}))

// 04. Industry Valuation
const industryPeMap = [
  { label: 'Internet Retail', value: 52 },
  { label: 'Semiconductors', value: 45 },
  { label: 'Software', value: 38 },
  { label: 'Biotechnology', value: 30 },
  { label: 'Retail', value: 24 },
  { label: 'Aerospace/Defense', value: 21 },
  { label: 'Pharmaceuticals', value: 18 },
  { label: 'Auto Manufacturers', value: 15 },
  { label: 'Telecomm', value: 14 },
  { label: 'Insurance', value: 13 },
  { label: 'Major Banks', value: 12 },
  { label: 'Oil & Gas', value: 9 }
]

const industryPeData = computed(() => ({
  labels: industryPeMap.map(i => i.label),
  datasets: [{
    data: industryPeMap.map(i => i.value),
    backgroundColor: COLOR_NEUTRAL,
    borderRadius: 2,
    barThickness: 10
  }]
}))

</script>

<style scoped>
.market-analysis {
  padding: 1rem 0;
  display: flex;
  flex-direction: column;
  gap: 3rem;
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
}

.divider {
  color: #e5e7eb;
  margin: 0 4px;
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
</style>
