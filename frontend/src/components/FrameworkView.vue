<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import API_BASE_URL from '@/config/api.js'

const { t } = useI18n()

// State
const ticker = ref('')
const activeTab = ref('income') // income, cash_flow, balance_sheet
const period = ref('annual') // annual or quarter
const loading = ref(false)
const error = ref(null)

// Data
const incomeData = ref([])
const cashFlowData = ref([])
const balanceSheetData = ref([])
const revenueSegmentation = ref([])

// Fetch financial data
const fetchFinancialData = async () => {
  if (!ticker.value || ticker.value.trim() === '') {
    error.value = 'Please enter a ticker symbol'
    return
  }

  loading.value = true
  error.value = null

  try {
    const token = localStorage.getItem('access_token')
    const headers = token ? { 'Authorization': `Bearer ${token}` } : {}

    const response = await fetch(
      `${API_BASE_URL}/api/framework/all/${ticker.value.toUpperCase()}?period=${period.value}&limit=5`,
      { headers }
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch data' }))
      throw new Error(errorData.detail || 'Failed to fetch financial data')
    }

    const data = await response.json()
    incomeData.value = data.income_statement || []
    cashFlowData.value = data.cash_flow || []
    balanceSheetData.value = data.balance_sheet || []
    revenueSegmentation.value = data.revenue_segmentation || []
  } catch (err) {
    error.value = err.message
    console.error('Error fetching financial data:', err)
  } finally {
    loading.value = false
  }
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

// Format currency
const formatCurrency = (value) => {
  if (value === null || value === undefined) return '-'
  const num = parseFloat(value)
  if (isNaN(num)) return '-'
  
  // Format in billions/millions
  if (Math.abs(num) >= 1e9) {
    return `$${(num / 1e9).toFixed(2)}B`
  } else if (Math.abs(num) >= 1e6) {
    return `$${(num / 1e6).toFixed(2)}M`
  } else if (Math.abs(num) >= 1e3) {
    return `$${(num / 1e3).toFixed(2)}K`
  }
  return `$${num.toFixed(2)}`
}

// Format value based on field type
const formatValue = (key, value) => {
  // Date fields should be displayed as-is
  const dateFields = ['date', 'filingDate', 'acceptedDate', 'fillingDate', 'calendarYear', 'period']
  if (dateFields.includes(key)) {
    return value || '-'
  }
  
  // Everything else is currency
  return formatCurrency(value)
}

// Convert camelCase to Title Case
const formatLineItemName = (name) => {
  // Add space before capital letters and capitalize first letter
  return name
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, (str) => str.toUpperCase())
    .trim()
}

// Format percentage
const formatPercentage = (value) => {
  if (value === null || value === undefined || isNaN(value)) return '-'
  return `${(value * 100).toFixed(2)}%`
}

// Calculate Revenue Growth Rate (YoY)
const calculateRevenueGrowth = (currentRevenue, previousRevenue) => {
  if (!previousRevenue || previousRevenue === 0) return null
  return (currentRevenue - previousRevenue) / previousRevenue
}

// Calculate Gross Margin
const calculateGrossMargin = (grossProfit, revenue) => {
  if (!revenue || revenue === 0) return null
  return grossProfit / revenue
}

// Calculate Operating Profit Margin (EBITDA / Revenue)
const calculateOperatingMargin = (ebitda, revenue) => {
  if (!revenue || revenue === 0) return null
  return ebitda / revenue
}

// Calculate Net Profit Margin
const calculateNetMargin = (netIncome, revenue) => {
  if (!revenue || revenue === 0) return null
  return netIncome / revenue
}

// Calculate Cash Burn Rate (monthly)
const calculateCashBurnRate = (cashBeginning, cashEnd, period) => {
  if (cashBeginning === null || cashBeginning === undefined || 
      cashEnd === null || cashEnd === undefined) return null
  
  const cashChange = cashBeginning - cashEnd
  // Determine number of months based on period
  const months = period === 'quarter' ? 3 : 12
  
  return cashChange / months
}

// Get revenue segment value for a specific date and product
const getSegmentValue = (productName, date) => {
  if (!revenueSegmentation.value || revenueSegmentation.value.length === 0) return null
  
  // Find the segment entry for this date
  const segmentEntry = revenueSegmentation.value.find(seg => seg.date === date)
  if (!segmentEntry || !segmentEntry.data) return null
  
  // Return the value for this product
  return segmentEntry.data[productName] || null
}

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

// Track expanded/collapsed state for each category
const expandedCategories = ref(new Set(['Revenue & Direct Costs', 'Operating Activities (Cash from Operations)', 'Assets (What the Company Owns)']))

const toggleCategory = (categoryName) => {
  if (expandedCategories.value.has(categoryName)) {
    expandedCategories.value.delete(categoryName)
  } else {
    expandedCategories.value.add(categoryName)
  }
}

const isCategoryExpanded = (categoryName) => {
  return expandedCategories.value.has(categoryName)
}

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
        <div class="tabs">
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
          <button
            :class="['tab', { active: activeTab === 'fundamental_analysis' }]"
            @click="activeTab = 'fundamental_analysis'"
          >
            {{ t('framework.tabs.fundamental_analysis') }}
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

      <!-- Financial Data Table -->
      <div v-if="currentData.length > 0" class="data-table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th class="line-item-header">{{ t('framework.line_item') }}</th>
              <th v-for="periodDate in periods" :key="periodDate" class="period-header">
                {{ periodDate }}
              </th>
            </tr>
          </thead>
          <tbody>
            <!-- Categorized view for all statements -->
            <template v-if="categorizedLineItems.length > 0">
              <template v-for="category in categorizedLineItems" :key="category.name">
                <!-- Category Header Row -->
                <tr class="category-header-row" @click="toggleCategory(category.name)">
                  <td class="category-header-cell" :colspan="periods.length + 1">
                    <div class="category-header-content">
                      <svg 
                        class="category-icon" 
                        :class="{ expanded: isCategoryExpanded(category.name) }"
                        xmlns="http://www.w3.org/2000/svg" 
                        width="16" 
                        height="16" 
                        viewBox="0 0 24 24" 
                        fill="none" 
                        stroke="currentColor" 
                        stroke-width="2" 
                        stroke-linecap="round" 
                        stroke-linejoin="round"
                      >
                        <polyline points="9 18 15 12 9 6"></polyline>
                      </svg>
                      <span class="category-name">{{ category.name }}</span>
                    </div>
                  </td>
                </tr>
                
                <!-- Category Content (when expanded) -->
                <template v-if="isCategoryExpanded(category.name)">
                  <!-- Subcategories (for Balance Sheet) -->
                  <template v-if="category.subcategories && category.subcategories.length > 0">
                    <template v-for="subcategory in category.subcategories" :key="subcategory.name">
                      <!-- Subcategory Header -->
                      <tr class="subcategory-header-row" @click.stop="toggleCategory(subcategory.name)">
                        <td class="subcategory-header-cell" :colspan="periods.length + 1">
                          <div class="subcategory-header-content">
                            <svg 
                              class="category-icon subcategory-icon" 
                              :class="{ expanded: isCategoryExpanded(subcategory.name) }"
                              xmlns="http://www.w3.org/2000/svg" 
                              width="14" 
                              height="14" 
                              viewBox="0 0 24 24" 
                              fill="none" 
                              stroke="currentColor" 
                              stroke-width="2" 
                              stroke-linecap="round" 
                              stroke-linejoin="round"
                            >
                              <polyline points="9 18 15 12 9 6"></polyline>
                            </svg>
                            <span class="subcategory-name">{{ subcategory.name }}</span>
                          </div>
                        </td>
                      </tr>
                      <!-- Subcategory Fields -->
                      <template v-if="isCategoryExpanded(subcategory.name)">
                        <tr v-for="field in subcategory.fields" :key="field" class="data-row subcategory-data-row">
                          <td class="line-item-cell subcategory-item">{{ formatLineItemName(field) }}</td>
                          <td v-for="(data, index) in currentData" :key="index" class="data-cell">
                            {{ formatValue(field, data[field]) }}
                          </td>
                        </tr>
                      </template>
                    </template>
                  </template>
                  
                  <!-- Category Fields (direct fields without subcategories) -->
                  <template v-for="(field, fieldIndex) in category.fields" :key="field">
                    <tr class="data-row">
                      <td class="line-item-cell">{{ formatLineItemName(field) }}</td>
                      <td v-for="(data, index) in currentData" :key="index" class="data-cell">
                        {{ formatValue(field, data[field]) }}
                      </td>
                    </tr>
                    
                    <!-- Revenue Product Segmentation after Revenue -->
                    <template v-if="field === 'revenue' && activeTab === 'income' && productNames.length > 0">
                      <tr v-for="productName in productNames" :key="productName" class="segmentation-row">
                        <td class="line-item-cell segmentation-item">{{ productName }}</td>
                        <td v-for="(data, index) in currentData" :key="index" class="data-cell">
                          {{ formatCurrency(getSegmentValue(productName, data.date)) }}
                        </td>
                      </tr>
                    </template>
                    
                    <!-- Calculated Metrics for Income Statement -->
                    <template v-if="activeTab === 'income'">
                      <!-- Revenue Growth Rate after Revenue -->
                      <tr v-if="field === 'revenue'" class="calculated-metric-row">
                        <td class="line-item-cell calculated-metric">Revenue Growth Rate ({{ period === 'annual' ? 'YoY' : 'QoQ' }})</td>
                        <td v-for="(data, index) in currentData" :key="`growth-${index}`" class="data-cell calculated-value">
                          {{ index < currentData.length - 1 ? formatPercentage(calculateRevenueGrowth(data.revenue, currentData[index + 1].revenue)) : '-' }}
                        </td>
                      </tr>
                      
                      <!-- Gross Margin after Gross Profit -->
                      <tr v-if="field === 'grossProfit'" class="calculated-metric-row">
                        <td class="line-item-cell calculated-metric">Gross Margin</td>
                        <td v-for="(data, index) in currentData" :key="`gm-${index}`" class="data-cell calculated-value">
                          {{ formatPercentage(calculateGrossMargin(data.grossProfit, data.revenue)) }}
                        </td>
                      </tr>
                      
                      <!-- Operating Profit Margin after EBITDA -->
                      <tr v-if="field === 'ebitda'" class="calculated-metric-row">
                        <td class="line-item-cell calculated-metric">Operating Profit Margin</td>
                        <td v-for="(data, index) in currentData" :key="`opm-${index}`" class="data-cell calculated-value">
                          {{ formatPercentage(calculateOperatingMargin(data.ebitda, data.revenue)) }}
                        </td>
                      </tr>
                      
                      <!-- Net Profit Margin after Net Income -->
                      <tr v-if="field === 'netIncome'" class="calculated-metric-row">
                        <td class="line-item-cell calculated-metric">Net Profit Margin</td>
                        <td v-for="(data, index) in currentData" :key="`npm-${index}`" class="data-cell calculated-value">
                          {{ formatPercentage(calculateNetMargin(data.netIncome, data.revenue)) }}
                        </td>
                      </tr>
                    </template>
                    
                    <!-- Calculated Metrics for Cash Flow Statement -->
                    <template v-if="activeTab === 'cash_flow'">
                      <!-- Net Income Growth after Net Income -->
                      <tr v-if="field === 'netIncome'" class="calculated-metric-row">
                        <td class="line-item-cell calculated-metric">Net Income Growth ({{ period === 'annual' ? 'YoY' : 'QoQ' }})</td>
                        <td v-for="(data, index) in currentData" :key="`ni-growth-${index}`" class="data-cell calculated-value">
                          {{ index < currentData.length - 1 ? formatPercentage(calculateRevenueGrowth(data.netIncome, currentData[index + 1].netIncome)) : '-' }}
                        </td>
                      </tr>
                      
                      <!-- Operating Cash Flow Growth after Net Cash Provided By Operating Activities -->
                      <tr v-if="field === 'netCashProvidedByOperatingActivities'" class="calculated-metric-row">
                        <td class="line-item-cell calculated-metric">Operating Cash Flow Growth ({{ period === 'annual' ? 'YoY' : 'QoQ' }})</td>
                        <td v-for="(data, index) in currentData" :key="`ocf-growth-${index}`" class="data-cell calculated-value">
                          {{ index < currentData.length - 1 ? formatPercentage(calculateRevenueGrowth(data.netCashProvidedByOperatingActivities, currentData[index + 1].netCashProvidedByOperatingActivities)) : '-' }}
                        </td>
                      </tr>
                      
                      <!-- Accounts Receivables Growth after Accounts Receivables -->
                      <tr v-if="field === 'accountsReceivables'" class="calculated-metric-row">
                        <td class="line-item-cell calculated-metric">Accounts Receivables Growth ({{ period === 'annual' ? 'YoY' : 'QoQ' }})</td>
                        <td v-for="(data, index) in currentData" :key="`ar-growth-${index}`" class="data-cell calculated-value">
                          {{ index < currentData.length - 1 ? formatPercentage(calculateRevenueGrowth(data.accountsReceivables, currentData[index + 1].accountsReceivables)) : '-' }}
                        </td>
                      </tr>
                      
                      <!-- Inventory Growth after Inventory -->
                      <tr v-if="field === 'inventory'" class="calculated-metric-row">
                        <td class="line-item-cell calculated-metric">Inventory Growth ({{ period === 'annual' ? 'YoY' : 'QoQ' }})</td>
                        <td v-for="(data, index) in currentData" :key="`inv-growth-${index}`" class="data-cell calculated-value">
                          {{ index < currentData.length - 1 ? formatPercentage(calculateRevenueGrowth(data.inventory, currentData[index + 1].inventory)) : '-' }}
                        </td>
                      </tr>
                      
                      <!-- Accounts Payables Growth after Accounts Payables -->
                      <tr v-if="field === 'accountsPayables'" class="calculated-metric-row">
                        <td class="line-item-cell calculated-metric">Accounts Payables Growth ({{ period === 'annual' ? 'YoY' : 'QoQ' }})</td>
                        <td v-for="(data, index) in currentData" :key="`ap-growth-${index}`" class="data-cell calculated-value">
                          {{ index < currentData.length - 1 ? formatPercentage(calculateRevenueGrowth(data.accountsPayables, currentData[index + 1].accountsPayables)) : '-' }}
                        </td>
                      </tr>
                      
                      <!-- Cash Burn Rate after Cash At End Of Period -->
                      <tr v-if="field === 'cashAtEndOfPeriod'" class="calculated-metric-row">
                        <td class="line-item-cell calculated-metric">Cash Burn Rate (Monthly)</td>
                        <td v-for="(data, index) in currentData" :key="`burn-${index}`" class="data-cell calculated-value">
                          {{ formatCurrency(calculateCashBurnRate(data.cashAtBeginningOfPeriod, data.cashAtEndOfPeriod, period)) }}
                        </td>
                      </tr>
                      
                      <!-- CapEx Growth Rate after Capital Expenditure -->
                      <tr v-if="field === 'capitalExpenditure'" class="calculated-metric-row">
                        <td class="line-item-cell calculated-metric">CapEx Growth Rate ({{ period === 'annual' ? 'YoY' : 'QoQ' }})</td>
                        <td v-for="(data, index) in currentData" :key="`capex-growth-${index}`" class="data-cell calculated-value">
                          {{ index < currentData.length - 1 ? formatPercentage(calculateRevenueGrowth(data.capitalExpenditure, currentData[index + 1].capitalExpenditure)) : '-' }}
                        </td>
                      </tr>
                    </template>
                  </template>
                </template>
              </template>
            </template>
            
            <!-- Fallback regular view (shouldn't be needed) -->
            <template v-else>
              <tr v-for="item in lineItems" :key="item">
                <td class="line-item-cell">{{ formatLineItemName(item) }}</td>
                <td v-for="(data, index) in currentData" :key="index" class="data-cell">
                  {{ formatValue(item, data[item]) }}
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
      <div v-else class="no-data">
        {{ t('framework.no_data') }}
      </div>
      
      <!-- Fundamental Analysis Tab Content -->
      <div v-if="activeTab === 'fundamental_analysis'" class="fundamental-analysis">
        <div class="analysis-sections">
          <!-- Income Statement Analysis -->
          <div class="analysis-section">
            <h3 class="section-title">{{ t('framework.analysis.income_statement') }}</h3>
            <div class="section-content">
              <p class="placeholder-text">Income Statement analysis coming soon...</p>
            </div>
          </div>

          <!-- Cash Flow Analysis -->
          <div class="analysis-section">
            <h3 class="section-title">{{ t('framework.analysis.cash_flow') }}</h3>
            <div class="section-content">
              <p class="placeholder-text">Cash Flow analysis coming soon...</p>
            </div>
          </div>

          <!-- Balance Sheet Analysis -->
          <div class="analysis-section">
            <h3 class="section-title">{{ t('framework.analysis.balance_sheet') }}</h3>
            <div class="section-content">
              <p class="placeholder-text">Balance Sheet analysis coming soon...</p>
            </div>
          </div>

          <!-- Working Capital Analysis -->
          <div class="analysis-section">
            <h3 class="section-title">{{ t('framework.analysis.working_capital') }}</h3>
            <div class="section-content">
              <p class="placeholder-text">Working Capital analysis coming soon...</p>
            </div>
          </div>

          <!-- CapEx Analysis -->
          <div class="analysis-section">
            <h3 class="section-title">{{ t('framework.analysis.capex') }}</h3>
            <div class="section-content">
              <p class="placeholder-text">CapEx analysis coming soon...</p>
            </div>
          </div>

          <!-- Valuation Analysis -->
          <div class="analysis-section">
            <h3 class="section-title">{{ t('framework.analysis.valuation') }}</h3>
            <div class="section-content">
              <p class="placeholder-text">Valuation analysis coming soon...</p>
            </div>
          </div>

          <!-- Calendar -->
          <div class="analysis-section">
            <h3 class="section-title">{{ t('framework.analysis.calendar') }}</h3>
            <div class="section-content">
              <p class="placeholder-text">Calendar coming soon...</p>
            </div>
          </div>
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

    <!-- Empty State -->
    <div v-if="!ticker && !loading" class="empty-state">
      <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="7" height="7"></rect>
        <rect x="14" y="3" width="7" height="7"></rect>
        <rect x="14" y="14" width="7" height="7"></rect>
        <rect x="3" y="14" width="7" height="7"></rect>
      </svg>
      <p>{{ t('framework.ticker_placeholder') }}</p>
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
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  flex-wrap: wrap;
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
  padding: 2rem 0;
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
