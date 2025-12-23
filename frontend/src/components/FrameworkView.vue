<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import API_BASE_URL from '@/config/api.js'
import { useFinancialData } from '@/composables/useFinancialData'
import { useFrameworkAnalysis } from '@/composables/useFrameworkAnalysis'
import { 
  formatCurrency, 
  formatValue, 
  formatLineItemName, 
  formatPercentage, 
} from '@/utils/financialUtils'
import FinancialStatementTable from '@/components/framework/FinancialStatementTable.vue'
import FinancialChart from '@/components/framework/charts/FinancialChart.vue'


const { t } = useI18n()

// State
const ticker = ref('')
const mainTab = ref('statements') // statements or fundamental_analysis
const activeTab = ref('income') // income, cash_flow, balance_sheet
const analysisTab = ref('profile') // profile, pricing_power, financial_health, working_capital, capex, valuation, structure
const profileTab = ref('business') // business, employee_count, mergers_acquisitions
const period = ref('annual') // annual or quarter
// State & Data from Composable
const { 
  loading, 
  error, 
  incomeData, 
  cashFlowData, 
  balanceSheetData, 
  revenueSegmentation, 
  dcfData, 
  earningsCalendar, 
  employeeCount, 
  mergersAcquisitions,
  fetchFinancialData: fetchFinData 
} = useFinancialData()

// Fetch financial data wrapper
const fetchFinancialData = async () => {
  await fetchFinData(ticker.value, period.value)
}

// Get current data based on active tab
const currentData = computed(() => {
  switch (activeTab.value) {
    case 'income':
      return incomeData.value
    case 'cash_flow':
      return cashFlowData.value
    case 'balance_sheet':
      return balanceSheetData.value
    default:
      return []
  }
})

// Get years/periods from data
const periods = computed(() => {
  if (!currentData.value || currentData.value.length === 0) return []
  return currentData.value.map(item => item.date || item.calendarYear)
})


// Get unique product names from revenue segmentation
const productNames = computed(() => {
  if (!revenueSegmentation.value || revenueSegmentation.value.length === 0) return []
  
  // Get product names from the first entry's data object
  const firstEntry = revenueSegmentation.value[0]
  if (!firstEntry || !firstEntry.data) return []
  
  return Object.keys(firstEntry.data)
})

// Get all line items for current statement type
const lineItems = computed(() => {
  if (!currentData.value || currentData.value.length === 0) return []
  
  const firstItem = currentData.value[0]
  const excludeKeys = ['date', 'symbol', 'reportedCurrency', 'cik', 'fillingDate', 'filingDate', 'acceptedDate', 'calendarYear', 'period', 'link', 'finalLink', 'fiscalYear']
  
  return Object.keys(firstItem).filter(key => !excludeKeys.includes(key))
})

// Income statement categories
const incomeCategories = [
  {
    name: 'Revenue & Direct Costs',
    fields: ['revenue', 'costOfRevenue', 'grossProfit']
  },
  {
    name: 'Operating Expenses',
    fields: ['researchAndDevelopmentExpenses', 'generalAndAdministrativeExpenses', 'sellingAndMarketingExpenses', 'sellingGeneralAndAdministrativeExpenses', 'otherExpenses', 'operatingExpenses', 'costAndExpenses']
  },
  {
    name: 'Profitability Metrics (Core Operations)',
    fields: ['operatingIncome', 'depreciationAndAmortization', 'ebitda', 'ebitdaratio', 'operatingIncomeRatio']
  },
  {
    name: 'Non-Operating, Interest & Taxes',
    fields: ['totalOtherIncomeExpensesNet', 'incomeBeforeTax', 'incomeBeforeTaxRatio', 'incomeTaxExpense', 'netInterestIncome', 'interestIncome', 'interestExpense']
  },
  {
    name: 'Net Income (Bottom Line)',
    fields: ['netIncome', 'netIncomeRatio', 'eps', 'epsdiluted']
  },
  {
    name: 'Shareholder Data',
    fields: ['weightedAverageShsOut', 'weightedAverageShsOutDil']
  }
]

// Cash flow statement categories
const cashFlowCategories = [
  {
    name: 'Operating Activities (Cash from Operations)',
    fields: ['netIncome', 'depreciationAndAmortization', 'deferredIncomeTax', 'stockBasedCompensation', 'changeInWorkingCapital', 'accountsReceivables', 'inventory', 'accountsPayables', 'otherWorkingCapital', 'otherNonCashItems', 'netCashProvidedByOperatingActivities']
  },
  {
    name: 'Investing Activities (Cash for Investing)',
    fields: ['investmentsInPropertyPlantAndEquipment', 'acquisitionsNet', 'purchasesOfInvestments', 'salesMaturitiesOfInvestments', 'otherInvestingActivites', 'netCashUsedForInvestingActivites']
  },
  {
    name: 'Financing Activities (Cash from Financing)',
    fields: ['debtRepayment', 'commonStockIssued', 'commonStockRepurchased', 'dividendsPaid', 'otherFinancingActivites', 'netCashUsedProvidedByFinancingActivities']
  },
  {
    name: 'Cash Reconciliation',
    fields: ['effectOfForexChangesOnCash', 'netChangeInCash', 'cashAtBeginningOfPeriod', 'cashAtEndOfPeriod']
  },
  {
    name: 'Supplemental Metrics',
    fields: ['operatingCashFlow', 'capitalExpenditure', 'freeCashFlow']
  }
]

// Balance sheet categories
const balanceSheetCategories = [
  {
    name: 'Assets (What the Company Owns)',
    subcategories: [
      {
        name: 'Current Assets (Liquid, <1 year)',
        fields: ['cashAndCashEquivalents', 'shortTermInvestments', 'cashAndShortTermInvestments', 'netReceivables', 'inventory', 'otherCurrentAssets', 'totalCurrentAssets']
      },
      {
        name: 'Non-Current Assets (Long-term, >1 year)',
        fields: ['propertyPlantEquipmentNet', 'goodwill', 'intangibleAssets', 'goodwillAndIntangibleAssets', 'longTermInvestments', 'taxAssets', 'otherNonCurrentAssets', 'totalNonCurrentAssets']
      }
    ],
    fields: ['otherAssets', 'totalAssets']
  },
  {
    name: 'Liabilities (What the Company Owes)',
    subcategories: [
      {
        name: 'Current Liabilities (Due within 1 year)',
        fields: ['accountPayables', 'shortTermDebt', 'taxPayables', 'deferredRevenue', 'otherCurrentLiabilities', 'totalCurrentLiabilities']
      },
      {
        name: 'Non-Current Liabilities (Due after 1 year)',
        fields: ['longTermDebt', 'deferredRevenueNonCurrent', 'deferredTaxLiabilitiesNonCurrent', 'otherNonCurrentLiabilities', 'totalNonCurrentLiabilities']
      }
    ],
    fields: ['otherLiabilities', 'capitalLeaseObligations', 'totalLiabilities']
  },
  {
    name: "Shareholders' Equity (Net Worth)",
    fields: ['preferredStock', 'commonStock', 'retainedEarnings', 'accumulatedOtherComprehensiveIncomeLoss', 'othertotalStockholdersEquity', 'totalStockholdersEquity', 'totalEquity', 'totalInvestments', 'totalDebt', 'netDebt']
  },
  {
    name: 'Supplemental / Summary Metrics',
    fields: ['totalLiabilitiesAndTotalEquity', 'minorityInterest', 'totalInvestments', 'totalDebt', 'netDebt']
  }
]


// Get categorized line items based on active tab
const categorizedLineItems = computed(() => {
  if (!currentData.value || currentData.value.length === 0) {
    return []
  }
  
  const firstItem = currentData.value[0]
  const availableFields = Object.keys(firstItem)
  
  let categories = []
  if (activeTab.value === 'income') {
    categories = incomeCategories
  } else if (activeTab.value === 'cash_flow') {
    categories = cashFlowCategories
  } else if (activeTab.value === 'balance_sheet') {
    categories = balanceSheetCategories
  } else {
    return []
  }
  
  // Process categories and filter by available fields
  return categories.map(category => {
    const processedCategory = {
      ...category,
      fields: category.fields ? category.fields.filter(field => availableFields.includes(field)) : []
    }
    
    // Handle subcategories for balance sheet
    if (category.subcategories) {
      processedCategory.subcategories = category.subcategories.map(sub => ({
        ...sub,
        fields: sub.fields.filter(field => availableFields.includes(field))
      })).filter(sub => sub.fields.length > 0)
    }
    
    return processedCategory
  }).filter(category => {
    // Keep category if it has fields or subcategories with fields
    return category.fields.length > 0 || (category.subcategories && category.subcategories.length > 0)
  })
})


// Framework Analysis (Charts & Data)
const {
    pricingPowerData,
    financialHealthData,
    workingCapitalData,
    capexAnalysisData,

    pricingPowerChartConfig,
    incomeVsCashFlowChartConfig,
    freeCashFlowChartConfig,
    capexChartConfig,
    arVsNiGrowthChartConfig,
    inventoryGrowthChartConfig,
    apGrowthChartConfig,
    capexAnalysisChartConfig
} = useFrameworkAnalysis(incomeData, cashFlowData)


// Handle search
const handleSearch = () => {
  fetchFinancialData()
}

// Handle period change
const changePeriod = (newPeriod) => {
  period.value = newPeriod
  if (ticker.value) {
    fetchFinancialData()
  }
}
</script>

<template>
  <div class="framework-container">
    <!-- Header -->
    <div class="header">
      <div>
        <h1 class="title">{{ t('framework.title') }}</h1>
        <p class="subtitle">{{ t('framework.subtitle') }}</p>
      </div>
    </div>

    <!-- Search Bar -->
    <div class="search-section">
      <input
        v-model="ticker"
        type="text"
        :placeholder="t('framework.ticker_placeholder')"
        class="ticker-input"
        @keyup.enter="handleSearch"
      />
      <button @click="handleSearch" class="search-btn" :disabled="loading">
        {{ loading ? t('framework.loading') : t('framework.search') }}
      </button>
    </div>

    <!-- Content -->
    <div v-if="ticker && !loading && !error" class="content">
      <!-- Company Header -->
      <div class="company-header">
        <h2>{{ ticker.toUpperCase() }}</h2>
        <p class="dataset-label">{{ period === 'annual' ? 'ANNUAL DATASET' : 'QUARTERLY DATASET' }}</p>
      </div>

      <!-- Tab Navigation -->
      <div class="tabs-section">
        <!-- Main Tabs -->
        <div class="main-tabs">
          <button
            :class="['main-tab', { active: mainTab === 'statements' }]"
            @click="mainTab = 'statements'"
          >
            {{ t('framework.main_tabs.statements') }}
          </button>
          <button
            :class="['main-tab', { active: mainTab === 'fundamental_analysis' }]"
            @click="mainTab = 'fundamental_analysis'"
          >
            {{ t('framework.main_tabs.fundamental_analysis') }}
          </button>
        </div>

        <!-- Sub-tabs and Period Toggle Container -->
        <div class="sub-tabs-container">
          <!-- Sub-tabs (only show for Financial Statements) -->
          <div v-if="mainTab === 'statements'" class="tabs">
            <button
              :class="['tab', { active: activeTab === 'income' }]"
              @click="activeTab = 'income'"
            >
              {{ t('framework.tabs.income') }}
            </button>
            <button
              :class="['tab', { active: activeTab === 'cash_flow' }]"
              @click="activeTab = 'cash_flow'"
            >
              {{ t('framework.tabs.cash_flow') }}
            </button>
            <button
              :class="['tab', { active: activeTab === 'balance_sheet' }]"
              @click="activeTab = 'balance_sheet'"
            >
              {{ t('framework.tabs.balance_sheet') }}
            </button>
          </div>

          <!-- Analysis Sub-tabs (only show for Fundamental Analysis) -->
          <div v-if="mainTab === 'fundamental_analysis'" class="tabs">
            <button
              :class="['tab', { active: analysisTab === 'profile' }]"
              @click="analysisTab = 'profile'"
            >
              {{ t('framework.analysis_tabs.profile') }}
            </button>
            <button
              :class="['tab', { active: analysisTab === 'pricing_power' }]"
              @click="analysisTab = 'pricing_power'"
            >
              {{ t('framework.analysis_tabs.pricing_power') }}
            </button>
            <button
              :class="['tab', { active: analysisTab === 'financial_health' }]"
              @click="analysisTab = 'financial_health'"
            >
              {{ t('framework.analysis_tabs.financial_health') }}
            </button>
            <button
              :class="['tab', { active: analysisTab === 'working_capital' }]"
              @click="analysisTab = 'working_capital'"
            >
              {{ t('framework.analysis_tabs.working_capital') }}
            </button>
            <button
              :class="['tab', { active: analysisTab === 'capex' }]"
              @click="analysisTab = 'capex'"
            >
              {{ t('framework.analysis_tabs.capex') }}
            </button>
            <button
              :class="['tab', { active: analysisTab === 'valuation' }]"
              @click="analysisTab = 'valuation'"
            >
              {{ t('framework.analysis_tabs.valuation') }}
            </button>
            <button
              :class="['tab', { active: analysisTab === 'structure' }]"
              @click="analysisTab = 'structure'"
            >
              {{ t('framework.analysis_tabs.structure') }}
            </button>
          </div>

          <!-- Period Toggle -->
          <div class="period-toggle">
          <button
            :class="['period-btn', { active: period === 'annual' }]"
            @click="changePeriod('annual')"
          >
            {{ t('framework.period.annual') }}
          </button>
          <button
            :class="['period-btn', { active: period === 'quarter' }]"
            @click="changePeriod('quarter')"
          >
            {{ t('framework.period.quarterly') }}
          </button>
        </div>
        </div>
      </div>

      <!-- Financial Data Table (only show for statements tab) -->
      <FinancialStatementTable 
        v-if="mainTab === 'statements' && currentData.length > 0"
        :data="currentData"
        :periods="periods"
        :categorized-items="categorizedLineItems"
        :active-tab="activeTab"
        :period="period"
        :product-names="productNames"
        :line-items="lineItems"
        :revenue-segmentation="revenueSegmentation"
      />


      <!-- Fundamental Analysis Tab Content -->
      <div v-if="mainTab === 'fundamental_analysis'" class="fundamental-analysis">
        <!-- Profile Sub-tabs (shown directly without section wrapper) -->
        <div v-if="analysisTab === 'profile'">
          <div class="profile-tabs">
            <button
              :class="['profile-tab', { active: profileTab === 'business' }]"
              @click="profileTab = 'business'"
            >
              {{ t('framework.profile_tabs.business') }}
            </button>
            <button
              :class="['profile-tab', { active: profileTab === 'employee_count' }]"
              @click="profileTab = 'employee_count'"
            >
              {{ t('framework.profile_tabs.employee_count') }}
            </button>
            <button
              :class="['profile-tab', { active: profileTab === 'mergers_acquisitions' }]"
              @click="profileTab = 'mergers_acquisitions'"
            >
              {{ t('framework.profile_tabs.mergers_acquisitions') }}
            </button>
          </div>

          <div class="profile-content">
            <!-- Business Tab -->
            <div v-if="profileTab === 'business'">
              <p class="placeholder-text">Company business information coming soon...</p>
            </div>

            <!-- Employee Count Tab -->
            <div v-if="profileTab === 'employee_count'">
              <div v-if="employeeCount.length > 0" class="employee-table">
                <table class="simple-table">
                  <thead>
                    <tr>
                      <th>Year</th>
                      <th>Employee Count</th>
                      <th>Filing Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="emp in employeeCount" :key="emp.filingDate">
                      <td>{{ emp.year || '-' }}</td>
                      <td>{{ emp.employeeCount?.toLocaleString() || '-' }}</td>
                      <td>{{ emp.filingDate || '-' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p v-else class="placeholder-text">No employee count data available</p>
            </div>

            <!-- Mergers & Acquisitions Tab -->
            <div v-if="profileTab === 'mergers_acquisitions'">
              <div v-if="mergersAcquisitions.length > 0" class="ma-list">
                <div v-for="ma in mergersAcquisitions.slice(0, 10)" :key="ma.transactionDate" class="ma-card">
                  <div class="ma-header">
                    <h4>{{ ma.companyName || 'Unknown Company' }}</h4>
                    <span class="ma-date">{{ ma.transactionDate || '-' }}</span>
                  </div>
                  <div class="ma-details">
                    <div class="ma-row">
                      <span class="ma-label">Target:</span>
                      <span>{{ ma.targetedCompany || '-' }}</span>
                    </div>
                    <div class="ma-row">
                      <span class="ma-label">Price:</span>
                      <span>{{ ma.price ? '$' + ma.price.toLocaleString() : '-' }}</span>
                    </div>
                    <div class="ma-row">
                      <span class="ma-label">Type:</span>
                      <span>{{ ma.transactionType || '-' }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <p v-else class="placeholder-text">No M&A data available</p>
            </div>
          </div>
        </div>

        <!-- Other analysis sections with wrappers removed -->
        <div v-if="analysisTab === 'pricing_power'">
          <div v-if="pricingPowerData" class="chart-container">
            <FinancialChart 
              v-if="pricingPowerChartConfig" 
              :type="pricingPowerChartConfig.type" 
              :data="pricingPowerChartConfig.data" 
              :options="pricingPowerChartConfig.options" 
            />
          </div>
          
          <!-- Pricing Power Data Table -->
          <div v-if="pricingPowerData" class="data-table-wrapper" style="margin-top: 2rem;">
            <table class="data-table">
              <thead>
                <tr>
                  <th class="line-item-header">{{ t('framework.line_item') }}</th>
                  <th v-for="date in pricingPowerData.dates" :key="date" class="period-header">
                    {{ date }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr class="calculated-metric-row">
                  <td class="line-item-cell calculated-metric">Revenue Growth Rate ({{ period === 'annual' ? 'YoY' : 'QoQ' }})</td>
                  <td v-for="(val, index) in pricingPowerData.revenueGrowth" :key="`rev-growth-${index}`" class="data-cell calculated-value">
                    {{ formatPercentage(val / 100) }}
                  </td>
                </tr>
                <tr class="calculated-metric-row">
                  <td class="line-item-cell calculated-metric">Gross Margin</td>
                  <td v-for="(val, index) in pricingPowerData.grossMargin" :key="`gross-margin-${index}`" class="data-cell calculated-value">
                    {{ formatPercentage(val / 100) }}
                  </td>
                </tr>
                <tr class="calculated-metric-row">
                  <td class="line-item-cell calculated-metric">Operating Profit Margin</td>
                  <td v-for="(val, index) in pricingPowerData.operatingMargin" :key="`op-margin-${index}`" class="data-cell calculated-value">
                    {{ formatPercentage(val / 100) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <p v-else class="placeholder-text">No pricing power data available</p>
        </div>

          <!-- Financial Health -->
        <div v-if="analysisTab === 'financial_health'">
          <!-- Net Income & Operating Cash Flow Chart -->
          <div v-if="financialHealthData" class="chart-group">
                <div class="chart-container">
                  <h4 class="chart-subtitle">Net Income & Operating Cash Flow</h4>
                  <FinancialChart 
                    v-if="incomeVsCashFlowChartConfig" 
                    :type="incomeVsCashFlowChartConfig.type" 
                    :data="incomeVsCashFlowChartConfig.data" 
                    :options="incomeVsCashFlowChartConfig.options" 
                  />
                </div>
                
                <!-- Free Cash Flow Chart -->
                <div class="chart-container">
                  <h4 class="chart-subtitle">Free Cash Flow</h4>
                  <FinancialChart 
                    v-if="freeCashFlowChartConfig" 
                    :type="freeCashFlowChartConfig.type" 
                    :data="freeCashFlowChartConfig.data" 
                    :options="freeCashFlowChartConfig.options" 
                  />
                </div>
                
                <!-- Capital Expenditure Chart -->
                <div class="chart-container">
                  <h4 class="chart-subtitle">Capital Expenditure</h4>
                  <FinancialChart 
                    v-if="capexChartConfig" 
                    :type="capexChartConfig.type" 
                    :data="capexChartConfig.data" 
                    :options="capexChartConfig.options" 
                  />
                </div>
              </div>

              <!-- Financial Health Data Table -->
              <div v-if="financialHealthData" class="data-table-wrapper" style="margin-top: 2rem;">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th class="line-item-header">{{ t('framework.line_item') }}</th>
                      <th v-for="date in financialHealthData.dates" :key="date" class="period-header">
                        {{ date }}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr class="data-row">
                      <td class="line-item-cell">Net Income</td>
                      <td v-for="(val, index) in financialHealthData.netIncome" :key="`ni-${index}`" class="data-cell">
                        {{ formatCurrency(val) }}
                      </td>
                    </tr>
                    <tr class="data-row">
                      <td class="line-item-cell">Operating Cash Flow</td>
                      <td v-for="(val, index) in financialHealthData.operatingCashFlow" :key="`ocf-${index}`" class="data-cell">
                        {{ formatCurrency(val) }}
                      </td>
                    </tr>
                    <tr class="data-row">
                      <td class="line-item-cell">Free Cash Flow</td>
                      <td v-for="(val, index) in financialHealthData.freeCashFlow" :key="`fcf-${index}`" class="data-cell">
                        {{ formatCurrency(val) }}
                      </td>
                    </tr>
                    <tr class="data-row">
                      <td class="line-item-cell">Capital Expenditure</td>
                      <td v-for="(val, index) in financialHealthData.capex" :key="`capex-${index}`" class="data-cell">
                        {{ formatCurrency(val) }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p v-else class="placeholder-text">No financial health data available</p>
        </div>

        <!-- Working Capital Analysis -->
        <div v-if="analysisTab === 'working_capital'">
          <div v-if="workingCapitalData" class="chart-group">
                <!-- AR vs NI Growth Chart -->
                <div class="chart-container">
                  <h4 class="chart-subtitle">Accounts Receivables Growth vs Net Income Growth</h4>
                  <FinancialChart 
                    v-if="arVsNiGrowthChartConfig" 
                    :type="arVsNiGrowthChartConfig.type" 
                    :data="arVsNiGrowthChartConfig.data" 
                    :options="arVsNiGrowthChartConfig.options" 
                  />
                </div>
                
                <!-- Inventory Growth Chart -->
                <div class="chart-container">
                  <h4 class="chart-subtitle">Inventory Growth</h4>
                  <FinancialChart 
                    v-if="inventoryGrowthChartConfig" 
                    :type="inventoryGrowthChartConfig.type" 
                    :data="inventoryGrowthChartConfig.data" 
                    :options="inventoryGrowthChartConfig.options" 
                  />
                </div>
                
                <!-- Accounts Payables Growth Chart -->
                <div class="chart-container">
                  <h4 class="chart-subtitle">Accounts Payables Growth</h4>
                  <FinancialChart 
                    v-if="apGrowthChartConfig" 
                    :type="apGrowthChartConfig.type" 
                    :data="apGrowthChartConfig.data" 
                    :options="apGrowthChartConfig.options" 
                  />
                </div>
              </div>

              <!-- Working Capital Data Table -->
              <div v-if="workingCapitalData" class="data-table-wrapper" style="margin-top: 2rem;">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th class="line-item-header">{{ t('framework.line_item') }}</th>
                      <th v-for="date in workingCapitalData.dates" :key="date" class="period-header">
                        {{ date }}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr class="calculated-metric-row">
                      <td class="line-item-cell calculated-metric">Accounts Receivables Growth ({{ period === 'annual' ? 'YoY' : 'QoQ' }})</td>
                      <td v-for="(val, index) in workingCapitalData.accountsReceivablesGrowth" :key="`ar-growth-${index}`" class="data-cell calculated-value">
                        {{ formatPercentage(val / 100) }}
                      </td>
                    </tr>
                    <tr class="calculated-metric-row">
                      <td class="line-item-cell calculated-metric">Net Income Growth ({{ period === 'annual' ? 'YoY' : 'QoQ' }})</td>
                      <td v-for="(val, index) in workingCapitalData.netIncomeGrowth" :key="`ni-growth-${index}`" class="data-cell calculated-value">
                        {{ formatPercentage(val / 100) }}
                      </td>
                    </tr>
                    <tr class="calculated-metric-row">
                      <td class="line-item-cell calculated-metric">Inventory Growth ({{ period === 'annual' ? 'YoY' : 'QoQ' }})</td>
                      <td v-for="(val, index) in workingCapitalData.inventoryGrowth" :key="`inv-growth-${index}`" class="data-cell calculated-value">
                        {{ formatPercentage(val / 100) }}
                      </td>
                    </tr>
                    <tr class="calculated-metric-row">
                      <td class="line-item-cell calculated-metric">Accounts Payables Growth ({{ period === 'annual' ? 'YoY' : 'QoQ' }})</td>
                      <td v-for="(val, index) in workingCapitalData.accountsPayablesGrowth" :key="`ap-growth-${index}`" class="data-cell calculated-value">
                        {{ formatPercentage(val / 100) }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p v-else class="placeholder-text">No working capital data available</p>
            </div>

          <!-- CapEx Analysis -->
        <div v-if="analysisTab === 'capex'">
          <div v-if="capexAnalysisData" class="chart-container">
                <h4 class="chart-subtitle">CapEx Growth vs Revenue Growth</h4>
                <FinancialChart 
                  v-if="capexAnalysisChartConfig" 
                  :type="capexAnalysisChartConfig.type" 
                  :data="capexAnalysisChartConfig.data" 
                  :options="capexAnalysisChartConfig.options" 
                />
              </div>

              <!-- CapEx Analysis Data Table -->
              <div v-if="capexAnalysisData" class="data-table-wrapper" style="margin-top: 2rem;">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th class="line-item-header">{{ t('framework.line_item') }}</th>
                      <th v-for="date in capexAnalysisData.dates" :key="date" class="period-header">
                        {{ date }}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr class="calculated-metric-row">
                      <td class="line-item-cell calculated-metric">CapEx Growth ({{ period === 'annual' ? 'YoY' : 'QoQ' }})</td>
                      <td v-for="(val, index) in capexAnalysisData.capexGrowth" :key="`capex-growth-${index}`" class="data-cell calculated-value">
                        {{ formatPercentage(val / 100) }}
                      </td>
                    </tr>
                    <tr class="calculated-metric-row">
                      <td class="line-item-cell calculated-metric">Revenue Growth ({{ period === 'annual' ? 'YoY' : 'QoQ' }})</td>
                      <td v-for="(val, index) in capexAnalysisData.revenueGrowth" :key="`rev-growth-${index}`" class="data-cell calculated-value">
                        {{ formatPercentage(val / 100) }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p v-else class="placeholder-text">No CapEx analysis data available</p>
            </div>

          <!-- Valuation Analysis -->
        <div v-if="analysisTab === 'valuation'">
          <div v-if="dcfData.length > 0">
                <!-- DCF Valuation -->
                <div class="valuation-subsection">
                  <h4 class="chart-subtitle">DCF Valuation</h4>
                  <div class="dcf-grid">
                    <div v-for="dcf in dcfData.slice(0, 1)" :key="dcf.date" class="dcf-card">
                      <div class="dcf-row">
                        <span class="dcf-label">Stock Price:</span>
                        <span class="dcf-value">${{ dcf.Stock_Price?.toFixed(2) || dcf.price?.toFixed(2) || '-' }}</span>
                      </div>
                      <div class="dcf-row">
                        <span class="dcf-label">DCF Value:</span>
                        <span class="dcf-value">${{ dcf.dcf?.toFixed(2) || '-' }}</span>
                      </div>
                      <div class="dcf-row">
                        <span class="dcf-label">Date:</span>
                        <span class="dcf-value">{{ dcf.date || '-' }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <p v-else class="placeholder-text">No valuation data available</p>
            </div>

          <!-- Structure (formerly Calendar) -->
        <div v-if="analysisTab === 'structure'">
          <div v-if="earningsCalendar.length > 0">
                <!-- Earnings Calendar -->
                <div class="calendar-subsection">
                  <h4 class="chart-subtitle">Earnings Calendar</h4>
                  <div class="calendar-grid">
                    <div v-for="event in earningsCalendar.slice(0, 5)" :key="event.date" class="calendar-card">
                      <div class="calendar-row">
                        <span class="calendar-label">Date:</span>
                        <span class="calendar-value">{{ event.date || '-' }}</span>
                      </div>
                      <div class="calendar-row">
                        <span class="calendar-label">EPS Estimate:</span>
                        <span class="calendar-value">${{ event.epsEstimated?.toFixed(2) || '-' }}</span>
                      </div>
                      <div class="calendar-row">
                        <span class="calendar-label">EPS Actual:</span>
                        <span class="calendar-value">${{ event.eps?.toFixed(2) || '-' }}</span>
                      </div>
                      <div class="calendar-row">
                        <span class="calendar-label">Revenue Estimate:</span>
                        <span class="calendar-value">${{ event.revenueEstimated ? (event.revenueEstimated / 1000000).toFixed(2) + 'M' : '-' }}</span>
                      </div>
                      <div class="calendar-row">
                        <span class="calendar-label">Revenue Actual:</span>
                        <span class="calendar-value">${{ event.revenue ? (event.revenue / 1000000).toFixed(2) + 'M' : '-' }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <p v-else class="placeholder-text">No calendar data available</p>
            </div>
        </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>{{ t('framework.loading') }}</p>
    </div>

    <!-- Error State -->
    <div v-if="error && !loading" class="error-state">
      <p>{{ t('framework.error') }}: {{ error }}</p>
    </div>
  </div>
</template>

<style scoped>
.framework-container {
  padding: 2rem;
  max-width: 1600px;
  margin: 0 auto;
  min-height: calc(100vh - 4rem);
}

.header {
  margin-bottom: 2rem;
}

.title {
  font-size: 2rem;
  font-weight: 700;
  color: #000;
  margin: 0 0 0.5rem 0;
  letter-spacing: 0.5px;
}

.subtitle {
  font-size: 0.875rem;
  color: #666;
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.search-section {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  max-width: 600px;
}

.ticker-input {
  flex: 1;
  padding: 0.875rem 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
  font-family: inherit;
  transition: border-color 0.2s;
}

.ticker-input:focus {
  outline: none;
  border-color: #000;
}

.search-btn {
  padding: 0.875rem 2rem;
  background: #000;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.search-btn:hover:not(:disabled) {
  background: #333;
}

.search-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.content {
  background: #fff;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.company-header {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 2px solid #f0f0f0;
}

.company-header h2 {
  font-size: 1.75rem;
  font-weight: 700;
  color: #000;
  margin: 0 0 0.5rem 0;
}

.dataset-label {
  font-size: 0.875rem;
  color: #999;
  margin: 0;
  letter-spacing: 0.5px;
}

.tabs-section {
  margin-bottom: 2rem;
}

.main-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.main-tab {
  padding: 0.5rem 1rem;
  background: transparent;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  color: #666;
  font-weight: 500;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.main-tab:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}

.main-tab.active {
  background: #000;
  color: #fff;
  border-color: #000;
}

.sub-tabs-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.tabs {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.tab {
  padding: 0.75rem 1.5rem;
  background: transparent;
  border: none;
  border-bottom: 3px solid transparent;
  font-size: 0.9375rem;
  font-weight: 600;
  color: #999;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.tab:hover {
  color: #000;
}

.tab.active {
  color: #000;
  border-bottom-color: #000;
}

.period-toggle {
  display: flex;
  gap: 0;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
}

.period-btn {
  padding: 0.75rem 1.5rem;
  background: #fff;
  border: none;
  font-size: 0.875rem;
  font-weight: 600;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.period-btn:first-child {
  border-right: 2px solid #e0e0e0;
}

.period-btn.active {
  background: #000;
  color: #fff;
}

.period-btn:hover:not(.active) {
  background: #f5f5f5;
}

.data-table-wrapper {
  overflow-x: auto;
  margin-top: 1.5rem;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9375rem;
}

.data-table thead {
  background: #f8f8f8;
  position: sticky;
  top: 0;
  z-index: 10;
}

.data-table th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  color: #000;
  border-bottom: 2px solid #e0e0e0;
  white-space: nowrap;
}

.line-item-header {
  position: sticky;
  left: 0;
  background: #f8f8f8;
  z-index: 11;
  min-width: 250px;
}

.period-header {
  text-align: right;
  min-width: 120px;
}

.data-table tbody tr {
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.2s;
}

.data-table tbody tr:hover {
  background: #fafafa;
}

.line-item-cell {
  padding: 1rem;
  font-weight: 500;
  color: #333;
  position: sticky;
  left: 0;
  background: #fff;
  border-right: 1px solid #f0f0f0;
}

.data-table tbody tr:hover .line-item-cell {
  background: #fafafa;
}

.data-cell {
  padding: 1rem;
  text-align: right;
  color: #666;
  font-family: 'Courier New', monospace;
}

.category-header-row {
  background: #f8f8f8;
  cursor: pointer;
  transition: background 0.2s;
  border-top: 2px solid #e0e0e0;
}

.category-header-row:hover {
  background: #f0f0f0;
}

.category-header-cell {
  padding: 0.875rem 1rem !important;
  font-weight: 600;
  color: #000;
  text-align: left !important;
}

.category-header-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.category-icon {
  color: #666;
  transition: transform 0.2s;
  flex-shrink: 0;
}

.category-icon.expanded {
  transform: rotate(90deg);
}

.category-name {
  font-size: 0.9375rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.subcategory-header-row {
  background: #fafafa;
  cursor: pointer;
  transition: background 0.2s;
}

.subcategory-header-row:hover {
  background: #f5f5f5;
}

.subcategory-header-cell {
  padding: 0.75rem 1rem 0.75rem 2.5rem !important;
  font-weight: 600;
  color: #333;
  text-align: left !important;
}

.subcategory-header-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.subcategory-icon {
  width: 14px;
  height: 14px;
}

.subcategory-name {
  font-size: 0.875rem;
  font-weight: 600;
  letter-spacing: 0.3px;
}

.subcategory-data-row {
  background: #fcfcfc;
}

.subcategory-data-row:hover {
  background: #f8f8f8;
}

.subcategory-item {
  padding-left: 3.5rem !important;
  font-weight: 400;
}

.calculated-metric-row {
  background: #f0f7ff;
  border-left: 3px solid #3b82f6;
}

.calculated-metric-row:hover {
  background: #e6f2ff;
}

.calculated-metric {
  font-style: italic;
  color: #1e40af;
  font-weight: 500;
}

.calculated-value {
  color: #1e40af;
  font-weight: 600;
}

.segmentation-row {
  background: #fef3c7;
  border-left: 3px solid #f59e0b;
}

.segmentation-row:hover {
  background: #fde68a;
}

.segmentation-item {
  padding-left: 2.5rem !important;
  font-style: italic;
  color: #92400e;
  font-weight: 500;
  font-size: 0.875rem;
}

.fundamental-analysis {
  padding: 0.5rem 0;
}

.analysis-sections {
  display: grid;
  gap: 2rem;
}

.analysis-section {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1.5rem;
  transition: box-shadow 0.2s;
}

.analysis-section:hover {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #111827;
  margin: 0 0 1rem 0;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid #3b82f6;
}

.section-content {
  color: #6b7280;
}

.placeholder-text {
  font-style: italic;
  color: #9ca3af;
  margin: 0;
}

.chart-container {
  margin-bottom: 2rem;
  height: 300px;
}

.chart-group {
  display: grid;
  gap: 2rem;
}

.chart-subtitle {
  font-size: 1rem;
  font-weight: 600;
  color: #374151;
  margin: 0 0 1rem 0;
}

.valuation-subsection {
  margin-bottom: 2rem;
}

.valuation-subsection:last-child {
  margin-bottom: 0;
}

.metrics-grid,
.dcf-grid {
  display: grid;
  gap: 1rem;
}

.metric-card,
.dcf-card {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1.5rem;
}

.metric-row,
.dcf-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 0;
  border-bottom: 1px solid #e5e7eb;
}

.metric-row:last-child,
.dcf-row:last-child {
  border-bottom: none;
}

.metric-label,
.dcf-label {
  font-weight: 500;
  color: #6b7280;
}

.metric-value,
.dcf-value {
  font-weight: 600;
  color: #111827;
  font-size: 1.125rem;
}

.calendar-subsection {
  margin-bottom: 2rem;
}

.calendar-subsection:last-child {
  margin-bottom: 0;
}

.calendar-grid {
  display: grid;
  gap: 1rem;
}

.calendar-card {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1.5rem;
}

.calendar-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid #e5e7eb;
}

.calendar-row:last-child {
  border-bottom: none;
}

.calendar-label {
  font-weight: 500;
  color: #6b7280;
  font-size: 0.875rem;
}

.calendar-value {
  font-weight: 600;
  color: #111827;
}

.profile-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  border-bottom: 2px solid #e5e7eb;
  padding-bottom: 0.5rem;
}

.profile-tab {
  padding: 0.5rem 1rem;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: #6b7280;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.profile-tab:hover {
  color: #111827;
}

.profile-tab.active {
  color: #3b82f6;
  border-bottom-color: #3b82f6;
}

.simple-table {
  width: 100%;
  border-collapse: collapse;
}

.simple-table th,
.simple-table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
}

.simple-table th {
  background: #f9fafb;
  font-weight: 600;
  color: #374151;
}

.ma-list {
  display: grid;
  gap: 1rem;
}

.ma-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem;
}

.ma-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #e5e7eb;
}

.ma-header h4 {
  margin: 0;
  font-size: 1rem;
  color: #111827;
}

.ma-date {
  font-size: 0.875rem;
  color: #6b7280;
}

.ma-details {
  display: grid;
  gap: 0.5rem;
}

.ma-row {
  display: flex;
  gap: 0.5rem;
}

.ma-label {
  font-weight: 600;
  color: #6b7280;
  min-width: 80px;
}

.loading-state,
.error-state,
.empty-state,
.no-data {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  color: #999;
  text-align: center;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f0f0f0;
  border-top-color: #000;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-state {
  color: #ef4444;
}

.no-data-message {
  text-align: center;
  padding: 3rem 0;
  color: #9ca3af;
  font-style: italic;
}

.no-data-message p {
  margin: 0;
  font-size: 1rem;
}

.empty-state svg {
  color: #d0d0d0;
  margin-bottom: 1rem;
}

@media (max-width: 768px) {
  .framework-container {
    padding: 1rem;
  }

  .title {
    font-size: 1.5rem;
  }

  .search-section {
    flex-direction: column;
  }

  .tabs-section {
    flex-direction: column;
    align-items: stretch;
  }

  .tabs {
    justify-content: center;
  }

  .period-toggle {
    width: 100%;
  }

  .period-btn {
    flex: 1;
  }
}
</style>
