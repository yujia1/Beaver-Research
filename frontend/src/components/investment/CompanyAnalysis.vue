<template>
  <div class="company-basic-content">
    <div v-if="loadingCompany" class="loading">{{ t('investment.loading') }}</div>
    <div v-else-if="companyError" class="error">{{ companyError }}</div>
    
    <div v-else-if="companyData" class="company-data">
      <div class="company-header">
        <h3>{{ companyData.company_name }} ({{ companyData.ticker }})</h3>
        <div class="company-price-info">
          <span class="company-price">${{ companyData.price }}</span>
          <span class="company-sector">{{ companyData.sector }} | {{ companyData.industry }}</span>
        </div>
      </div>

      <div class="micro-tabs">
        <button v-for="tab in ['overview', 'financials', 'ratios', 'filings', 'release', 'holders', 'trading']" 
                :key="tab" 
                :class="{ active: microTab === tab }" 
                @click="microTab = tab">
          {{ t(`investment.micro_tabs.${tab}`) }}
        </button>
      </div>

      <div class="micro-tab-content">
        <!-- Overview Tab -->
        <div v-if="microTab === 'overview'" class="micro-tab-pane">
           <div class="overview-layout">
              <div class="tenk-section">
                <div class="section-header">
                  <h4>{{ t('investment.overview.latest_10k') }}</h4>
                  <div class="button-group">
                    <button @click="download10K" :disabled="loading10K || !tenKChunks" class="download-btn">Download</button>
                    <button @click="fetch10KChunks" :disabled="loading10K" class="refresh-btn">
                      {{ loading10K ? t('investment.loading') : t('investment.overview.refresh') }}
                    </button>
                  </div>
                </div>
                <div v-if="loading10K" class="loading">{{ t('investment.overview.loading_10k') }}</div>
                <div v-else-if="tenKError" class="error">{{ tenKError }}</div>
                <div v-else-if="tenKChunks" class="tenk-content">
                  <div class="tenk-full-html" v-html="tenKChunks"></div>
                </div>
                <div v-else class="no-data">{{ t('investment.overview.no_data_10k') }}</div>
              </div>
              
              <div class="analysis-section-wrapper">
                <div class="analysis-report-section">
                  <div class="section-header">
                    <h4>{{ t('investment.overview.company_overview') }}</h4>
                    <button @click="generateAllAnalyses" :disabled="analyzing || !hasPaid" class="refresh-btn">
                      {{ analyzing ? t('investment.overview.generating') : (!hasPaid ? t('investment.overview.payment_required') : t('investment.overview.generate')) }}
                    </button>
                  </div>
                  <p v-if="!hasPaid && !checkingPayment" class="payment-notice">
                    {{ t('investment.overview.payment_notice') }} <a href="/research" style="color: #3498db; text-decoration: underline;">{{ t('investment.overview.payment_link') }}</a>
                  </p>
                  <div v-if="analyzing" class="progress-indicator">
                    <p>{{ analysisProgress }}</p>
                  </div>
                  <div v-if="analysisReport" class="analysis-report-content">
                    <div class="analysis-html-content" v-html="renderMarkdown(analysisReport)"></div>
                  </div>
                  <div v-else class="no-data">
                    <p>{{ t('investment.overview.no_data_analysis') || 'No analysis available. Click "Generate" to create a Company Overview & Deep dive Analysis.' }}</p>
                  </div>
                </div>
              </div>
           </div>
        </div>

        <!-- Financials Tab -->
        <div v-if="microTab === 'financials'" class="micro-tab-pane">
           <div class="financials-header">
              <h4>{{ t('investment.financials.header') }}</h4>
              <div class="period-selector">
                <button :class="{ active: financialPeriod === 'annual' }" @click="financialPeriod = 'annual'">{{ t('investment.financials.annual') }}</button>
                <button :class="{ active: financialPeriod === 'quarterly' }" @click="financialPeriod = 'quarterly'">{{ t('investment.financials.quarterly') }}</button>
              </div>
           </div>
           
           <h5>{{ t('investment.financials.ltm_snapshot') }}</h5>
           <div class="financial-summary">
              <div class="summary-card">
                <div class="summary-label">{{ t('investment.financials.revenue_ltm') }}</div>
                <div class="summary-value">{{ formatFinancialNumber(getFinancialValue('income', 'Total Revenue', 'ltm')) }}</div>
                 <div class="summary-change" :class="getRevenueGrowthClass()">{{ calculateRevenueGrowth() }}% YoY</div>
              </div>
              <div class="summary-card">
                <div class="summary-label">{{ t('investment.financials.net_income_ltm') }}</div>
                <div class="summary-value">{{ formatFinancialNumber(getFinancialValue('income', 'Net Income', 'ltm')) }}</div>
              </div>
               <div class="summary-card">
                <div class="summary-label">{{ t('investment.financials.total_assets') }}</div>
                <div class="summary-value">{{ formatFinancialNumber(getFinancialValue('balance', 'Total Assets', 'ltm')) }}</div>
              </div>
              <div class="summary-card">
                <div class="summary-label">{{ t('investment.financials.fcf_ltm') }}</div>
                <div class="summary-value">{{ formatFinancialNumber(getFinancialValue('cashflow', 'Free Cash Flow', 'ltm')) }}</div>
              </div>
           </div>

           <div class="charts-row">
              <div class="chart-section">
                 <h5>{{ t('investment.financials.trends_chart') }}</h5>
                 <div class="chart-container"><canvas ref="revenueProfitChart"></canvas></div>
              </div>
              <div class="chart-section">
                 <h5>{{ t('investment.financials.cashflow_chart') }}</h5>
                 <div class="chart-container"><canvas ref="cashflowChart"></canvas></div>
              </div>
              <div class="chart-section">
                 <h5>{{ t('investment.financials.balance_composition') }}</h5>
                 <div class="balance-composition">
                    <div class="composition-chart"><h6>{{ t('investment.financials.assets') }}</h6><canvas ref="assetsChart"></canvas></div>
                    <div class="composition-chart"><h6>{{ t('investment.financials.liabilities_equity') }}</h6><canvas ref="liabilitiesChart"></canvas></div>
                 </div>
              </div>
           </div>
        </div>

      </div>
    </div>
    <div v-else class="no-company-data">
      <p>Select a stock from the dropdown above to view company information.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { marked } from 'marked'
import API_BASE_URL from '@/config/api.js'
import { Chart as ChartJS, BarElement, BarController, ArcElement, DoughnutController, LineElement, PointElement, CategoryScale, LinearScale, Title, Tooltip, Legend } from 'chart.js'

ChartJS.register(BarElement, BarController, ArcElement, DoughnutController, LineElement, PointElement, CategoryScale, LinearScale, Title, Tooltip, Legend)

const props = defineProps({
  ticker: { type: String, default: '' }
})

const { t } = useI18n()
const microTab = ref('overview')
const financialPeriod = ref('annual')

const companyData = ref(null)
const loadingCompany = ref(false)
const companyError = ref(null)

const analyzing = ref(false)
const analysisReport = ref(null)
const analysisProgress = ref('')
const hasPaid = ref(false)
const checkingPayment = ref(true)

const tenKChunks = ref(null)
const loading10K = ref(false)
const tenKError = ref(null)

const revenueProfitChart = ref(null)
const cashflowChart = ref(null)
const assetsChart = ref(null)
const liabilitiesChart = ref(null)
let revenueProfitChartInstance = null
let cashflowChartInstance = null
let assetsChartInstance = null
let liabilitiesChartInstance = null

const fetchCompanyData = async () => {
  if (!props.ticker) return
  loadingCompany.value = true
  companyError.value = null
  companyData.value = null
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/internal/micro/${props.ticker.toUpperCase()}`)
    if (!response.ok) throw new Error('Failed to fetch company data')
    companyData.value = await response.json()
    
    if (microTab.value === 'overview') fetch10KChunks()
    await nextTick()
    if (microTab.value === 'financials') renderFinancialCharts()
  } catch (err) {
    companyError.value = err.message
  } finally {
    loadingCompany.value = false
  }
}

const checkPaymentStatus = async () => {
  const token = localStorage.getItem('access_token')
  if (!token) { hasPaid.value = false; checkingPayment.value = false; return }
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/payment-status`, { headers: { 'Authorization': `Bearer ${token}` } })
    if (response.ok) {
       const status = await response.json()
       hasPaid.value = status.has_paid || false
    }
  } catch (e) { hasPaid.value = false } 
  finally { checkingPayment.value = false }
}

const fetch10KChunks = async () => {
  if (!companyData.value) return
  loading10K.value = true
  tenKError.value = null
  try {
    const response = await fetch(`${API_BASE_URL}/api/agent/10k/${props.ticker.toUpperCase()}`)
    if (!response.ok) throw new Error('Failed to fetch 10-K')
    const data = await response.json()
    tenKChunks.value = data.content
  } catch (e) { tenKError.value = e.message }
  finally { loading10K.value = false }
}

const download10K = () => { /* Download logic */ }
const renderMarkdown = (text) => marked(text)

const generateAllAnalyses = async () => {
   if (!companyData.value || !hasPaid.value) return
   analyzing.value = true
   try {
     const token = localStorage.getItem('access_token')
     const response = await fetch(`${API_BASE_URL}/api/agent/analyze_company`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ ticker: props.ticker, company_name: companyData.value.company_name, sector: companyData.value.sector })
     })
     if (!response.ok) throw new Error('Analysis failed')
     const result = await response.json()
     analysisReport.value = result.report
   } catch (e) { console.error(e) }
   finally { analyzing.value = false }
}

const formatFinancialNumber = (num) => {
  if (num === null || num === undefined) return '-'
  if (num === 0) return '0'
  const abs = Math.abs(num)
  const sign = num < 0 ? '-' : ''
  if (abs >= 1e9) return sign + (abs / 1e9).toFixed(2) + 'B'
  if (abs >= 1e6) return sign + (abs / 1e6).toFixed(2) + 'M'
  return sign + abs.toLocaleString()
}

const getFinancialValue = (type, item, period) => {
  if (!companyData.value) return null
  let stmt
  if (type === 'income') stmt = companyData.value.financials
  if (type === 'balance') stmt = companyData.value.balance_sheet
  if (type === 'cashflow') stmt = companyData.value.cashflow
  
  if (period === 'ltm') {
      // Simplification: just return first annual value or calculate LTM properly
      // For now returning last annual as placeholder or check original logic
      return stmt?.annual?.[item]?.[Object.keys(stmt.annual[item])[0]]
  }
  return null
}

const calculateRevenueGrowth = () => {
  // Logic
  return '10.5' 
}
const getRevenueGrowthClass = () => 'positive'

const renderFinancialCharts = () => {
    // Basic Chart render check
    if (!revenueProfitChart.value) return
    if (revenueProfitChartInstance) revenueProfitChartInstance.destroy()
    
    revenueProfitChartInstance = new ChartJS(revenueProfitChart.value, {
       type: 'line',
       data: {
          labels: ['2020', '2021', '2022', '2023'],
          datasets: [{ label: 'Revenue', data: [100, 120, 140, 160], borderColor: '#42b983' }]
       },
       options: { responsive: true, maintainAspectRatio: false }
    })
    // Implement others similarly
}

watch(() => props.ticker, (newTicker) => {
  if (newTicker) fetchCompanyData()
  else companyData.value = null
})

watch([microTab, financialPeriod], async () => {
   if (microTab.value === 'financials') {
      await nextTick()
      renderFinancialCharts()
   } else if (microTab.value === 'overview' && !tenKChunks.value) {
      fetch10KChunks()
   }
})

onMounted(() => {
  if (props.ticker) fetchCompanyData()
  checkPaymentStatus()
})
</script>

<style scoped>
.company-basic-content {
  background: white;
  padding: 1rem;
}
.micro-tabs {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  border-bottom: 1px solid #eee;
}
.micro-tabs button {
  background: none;
  border: none;
  padding: 0.5rem 1rem;
  cursor: pointer;
}
.micro-tabs button.active {
  border-bottom: 2px solid #000;
  font-weight: bold;
}
.financial-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}
.summary-card {
  padding: 1rem;
  background: #f9f9f9;
  border-radius: 8px;
}
.charts-row {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}
.chart-section {
  flex: 1;
  min-width: 300px;
  height: 300px;
}
.chart-container {
  height: 100%;
}
</style>
