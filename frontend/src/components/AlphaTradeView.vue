<script setup>
import API_BASE_URL from '@/config/api.js'

import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import AddTradeLotModal from './AddTradeLotModal.vue'
import EditTradeLotModal from './EditTradeLotModal.vue'

const showAddLotModal = ref(false)
const showEditLotModal = ref(false)
const editingLot = ref(null)
const editingTicker = ref('')
const positions = ref([])
const expandedPositions = ref(new Set())
const loading = ref(false)
const activeTab = ref({}) // Track active tab per position: { ticker: 'lot' | 'fundamental' | 'scenario' }
const hypotheticalAdjustment = ref({}) // Track hypothetical price adjustment per position: { ticker: percentage }

// Drag and drop state
const draggedIndex = ref(null)
const dragOverIndex = ref(null)

// Fundamental analysis questions organized by category
const { t } = useI18n()

// Fundamental analysis questions organized by category
const fundamentalQuestions = computed(() => [
  // FUNDAMENTAL SECTION
  {
    id: 1,
    category: 'FUNDAMENTAL',
    title: t('alphatrade.questions.income_statement.title'),
    subtitle: t('alphatrade.questions.income_statement.subtitle'),
    placeholder: t('alphatrade.questions.income_statement.placeholder')
  },
  {
    id: 2,
    category: 'FUNDAMENTAL',
    title: t('alphatrade.questions.cash_flow.title'),
    subtitle: t('alphatrade.questions.cash_flow.subtitle'),
    placeholder: t('alphatrade.questions.cash_flow.placeholder')
  },
  {
    id: 3,
    category: 'FUNDAMENTAL',
    title: t('alphatrade.questions.working_capital.title'),
    subtitle: t('alphatrade.questions.working_capital.subtitle'),
    placeholder: t('alphatrade.questions.working_capital.placeholder')
  },
  {
    id: 4,
    category: 'FUNDAMENTAL',
    title: t('alphatrade.questions.balance_sheet.title'),
    subtitle: t('alphatrade.questions.balance_sheet.subtitle'),
    placeholder: t('alphatrade.questions.balance_sheet.placeholder')
  },
  {
    id: 5,
    category: 'FUNDAMENTAL',
    title: t('alphatrade.questions.capex.title'),
    subtitle: t('alphatrade.questions.capex.subtitle'),
    placeholder: t('alphatrade.questions.capex.placeholder')
  },
  {
    id: 6,
    category: 'FUNDAMENTAL',
    title: t('alphatrade.questions.accounting.title'),
    subtitle: t('alphatrade.questions.accounting.subtitle'),
    placeholder: t('alphatrade.questions.accounting.placeholder')
  },
  {
    id: 7,
    category: 'FUNDAMENTAL',
    title: t('alphatrade.questions.management.title'),
    subtitle: t('alphatrade.questions.management.subtitle'),
    placeholder: t('alphatrade.questions.management.placeholder')
  },
  {
    id: 8,
    category: 'FUNDAMENTAL',
    title: t('alphatrade.questions.valuation.title'),
    subtitle: t('alphatrade.questions.valuation.subtitle'),
    placeholder: t('alphatrade.questions.valuation.placeholder')
  },
  {
    id: 9,
    category: 'FUNDAMENTAL',
    title: t('alphatrade.questions.catalyst.title'),
    subtitle: t('alphatrade.questions.catalyst.subtitle'),
    placeholder: t('alphatrade.questions.catalyst.placeholder')
  },
  {
    id: 10,
    category: 'FUNDAMENTAL',
    title: t('alphatrade.questions.sizing.title'),
    subtitle: t('alphatrade.questions.sizing.subtitle'),
    placeholder: t('alphatrade.questions.sizing.placeholder')
  },
  
  // TIMING SECTION
  {
    id: 101,
    category: 'TIMING',
    title: t('alphatrade.questions.earnings.title'),
    subtitle: t('alphatrade.questions.earnings.subtitle'),
    placeholder: t('alphatrade.questions.earnings.placeholder')
  },
  {
    id: 102,
    category: 'TIMING',
    title: t('alphatrade.questions.liquidity.title'),
    subtitle: t('alphatrade.questions.liquidity.subtitle'),
    placeholder: t('alphatrade.questions.liquidity.placeholder')
  },
  {
    id: 103,
    category: 'TIMING',
    title: t('alphatrade.questions.balance_sheet_deadlines.title'),
    subtitle: t('alphatrade.questions.balance_sheet_deadlines.subtitle'),
    placeholder: t('alphatrade.questions.balance_sheet_deadlines.placeholder')
  },
  {
    id: 104,
    category: 'TIMING',
    title: t('alphatrade.questions.regulatory.title'),
    subtitle: t('alphatrade.questions.regulatory.subtitle'),
    placeholder: t('alphatrade.questions.regulatory.placeholder')
  },
  {
    id: 105,
    category: 'TIMING',
    title: t('alphatrade.questions.macro.title'),
    subtitle: t('alphatrade.questions.macro.subtitle'),
    placeholder: t('alphatrade.questions.macro.placeholder')
  },
  
  // STRUCTURE SECTION
  {
    id: 201,
    category: 'STRUCTURE',
    title: t('alphatrade.questions.ownership.title'),
    subtitle: t('alphatrade.questions.ownership.subtitle'),
    placeholder: t('alphatrade.questions.ownership.placeholder')
  },
  {
    id: 202,
    category: 'STRUCTURE',
    title: t('alphatrade.questions.float.title'),
    subtitle: t('alphatrade.questions.float.subtitle'),
    placeholder: t('alphatrade.questions.float.placeholder')
  },
  {
    id: 203,
    category: 'STRUCTURE',
    title: t('alphatrade.questions.price_structure.title'),
    subtitle: t('alphatrade.questions.price_structure.subtitle'),
    placeholder: t('alphatrade.questions.price_structure.placeholder')
  },
  {
    id: 204,
    category: 'STRUCTURE',
    title: t('alphatrade.questions.options.title'),
    subtitle: t('alphatrade.questions.options.subtitle'),
    placeholder: t('alphatrade.questions.options.placeholder')
  },
  {
    id: 205,
    category: 'STRUCTURE',
    title: t('alphatrade.questions.short_interest.title'),
    subtitle: t('alphatrade.questions.short_interest.subtitle'),
    placeholder: t('alphatrade.questions.short_interest.placeholder')
  },
  {
    id: 206,
    category: 'STRUCTURE',
    title: t('alphatrade.questions.borrow.title'),
    subtitle: t('alphatrade.questions.borrow.subtitle'),
    placeholder: t('alphatrade.questions.borrow.placeholder')
  }
])



onMounted(() => {
  // Load positions from localStorage or API
  const savedPositions = localStorage.getItem('alphatrade_positions')
  if (savedPositions) {
    positions.value = JSON.parse(savedPositions)
    // Fetch current prices for all positions
    fetchStockPrices()
  } else {
    // Start with empty positions - no mock data
    savePositions()
    fetchStockPrices()
  }
})

const savePositions = () => {
  localStorage.setItem('alphatrade_positions', JSON.stringify(positions.value))
}

const fetchStockPrices = async () => {
  if (positions.value.length === 0) return
  
  loading.value = true
  try {
    const tickers = positions.value.map(p => p.ticker)
    const response = await fetch(`${API_BASE_URL}/api/alphatrade/stock-prices`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(tickers)
    })
    
    if (response.ok) {
      const priceData = await response.json()
      
      // Update positions with real-time data
      positions.value.forEach(position => {
        const data = priceData[position.ticker]
        if (data && !data.error) {
          position.currentPrice = data.currentPrice
          position.companyName = data.companyName
          position.sector = data.sector
        }
      })
      
      savePositions()
    }
  } catch (error) {
    console.error('Error fetching stock prices:', error)
  } finally {
    loading.value = false
  }
}

const fetchSingleStockPrice = async (ticker) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/alphatrade/stock-price/${ticker}`)
    
    if (response.ok) {
      const data = await response.json()
      return data
    }
  } catch (error) {
    console.error(`Error fetching price for ${ticker}:`, error)
  }
  
  return null
}

const togglePosition = (ticker) => {
  if (expandedPositions.value.has(ticker)) {
    expandedPositions.value.delete(ticker)
  } else {
    expandedPositions.value.add(ticker)
    // Set default tab to 'lot' when expanding
    if (!activeTab.value[ticker]) {
      activeTab.value[ticker] = 'lot'
    }
  }
}

const isExpanded = (ticker) => {
  return expandedPositions.value.has(ticker)
}

const setActiveTab = (ticker, tab) => {
  activeTab.value[ticker] = tab
}

const getActiveTab = (ticker) => {
  return activeTab.value[ticker] || 'lot'
}

// Auto-save state
const saveIndicators = ref({}) // Track save status per question
let saveTimeouts = {} // Store timeout IDs for debouncing

const saveFundamentalAnalysis = (ticker, questionId, value) => {
  const key = `${ticker}-${questionId}`
  
  // Clear existing timeout
  if (saveTimeouts[key]) {
    clearTimeout(saveTimeouts[key])
  }
  
  // Show saving indicator
  saveIndicators.value[key] = 'saving'
  
  // Debounce the actual save (wait 500ms after last keystroke)
  saveTimeouts[key] = setTimeout(() => {
    const position = positions.value.find(p => p.ticker === ticker)
    if (position) {
      if (!position.fundamentalAnalysis) {
        position.fundamentalAnalysis = {}
      }
      position.fundamentalAnalysis[questionId] = value
      savePositions()
      
      // Show saved indicator
      saveIndicators.value[key] = 'saved'
      
      // Clear saved indicator after 2 seconds
      setTimeout(() => {
        saveIndicators.value[key] = null
      }, 2000)
    }
  }, 500)
}

const getSaveIndicator = (ticker, questionId) => {
  const key = `${ticker}-${questionId}`
  return saveIndicators.value[key] || null
}

const getFundamentalAnalysis = (ticker, questionId) => {
  const position = positions.value.find(p => p.ticker === ticker)
  return position?.fundamentalAnalysis?.[questionId] || ''
}

const getQuestionScore = (ticker, questionId) => {
  const position = positions.value.find(p => p.ticker === ticker)
  return position?.fundamentalScores?.[questionId] || null
}

const setQuestionScore = (ticker, questionId, score) => {
  const position = positions.value.find(p => p.ticker === ticker)
  if (position) {
    if (!position.fundamentalScores) {
      position.fundamentalScores = {}
    }
    position.fundamentalScores[questionId] = score
    savePositions()
  }
}

// Scenario analysis functions
const getHypotheticalAdjustment = (ticker) => {
  return hypotheticalAdjustment.value[ticker] || 0
}

const setHypotheticalAdjustment = (ticker, percentage) => {
  hypotheticalAdjustment.value[ticker] = percentage
}

const handleSliderDrag = (event, ticker) => {
  const slider = event.currentTarget
  const rect = slider.getBoundingClientRect()
  const updatePosition = (clientX) => {
    const x = clientX - rect.left
    const percentage = (x / rect.width) * 100
    // Map 0-100% position to -100% to +100% range
    const adjustment = Math.round((percentage / 100) * 200 - 100)
    // Clamp between -100 and +100
    const clampedAdjustment = Math.max(-100, Math.min(100, adjustment))
    setHypotheticalAdjustment(ticker, clampedAdjustment)
  }

  const onMouseMove = (e) => {
    updatePosition(e.clientX)
  }

  const onMouseUp = () => {
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }

  updatePosition(event.clientX)
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

const getHypotheticalPrice = (ticker) => {
  const position = positions.value.find(p => p.ticker === ticker)
  if (!position) return 0
  
  const adjustment = getHypotheticalAdjustment(ticker)
  return position.currentPrice * (1 + adjustment / 100)
}

const calculateHypotheticalLotMetrics = (lot, hypotheticalPrice) => {
  const cost = lot.quantity * lot.costPerShare
  const hypotheticalValue = lot.quantity * hypotheticalPrice
  
  let hypotheticalPL, hypotheticalROI
  if (lot.side === 'SHORT') {
    hypotheticalPL = (lot.costPerShare - hypotheticalPrice) * lot.quantity
    hypotheticalROI = ((lot.costPerShare - hypotheticalPrice) / lot.costPerShare) * 100
  } else {
    hypotheticalPL = (hypotheticalPrice - lot.costPerShare) * lot.quantity
    hypotheticalROI = ((hypotheticalPrice - lot.costPerShare) / lot.costPerShare) * 100
  }
  
  return {
    hypotheticalValue,
    hypotheticalPL,
    hypotheticalROI
  }
}

const calculatePositionMetrics = (position) => {
  const totalQuantity = position.lots.reduce((sum, lot) => sum + lot.quantity, 0)
  const totalCost = position.lots.reduce((sum, lot) => sum + (lot.quantity * lot.costPerShare), 0)
  const averageCost = totalQuantity > 0 ? totalCost / totalQuantity : 0
  const marketValue = totalQuantity * position.currentPrice
  
  // Calculate unrealized P/L by summing individual lot P/L (handles both long and short correctly)
  const unrealizedPL = position.lots.reduce((sum, lot) => {
    const lotMetrics = calculateLotMetrics(lot, position.currentPrice)
    return sum + lotMetrics.lotPL
  }, 0)
  
  // Calculate performance based on total cost
  const performance = totalCost > 0 ? (unrealizedPL / totalCost) * 100 : 0
  
  return {
    totalQuantity,
    totalCost,
    averageCost,
    marketValue,
    unrealizedPL,
    performance
  }
}

const calculateLotMetrics = (lot, currentPrice) => {
  const cost = lot.quantity * lot.costPerShare
  const marketValue = lot.quantity * currentPrice
  
  // For short positions, P/L is inverted (profit when price goes down)
  let lotPL, performance
  if (lot.side === 'SHORT') {
    // Short: P/L = (entry price - current price) * quantity
    // If price goes UP (current > entry), this is NEGATIVE (loss)
    // If price goes DOWN (current < entry), this is POSITIVE (profit)
    lotPL = (lot.costPerShare - currentPrice) * lot.quantity
    performance = ((lot.costPerShare - currentPrice) / lot.costPerShare) * 100
  } else {
    // Long: P/L = (current price - entry price) * quantity
    // If price goes UP (current > entry), this is POSITIVE (profit)
    // If price goes DOWN (current < entry), this is NEGATIVE (loss)
    lotPL = (currentPrice - lot.costPerShare) * lot.quantity
    performance = ((currentPrice - lot.costPerShare) / lot.costPerShare) * 100
  }
  
  return {
    cost,
    marketValue,
    lotPL,
    performance
  }
}

const formatCurrency = (value) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value)
}

const formatPercent = (value) => {
  if (value >= 0) {
    return `+${value.toFixed(2)}%`
  } else {
    return `${value.toFixed(2)}%`
  }
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { month: '2-digit', day: '2-digit', year: 'numeric' })
}

const portfolioTotals = computed(() => {
  let totalValue = 0
  let totalCost = 0
  let unrealizedPL = 0
  
  positions.value.forEach(position => {
    const metrics = calculatePositionMetrics(position)
    totalValue += metrics.marketValue
    totalCost += metrics.totalCost
    unrealizedPL += metrics.unrealizedPL  // Sum actual P/L from each position
  })
  
  const totalReturn = totalCost > 0 ? (unrealizedPL / totalCost) * 100 : 0
  
  return {
    totalValue,
    totalCost,
    unrealizedPL,
    totalReturn
  }
})

const handleAddLot = async (lotData) => {
  // Find or create position for ticker
  let position = positions.value.find(p => p.ticker === lotData.ticker.toUpperCase())
  
  if (!position) {
    // Fetch real-time stock data
    const stockData = await fetchSingleStockPrice(lotData.ticker)
    
    // Create new position
    position = {
      ticker: lotData.ticker.toUpperCase(),
      companyName: stockData?.companyName || lotData.ticker.toUpperCase(),
      sector: stockData?.sector || 'UNKNOWN',
      currentPrice: stockData?.currentPrice || 0,
      side: lotData.side || 'LONG',
      lots: []
    }
    positions.value.push(position)
  }
  
  // Add new lot
  const newLot = {
    id: Date.now(),
    purchaseDate: lotData.purchaseDate,
    quantity: lotData.quantity,
    costPerShare: lotData.costPerShare,
    side: lotData.side || 'LONG',
    note: lotData.note || '',
    link: lotData.link || ''
  }
  
  position.lots.push(newLot)
  savePositions()
  showAddLotModal.value = false
}

const deletePosition = (ticker) => {
  if (confirm(`Are you sure you want to delete the entire ${ticker} position?`)) {
    const index = positions.value.findIndex(p => p.ticker === ticker)
    if (index !== -1) {
      positions.value.splice(index, 1)
      expandedPositions.value.delete(ticker)
      delete activeTab.value[ticker]
      savePositions()
    }
  }
}

const deleteLot = (ticker, lotId) => {
  if (confirm('Are you sure you want to delete this lot?')) {
    const position = positions.value.find(p => p.ticker === ticker)
    if (position) {
      const lotIndex = position.lots.findIndex(lot => lot.id === lotId)
      if (lotIndex !== -1) {
        position.lots.splice(lotIndex, 1)
        
        // If no lots left, delete the entire position
        if (position.lots.length === 0) {
          deletePosition(ticker)
        } else {
          savePositions()
        }
      }
    }
  }
}

const editLot = (ticker, lotId) => {
  const position = positions.value.find(p => p.ticker === ticker)
  if (position) {
    const lot = position.lots.find(l => l.id === lotId)
    if (lot) {
      editingLot.value = { ...lot }
      editingTicker.value = ticker
      showEditLotModal.value = true
    }
  }
}

const handleEditLot = (updatedData) => {
  const position = positions.value.find(p => p.ticker === editingTicker.value)
  if (position && editingLot.value) {
    const lot = position.lots.find(l => l.id === editingLot.value.id)
    if (lot) {
      lot.purchaseDate = updatedData.purchaseDate
      lot.quantity = updatedData.quantity
      lot.costPerShare = updatedData.costPerShare
      lot.link = updatedData.link
      lot.note = updatedData.note
      
      savePositions()
      showEditLotModal.value = false
      editingLot.value = null
      editingTicker.value = ''
    }
  }
}

// Drag and drop handlers
const handleDragStart = (index) => {
  draggedIndex.value = index
}

const handleDragOver = (event, index) => {
  event.preventDefault()
  dragOverIndex.value = index
}

const handleDragLeave = () => {
  dragOverIndex.value = null
}

const handleDrop = (event, dropIndex) => {
  event.preventDefault()
  
  if (draggedIndex.value !== null && draggedIndex.value !== dropIndex) {
    const items = [...positions.value]
    const draggedItem = items[draggedIndex.value]
    
    // Remove from old position
    items.splice(draggedIndex.value, 1)
    
    // Insert at new position
    items.splice(dropIndex, 0, draggedItem)
    
    positions.value = items
    savePositions()
  }
  
  draggedIndex.value = null
  dragOverIndex.value = null
}

const handleDragEnd = () => {
  draggedIndex.value = null
  dragOverIndex.value = null
}
</script>

<template>
  <div class="alphatrade-container">
    <div class="header">
      <div class="header-left">
        <h1 class="title">{{ t('alphatrade.title') }}</h1>
        <p class="subtitle">{{ t('alphatrade.subtitle') }}</p>
      </div>
      <button class="add-lot-btn" @click="showAddLotModal = true">
        <span class="btn-icon">+</span>
        <span class="btn-text">{{ t('alphatrade.new_execution') }}</span>
      </button>
    </div>

    <!-- Portfolio Summary Cards -->
    <div v-if="positions.length > 0" class="summary-cards">
      <div class="summary-card">
        <div class="card-header">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12 6 12 12 16 14"></polyline>
          </svg>
          <span class="card-label">{{ t('alphatrade.total_value') }}</span>
        </div>
        <div class="card-value">{{ formatCurrency(portfolioTotals.totalValue) }}</div>
      </div>

      <div class="summary-card">
        <div class="card-header">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="1" x2="12" y2="23"></line>
            <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
          </svg>
          <span class="card-label">{{ t('alphatrade.total_cost') }}</span>
        </div>
        <div class="card-value">{{ formatCurrency(portfolioTotals.totalCost) }}</div>
      </div>

      <div class="summary-card pl-card">
        <div class="card-header">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <polyline points="19 12 12 19 5 12"></polyline>
          </svg>
          <span class="card-label">{{ t('alphatrade.unrealized_pl') }}</span>
        </div>
        <div class="card-value" :class="{ positive: portfolioTotals.unrealizedPL >= 0, negative: portfolioTotals.unrealizedPL < 0 }">
          {{ formatCurrency(portfolioTotals.unrealizedPL) }}
        </div>
      </div>

      <div class="summary-card return-card" :class="{ positive: portfolioTotals.totalReturn >= 0, negative: portfolioTotals.totalReturn < 0 }">
        <div class="card-header">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
            <polyline points="17 6 23 6 23 12"></polyline>
          </svg>
          <span class="card-label">{{ t('alphatrade.total_return') }}</span>
        </div>
        <div class="card-value">{{ formatPercent(portfolioTotals.totalReturn) }}</div>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>{{ t('alphatrade.loading') }}</p>
    </div>

    <div v-else-if="positions.length === 0" class="empty-state">
      <p>{{ t('alphatrade.empty_state') }}</p>
    </div>

    <div v-else class="positions-list">
      <div 
        v-for="(position, index) in positions" 
        :key="position.ticker" 
        class="position-card"
        :class="{ 
          expanded: isExpanded(position.ticker),
          'drag-over': dragOverIndex === index,
          'dragging': draggedIndex === index
        }"
        draggable="true"
        @dragstart="handleDragStart(index)"
        @dragover="handleDragOver($event, index)"
        @dragleave="handleDragLeave"
        @drop="handleDrop($event, index)"
        @dragend="handleDragEnd"
      >
        <div class="position-header" @click="togglePosition(position.ticker)">
          <div class="position-info">
            <div class="ticker-icon-wrapper">
              <div class="ticker-icon">{{ position.ticker.charAt(0) }}</div>
              <div class="position-indicator" :class="position.side || 'LONG'">
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="18 15 12 9 6 15"></polyline>
                </svg>
              </div>
            </div>
            <div class="ticker-details">
              <div class="ticker-row">
                <h3 class="ticker">{{ position.ticker }}</h3>
                <span class="position-badge" :class="position.side || 'LONG'">
                  {{ position.side || 'LONG' }}
                </span>
              </div>
              <p class="sector">{{ position.sector }}</p>
            </div>
          </div>
          
          <div class="position-metrics">
            <div class="metric">
              <span class="metric-label">{{ t('alphatrade.market_price') }}</span>
              <span class="metric-value">{{ formatCurrency(position.currentPrice) }}</span>
            </div>
            <div class="metric">
              <span class="metric-label">{{ t('alphatrade.valuation') }}</span>
              <span class="metric-value">{{ formatCurrency(calculatePositionMetrics(position).marketValue) }}</span>
            </div>
            <div class="metric">
              <span class="metric-label">{{ t('alphatrade.unrealized_pl') }}</span>
              <span 
                class="metric-value pl-value" 
                :class="{ positive: calculatePositionMetrics(position).unrealizedPL >= 0, negative: calculatePositionMetrics(position).unrealizedPL < 0 }"
              >
                {{ formatCurrency(calculatePositionMetrics(position).unrealizedPL) }}
              </span>
            </div>
          </div>
          
          <button 
            class="delete-position-btn" 
            @click.stop="deletePosition(position.ticker)"
            :title="t('alphatrade.delete_position')"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              <line x1="10" y1="11" x2="10" y2="17"></line>
              <line x1="14" y1="11" x2="14" y2="17"></line>
            </svg>
          </button>
          
          <div class="expand-icon">
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              width="20" 
              height="20" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              stroke-width="2" 
              stroke-linecap="round" 
              stroke-linejoin="round"
              :style="{ transform: isExpanded(position.ticker) ? 'rotate(180deg)' : 'rotate(0deg)' }"
            >
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </div>
        </div>

        <div v-if="isExpanded(position.ticker)" class="expanded-content">
          <!-- Tab Navigation -->
          <div class="tab-nav">
            <button 
              class="tab-btn" 
              :class="{ active: getActiveTab(position.ticker) === 'lot' }"
              @click.stop="setActiveTab(position.ticker, 'lot')"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 3h7v7H3z"></path>
                <path d="M14 3h7v7h-7z"></path>
                <path d="M14 14h7v7h-7z"></path>
                <path d="M3 14h7v7H3z"></path>
              </svg>
              {{ t('alphatrade.tabs.lot_inventory') }}
            </button>
            <button 
              class="tab-btn" 
              :class="{ active: getActiveTab(position.ticker) === 'fundamental' }"
              @click.stop="setActiveTab(position.ticker, 'fundamental')"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
              </svg>
              {{ t('alphatrade.tabs.fundamental_analysis') }}
            </button>
            <button 
              class="tab-btn" 
              :class="{ active: getActiveTab(position.ticker) === 'scenario' }"
              @click.stop="setActiveTab(position.ticker, 'scenario')"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
              </svg>
              {{ t('alphatrade.tabs.scenario_analysis') }}
            </button>
          </div>

          <!-- Lot Inventory Tab -->
          <div v-if="getActiveTab(position.ticker) === 'lot'" class="lot-details">
            <table class="lots-table">
              <thead>
                <tr>
                  <th>{{ t('alphatrade.lot_table.purchase_date') }}</th>
                  <th>{{ t('alphatrade.lot_table.qty') }}</th>
                  <th>{{ t('alphatrade.lot_table.price') }}</th>
                  <th>{{ t('alphatrade.lot_table.cost') }}</th>
                  <th>{{ t('alphatrade.lot_table.equity_now') }}</th>
                  <th>{{ t('alphatrade.lot_table.cost_val') }}</th>
                  <th>{{ t('alphatrade.lot_table.pl') }}</th>
                  <th>{{ t('alphatrade.lot_table.pct') }}</th>
                  <th>{{ t('alphatrade.lot_table.note') }}</th>
                  <th>{{ t('alphatrade.lot_table.actions') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="lot in position.lots" :key="lot.id" class="lot-row">
                  <td>{{ formatDate(lot.purchaseDate) }}</td>
                  <td>{{ lot.quantity }}</td>
                  <td>{{ formatCurrency(position.currentPrice) }}</td>
                  <td>{{ formatCurrency(lot.costPerShare) }}</td>
                  <td>{{ formatCurrency(calculateLotMetrics(lot, position.currentPrice).marketValue) }}</td>
                  <td>{{ formatCurrency(calculateLotMetrics(lot, position.currentPrice).cost) }}</td>
                  <td :class="{ positive: calculateLotMetrics(lot, position.currentPrice).lotPL >= 0, negative: calculateLotMetrics(lot, position.currentPrice).lotPL < 0 }">
                    {{ formatCurrency(calculateLotMetrics(lot, position.currentPrice).lotPL) }}
                  </td>
                  <td :class="{ positive: calculateLotMetrics(lot, position.currentPrice).performance >= 0, negative: calculateLotMetrics(lot, position.currentPrice).performance < 0 }">
                    {{ formatPercent(calculateLotMetrics(lot, position.currentPrice).performance) }}
                  </td>
                  <td class="note-cell">{{ lot.note || '-' }}</td>
                  <td class="actions-cell">
                    <div class="action-buttons">
                      <button 
                        class="action-btn link-btn"
                        :class="{ disabled: !lot.link }"
                        @click.stop="lot.link && window.open(lot.link, '_blank')"
                        :disabled="!lot.link"
                        title="Open Link"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                          <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                          <polyline points="15 3 21 3 21 9"></polyline>
                          <line x1="10" y1="14" x2="21" y2="3"></line>
                        </svg>
                      </button>
                      <button 
                        class="action-btn edit-btn"
                        @click.stop="editLot(position.ticker, lot.id)"
                        title="Modify Lot"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                        </svg>
                      </button>
                      <button 
                        class="action-btn delete-btn"
                        @click.stop="deleteLot(position.ticker, lot.id)"
                        title="Delete Lot"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                          <polyline points="3 6 5 6 21 6"></polyline>
                          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                          <line x1="10" y1="11" x2="10" y2="17"></line>
                          <line x1="14" y1="11" x2="14" y2="17"></line>
                        </svg>
                      </button>
                    </div>
                  </td>
                </tr>
                <tr class="total-row">
                  <td><strong>{{ t('alphatrade.lot_table.total_stats') }}</strong></td>
                  <td><strong>{{ calculatePositionMetrics(position).totalQuantity }}</strong></td>
                  <td><strong>{{ formatCurrency(position.currentPrice) }}</strong></td>
                  <td><strong>{{ formatCurrency(calculatePositionMetrics(position).averageCost) }}</strong></td>
                  <td><strong>{{ formatCurrency(calculatePositionMetrics(position).marketValue) }}</strong></td>
                  <td><strong>{{ formatCurrency(calculatePositionMetrics(position).totalCost) }}</strong></td>
                  <td :class="{ positive: calculatePositionMetrics(position).unrealizedPL >= 0, negative: calculatePositionMetrics(position).unrealizedPL < 0 }">
                    <strong>{{ formatCurrency(calculatePositionMetrics(position).unrealizedPL) }}</strong>
                  </td>
                  <td :class="{ positive: calculatePositionMetrics(position).performance >= 0, negative: calculatePositionMetrics(position).performance < 0 }">
                    <strong>{{ formatPercent(calculatePositionMetrics(position).performance) }}</strong>
                  </td>
                  <td colspan="2"></td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Fundamental Analysis Tab -->
          <div v-if="getActiveTab(position.ticker) === 'fundamental'" class="fundamental-analysis">
            <div class="golden-rule">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
              </svg>
              <span class="rule-title">{{ t('alphatrade.fundamental.golden_rule_title') }}</span>
              <p class="rule-text">{{ t('alphatrade.fundamental.golden_rule_text') }}</p>
            </div>

            <!-- FUNDAMENTAL SECTION -->
            <div class="analysis-section">
              <h3 class="section-header">{{ t('alphatrade.fundamental.section_fundamental') }}</h3>
              <div class="analysis-grid">
                <div v-for="question in fundamentalQuestions.filter(q => q.category === 'FUNDAMENTAL')" :key="question.id" class="analysis-card">
                  <div class="card-header">
                    <div class="card-title-section">
                      <h4 class="card-number">{{ question.id }}.</h4>
                      <div>
                        <h4 class="card-title">{{ question.title }}</h4>
                        <p class="card-subtitle">{{ question.subtitle }}</p>
                      </div>
                    </div>
                    <div class="score-buttons">
                      <button 
                        v-for="score in [1, 2, 3, 4, 5]" 
                        :key="score"
                        class="score-btn"
                        :class="{ active: getQuestionScore(position.ticker, question.id) === score }"
                        @click.stop="setQuestionScore(position.ticker, question.id, score)"
                        :title="`Score: ${score}`"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="none">
                          <circle cx="12" cy="12" r="10"></circle>
                        </svg>
                      </button>
                    </div>
                  </div>
                  <textarea 
                    :value="getFundamentalAnalysis(position.ticker, question.id)"
                    @input="saveFundamentalAnalysis(position.ticker, question.id, $event.target.value)"
                    :placeholder="question.placeholder"
                    class="analysis-input"
                    rows="2"
                  ></textarea>
                </div>
              </div>
            </div>

            <!-- TIMING SECTION -->
            <div class="analysis-section">
              <h3 class="section-header">{{ t('alphatrade.fundamental.section_timing') }}</h3>
              <div class="analysis-grid">
                <div v-for="question in fundamentalQuestions.filter(q => q.category === 'TIMING')" :key="question.id" class="analysis-card">
                  <div class="card-header">
                    <div class="card-title-section">
                      <div>
                        <h4 class="card-title">{{ question.title }}</h4>
                        <p class="card-subtitle">{{ question.subtitle }}</p>
                      </div>
                    </div>
                    <div class="score-buttons">
                      <button 
                        v-for="score in [1, 2, 3, 4, 5]" 
                        :key="score"
                        class="score-btn"
                        :class="{ active: getQuestionScore(position.ticker, question.id) === score }"
                        @click.stop="setQuestionScore(position.ticker, question.id, score)"
                        :title="`Score: ${score}`"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="none">
                          <circle cx="12" cy="12" r="10"></circle>
                        </svg>
                      </button>
                    </div>
                  </div>
                  <textarea 
                    :value="getFundamentalAnalysis(position.ticker, question.id)"
                    @input="saveFundamentalAnalysis(position.ticker, question.id, $event.target.value)"
                    :placeholder="question.placeholder"
                    class="analysis-input"
                    rows="2"
                  ></textarea>
                </div>
              </div>
            </div>

            <!-- STRUCTURE SECTION -->
            <div class="analysis-section">
              <h3 class="section-header">{{ t('alphatrade.fundamental.section_structure') }}</h3>
              <div class="analysis-grid">
                <div v-for="question in fundamentalQuestions.filter(q => q.category === 'STRUCTURE')" :key="question.id" class="analysis-card">
                  <div class="card-header">
                    <div class="card-title-section">
                      <div>
                        <h4 class="card-title">{{ question.title }}</h4>
                        <p class="card-subtitle">{{ question.subtitle }}</p>
                      </div>
                    </div>
                    <div class="score-buttons">
                      <button 
                        v-for="score in [1, 2, 3, 4, 5]" 
                        :key="score"
                        class="score-btn"
                        :class="{ active: getQuestionScore(position.ticker, question.id) === score }"
                        @click.stop="setQuestionScore(position.ticker, question.id, score)"
                        :title="`Score: ${score}`"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="none">
                          <circle cx="12" cy="12" r="10"></circle>
                        </svg>
                      </button>
                    </div>
                  </div>
                  <textarea 
                    :value="getFundamentalAnalysis(position.ticker, question.id)"
                    @input="saveFundamentalAnalysis(position.ticker, question.id, $event.target.value)"
                    :placeholder="question.placeholder"
                    class="analysis-input"
                    rows="2"
                  ></textarea>
                </div>
              </div>
            </div>
          </div>

          <!-- Scenario Analysis Tab -->
          <div v-if="getActiveTab(position.ticker) === 'scenario'" class="scenario-analysis">
            <div class="scenario-header">
              <div class="scenario-title">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path>
                </svg>
                <span>{{ t('alphatrade.scenario.hypothetical_target') }}</span>
              </div>
              <div class="current-price-display">{{ formatCurrency(getHypotheticalPrice(position.ticker)) }}</div>
            </div>

            <div class="scenario-controls">
              <div class="percentage-buttons">
                <button class="pct-btn negative" @click.stop="setHypotheticalAdjustment(position.ticker, -100)" :class="{ active: getHypotheticalAdjustment(position.ticker) === -100 }">-100%</button>
                <button class="pct-btn negative" @click.stop="setHypotheticalAdjustment(position.ticker, -50)" :class="{ active: getHypotheticalAdjustment(position.ticker) === -50 }">-50%</button>
                <button class="pct-btn negative" @click.stop="setHypotheticalAdjustment(position.ticker, -20)" :class="{ active: getHypotheticalAdjustment(position.ticker) === -20 }">-20%</button>
                <button class="pct-btn negative" @click.stop="setHypotheticalAdjustment(position.ticker, -10)" :class="{ active: getHypotheticalAdjustment(position.ticker) === -10 }">-10%</button>
                <button class="pct-btn reset" @click.stop="setHypotheticalAdjustment(position.ticker, 0)" :class="{ active: getHypotheticalAdjustment(position.ticker) === 0 }">{{ t('alphatrade.scenario.reset') }}</button>
                <button class="pct-btn positive" @click.stop="setHypotheticalAdjustment(position.ticker, 10)" :class="{ active: getHypotheticalAdjustment(position.ticker) === 10 }">+10%</button>
                <button class="pct-btn positive" @click.stop="setHypotheticalAdjustment(position.ticker, 20)" :class="{ active: getHypotheticalAdjustment(position.ticker) === 20 }">+20%</button>
                <button class="pct-btn positive" @click.stop="setHypotheticalAdjustment(position.ticker, 50)" :class="{ active: getHypotheticalAdjustment(position.ticker) === 50 }">+50%</button>
                <button class="pct-btn positive" @click.stop="setHypotheticalAdjustment(position.ticker, 100)" :class="{ active: getHypotheticalAdjustment(position.ticker) === 100 }">+100%</button>
              </div>

              <div class="price-range-slider">
                <div class="slider-track" @mousedown="handleSliderDrag($event, position.ticker)">
                  <div class="slider-fill" :style="{ left: '50%', width: `${(getHypotheticalAdjustment(position.ticker) / 200) * 100}%` }"></div>
                  <div class="slider-thumb" :style="{ left: `${((getHypotheticalAdjustment(position.ticker) + 100) / 200) * 100}%` }"></div>
                </div>
                <div class="slider-labels">
                  <span class="label-left">{{ t('alphatrade.scenario.crash') }}</span>
                  <span class="label-center">{{ t('alphatrade.scenario.current') }} ({{ formatCurrency(position.currentPrice) }})</span>
                  <span class="label-right">{{ t('alphatrade.scenario.moon') }}</span>
                </div>
              </div>
            </div>

            <table class="lots-table scenario-table">
              <thead>
                <tr>
                  <th>{{ t('alphatrade.scenario.table.lot') }}</th>
                  <th>{{ t('alphatrade.scenario.table.qty') }}</th>
                  <th>{{ t('alphatrade.scenario.table.cost_avg') }}</th>
                  <th>{{ t('alphatrade.scenario.table.hypo_equity') }}</th>
                  <th>{{ t('alphatrade.scenario.table.hypo_pl') }}</th>
                  <th>{{ t('alphatrade.scenario.table.hypo_roi') }}</th>
                  <th>{{ t('alphatrade.scenario.table.current_delta') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="lot in position.lots" :key="lot.id">
                  <td>{{ lot.purchaseDate }}</td>
                  <td>{{ lot.quantity }}</td>
                  <td>{{ formatCurrency(lot.costPerShare) }}</td>
                  <td>{{ formatCurrency(calculateHypotheticalLotMetrics(lot, getHypotheticalPrice(position.ticker)).hypotheticalValue) }}</td>
                  <td :class="{ positive: calculateHypotheticalLotMetrics(lot, getHypotheticalPrice(position.ticker)).hypotheticalPL >= 0, negative: calculateHypotheticalLotMetrics(lot, getHypotheticalPrice(position.ticker)).hypotheticalPL < 0 }">
                    {{ formatCurrency(calculateHypotheticalLotMetrics(lot, getHypotheticalPrice(position.ticker)).hypotheticalPL) }}
                  </td>
                  <td :class="{ positive: calculateHypotheticalLotMetrics(lot, getHypotheticalPrice(position.ticker)).hypotheticalROI >= 0, negative: calculateHypotheticalLotMetrics(lot, getHypotheticalPrice(position.ticker)).hypotheticalROI < 0 }">
                    {{ formatPercent(calculateHypotheticalLotMetrics(lot, getHypotheticalPrice(position.ticker)).hypotheticalROI) }}
                  </td>
                  <td :class="{ positive: (calculateHypotheticalLotMetrics(lot, getHypotheticalPrice(position.ticker)).hypotheticalPL - calculateLotMetrics(lot, position.currentPrice).lotPL) >= 0, negative: (calculateHypotheticalLotMetrics(lot, getHypotheticalPrice(position.ticker)).hypotheticalPL - calculateLotMetrics(lot, position.currentPrice).lotPL) < 0 }">
                    {{ formatCurrency(calculateHypotheticalLotMetrics(lot, getHypotheticalPrice(position.ticker)).hypotheticalPL - calculateLotMetrics(lot, position.currentPrice).lotPL) }}
                  </td>
                </tr>
                <tr class="total-row">
                  <td><strong>{{ t('alphatrade.scenario.table.hypo_total') }}</strong></td>
                  <td><strong>{{ position.lots.reduce((sum, lot) => sum + lot.quantity, 0) }}</strong></td>
                  <td><strong>{{ formatCurrency(position.lots.reduce((sum, lot) => sum + (lot.quantity * lot.costPerShare), 0) / position.lots.reduce((sum, lot) => sum + lot.quantity, 0)) }}</strong></td>
                  <td><strong>{{ formatCurrency(position.lots.reduce((sum, lot) => sum + calculateHypotheticalLotMetrics(lot, getHypotheticalPrice(position.ticker)).hypotheticalValue, 0)) }}</strong></td>
                  <td :class="{ positive: position.lots.reduce((sum, lot) => sum + calculateHypotheticalLotMetrics(lot, getHypotheticalPrice(position.ticker)).hypotheticalPL, 0) >= 0, negative: position.lots.reduce((sum, lot) => sum + calculateHypotheticalLotMetrics(lot, getHypotheticalPrice(position.ticker)).hypotheticalPL, 0) < 0 }">
                    <strong>{{ formatCurrency(position.lots.reduce((sum, lot) => sum + calculateHypotheticalLotMetrics(lot, getHypotheticalPrice(position.ticker)).hypotheticalPL, 0)) }}</strong>
                  </td>
                  <td :class="{ positive: (position.lots.reduce((sum, lot) => sum + calculateHypotheticalLotMetrics(lot, getHypotheticalPrice(position.ticker)).hypotheticalPL, 0) / position.lots.reduce((sum, lot) => sum + (lot.quantity * lot.costPerShare), 0)) >= 0, negative: (position.lots.reduce((sum, lot) => sum + calculateHypotheticalLotMetrics(lot, getHypotheticalPrice(position.ticker)).hypotheticalPL, 0) / position.lots.reduce((sum, lot) => sum + (lot.quantity * lot.costPerShare), 0)) < 0 }">
                    <strong>{{ formatPercent((position.lots.reduce((sum, lot) => sum + calculateHypotheticalLotMetrics(lot, getHypotheticalPrice(position.ticker)).hypotheticalPL, 0) / position.lots.reduce((sum, lot) => sum + (lot.quantity * lot.costPerShare), 0)) * 100) }}</strong>
                  </td>
                  <td :class="{ positive: (position.lots.reduce((sum, lot) => sum + calculateHypotheticalLotMetrics(lot, getHypotheticalPrice(position.ticker)).hypotheticalPL, 0) - position.lots.reduce((sum, lot) => sum + calculateLotMetrics(lot, position.currentPrice).lotPL, 0)) >= 0, negative: (position.lots.reduce((sum, lot) => sum + calculateHypotheticalLotMetrics(lot, getHypotheticalPrice(position.ticker)).hypotheticalPL, 0) - position.lots.reduce((sum, lot) => sum + calculateLotMetrics(lot, position.currentPrice).lotPL, 0)) < 0 }">
                    <strong>{{ formatCurrency(position.lots.reduce((sum, lot) => sum + calculateHypotheticalLotMetrics(lot, getHypotheticalPrice(position.ticker)).hypotheticalPL, 0) - position.lots.reduce((sum, lot) => sum + calculateLotMetrics(lot, position.currentPrice).lotPL, 0)) }}</strong>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <AddTradeLotModal 
      v-if="showAddLotModal" 
      @close="showAddLotModal = false"
      @submit="handleAddLot"
    />

    <EditTradeLotModal 
      v-if="showEditLotModal && editingLot" 
      :lot="editingLot"
      :ticker="editingTicker"
      @close="showEditLotModal = false; editingLot = null; editingTicker = ''"
      @submit="handleEditLot"
    />
  </div>
</template>

<style scoped>
.alphatrade-container {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
}

.header-left {
  flex: 1;
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

.add-lot-btn {
  background: #000;
  color: #fff;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-size: 0.9375rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: background 0.2s;
}

.add-lot-btn:hover {
  background: #333;
}

.btn-icon {
  font-size: 1.25rem;
  font-weight: 400;
}

/* Portfolio Summary Cards */
.summary-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.summary-card {
  background: #fff;
  border: 2px solid #000;
  border-radius: 8px;
  padding: 1.5rem;
  transition: transform 0.2s, box-shadow 0.2s;
}

.summary-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.summary-card .card-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.summary-card .card-header svg {
  color: #666;
  flex-shrink: 0;
}

.summary-card .card-label {
  font-size: 0.6875rem;
  font-weight: 600;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.summary-card .card-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: #000;
  line-height: 1.2;
}

.summary-card.pl-card .card-value.positive {
  color: #10b981;
}

.summary-card.pl-card .card-value.negative {
  color: #ef4444;
}

.summary-card.return-card {
  background: #10b981;
  border-color: #10b981;
}

.summary-card.return-card.negative {
  background: #ef4444;
  border-color: #ef4444;
}

.summary-card.return-card .card-header svg,
.summary-card.return-card .card-label,
.summary-card.return-card .card-value {
  color: #fff;
}

@media (max-width: 1024px) {
  .summary-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .summary-cards {
    grid-template-columns: 1fr;
  }
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  color: #666;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #000;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.positions-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.position-card {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  transition: box-shadow 0.2s;
}

.position-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.position-header {
  display: flex;
  align-items: center;
  padding: 1.5rem;
  cursor: pointer;
  gap: 2rem;
}

.position-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  min-width: 200px;
}

.ticker-icon-wrapper {
  position: relative;
}

.ticker-icon {
  width: 48px;
  height: 48px;
  background: #000;
  color: #fff;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  font-weight: 700;
}

.position-indicator {
  position: absolute;
  top: -4px;
  right: -4px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #fff;
}

.position-indicator.LONG {
  background: #3b82f6;
}

.position-indicator.SHORT {
  background: #ff6b35;
}

.position-indicator svg {
  color: #fff;
}

.position-indicator.SHORT svg {
  transform: rotate(180deg);
}

.ticker-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.ticker {
  font-size: 1.125rem;
  font-weight: 700;
  margin: 0;
  color: #000;
}

.position-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-size: 0.625rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.position-badge.LONG {
  background: #dbeafe;
  color: #3b82f6;
}

.position-badge.SHORT {
  background: #fed7aa;
  color: #ff6b35;
}

.sector {
  font-size: 0.75rem;
  color: #666;
  margin: 0.25rem 0 0 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.position-metrics {
  display: flex;
  gap: 3rem;
  flex: 1;
}

.metric {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.metric-label {
  font-size: 0.6875rem;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 500;
}

.metric-value {
  font-size: 1rem;
  font-weight: 600;
  color: #000;
}

.pl-value.positive {
  color: #10b981;
}

.pl-value.negative {
  color: #ef4444;
}

.expand-icon {
  margin-left: auto;
  color: #666;
  transition: transform 0.2s;
}

.lot-details {
  border-top: 1px solid #e0e0e0;
  padding: 1.5rem;
  background: #fafafa;
}

.lots-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.lots-table th {
  text-align: left;
  padding: 0.75rem 0.5rem;
  font-size: 0.6875rem;
  font-weight: 600;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 2px solid #e0e0e0;
}

.lots-table td {
  padding: 1rem 0.5rem;
  border-bottom: 1px solid #e0e0e0;
  color: #333;
}

.lot-row:hover {
  background: #f5f5f5;
}

.total-row {
  background: #fff;
  font-weight: 600;
}

.total-row td {
  padding: 1rem 0.5rem;
  border-bottom: none;
  border-top: 2px solid #000;
}

.positive {
  color: #10b981;
  font-weight: 600;
}

.negative {
  color: #ef4444;
  font-weight: 600;
}

.note-cell {
  font-style: italic;
  color: #666;
  max-width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.actions-cell {
  text-align: center;
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
  align-items: center;
}

.action-btn {
  background: none;
  border: 1px solid #d0d0d0;
  padding: 0.375rem;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.action-btn:hover {
  background: #f5f5f5;
}

.link-btn {
  color: #3b82f6;
  border-color: #3b82f6;
}

.link-btn:hover:not(:disabled) {
  background: #eff6ff;
  border-color: #2563eb;
  color: #2563eb;
}

.link-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.edit-btn {
  color: #000;
  border-color: #d0d0d0;
}

.edit-btn:hover {
  background: #f5f5f5;
  border-color: #000;
}

.delete-btn {
  color: #ef4444;
  border-color: #ef4444;
}

.delete-btn:hover {
  background: #fef2f2;
  border-color: #dc2626;
  color: #dc2626;
}

.delete-position-btn {
  background: none;
  border: none;
  padding: 0.5rem;
  cursor: pointer;
  color: #999;
  transition: all 0.2s;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: 1rem;
}

.delete-position-btn:hover {
  background: #fef2f2;
  color: #ef4444;
}

/* Tab Navigation */
.expanded-content {
  border-top: 1px solid #e0e0e0;
}

.tab-nav {
  display: flex;
  background: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
}

.tab-btn {
  flex: 1;
  padding: 1rem 1.5rem;
  background: none;
  border: none;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: #666;
  transition: all 0.2s;
  border-bottom: 3px solid transparent;
}

.tab-btn:hover {
  background: #ebebeb;
  color: #000;
}

.tab-btn.active {
  background: #fff;
  color: #000;
  border-bottom-color: #000;
}

.tab-btn svg {
  flex-shrink: 0;
}

/* Fundamental Analysis */
.fundamental-analysis {
  padding: 2rem;
  background: #fff;
}

.golden-rule {
  background: #000;
  color: #fff;
  padding: 1.5rem;
  border-radius: 8px;
  margin-bottom: 2rem;
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.golden-rule svg {
  flex-shrink: 0;
  margin-top: 0.25rem;
}

.rule-title {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  display: block;
  margin-bottom: 0.5rem;
}

.rule-text {
  font-size: 0.875rem;
  line-height: 1.5;
  font-style: italic;
  margin: 0;
  opacity: 0.9;
}

.analysis-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

/* Analysis Section Styles */
.analysis-section {
  margin-bottom: 3rem;
}

.section-header {
  font-size: 1.25rem;
  font-weight: 700;
  color: #000;
  margin-bottom: 1.5rem;
  padding-bottom: 0.75rem;
  border-bottom: 3px solid #000;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.analysis-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1.25rem;
  background: #fafafa;
  transition: box-shadow 0.2s;
}

.analysis-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
  gap: 1rem;
}

.card-title-section {
  display: flex;
  gap: 0.5rem;
  flex: 1;
}

.card-number {
  font-size: 0.875rem;
  font-weight: 700;
  color: #000;
  margin: 0;
  flex-shrink: 0;
}

.card-title {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #000;
  margin: 0 0 0.25rem 0;
}

.card-subtitle {
  font-size: 0.6875rem;
  color: #666;
  line-height: 1.4;
  margin: 0;
  font-style: italic;
}

.score-buttons {
  display: flex;
  gap: 0.25rem;
  flex-shrink: 0;
}

.score-btn {
  background: none;
  border: none;
  padding: 0.25rem;
  cursor: pointer;
  color: #d0d0d0;
  transition: color 0.2s;
}

.score-btn:hover {
  color: #999;
}

.score-btn.active {
  color: #000;
}

.analysis-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  font-size: 0.8125rem;
  font-family: inherit;
  resize: vertical;
  min-height: 60px;
  background: #fff;
  transition: border-color 0.2s;
}

.analysis-input:focus {
  outline: none;
  border-color: #000;
}

.analysis-input::placeholder {
  color: #999;
  font-style: italic;
}

@media (max-width: 1024px) {
  .analysis-grid {
    grid-template-columns: 1fr;
  }
}

/* Scenario Analysis Styles */
.scenario-analysis {
  padding: 2rem;
  background: #fafafa;
}

.scenario-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e0e0e0;
}

.scenario-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.scenario-title svg {
  color: #ff6b35;
}

.current-price-display {
  font-size: 2rem;
  font-weight: 700;
  color: #000;
}

.scenario-controls {
  margin-bottom: 2rem;
}

.percentage-buttons {
  display: grid;
  grid-template-columns: repeat(9, 1fr);
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.pct-btn {
  padding: 0.75rem 1rem;
  border: 1px solid #d0d0d0;
  background: #fff;
  color: #666;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border-radius: 4px;
  text-transform: uppercase;
}

.pct-btn:hover {
  background: #f5f5f5;
}

.pct-btn.active {
  background: #000;
  color: #fff;
  border-color: #000;
}

.pct-btn.negative.active {
  background: #ef4444;
  border-color: #ef4444;
}

.pct-btn.positive.active {
  background: #10b981;
  border-color: #10b981;
}

.pct-btn.reset.active {
  background: #3b82f6;
  border-color: #3b82f6;
}

.price-range-slider {
  margin-top: 1.5rem;
}

.slider-track {
  position: relative;
  height: 8px;
  background: linear-gradient(to right, #ef4444 0%, #fbbf24 33.33%, #10b981 100%);
  border-radius: 4px;
  margin-bottom: 0.75rem;
  cursor: pointer;
}

.slider-fill {
  position: absolute;
  top: 0;
  height: 100%;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
  transition: all 0.3s;
  pointer-events: none;
}

.slider-thumb {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 20px;
  height: 20px;
  background: #000;
  border: 3px solid #fff;
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  transition: all 0.3s;
  cursor: grab;
  pointer-events: none;
}

.slider-thumb:active {
  cursor: grabbing;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #666;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.label-left {
  color: #ef4444;
}

.label-center {
  color: #666;
}

.label-right {
  color: #10b981;
}

.scenario-table {
  margin-top: 2rem;
}

.scenario-table th {
  font-size: 0.75rem;
  background: #000;
  color: #fff;
}

.scenario-table td {
  font-size: 0.875rem;
}
</style>

/* Analysis Section Styles */
.analysis-section {
  margin-bottom: 3rem;
}

.section-header {
  font-size: 1.25rem;
  font-weight: 700;
  color: #000;
  margin-bottom: 1.5rem;
  padding-bottom: 0.75rem;
  border-bottom: 3px solid #000;
  text-transform: uppercase;
  letter-spacing: 1px;
}
