<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import API_BASE_URL from '@/config/api.js'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
)

const { t } = useI18n()

// State
const ticker = ref('')
const mainTab = ref('statements') // statements or fundamental_analysis
const activeTab = ref('income') // income, cash_flow, balance_sheet
const analysisTab = ref('profile') // profile, pricing_power, financial_health, working_capital, capex, valuation, structure
const period = ref('annual') // annual or quarter
const loading = ref(false)
const error = ref(null)

// Data
const incomeData = ref([])
const cashFlowData = ref([])
const balanceSheetData = ref([])
const revenueSegmentation = ref([])
const dcfData = ref([])
const earningsCalendar = ref([])

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
    dcfData.value = data.dcf || []
    earningsCalendar.value = data.earnings_calendar || []
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

// Pricing Power Metrics (from Income Statement)
const pricingPowerData = computed(() => {
  if (!incomeData.value || incomeData.value.length === 0) return null
  
  return {
    dates: incomeData.value.map(d => d.date).reverse(),
    revenueGrowth: incomeData.value.map((d, i) => {
      if (i < incomeData.value.length - 1) {
        const growth = calculateRevenueGrowth(d.revenue, incomeData.value[i + 1].revenue)
        return growth ? growth * 100 : null
      }
      return null
    }).reverse(),
    grossMargin: incomeData.value.map(d => {
      const margin = calculateGrossMargin(d.grossProfit, d.revenue)
      return margin ? margin * 100 : null
    }).reverse(),
    operatingMargin: incomeData.value.map(d => {
      const margin = calculateOperatingMargin(d.ebitda, d.revenue)
      return margin ? margin * 100 : null
    }).reverse()
  }
})

// Financial Health Metrics (from Cash Flow)
const financialHealthData = computed(() => {
  if (!cashFlowData.value || cashFlowData.value.length === 0) return null
  
  return {
    dates: cashFlowData.value.map(d => d.date).reverse(),
    netIncome: cashFlowData.value.map(d => d.netIncome).reverse(),
    operatingCashFlow: cashFlowData.value.map(d => d.netCashProvidedByOperatingActivities).reverse(),
    freeCashFlow: cashFlowData.value.map(d => d.freeCashFlow).reverse(),
    capex: cashFlowData.value.map(d => Math.abs(d.capitalExpenditure || 0)).reverse()
  }
})

// Working Capital Metrics (from Cash Flow)
const workingCapitalData = computed(() => {
  if (!cashFlowData.value || cashFlowData.value.length === 0) return null
  
  return {
    dates: cashFlowData.value.map(d => d.date).reverse(),
    accountsReceivablesGrowth: cashFlowData.value.map((d, i) => {
      if (i < cashFlowData.value.length - 1) {
        const growth = calculateRevenueGrowth(d.accountsReceivables, cashFlowData.value[i + 1].accountsReceivables)
        return growth ? growth * 100 : null
      }
      return null
    }).reverse(),
    netIncomeGrowth: cashFlowData.value.map((d, i) => {
      if (i < cashFlowData.value.length - 1) {
        const growth = calculateRevenueGrowth(d.netIncome, cashFlowData.value[i + 1].netIncome)
        return growth ? growth * 100 : null
      }
      return null
    }).reverse(),
    inventoryGrowth: cashFlowData.value.map((d, i) => {
      if (i < cashFlowData.value.length - 1) {
        const growth = calculateRevenueGrowth(d.inventory, cashFlowData.value[i + 1].inventory)
        return growth ? growth * 100 : null
      }
      return null
    }).reverse(),
    accountsPayablesGrowth: cashFlowData.value.map((d, i) => {
      if (i < cashFlowData.value.length - 1) {
        const growth = calculateRevenueGrowth(d.accountsPayables, cashFlowData.value[i + 1].accountsPayables)
        return growth ? growth * 100 : null
      }
      return null
    }).reverse()
  }
})

// CapEx Analysis Metrics (combining Cash Flow and Income data)
const capexAnalysisData = computed(() => {
  if (!cashFlowData.value || cashFlowData.value.length === 0 || 
      !incomeData.value || incomeData.value.length === 0) return null
  
  // Use the shorter dataset length to ensure alignment
  const minLength = Math.min(cashFlowData.value.length, incomeData.value.length)
  
  return {
    dates: cashFlowData.value.slice(0, minLength).map(d => d.date).reverse(),
    capexGrowth: cashFlowData.value.slice(0, minLength).map((d, i) => {
      if (i < minLength - 1) {
        const growth = calculateRevenueGrowth(d.capitalExpenditure, cashFlowData.value[i + 1].capitalExpenditure)
        return growth ? growth * 100 : null
      }
      return null
    }).reverse(),
    revenueGrowth: incomeData.value.slice(0, minLength).map((d, i) => {
      if (i < minLength - 1) {
        const growth = calculateRevenueGrowth(d.revenue, incomeData.value[i + 1].revenue)
        return growth ? growth * 100 : null
      }
      return null
    }).reverse()
  }
})

// Chart refs
const pricingPowerChart = ref(null)
const incomeVsCashFlowChart = ref(null)
const freeCashFlowChart = ref(null)
const capexChart = ref(null)
const arVsNiGrowthChart = ref(null)
const inventoryGrowthChart = ref(null)
const apGrowthChart = ref(null)
const capexAnalysisChart = ref(null)

// Chart instances
let pricingPowerChartInstance = null
let incomeVsCashFlowChartInstance = null
let freeCashFlowChartInstance = null
let capexChartInstance = null
let arVsNiGrowthChartInstance = null
let inventoryGrowthChartInstance = null
let apGrowthChartInstance = null
let capexAnalysisChartInstance = null

// Create Pricing Power Chart
const createPricingPowerChart = () => {
  if (!pricingPowerChart.value || !pricingPowerData.value) return
  
  if (pricingPowerChartInstance) {
    pricingPowerChartInstance.destroy()
  }
  
  const ctx = pricingPowerChart.value.getContext('2d')
  pricingPowerChartInstance = new ChartJS(ctx, {
    type: 'line',
    data: {
      labels: pricingPowerData.value.dates,
      datasets: [
        {
          label: 'Revenue Growth Rate (%)',
          data: pricingPowerData.value.revenueGrowth,
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          yAxisID: 'y'
        },
        {
          label: 'Gross Margin (%)',
          data: pricingPowerData.value.grossMargin,
          borderColor: 'rgb(16, 185, 129)',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          yAxisID: 'y'
        },
        {
          label: 'Operating Margin (%)',
          data: pricingPowerData.value.operatingMargin,
          borderColor: 'rgb(245, 158, 11)',
          backgroundColor: 'rgba(245, 158, 11, 0.1)',
          yAxisID: 'y'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      scales: {
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          title: {
            display: true,
            text: 'Percentage (%)'
          }
        }
      }
    }
  })
}

// Create Income vs Cash Flow Chart
const createIncomeVsCashFlowChart = () => {
  if (!incomeVsCashFlowChart.value || !financialHealthData.value) return
  
  if (incomeVsCashFlowChartInstance) {
    incomeVsCashFlowChartInstance.destroy()
  }
  
  const ctx = incomeVsCashFlowChart.value.getContext('2d')
  incomeVsCashFlowChartInstance = new ChartJS(ctx, {
    type: 'bar',
    data: {
      labels: financialHealthData.value.dates,
      datasets: [
        {
          label: 'Net Income',
          data: financialHealthData.value.netIncome,
          backgroundColor: 'rgba(59, 130, 246, 0.7)',
          borderColor: 'rgb(59, 130, 246)',
          borderWidth: 1
        },
        {
          label: 'Operating Cash Flow',
          data: financialHealthData.value.operatingCashFlow,
          backgroundColor: 'rgba(16, 185, 129, 0.7)',
          borderColor: 'rgb(16, 185, 129)',
          borderWidth: 1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Amount ($)'
          }
        }
      }
    }
  })
}

// Create Free Cash Flow Chart
const createFreeCashFlowChart = () => {
  if (!freeCashFlowChart.value || !financialHealthData.value) return
  
  if (freeCashFlowChartInstance) {
    freeCashFlowChartInstance.destroy()
  }
  
  const ctx = freeCashFlowChart.value.getContext('2d')
  freeCashFlowChartInstance = new ChartJS(ctx, {
    type: 'line',
    data: {
      labels: financialHealthData.value.dates,
      datasets: [
        {
          label: 'Free Cash Flow',
          data: financialHealthData.value.freeCashFlow,
          borderColor: 'rgb(139, 92, 246)',
          backgroundColor: 'rgba(139, 92, 246, 0.1)',
          fill: true
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Amount ($)'
          }
        }
      }
    }
  })
}

// Create CapEx Chart
const createCapexChart = () => {
  if (!capexChart.value || !financialHealthData.value) return
  
  if (capexChartInstance) {
    capexChartInstance.destroy()
  }
  
  const ctx = capexChart.value.getContext('2d')
  capexChartInstance = new ChartJS(ctx, {
    type: 'bar',
    data: {
      labels: financialHealthData.value.dates,
      datasets: [
        {
          label: 'Capital Expenditure',
          data: financialHealthData.value.capex,
          backgroundColor: 'rgba(239, 68, 68, 0.7)',
          borderColor: 'rgb(239, 68, 68)',
          borderWidth: 1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Amount ($)'
          }
        }
      }
    }
  })
}

// Create AR vs NI Growth Chart
const createARvsNIGrowthChart = () => {
  if (!arVsNiGrowthChart.value || !workingCapitalData.value) return
  
  if (arVsNiGrowthChartInstance) {
    arVsNiGrowthChartInstance.destroy()
  }
  
  const ctx = arVsNiGrowthChart.value.getContext('2d')
  arVsNiGrowthChartInstance = new ChartJS(ctx, {
    type: 'line',
    data: {
      labels: workingCapitalData.value.dates,
      datasets: [
        {
          label: 'Accounts Receivables Growth (%)',
          data: workingCapitalData.value.accountsReceivablesGrowth,
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          fill: false
        },
        {
          label: 'Net Income Growth (%)',
          data: workingCapitalData.value.netIncomeGrowth,
          borderColor: 'rgb(16, 185, 129)',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      scales: {
        y: {
          title: {
            display: true,
            text: 'Growth Rate (%)'
          }
        }
      }
    }
  })
}

// Create Inventory Growth Chart
const createInventoryGrowthChart = () => {
  if (!inventoryGrowthChart.value || !workingCapitalData.value) return
  
  if (inventoryGrowthChartInstance) {
    inventoryGrowthChartInstance.destroy()
  }
  
  const ctx = inventoryGrowthChart.value.getContext('2d')
  inventoryGrowthChartInstance = new ChartJS(ctx, {
    type: 'bar',
    data: {
      labels: workingCapitalData.value.dates,
      datasets: [
        {
          label: 'Inventory Growth (%)',
          data: workingCapitalData.value.inventoryGrowth,
          backgroundColor: 'rgba(139, 92, 246, 0.7)',
          borderColor: 'rgb(139, 92, 246)',
          borderWidth: 1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          title: {
            display: true,
            text: 'Growth Rate (%)'
          }
        }
      }
    }
  })
}

// Create Accounts Payables Growth Chart
const createAPGrowthChart = () => {
  if (!apGrowthChart.value || !workingCapitalData.value) return
  
  if (apGrowthChartInstance) {
    apGrowthChartInstance.destroy()
  }
  
  const ctx = apGrowthChart.value.getContext('2d')
  apGrowthChartInstance = new ChartJS(ctx, {
    type: 'bar',
    data: {
      labels: workingCapitalData.value.dates,
      datasets: [
        {
          label: 'Accounts Payables Growth (%)',
          data: workingCapitalData.value.accountsPayablesGrowth,
          backgroundColor: 'rgba(245, 158, 11, 0.7)',
          borderColor: 'rgb(245, 158, 11)',
          borderWidth: 1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          title: {
            display: true,
            text: 'Growth Rate (%)'
          }
        }
      }
    }
  })
}

// Create CapEx Analysis Chart (CapEx Growth vs Revenue Growth)
const createCapexAnalysisChart = () => {
  if (!capexAnalysisChart.value || !capexAnalysisData.value) return
  
  if (capexAnalysisChartInstance) {
    capexAnalysisChartInstance.destroy()
  }
  
  const ctx = capexAnalysisChart.value.getContext('2d')
  capexAnalysisChartInstance = new ChartJS(ctx, {
    type: 'line',
    data: {
      labels: capexAnalysisData.value.dates,
      datasets: [
        {
          label: 'CapEx Growth Rate (%)',
          data: capexAnalysisData.value.capexGrowth,
          borderColor: 'rgb(239, 68, 68)',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          fill: false
        },
        {
          label: 'Revenue Growth Rate (%)',
          data: capexAnalysisData.value.revenueGrowth,
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      scales: {
        y: {
          title: {
            display: true,
            text: 'Growth Rate (%)'
          }
        }
      }
    }
  })
}

// Watch for data changes and render charts
watch([pricingPowerData, activeTab], async () => {
  if (activeTab.value === 'fundamental_analysis' && pricingPowerData.value) {
    await nextTick()
    createPricingPowerChart()
  }
})

watch([financialHealthData, activeTab], async () => {
  if (activeTab.value === 'fundamental_analysis' && financialHealthData.value) {
    await nextTick()
    createIncomeVsCashFlowChart()
    createFreeCashFlowChart()
    createCapexChart()
  }
})

watch([workingCapitalData, activeTab], async () => {
  if (activeTab.value === 'fundamental_analysis' && workingCapitalData.value) {
    await nextTick()
    createARvsNIGrowthChart()
    createInventoryGrowthChart()
    createAPGrowthChart()
  }
})

watch([capexAnalysisData, activeTab], async () => {
  if (activeTab.value === 'fundamental_analysis' && capexAnalysisData.value) {
    await nextTick()
    createCapexAnalysisChart()
  }
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
      <div v-if="mainTab === 'statements' && currentData.length > 0" class="data-table-wrapper">
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
      <div v-if="mainTab === 'fundamental_analysis'" class="fundamental-analysis">
        <div class="analysis-sections">
          <!-- Profile (placeholder for now) -->
          <div v-if="analysisTab === 'profile'" class="analysis-section">
            <h3 class="section-title">{{ t('framework.analysis.profile') }}</h3>
            <div class="section-content">
              <p class="placeholder-text">Company profile coming soon...</p>
            </div>
          </div>

          <!-- Pricing Power -->
          <div v-if="analysisTab === 'pricing_power'" class="analysis-section">
            <h3 class="section-title">{{ t('framework.analysis.pricing_power') }}</h3>
            <div class="section-content">
              <div v-if="pricingPowerData" class="chart-container">
                <canvas ref="pricingPowerChart"></canvas>
              </div>
              <p v-else class="placeholder-text">No pricing power data available</p>
            </div>
          </div>

          <!-- Financial Health -->
          <div v-if="analysisTab === 'financial_health'" class="analysis-section">
            <h3 class="section-title">{{ t('framework.analysis.financial_health') }}</h3>
            <div class="section-content">
              <!-- Net Income & Operating Cash Flow Chart -->
              <div v-if="financialHealthData" class="chart-group">
                <div class="chart-container">
                  <h4 class="chart-subtitle">Net Income & Operating Cash Flow</h4>
                  <canvas ref="incomeVsCashFlowChart"></canvas>
                </div>
                
                <!-- Free Cash Flow Chart -->
                <div class="chart-container">
                  <h4 class="chart-subtitle">Free Cash Flow</h4>
                  <canvas ref="freeCashFlowChart"></canvas>
                </div>
                
                <!-- Capital Expenditure Chart -->
                <div class="chart-container">
                  <h4 class="chart-subtitle">Capital Expenditure</h4>
                  <canvas ref="capexChart"></canvas>
                </div>
              </div>
              <p v-else class="placeholder-text">No financial health data available</p>
            </div>
          </div>

          <!-- Working Capital Analysis -->
          <div v-if="analysisTab === 'working_capital'" class="analysis-section">
            <h3 class="section-title">{{ t('framework.analysis.working_capital') }}</h3>
            <div class="section-content">
              <div v-if="workingCapitalData" class="chart-group">
                <!-- AR vs NI Growth Chart -->
                <div class="chart-container">
                  <h4 class="chart-subtitle">Accounts Receivables Growth vs Net Income Growth</h4>
                  <canvas ref="arVsNiGrowthChart"></canvas>
                </div>
                
                <!-- Inventory Growth Chart -->
                <div class="chart-container">
                  <h4 class="chart-subtitle">Inventory Growth</h4>
                  <canvas ref="inventoryGrowthChart"></canvas>
                </div>
                
                <!-- Accounts Payables Growth Chart -->
                <div class="chart-container">
                  <h4 class="chart-subtitle">Accounts Payables Growth</h4>
                  <canvas ref="apGrowthChart"></canvas>
                </div>
              </div>
              <p v-else class="placeholder-text">No working capital data available</p>
            </div>
          </div>

          <!-- CapEx Analysis -->
          <div v-if="analysisTab === 'capex'" class="analysis-section">
            <h3 class="section-title">{{ t('framework.analysis.capex') }}</h3>
            <div class="section-content">
              <div v-if="capexAnalysisData" class="chart-container">
                <h4 class="chart-subtitle">CapEx Growth vs Revenue Growth</h4>
                <canvas ref="capexAnalysisChart"></canvas>
              </div>
              <p v-else class="placeholder-text">No CapEx analysis data available</p>
            </div>
          </div>

          <!-- Valuation Analysis -->
          <div v-if="analysisTab === 'valuation'" class="analysis-section">
            <h3 class="section-title">{{ t('framework.analysis.valuation') }}</h3>
            <div class="section-content">
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
          </div>

          <!-- Structure (formerly Calendar) -->
          <div v-if="analysisTab === 'structure'" class="analysis-section">
            <h3 class="section-title">{{ t('framework.analysis.structure') }}</h3>
            <div class="section-content">
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
