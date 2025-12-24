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
import PriceVolumeChart from '@/components/framework/charts/PriceVolumeChart.vue'


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
  employeeCount, 
  mergersAcquisitions,
  filings,
  keyMetrics,
  financialRatios,
  earnings,
  dividends,
  splits,
  insiderTrading,
  businessDescription,
  historicalPrice,
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

// Price Header Logic
const latestPriceData = computed(() => {
  if (!historicalPrice.value || historicalPrice.value.length === 0) return null;
  // FMP usually returns Descending (newest first), but we ensure it.
  const data = [...historicalPrice.value].sort((a, b) => new Date(b.date) - new Date(a.date));
  return data[0]; 
})

const currentPrice = computed(() => latestPriceData.value ? latestPriceData.value.close : 0);
const priceChange = computed(() => latestPriceData.value ? latestPriceData.value.change : 0);
const priceChangePercent = computed(() => latestPriceData.value ? latestPriceData.value.changePercent : 0);

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
    capexAnalysisChartConfig,
    employeeCountChartConfig
} = useFrameworkAnalysis(incomeData, cashFlowData, employeeCount)


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

// Filings Logic
const filingsSortField = ref('date')
const filingsSortDirection = ref('desc')

const selectedFilingType = ref('ALL')

const sortedFilings = computed(() => {
  if (!filings.value) return []
  
  let data = [...filings.value]
  
  if (selectedFilingType.value !== 'ALL') {
    data = data.filter(f => f.type === selectedFilingType.value)
  }
  
  return data.sort((a, b) => {
    let valA = a[filingsSortField.value]
    let valB = b[filingsSortField.value]
    
    if (valA === valB) return 0
    let comparison = 0
    if (valA > valB) comparison = 1
    else comparison = -1
    
    return filingsSortDirection.value === 'asc' ? comparison : -comparison
  })
})

const sortFilings = (field) => {
  if (filingsSortField.value === field) {
    filingsSortDirection.value = filingsSortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    filingsSortField.value = field
    filingsSortDirection.value = 'desc'
  }
}

const getSortIcon = (field) => {
  if (filingsSortField.value !== field) return '↕'
  return filingsSortDirection.value === 'asc' ? '↑' : '↓'
}

const formatFilingDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString()
}

const calendarTab = ref('earning')


// Ratio Logic
const ratioTab = ref('key_matrix')

const getRatioKeys = computed(() => {
  if (!financialRatios.value || financialRatios.value.length === 0) return []
  const first = financialRatios.value[0]
  // Filter out non-metric keys
  return Object.keys(first).filter(k => !['symbol', 'date', 'period', 'calendarYear'].includes(k))
})

const keyMatrixCategories = {
  "Valuation Metrics": [
    { label: "Market Cap", key: "marketCap" },
    { label: "Enterprise Value (EV) TTM", key: "enterpriseValueTTM" },
    { label: "EV To Sales TTM", key: "evToSalesTTM" },
    { label: "EV To Operating Cash Flow TTM", key: "evToOperatingCashFlowTTM" },
    { label: "EV To Free Cash Flow TTM", key: "evToFreeCashFlowTTM" },
    { label: "EV To EBITDA TTM", key: "evToEBITDATTM" },
    { label: "Earnings Yield TTM", key: "earningsYieldTTM" },
    { label: "Free Cash Flow Yield TTM", key: "freeCashFlowYieldTTM" },
    { label: "Graham Number TTM", key: "grahamNumberTTM" },
    { label: "Graham Net Net TTM", key: "grahamNetNetTTM" }
  ],
  "Profitability & Returns": [
    { label: "Return On Assets (ROA) TTM", key: "returnOnAssetsTTM" },
    { label: "Operating Return On Assets TTM", key: "operatingReturnOnAssetsTTM" },
    { label: "Return On Tangible Assets TTM", key: "returnOnTangibleAssetsTTM" },
    { label: "Return On Equity (ROE) TTM", key: "returnOnEquityTTM" },
    { label: "Return On Invested Capital (ROIC) TTM", key: "returnOnInvestedCapitalTTM" },
    { label: "Return On Capital Employed (ROCE) TTM", key: "returnOnCapitalEmployedTTM" },
    { label: "Income Quality TTM", key: "incomeQualityTTM" },
    { label: "Tax Burden TTM", key: "taxBurdenTTM" },
    { label: "Interest Burden TTM", key: "interestBurdenTTM" }
  ],
  "Operating Efficiency & Working Capital": [
    { label: "Days Of Sales Outstanding (DSO) TTM", key: "daysOfSalesOutstandingTTM" },
    { label: "Days Of Payables Outstanding (DPO) TTM", key: "daysOfPayablesOutstandingTTM" },
    { label: "Days Of Inventory Outstanding (DIO) TTM", key: "daysOfInventoryOutstandingTTM" },
    { label: "Operating Cycle TTM", key: "operatingCycleTTM" },
    { label: "Cash Conversion Cycle TTM", key: "cashConversionCycleTTM" },
    { label: "Average Receivables TTM", key: "averageReceivablesTTM" },
    { label: "Average Payables TTM", key: "averagePayablesTTM" },
    { label: "Average Inventory TTM", key: "averageInventoryTTM" }
  ],
  "Capital Expenditure & Cost Structure": [
    { label: "Capex To Operating Cash Flow TTM", key: "capexToOperatingCashFlowTTM" },
    { label: "Capex To Depreciation TTM", key: "capexToDepreciationTTM" },
    { label: "Capex To Revenue TTM", key: "capexToRevenueTTM" },
    { label: "Sales General And Administrative (SG&A) To Revenue TTM", key: "salesGeneralAndAdministrativeToRevenueTTM" },
    { label: "Research And Developement (R&D) To Revenue TTM", key: "researchAndDevelopementToRevenueTTM" },
    { label: "Stock Based Compensation To Revenue TTM", key: "stockBasedCompensationToRevenueTTM" }
  ],
  "Liquidity & Solvency": [
    { label: "Current Ratio TTM", key: "currentRatioTTM" },
    { label: "Net Debt To EBITDA TTM", key: "netDebtToEBITDATTM" },
    { label: "Intangibles To Total Assets TTM", key: "intangiblesToTotalAssetsTTM" }
  ],
  "Absolute Financial Values": [
    { label: "Working Capital TTM", key: "workingCapitalTTM" },
    { label: "Invested Capital TTM", key: "investedCapitalTTM" },
    { label: "Tangible Asset Value TTM", key: "tangibleAssetValueTTM" },
    { label: "Net Current Asset Value TTM", key: "netCurrentAssetValueTTM" },
    { label: "Free Cash Flow To Equity TTM", key: "freeCashFlowToEquityTTM" },
    { label: "Free Cash Flow To Firm TTM", key: "freeCashFlowToFirmTTM" }
  ]
}

const financialRatioCategories = {
  "Profitability & Margins": [
    { label: "Gross Profit Margin TTM", key: "grossProfitMarginTTM" },
    { label: "EBIT Margin TTM", key: "ebitMarginTTM" },
    { label: "EBITDA Margin TTM", key: "ebitdaMarginTTM" },
    { label: "Operating Profit Margin TTM", key: "operatingProfitMarginTTM" },
    { label: "Pretax Profit Margin TTM", key: "pretaxProfitMarginTTM" },
    { label: "Continuous Operations Profit Margin TTM", key: "continuousOperationsProfitMarginTTM" },
    { label: "Net Profit Margin TTM", key: "netProfitMarginTTM" },
    { label: "Bottom Line Profit Margin TTM", key: "bottomLineProfitMarginTTM" },
    { label: "Effective Tax Rate TTM", key: "effectiveTaxRateTTM" },
    { label: "Net Income Per EBT TTM (Tax Burden)", key: "netIncomePerEBTTTM" },
    { label: "EBT Per EBIT TTM (Interest Burden)", key: "ebtPerEbitTTM" }
  ],
  "Valuation Multiples": [
    { label: "Price To Earnings (P/E) Ratio TTM", key: "priceEarningsRatioTTM" },
    { label: "Price To Earnings Growth (PEG) Ratio TTM", key: "priceEarningsToGrowthRatioTTM" },
    { label: "Price To Book (P/B) Ratio TTM", key: "priceToBookRatioTTM" },
    { label: "Price To Sales (P/S) Ratio TTM", key: "priceToSalesRatioTTM" },
    { label: "Price To Free Cash Flow Ratio TTM", key: "priceToFreeCashFlowRatioTTM" },
    { label: "Price To Operating Cash Flow Ratio TTM", key: "priceToOperatingCashFlowRatioTTM" },
    { label: "Price To Fair Value TTM", key: "priceToFairValueTTM" },
    { label: "Enterprise Value Multiple TTM", key: "enterpriseValueMultipleTTM" },
    { label: "Enterprise Value TTM", key: "enterpriseValueTTM" }
  ],
  "Efficiency & Turnover": [
    { label: "Receivables Turnover TTM", key: "receivablesTurnoverTTM" },
    { label: "Payables Turnover TTM", key: "payablesTurnoverTTM" },
    { label: "Inventory Turnover TTM", key: "inventoryTurnoverTTM" },
    { label: "Fixed Asset Turnover TTM", key: "fixedAssetTurnoverTTM" },
    { label: "Asset Turnover TTM", key: "assetTurnoverTTM" },
    { label: "Working Capital Turnover Ratio TTM", key: "workingCapitalTurnoverRatioTTM" }
  ],
  "Liquidity & Solvency": [
    { label: "Current Ratio TTM", key: "currentRatioTTM" },
    { label: "Quick Ratio TTM", key: "quickRatioTTM" },
    { label: "Cash Ratio TTM", key: "cashRatioTTM" },
    { label: "Solvency Ratio TTM", key: "solvencyRatioTTM" }
  ],
  "Leverage & Debt Structure": [
    { label: "Debt To Assets Ratio TTM", key: "debtToAssetsRatioTTM" },
    { label: "Debt To Equity Ratio TTM", key: "debtToEquityRatioTTM" },
    { label: "Debt To Capital Ratio TTM", key: "debtToCapitalRatioTTM" },
    { label: "Long Term Debt To Capital Ratio TTM", key: "longTermDebtToCapitalRatioTTM" },
    { label: "Financial Leverage Ratio TTM", key: "financialLeverageRatioTTM" },
    { label: "Debt To Market Cap TTM", key: "debtToMarketCapTTM" }
  ],
  "Cash Flow & Coverage Ratios": [
    { label: "Operating Cash Flow Ratio TTM", key: "operatingCashFlowRatioTTM" },
    { label: "Operating Cash Flow Sales Ratio TTM", key: "operatingCashFlowSalesRatioTTM" },
    { label: "Free Cash Flow / Operating Cash Flow Ratio TTM", key: "freeCashFlowOperatingCashFlowRatioTTM" },
    { label: "Debt Service Coverage Ratio TTM", key: "debtServiceCoverageRatioTTM" },
    { label: "Interest Coverage Ratio TTM", key: "interestCoverageRatioTTM" },
    { label: "Short Term Operating Cash Flow Coverage Ratio TTM", key: "shortTermOperatingCashFlowCoverageRatioTTM" },
    { label: "Operating Cash Flow Coverage Ratio TTM", key: "operatingCashFlowCoverageRatioTTM" },
    { label: "Capital Expenditure Coverage Ratio TTM", key: "capitalExpenditureCoverageRatioTTM" },
    { label: "Dividend Paid And Capex Coverage Ratio TTM", key: "dividendPaidAndCapexCoverageRatioTTM" },
    { label: "Dividend Payout Ratio TTM", key: "dividendPayoutRatioTTM" },
    { label: "Dividend Yield TTM", key: "dividendYieldTTM" }
  ],
  "Per Share Data": [
    { label: "Revenue Per Share TTM", key: "revenuePerShareTTM" },
    { label: "Net Income Per Share TTM", key: "netIncomePerShareTTM" },
    { label: "Interest Debt Per Share TTM", key: "interestDebtPerShareTTM" },
    { label: "Cash Per Share TTM", key: "cashPerShareTTM" },
    { label: "Book Value Per Share TTM", key: "bookValuePerShareTTM" },
    { label: "Tangible Book Value Per Share TTM", key: "tangibleBookValuePerShareTTM" },
    { label: "Shareholders Equity Per Share TTM", key: "shareholdersEquityPerShareTTM" },
    { label: "Operating Cash Flow Per Share TTM", key: "operatingCashFlowPerShareTTM" },
    { label: "Capex Per Share TTM", key: "capexPerShareTTM" },
    { label: "Free Cash Flow Per Share TTM", key: "freeCashFlowPerShareTTM" }
  ]
}

const formatMetric = (val) => {
  if (val === null || val === undefined) return '-'
  if (typeof val === 'number') {
    // Large numbers check
    if (Math.abs(val) > 1000000) return (val / 1000000).toFixed(2) + 'M'
    return val.toFixed(2)
  }
  return val
}

const formatKey = (key) => {
  if (!key) return ''
  // Split camelCase and capitalize
  return key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())
}
</script>

<template>
  <div class="framework-container">

    <!-- Header -->
    <div class="custom-header">
       <div class="header-content">
          <div class="header-left">
             <h1>{{ t('framework.header.title') }}</h1>
             <p>{{ t('framework.header.subtitle') }}</p>
          </div>
          <div class="header-right" v-if="latestPriceData">
             <div class="price-top">
                <span class="badge" :class="priceChange >= 0 ? 'bg-red' : 'bg-red'"> <!-- Image puts negative in red. Positive usually green.  -->
                   {{ priceChangePercent.toFixed(2) }}%
                </span>
                <span class="price-val">{{ formatCurrency(currentPrice) }}</span>
             </div>
             <div class="price-sub">
                <span :class="priceChange >= 0 ? 'text-green' : 'text-red'">
                  {{ priceChange > 0 ? '+' : '' }}{{ priceChange.toFixed(2) }} ({{ priceChangePercent.toFixed(2) }}%) since last close
                </span>
             </div>
          </div>
       </div>
       <div class="header-line"></div>
    </div>

    <!-- Search Bar -->
    <div class="search-box-section">
       <span class="search-label">{{ t('framework.search_stock') }}</span>
       <div class="input-group">
          <input
            v-model="ticker"
            type="text"
            placeholder="TSLA"
            class="styled-input"
            @keyup.enter="handleSearch"
          />
          <button @click="handleSearch" class="styled-search-btn" :disabled="loading">
            {{ t('framework.search_action') }}
          </button>
       </div>
    </div>

    <!-- Content -->
    <div v-if="ticker && !loading && !error" class="content">
      <!-- 3. Chart Section -->
      <div class="section-card chart-section-card">
         <div class="section-header-row">
             <h3>{{ ticker.toUpperCase() }} - {{ new Date().getFullYear() }} {{ t('framework.chart.price_timeline') }}</h3>
         </div>
         <PriceVolumeChart 
           :data="historicalPrice" 
           :symbol="ticker" 
         />
      </div>

      <!-- 4. Dataset Section -->
      <div class="section-card dataset-section-card">
         <div class="section-header-row">
             <h3>{{ t('framework.dataset.title') }}</h3>
             <div v-if="['statements'].includes(mainTab)" class="period-toggle-badge">
                 <button :class="{ active: period === 'annual' }" @click="changePeriod('annual')">{{ t('framework.period.annual') }}</button>
                 <button :class="{ active: period === 'quarter' }" @click="changePeriod('quarter')">{{ t('framework.period.quarterly') }}</button>
             </div>
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
          <button
            :class="['main-tab', { active: mainTab === 'ratio' }]"
            @click="mainTab = 'ratio'"
          >
            {{ t('framework.main_tabs.ratio') }}
          </button>
          <button
            :class="['main-tab', { active: mainTab === 'calendar' }]"
            @click="mainTab = 'calendar'"
          >
             {{ t('framework.main_tabs.calendar') }}
          </button>
          <button
            :class="['main-tab', { active: mainTab === 'filling' }]"
            @click="mainTab = 'filling'"
          >
             {{ t('framework.main_tabs.filling') }}
          </button>
          <button
            :class="['main-tab', { active: mainTab === 'insider' }]"
            @click="mainTab = 'insider'"
          >
             {{ t('framework.main_tabs.insider') }}
          </button>
        </div>

        <!-- Sub-tabs and Period Toggle Container -->
        <div v-if="['statements', 'fundamental_analysis'].includes(mainTab)" class="sub-tabs-container">
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



      <!-- Ratio Content -->
      <div v-if="mainTab === 'ratio'" class="ratio-analysis">
         <div class="profile-tabs" style="margin-bottom: 20px;">
           <button class="profile-tab" :class="{ active: ratioTab === 'key_matrix' }" @click="ratioTab = 'key_matrix'">{{ t('framework.ratio_tabs.key_matrix') }}</button>
           <button class="profile-tab" :class="{ active: ratioTab === 'financial_ratio' }" @click="ratioTab = 'financial_ratio'">{{ t('framework.ratio_tabs.financial_ratio') }}</button>
         </div>

         <!-- Key Matrix -->
         <div v-if="ratioTab === 'key_matrix'">
            <div v-if="keyMetrics && keyMetrics.length > 0" class="metrics-container">
              <div v-for="(items, category) in keyMatrixCategories" :key="category" class="category-section" style="margin-bottom: 30px;">
                <h3 style="font-size: 1.1em; color: #374151; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; margin-bottom: 15px;">{{ category }}</h3>
                <div class="metrics-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px;">
                  <div v-for="item in items" :key="item.key" class="metric-card" style="padding: 15px; border: 1px solid #e5e7eb; border-radius: 8px; background: #fff;">
                    <div style="font-size: 0.85em; color: #6b7280; margin-bottom: 5px;">{{ item.label }}</div>
                    <div style="font-size: 1.1em; font-weight: 600; color: #111827;">{{ formatMetric(keyMetrics[0][item.key]) }}</div>
                  </div>
                </div>
              </div>
            </div>
            <p v-else class="placeholder-text">No key metrics data available</p>
         </div>

         <!-- Financial Ratio -->
         <div v-if="ratioTab === 'financial_ratio'">
            <div v-if="financialRatios && financialRatios.length > 0" class="data-table-wrapper" style="overflow-x: auto;">
              <table class="data-table">
                <thead>
                  <tr>
                    <th class="line-item-header">Ratio</th>
                    <th v-for="company in financialRatios" :key="company.symbol" class="period-header">{{ company.symbol }}</th>
                  </tr>
                </thead>
                <tbody>
                  <template v-for="(items, category) in financialRatioCategories" :key="category">
                    <tr class="section-header" style="background-color: #f3f4f6;">
                      <td :colspan="financialRatios.length + 1" style="font-weight: 600; color: #374151; padding: 12px 15px;">{{ category }}</td>
                    </tr>
                    <tr v-for="item in items" :key="item.key" class="data-row">
                      <td class="line-item-cell">{{ item.label }}</td>
                      <td v-for="company in financialRatios" :key="company.symbol + item.key" class="data-cell">
                        {{ formatMetric(company[item.key]) }}
                      </td>
                    </tr>
                  </template>
                </tbody>
              </table>
            </div>
            <p v-else class="placeholder-text">No financial ratio comparison data available</p>
         </div>
      </div>

      <!-- Calendar Content -->
      <div v-if="mainTab === 'calendar'" class="calendar-analysis">
          <div class="profile-tabs" style="margin-bottom: 20px;">
             <button class="profile-tab" :class="{ active: calendarTab === 'earning' }" @click="calendarTab = 'earning'">{{ t('framework.calendar_tabs.earning') }}</button>
             <button class="profile-tab" :class="{ active: calendarTab === 'dividends' }" @click="calendarTab = 'dividends'">{{ t('framework.calendar_tabs.dividends') }}</button>
             <button class="profile-tab" :class="{ active: calendarTab === 'splits' }" @click="calendarTab = 'splits'">{{ t('framework.calendar_tabs.splits') }}</button>
          </div>

          <!-- Earning -->
          <div v-if="calendarTab === 'earning'">
             <div v-if="earnings && earnings.length > 0" class="data-table-wrapper" style="overflow-x: auto;">
                <table class="data-table">
                   <thead>
                      <tr>
                         <th class="period-header">{{ t('framework.calendar_data.date') }}</th>
                         <th class="period-header">{{ t('framework.calendar_data.eps_actual') }}</th>
                         <th class="period-header">{{ t('framework.calendar_data.eps_estimated') }}</th>
                         <th class="period-header">{{ t('framework.calendar_data.revenue_actual') }}</th>
                         <th class="period-header">{{ t('framework.calendar_data.revenue_estimated') }}</th>
                      </tr>
                   </thead>
                   <tbody>
                      <tr v-for="(item, index) in earnings" :key="index" class="data-row">
                         <td class="data-cell">{{ formatFilingDate(item.date) }}</td>
                         <td class="data-cell">{{ item.epsActual !== null ? item.epsActual : '-' }}</td>
                         <td class="data-cell">{{ item.epsEstimated !== null ? item.epsEstimated : '-' }}</td>
                         <td class="data-cell">{{ item.revenueActual !== null ? formatMetric(item.revenueActual) : '-' }}</td>
                         <td class="data-cell">{{ item.revenueEstimated !== null ? formatMetric(item.revenueEstimated) : '-' }}</td>
                      </tr>
                   </tbody>
                </table>
             </div>
             <p v-else class="placeholder-text">{{ t('framework.calendar_data.no_earning') }}</p>
          </div>

          <!-- Dividends -->
          <div v-if="calendarTab === 'dividends'">
             <div v-if="dividends && dividends.length > 0" class="data-table-wrapper" style="overflow-x: auto;">
                <table class="data-table">
                   <thead>
                      <tr>
                         <th class="period-header">{{ t('framework.calendar_data.date') }}</th>
                         <th class="period-header">{{ t('framework.calendar_data.dividend') }}</th>
                         <th class="period-header">{{ t('framework.calendar_data.record_date') }}</th>
                         <th class="period-header">{{ t('framework.calendar_data.payment_date') }}</th>
                         <th class="period-header">{{ t('framework.calendar_data.declaration_date') }}</th>
                      </tr>
                   </thead>
                   <tbody>
                      <tr v-for="(item, index) in dividends" :key="index" class="data-row">
                         <td class="data-cell">{{ formatFilingDate(item.date) }}</td>
                         <td class="data-cell">{{ item.dividend }}</td>
                         <td class="data-cell">{{ formatFilingDate(item.recordDate) }}</td>
                         <td class="data-cell">{{ formatFilingDate(item.paymentDate) }}</td>
                         <td class="data-cell">{{ formatFilingDate(item.declarationDate) }}</td>
                      </tr>
                   </tbody>
                </table>
             </div>
             <p v-else class="placeholder-text">{{ t('framework.calendar_data.no_dividend') }}</p>
          </div>

          <!-- Splits -->
          <div v-if="calendarTab === 'splits'">
             <div v-if="splits && splits.length > 0" class="data-table-wrapper" style="overflow-x: auto;">
                <table class="data-table">
                   <thead>
                      <tr>
                         <th class="period-header">{{ t('framework.calendar_data.date') }}</th>
                         <th class="period-header">{{ t('framework.calendar_data.numerator') }}</th>
                         <th class="period-header">{{ t('framework.calendar_data.denominator') }}</th>
                      </tr>
                   </thead>
                   <tbody>
                      <tr v-for="(item, index) in splits" :key="index" class="data-row">
                         <td class="data-cell">{{ formatFilingDate(item.date) }}</td>
                         <td class="data-cell">{{ item.numerator }}</td>
                         <td class="data-cell">{{ item.denominator }}</td>
                      </tr>
                   </tbody>
                </table>
             </div>
             <p v-else class="placeholder-text">{{ t('framework.calendar_data.no_split') }}</p>
          </div>
      </div>

      <!-- Filling Content -->
      <div v-if="mainTab === 'filling'" class="filling-analysis">
         <div v-if="filings && filings.length > 0" class="filings-container">
            <div class="filings-controls" style="margin-bottom: 1rem; display: flex; align-items: center;">
              <label style="margin-right: 10px; font-weight: 500; font-size: 0.9em; color: #374151;">{{ t('framework.filings.filter_label') }}</label>
              <select v-model="selectedFilingType" style="padding: 6px 12px; border-radius: 6px; border: 1px solid #d1d5db; font-size: 0.9em; background-color: white;">
                <option value="ALL">{{ t('framework.filings.all_types') }}</option>
                <option value="10-K">10-K (Annual Report)</option>
                <option value="10-Q">10-Q (Quarterly Report)</option>
                <option value="8-K">8-K (Current Report)</option>
                <option value="SC 13G">SC 13G (Statement of Ownership)</option>
                <option value="SD">SD (Specialized Disclosure)</option>
                <option value="4">Form 4 (Insider Trading)</option>
              </select>
            </div>
             <div class="data-table-wrapper" style="overflow-x: auto;">
                <table class="data-table">
                   <thead>
                      <tr>
                         <th class="period-header" @click="sortFilings('date')" style="cursor: pointer;">
                           {{ t('framework.filings.date') }} <span class="sort-icon">{{ getSortIcon('date') }}</span>
                         </th>
                         <th class="period-header" @click="sortFilings('type')" style="cursor: pointer;">
                           {{ t('framework.filings.type') }} <span class="sort-icon">{{ getSortIcon('type') }}</span>
                         </th>
                         <th class="period-header">{{ t('framework.filings.link') }}</th>
                      </tr>
                   </thead>
                   <tbody>
                      <tr v-for="(filing, index) in sortedFilings" :key="index" class="data-row">
                         <td class="data-cell">{{ formatFilingDate(filing.date) }}</td>
                         <td class="data-cell">
                           <span class="filing-type-badge">{{ filing.type }}</span>
                         </td>
                         <td class="data-cell">
                            <a :href="filing.link" target="_blank" class="filing-link">{{ t('framework.filings.view_filing') }}</a>
                         </td>
                      </tr>
                   </tbody>
                </table>
             </div>
         </div>
         <p v-else class="placeholder-text">{{ t('framework.filings.no_data') }}</p>
      </div>

      <!-- Insider Trading Content -->
      <div v-if="mainTab === 'insider'" class="insider-analysis">
         <div v-if="insiderTrading && insiderTrading.length > 0" class="data-table-wrapper" style="overflow-x: auto;">
            <table class="data-table">
               <thead>
                  <tr>
                     <th class="period-header">{{ t('framework.insider.filing_date') }}</th>
                     <th class="period-header">{{ t('framework.insider.trans_date') }}</th>
                     <th class="period-header">{{ t('framework.insider.type') }}</th>
                     <th class="period-header">{{ t('framework.insider.securities_owned') }}</th>
                     <th class="period-header">{{ t('framework.insider.reporting_name') }}</th>
                     <th class="period-header">{{ t('framework.insider.owner_type') }}</th>
                     <th class="period-header">{{ t('framework.insider.transacted') }}</th>
                     <th class="period-header">{{ t('framework.insider.price') }}</th>
                     <th class="period-header">{{ t('framework.insider.acq_disp') }}</th>
                     <th class="period-header">Direct/Indirect</th>
                     <th class="period-header">Security Name</th>
                  </tr>
               </thead>
               <tbody>
                  <tr v-for="(item, index) in insiderTrading" :key="index" class="data-row">
                     <td class="data-cell">{{ formatFilingDate(item.filingDate) }}</td>
                     <td class="data-cell">{{ formatFilingDate(item.transactionDate) }}</td>
                     <td class="data-cell">{{ item.transactionType }}</td>
                     <td class="data-cell">{{ item.securitiesOwned !== null ? item.securitiesOwned.toLocaleString() : '-' }}</td>
                     <td class="data-cell">{{ item.reportingName }}</td>
                     <td class="data-cell">{{ item.typeOfOwner }}</td>
                     <td class="data-cell">{{ item.securitiesTransacted !== null ? item.securitiesTransacted.toLocaleString() : '-' }}</td>
                     <td class="data-cell">{{ item.price !== null ? formatCurrency(item.price) : '-' }}</td>
                     <td class="data-cell">{{ item.acquisitionOrDisposition }}</td>
                     <td class="data-cell">{{ item.directOrIndirect }}</td>
                     <td class="data-cell">{{ item.securityName }}</td>
                  </tr>
               </tbody>
            </table>
         </div>
         <p v-else class="placeholder-text">{{ t('framework.insider.no_data') }}</p>
      </div>

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
          </div>

          <div class="profile-content">
            <!-- Business Tab -->
            <div v-if="profileTab === 'business'">
              <div v-if="businessDescription" class="business-description">
                <p style="white-space: pre-line; margin-bottom: 2rem; color: #4b5563; line-height: 1.6;">{{ businessDescription }}</p>
              </div>
              <p v-else class="placeholder-text">Company business information coming soon...</p>
            </div>

            <!-- Employee Count Tab -->
            <div v-if="profileTab === 'employee_count'">
              <div v-if="employeeCount.length > 0" class="chart-container" style="height: 400px; padding: 1rem;">
                <FinancialChart 
                  v-if="employeeCountChartConfig"
                  :type="employeeCountChartConfig.type"
                  :data="employeeCountChartConfig.data"
                  :options="employeeCountChartConfig.options"
                />
              </div>
              <p v-else class="placeholder-text">No employee count data available</p>
            </div>


          </div>
        </div>

        <!-- Other analysis sections with wrappers removed -->
        <div v-if="analysisTab === 'pricing_power'">          
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

.filings-container {
  margin-top: 20px;
}

.filings-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  overflow: hidden;
}

.filings-table thead {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.filings-table th {
  padding: 15px;
  text-align: left;
  font-weight: 600;
  font-size: 0.95em;
  color: white;
}

.filings-table th.sortable {
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.filings-table th.sortable:hover {
  background: rgba(255, 255, 255, 0.1);
}

.filings-table .sort-icon {
  margin-left: 8px;
  font-size: 0.9em;
  opacity: 0.8;
}

.filings-table tbody tr {
  border-bottom: 1px solid #e0e0e0;
  transition: background 0.2s;
}

.filings-table tbody tr:hover {
  background: #f8f9fa;
}

.filings-table tbody tr:last-child {
  border-bottom: none;
}

.filings-table td {
  padding: 12px 15px;
  font-size: 0.9em;
  color: #000;
}

.filing-type {
  font-weight: 600;
  color: #000;
}

.filing-date {
  color: #000;
}

.filing-link a {
  color: #42b983;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
}

.filing-link a:hover {
  color: #35a372;
  text-decoration: underline;
}

.data-table-wrapper {
  margin-top: 1rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

/* Global Data Table Styles within Component */
.period-header {
  background: #f8fafc;
  padding: 1rem;
  text-align: left !important;
  vertical-align: middle !important;
  font-weight: 600;
  color: #475569;
  border-bottom: 2px solid #e2e8f0;
  white-space: nowrap;
}

.data-row {
  border-bottom: 1px solid #e2e8f0;
}

.data-row:last-child {
  border-bottom: none;
}

.data-row:hover {
  background: #f8fafc;
}

.data-cell {
  padding: 1rem;
  color: #1e293b;
  text-align: left !important;
  vertical-align: middle !important;
}
</style>

<style scoped>
/* New Layout Styles */
.custom-header {
  margin-bottom: 2rem;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.header-left h1 {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: 0.05em;
  margin: 0;
  text-transform: uppercase;
  color: #000000;
}

.header-left p {
  font-size: 0.9rem;
  color: #666;
  font-style: italic;
  margin: 0.25rem 0 0 0;
}

.header-right {
  text-align: right;
}

.price-top {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 1rem;
}

.badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 0.9rem;
}

.bg-red { background: #fee2e2; color: #ef4444; }
.bg-green { background: #dcfce7; color: #22c55e; }

.price-val {
  font-size: 2.5rem;
  font-weight: 800;
  line-height: 1;
  color: #000000;
}

.price-sub {
  font-size: 0.85rem;
  font-weight: 500;
  margin-top: 4px;
}
.text-red { color: #ef4444; }
.text-green { color: #22c55e; }

.header-line {
  height: 2px;
  background: #000;
  width: 100%;
}

/* Search Box */
.search-box-section {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  padding: 1.5rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.search-label {
  font-weight: 800;
  font-size: 0.9rem;
  text-transform: uppercase;
  white-space: nowrap;
  color: #000000;
}

.input-group {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
}

.styled-input {
  flex: 0 0 300px;
  padding: 8px 12px;
  background: #eef2ff; /* Light blueish tint */
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 1rem;
}

.styled-search-btn {
  background: #000;
  color: white;
  border: none;
  padding: 8px 24px;
  font-weight: 700;
  font-size: 0.9rem;
  border-radius: 4px;
  cursor: pointer;
  letter-spacing: 0.05em;
}

.styled-search-btn:hover {
  background: #333;
}

/* Sections */
.section-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.section-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid #f3f4f6;
  padding-bottom: 1rem;
}

.section-header-row h3 {
  font-size: 1.1rem;
  font-weight: 800;
  margin: 0;
  text-transform: uppercase;
  color: #000000;
}

.period-toggle-badge {
  display: flex;
  background: #f3f4f6;
  border-radius: 4px;
  padding: 2px;
}

.period-toggle-badge button {
  border: none;
  background: transparent;
  padding: 4px 12px;
  font-size: 0.8rem;
  font-weight: 600;
  color: #6b7280;
  cursor: pointer;
  border-radius: 4px;
}

.period-toggle-badge button.active {
  background: white;
  color: #000;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}
</style>
