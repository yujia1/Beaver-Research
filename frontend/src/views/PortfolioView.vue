<script setup>
import API_BASE_URL from '@/config/api.js'

import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/stores/userStore'
import AddTradeLotModal from '@/components/AddTradeLotModal.vue'
import EditTradeLotModal from '@/components/EditTradeLotModal.vue'

const userStore = useUserStore()
// Portfolio is a single entity shared by every role. Only admin/creator can edit it.
const isReadOnly = computed(() => !['admin', 'creator'].includes(userStore.user?.role))

const showAddLotModal = ref(false)
const showEditLotModal = ref(false)
const editingLot = ref(null)
const editingTicker = ref('')
const positions = ref([])
const expandedPositions = ref(new Set())
const loading = ref(false)

// Drag and drop state
const draggedIndex = ref(null)
const dragOverIndex = ref(null)

const { t } = useI18n()



// Helper function to calculate position side based on lots
// Returns 'LONG' if net quantity is positive, 'SHORT' if negative
const getPositionSide = (position) => {
  if (!position.lots || position.lots.length === 0) {
    return 'LONG' // Default to LONG if no lots
  }
  
  // Calculate net quantity: LONG lots add, SHORT lots subtract
  const netQuantity = position.lots.reduce((total, lot) => {
    if (lot.side === 'LONG') {
      return total + lot.quantity
    } else if (lot.side === 'SHORT') {
      return total - lot.quantity
    }
    return total
  }, 0)
  
  return netQuantity >= 0 ? 'LONG' : 'SHORT'
}

const fetchPositions = async () => {
  loading.value = true
  try {
    const token = localStorage.getItem('access_token')
    const response = await fetch(`${API_BASE_URL}/api/portfolio/positions`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (response.ok) {
      positions.value = await response.json()
    } else {
      console.error('Failed to fetch positions')
    }
  } catch (error) {
    console.error('Error fetching positions:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchPositions()
})

// Removed savePositions as we now rely on backend persistence

// fetchStockPrices is no longer needed as getPositions returns current prices
// We can keep a simplified version if we want to manually refresh prices button later
const refreshPrices = async () => {
  if (positions.value.length === 0) return
  
  loading.value = true
  try {
    const token = localStorage.getItem('access_token')
    const tickers = positions.value.map(p => p.ticker)
    
    // 1. Fetch real-time prices
    const response = await fetch(`${API_BASE_URL}/api/portfolio/stock-prices`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(tickers)
    })
    
    if (response.ok) {
      const priceData = await response.json()
      
      // 2. Update local state AND backend
      const updatePromises = positions.value.map(async (position) => {
        const data = priceData[position.ticker]
        if (data && !data.error) {
          position.currentPrice = data.currentPrice
          position.companyName = data.companyName
          position.sector = data.sector
          
          // Sync with backend
          try {
             await fetch(`${API_BASE_URL}/api/portfolio/positions/${position.ticker}/price`, {
                method: 'PUT',
                headers: {
                  'Authorization': `Bearer ${token}`
                }
             })
          } catch (e) {
             console.error(`Failed to sync price for ${position.ticker}`, e)
          }
        }
      })
      
      await Promise.all(updatePromises)
    }
  } catch (error) {
    console.error('Error refreshing prices:', error)
  } finally {
    loading.value = false
  }
}

const fetchSingleStockPrice = async (ticker) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/portfolio/stock-price/${ticker}`)
    
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
  }
}

const isExpanded = (ticker) => {
  return expandedPositions.value.has(ticker)
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
  if (isReadOnly.value) return
  loading.value = true
  try {
    const token = localStorage.getItem('access_token')
    const ticker = lotData.ticker.toUpperCase()
    
    // Check if position exists in our local list
    let position = positions.value.find(p => p.ticker === ticker)
    
    if (!position) {
      // Try to fetch stock info (optional, just for sector)
      // Note: This endpoint might need to be implemented on backend or we assume UNKNOWN
      // For now we just create the position.
      
      const posResponse = await fetch(`${API_BASE_URL}/api/portfolio/positions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ 
          ticker: ticker,
          sector: 'UNKNOWN' // Backend could be improved to fetch this
        })
      })
      
      if (!posResponse.ok) {
        const error = await posResponse.json()
        // If it says it exists (race condition), ignore error
        if (posResponse.status !== 400 || !error.detail.includes('exists')) {
             throw new Error(error.detail || 'Failed to create position')
        }
      }
    }
    
    // Add new lot
    const lotResponse = await fetch(`${API_BASE_URL}/api/portfolio/positions/${ticker}/lots`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(lotData)
    })
    
    if (!lotResponse.ok) {
        const error = await lotResponse.json()
        throw new Error(error.detail || 'Failed to create lot')
    }
    
    await fetchPositions()
    showAddLotModal.value = false
  } catch (error) {
    console.error('Error adding lot:', error)
    alert('Failed to add lot: ' + error.message)
  } finally {
    loading.value = false
  }
}

const deletePosition = async (ticker) => {
  if (isReadOnly.value) return
  if (confirm(`Are you sure you want to delete the entire ${ticker} position?`)) {
    loading.value = true
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_BASE_URL}/api/portfolio/positions/${ticker}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        // Remove from local state immediately to feel responsive, or just refetch
        // Refetching is safer to keep sync
        await fetchPositions()
        expandedPositions.value.delete(ticker)
      } else {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to delete position')
      }
    } catch (error) {
      console.error('Error deleting position:', error)
      alert('Failed to delete position: ' + error.message)
    } finally {
      loading.value = false
    }
  }
}

const deleteLot = async (ticker, lotId) => {
  if (isReadOnly.value) return
  if (confirm('Are you sure you want to delete this lot?')) {
    loading.value = true
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_BASE_URL}/api/portfolio/lots/${lotId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        await fetchPositions()
      } else {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to delete lot')
      }
    } catch (error) {
      console.error('Error deleting lot:', error)
      alert('Failed to delete lot: ' + error.message)
    } finally {
      loading.value = false
    }
  }
}

const editLot = (ticker, lotId) => {
  if (isReadOnly.value) return
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

const handleEditLot = async (updatedData) => {
  const position = positions.value.find(p => p.ticker === editingTicker.value)
  if (position && editingLot.value) {
    loading.value = true
    try {
      console.log('Updating lot with data:', updatedData)
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_BASE_URL}/api/portfolio/lots/${editingLot.value.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(updatedData)
      })
      
      if (response.ok) {
        await fetchPositions()
        showEditLotModal.value = false
        editingLot.value = null
        editingTicker.value = ''
      } else {
        const error = await response.json()
        console.error('Server error response:', error)
        throw new Error(JSON.stringify(error.detail || error))
      }
    } catch (error) {
       console.error('Error updating lot:', error)
       alert('Failed to update lot: ' + error.message)
    } finally {
      loading.value = false
    }
  }
}

// Drag and drop handlers
const handleDragStart = (index) => {
  if (isReadOnly.value) return
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
    // Note: Reordering is currently local-only as backend doesn't support sort order persistence yet
  }
  
  draggedIndex.value = null
  dragOverIndex.value = null
}

const handleDragEnd = () => {
  draggedIndex.value = null
  dragOverIndex.value = null
}

// Helper function to open links
const openLink = (url) => {
  if (url) {
    window.open(url, '_blank')
  }
}
</script>

<template>
  <div class="alphatrade-container">
    <div class="header">
      <div class="header-left">
        <h1 class="title">{{ t('portfolio.title') }}</h1>
        <p class="subtitle">{{ t('portfolio.subtitle') }}</p>
      </div>
    </div>

    <div v-if="!isReadOnly" class="controls-row">
        <button class="add-lot-btn" @click="showAddLotModal = true">
            <span class="btn-icon">+</span>
            <span class="btn-text">{{ t('portfolio.new_execution') }}</span>
        </button>
    </div>

    <!-- Portfolio View -->
    <div>
    <!-- Portfolio Summary Cards -->
    <div v-if="positions.length > 0" class="summary-cards">
      <div class="summary-card">
        <div class="card-header">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12 6 12 12 16 14"></polyline>
          </svg>
          <span class="card-label">{{ t('portfolio.total_value') }}</span>
        </div>
        <div class="card-value">{{ formatCurrency(portfolioTotals.totalValue) }}</div>
      </div>

      <div class="summary-card">
        <div class="card-header">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="1" x2="12" y2="23"></line>
            <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
          </svg>
          <span class="card-label">{{ t('portfolio.total_cost') }}</span>
        </div>
        <div class="card-value">{{ formatCurrency(portfolioTotals.totalCost) }}</div>
      </div>

      <div class="summary-card pl-card">
        <div class="card-header">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <polyline points="19 12 12 19 5 12"></polyline>
          </svg>
          <span class="card-label">{{ t('portfolio.unrealized_pl') }}</span>
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
          <span class="card-label">{{ t('portfolio.total_return') }}</span>
        </div>
        <div class="card-value">{{ formatPercent(portfolioTotals.totalReturn) }}</div>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>{{ t('portfolio.loading') }}</p>
    </div>

    <div v-else-if="positions.length === 0" class="empty-state">
      <p>{{ t('portfolio.empty_state') }}</p>
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
        :draggable="!isReadOnly"
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
              <div class="position-indicator" :class="getPositionSide(position)">
                <svg v-if="getPositionSide(position) === 'LONG'" xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="18 15 12 9 6 15"></polyline>
                </svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
              </div>
            </div>
            <div class="ticker-details">
              <div class="ticker-row">
                <h3 class="ticker">{{ position.ticker }}</h3>
                <span class="position-badge" :class="getPositionSide(position)">
                  {{ getPositionSide(position) }}
                </span>
              </div>
              <p class="sector">{{ position.sector }}</p>
            </div>
          </div>
          
          <div class="position-metrics">
            <div class="metric">
              <span class="metric-label">{{ t('portfolio.market_price') }}</span>
              <span class="metric-value">{{ formatCurrency(position.currentPrice) }}</span>
            </div>
            <div class="metric">
              <span class="metric-label">{{ t('portfolio.valuation') }}</span>
              <span class="metric-value">{{ formatCurrency(calculatePositionMetrics(position).marketValue) }}</span>
            </div>
            <div class="metric">
              <span class="metric-label">{{ t('portfolio.unrealized_pl') }}</span>
              <span 
                class="metric-value pl-value" 
                :class="{ positive: calculatePositionMetrics(position).unrealizedPL >= 0, negative: calculatePositionMetrics(position).unrealizedPL < 0 }"
              >
                {{ formatCurrency(calculatePositionMetrics(position).unrealizedPL) }}
              </span>
            </div>
          </div>
          
          <button
            v-if="!isReadOnly"
            class="delete-position-btn"
            @click.stop="deletePosition(position.ticker)"
            :title="t('portfolio.delete_position')"
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
          <div class="lot-details">
            <table class="lots-table">
              <thead>
                <tr>
                  <th>{{ t('portfolio.lot_table.purchase_date') }}</th>
                  <th>{{ t('portfolio.lot_table.qty') }}</th>
                  <th>{{ t('portfolio.lot_table.price') }}</th>
                  <th>{{ t('portfolio.lot_table.cost') }}</th>
                  <th>{{ t('portfolio.lot_table.equity_now') }}</th>
                  <th>{{ t('portfolio.lot_table.cost_val') }}</th>
                  <th>{{ t('portfolio.lot_table.pl') }}</th>
                  <th>{{ t('portfolio.lot_table.pct') }}</th>
                  <th>{{ t('portfolio.lot_table.note') }}</th>
                  <th>{{ t('portfolio.lot_table.actions') }}</th>
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
                        @click.stop="openLink(lot.link)"
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
                        v-if="!isReadOnly"
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
                        v-if="!isReadOnly"
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
                  <td><strong>{{ t('portfolio.lot_table.total_stats') }}</strong></td>
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
  box-shadow: 0 4px 12px rgba(248, 113, 113, 0.4);
}

.view-tabs {
    display: flex;
    gap: 2rem;
    margin-bottom: 2rem;
    border-bottom: 1px solid #e5e7eb;
}

.view-tab {
    background: none;
    border: none;
    padding: 0.75rem 0;
    font-size: 0.875rem;
    font-weight: 600;
    color: #9ca3af;
    cursor: pointer;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    position: relative;
    transition: color 0.2s;
}

.view-tab:hover {
    color: #374151;
}

.view-tab.active {
    color: #111827;
}

.view-tab.active::after {
    content: '';
    position: absolute;
    bottom: -1px;
    left: 0;
    width: 100%;
    height: 2px;
    background-color: #2563eb;
}

.controls-row {
    display: flex;
    justify-content: flex-end; /* Align button to the right */
    align-items: center;
    margin-bottom: 2rem;
}


.watchlist-placeholder {
    text-align: center;
    padding: 4rem;
    color: #6b7280;
    background: #f9fafb;
    border-radius: 12px;
    border: 1px dashed #e5e7eb;
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

</style>
