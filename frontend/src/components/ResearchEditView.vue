<template>
  <div class="research-edit-view" :class="{ 'market-mode': viewMode === 'MARKET' }">
    <!-- Top Bar with Logo and Location -->
    <div class="top-bar">
      <div class="top-bar-left">
        <div class="logo-container">
          <div class="hexagon-logo">
            <svg width="40" height="40" viewBox="0 0 40 40">
              <path d="M20 2 L35 10 L35 30 L20 38 L5 30 L5 10 Z" fill="none" stroke="#f59e0b" stroke-width="2"/>
              <text x="20" y="25" text-anchor="middle" fill="#f59e0b" font-size="20" font-weight="bold">C</text>
            </svg>
          </div>
          <div class="logo-text">
            <div class="logo-title">CHRONOS LEDGER</div>
            <div class="logo-subtitle">FINANCIAL INTELLIGENCE UNIT</div>
          </div>
        </div>
      </div>
      <div class="top-bar-right">
        <div class="location-info">
          <div class="location-label">LOCATION</div>
          <div class="location-value">NEW YORK (EST)</div>
        </div>
        <div class="location-indicator"></div>
      </div>
    </div>

    <!-- Main Header Section -->
    <header class="editor-header">
      <div class="header-content">
        <!-- Title -->
        <h1 class="header-title">DAILY BRIEFING</h1>
        
        <!-- Mode Toggle Switch -->
        <div class="mode-toggle-switch" @click="toggleViewMode">
          <div class="switch-track" :class="{ 'market-active': viewMode === 'MARKET' }">
            <div class="switch-section company-section" :class="{ 'active': viewMode === 'COMPANY' }">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
              </svg>
            </div>
            <div class="switch-section market-section" :class="{ 'active': viewMode === 'MARKET' }">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="2" x2="12" y2="6"></line>
                <line x1="12" y1="18" x2="12" y2="22"></line>
                <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line>
                <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line>
                <line x1="2" y1="12" x2="6" y2="12"></line>
                <line x1="18" y1="12" x2="22" y2="12"></line>
                <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line>
                <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line>
              </svg>
            </div>
          </div>
        </div>

        <!-- Ticker Search (only in Company mode) -->
        <div v-if="props.viewMode === 'COMPANY'" class="search-container">
          <input
            type="text"
            v-model="tickerInput"
            @keyup.enter="handleTickerSearch"
            placeholder="Q TSLA"
            class="search-input"
          />
        </div>

        <!-- Icon Group (Agent Selector) -->
        <div class="icon-group">
          <button
            v-for="(agent, index) in availableAgents"
            :key="agent.id"
            :class="{ active: props.activeAgent === agent.id }"
            @click="emit('update:active-agent', agent.id)"
            class="icon-btn"
            :title="agent.name"
          >
            <span class="agent-icon-emoji">{{ agent.icon }}</span>
          </button>
        </div>

        <!-- Action Buttons -->
        <div class="header-actions">
          <button @click="clearEditor" class="action-btn clear-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 4H8l-7 8 7 8h13a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2z"></path>
              <line x1="18" y1="9" x2="12" y2="15"></line>
              <line x1="12" y1="9" x2="18" y2="15"></line>
            </svg>
            <span>CLEAR</span>
          </button>
          <button @click="auditReport" class="action-btn audit-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
            </svg>
            <span>AUDIT</span>
          </button>
        </div>

        <!-- Active Agent Display -->
        <div class="active-agent-display">
          ACTIVE AGENT: <span class="agent-name-highlight">{{ currentAgentName.toUpperCase() }}</span>
        </div>
      </div>
    </header>

    <!-- Main Editor Area -->
    <div class="editor-container">
      <!-- Editor Panel -->
      <div class="editor-panel">
        <div
          v-if="editorContent.trim() === ''"
          class="editor-placeholder"
        >
          <h2 class="placeholder-title">
            Begin analysis for {{ companyName || 'Company' }}...
          </h2>
          <div class="placeholder-instructions">
            <div class="instruction-item">
              <span class="instruction-number">1.</span>
              <span>Select an AI AGENT.</span>
            </div>
            <div class="instruction-item">
              <span class="instruction-number">2.</span>
              <span>Drag data modules to interpret.</span>
            </div>
          </div>
        </div>

        <div
          ref="editorRef"
          class="editor-content"
          contenteditable="true"
          @drop.prevent="handleDrop"
          @dragover.prevent="handleDragOver"
          @dragenter.prevent="handleDragEnter"
          @dragleave.prevent="handleDragLeave"
          :class="{ 'drag-active': isDragging, 'has-content': editorContent.trim() !== '' }"
          v-html="editorContent"
          @input="handleEditorInput"
        ></div>
      </div>

      <!-- Data Stream Sidebar -->
      <div class="data-sidebar">
        <div class="sidebar-header">
          <div class="sidebar-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h9l2 3h9a2 2 0 0 1 2 2z"></path>
            </svg>
            <span>DATA VAULT</span>
          </div>
          <div class="sidebar-stream">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
            </svg>
            <span>{{ viewMode === 'MARKET' ? 'GLOBAL FEED' : `${ticker} STREAM` }}</span>
            <button @click="refreshData" class="refresh-btn">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="23 4 23 10 17 10"></polyline>
                <polyline points="1 20 1 14 7 14"></polyline>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
              </svg>
            </button>
          </div>
        </div>

        <div class="data-bubbles">
          <div
            v-for="bubble in filteredBubbles"
            :key="bubble.id"
            :draggable="true"
            @dragstart="handleDragStart($event, bubble)"
            class="data-bubble"
            :class="`bubble-${bubble.type}`"
          >
            <div class="bubble-header">
              <div class="bubble-icon">{{ bubble.icon }}</div>
              <div class="bubble-meta">
                <span class="bubble-category-badge">{{ bubble.category }}</span>
                <span class="bubble-time">{{ formatTime(bubble.timestamp) }}</span>
              </div>
            </div>
            <div class="bubble-title">{{ bubble.title }}</div>
            <div class="bubble-data">
              <div
                v-for="(value, key) in (bubble.data?.data_metrics || bubble.data || {})"
                :key="key"
                class="bubble-data-item"
              >
                <span class="data-label">{{ key }}</span>
                <span class="data-value" :class="getValueClass(value)">{{ formatValue(value) }}</span>
              </div>
            </div>
          </div>

          <div v-if="filteredBubbles.length === 0" class="no-bubbles">
            <div class="lock-icon">🔒</div>
            <div class="folder-icon">📁</div>
            <p class="no-data-text">NO RELEVANT DATA FOR THIS AGENT</p>
          </div>
        </div>

        <!-- Sidebar Footer -->
        <div class="sidebar-footer">
          <span class="encryption-text">ENCRYPTION: AES-256</span>
          <span class="sync-status synced">SYNCED</span>
        </div>
      </div>
    </div>

    <!-- Bottom Status Bar -->
    <div class="status-bar">
      <div class="status-left">
        <span>CHARS: {{ characterCount }}</span>
        <span class="status-separator">|</span>
        <span>MODE: {{ viewMode }}</span>
      </div>
      <div class="status-right">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="7 10 12 15 17 10"></polyline>
          <line x1="12" y1="15" x2="12" y2="3"></line>
        </svg>
        <span>AUTOSAVE ON</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { getDailyCache, setDailyCache } from '../utils/dailyCache.js'

const props = defineProps({
  viewMode: {
    type: String,
    required: true,
    validator: (value) => ['COMPANY', 'MARKET'].includes(value)
  },
  activeAgent: {
    type: String,
    required: true
  },
  ticker: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['update:view-mode', 'update:active-agent', 'update:ticker'])

// Editor state
const editorRef = ref(null)
const editorContent = ref('')
const tickerInput = ref(props.ticker)
const isDragging = ref(false)
const draggedBubble = ref(null)
const companyName = ref('Alphabet Inc.')

// Character count
const characterCount = computed(() => {
  if (!editorRef.value) return 0
  const text = editorRef.value.innerText || ''
  return text.length
})

// Agent definitions
const companyAgents = [
  { 
    id: 'FUNDAMENTAL_AGENT', 
    name: 'Fundamental Agent', 
    icon: '📊', 
    focus: ['income', 'balance', 'cashflow'],
    subAgents: ['INCOME_ANALYST_AGENT', 'BALANCE_ANALYST_AGENT', 'CASHFLOW_ANALYST_AGENT']
  },
  { 
    id: 'TRADING_AGENT', 
    name: 'Trading Agent', 
    icon: '📈', 
    focus: ['technical', 'options', 'insider'],
    subAgents: ['TECHNICAL_ANALYST_AGENT', 'OPTION_ANALYST_AGENT', 'INSIDE_TRADING_ANALYST_AGENT']
  },
  { 
    id: 'CSUIT_AGENT', 
    name: 'C-Suite Agent', 
    icon: '👤', 
    focus: ['csuite', 'executive', 'leadership'],
    subAgents: ['csuite']
  },
  { 
    id: 'MANAGEMENT_AGENT', 
    name: 'Management Agent', 
    icon: '📝', 
    focus: ['10k', '10q', 'filing', 'management'],
    subAgents: ['management']
  },
  { 
    id: 'MARKET_AGENT', 
    name: 'Market Agent', 
    icon: '📈', 
    focus: ['market', 'sp500', 'equity'],
    subAgents: ['market']
  },
  { 
    id: 'BOND_AGENT', 
    name: 'Bond Agent', 
    icon: '💵', 
    focus: ['bond', 'credit', 'yield'],
    subAgents: ['BOND_ANALYST_AGENT', 'CREDIT_ANALYST_AGENT']
  },
  { 
    id: 'ECONOMICS_AGENT', 
    name: 'Economics Agent', 
    icon: '🌐', 
    focus: ['economics', 'cpi', 'macro'],
    subAgents: ['economics']
  }
]

const marketAgents = [
  { id: 'EQUITY_AGENT', name: 'Equity Agent', icon: '📊', focus: ['equity', 'sector', 'sp500'], subAgents: ['sp500_index'] },
  { id: 'BOND_AGENT', name: 'Bond Agent', icon: '💵', focus: ['yield', 'treasury', 'rates'], subAgents: ['treasury_yield'] },
  { id: 'ECONOMICS_AGENT', name: 'Economics Agent', icon: '🌐', focus: ['cpi', 'jobs', 'macro'], subAgents: ['cpi_inflation'] }
]

const availableAgents = computed(() => {
  return props.viewMode === 'COMPANY' ? companyAgents : marketAgents
})

const currentAgentName = computed(() => {
  const agent = availableAgents.value.find(a => a.id === props.activeAgent)
  return agent ? agent.name : props.activeAgent
})

// Data bubbles state
const dataBubbles = ref([])

// Filter bubbles based on active agent
const filteredBubbles = computed(() => {
  // For market mode, bubbles are already filtered by agent on the backend
  // For company mode, we filter by agent focus
  if (props.viewMode === 'MARKET') {
    return dataBubbles.value
  }
  
  if (!dataBubbles.value.length) return []
  
  const agent = availableAgents.value.find(a => a.id === props.activeAgent)
  if (!agent) return dataBubbles.value
  
  return dataBubbles.value.filter(bubble => {
    return agent.focus.some(focus => 
      bubble.type.toLowerCase().includes(focus) || 
      bubble.category.toLowerCase().includes(focus)
    )
  })
})

// Drag and Drop handlers
const handleDragStart = (event, bubble) => {
  draggedBubble.value = bubble
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/html', bubble.id)
}

const handleDragOver = (event) => {
  event.preventDefault()
  isDragging.value = true
}

const handleDragEnter = (event) => {
  event.preventDefault()
  isDragging.value = true
}

const handleDragLeave = (event) => {
  if (!event.currentTarget.contains(event.relatedTarget)) {
    isDragging.value = false
  }
}

const handleDrop = async (event) => {
  event.preventDefault()
  isDragging.value = false
  
  if (!draggedBubble.value) return

  const selection = window.getSelection()
  const range = selection.rangeCount > 0 ? selection.getRangeAt(0) : null
  
  try {
    // Call backend to interpret data
    const insight = await interpretData(draggedBubble.value, editorContent.value)
    
    // Insert insight into editor
    insertInsight(insight, range)
    
    draggedBubble.value = null
  } catch (error) {
    console.error('Error interpreting data:', error)
    alert('Failed to generate insight. Please try again.')
  }
}

const insertInsight = (insight, range) => {
  if (!editorRef.value) return
  
  const selection = window.getSelection()
  let insertRange = range
  
  if (!insertRange && selection.rangeCount > 0) {
    insertRange = selection.getRangeAt(0)
  }
  
  if (insertRange) {
    insertRange.deleteContents()
    
    const div = document.createElement('div')
    div.innerHTML = insight
    const fragment = document.createDocumentFragment()
    
    while (div.firstChild) {
      fragment.appendChild(div.firstChild)
    }
    
    insertRange.insertNode(fragment)
    insertRange.collapse(false)
    selection.removeAllRanges()
    selection.addRange(insertRange)
    
    editorContent.value = editorRef.value.innerHTML
  } else {
    // Append to end if no selection
    editorContent.value += insight
    editorRef.value.innerHTML = editorContent.value
  }
}

const handleEditorInput = () => {
  if (editorRef.value) {
    editorContent.value = editorRef.value.innerHTML
  }
}

// Data interpretation
const interpretData = async (bubble, context) => {
  try {
    const response = await fetch('http://localhost:8000/api/research/interpret', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
      },
      body: JSON.stringify({
        bubble: bubble,
        agent: props.activeAgent,
        view_mode: props.viewMode,
        ticker: props.ticker,
        context: context
      })
    })
    
    if (!response.ok) {
      throw new Error('Failed to interpret data')
    }
    
    const data = await response.json()
    return data.insight
  } catch (error) {
    console.error('Interpretation error:', error)
    // Fallback: return basic markdown table
    return generateFallbackInsight(bubble)
  }
}

const generateFallbackInsight = (bubble) => {
  let table = '## ' + bubble.title + '\n\n'
  table += '| Metric | Value |\n'
  table += '|--------|-------|\n'
  
  const metrics = bubble.data?.data_metrics || bubble.data || {}
  Object.entries(metrics).forEach(([key, value]) => {
    table += `| ${key} | ${formatValue(value)} |\n`
  })
  
  // Include insights if available
  if (bubble.data?.insights) {
    const insights = bubble.data.insights
    if (insights.analysis) {
      table += '\n**Analysis:**\n\n' + insights.analysis + '\n\n'
    }
    if (insights.bullet_points && insights.bullet_points.length > 0) {
      table += '**Key Points:**\n\n'
      insights.bullet_points.forEach(point => {
        table += '- ' + point + '\n'
      })
    }
  } else {
    table += '\n**Analysis:**\n\n'
    table += '- Data extracted from ' + (bubble.category || 'DATA') + '\n'
    table += '- Timestamp: ' + formatTime(bubble.timestamp) + '\n'
  }
  
  return table
}

// Market data cache (for async loading in company mode)
const marketDataCache = ref({})

// Async load market data when in company mode
const loadMarketDataAsync = async () => {
  if (props.viewMode !== 'COMPANY') return
  
  // Load market data for MARKET_AGENT asynchronously (non-blocking)
  const marketCacheKey = `research_market_MARKET_AGENT`
  
  // Check if already cached
  const cached = getDailyCache(marketCacheKey)
  if (cached) {
    marketDataCache.value['MARKET_AGENT'] = cached
    console.log('Market data already cached')
    return
  }
  
  // Fetch in background (don't await - fire and forget)
  fetch(`http://localhost:8000/api/research/market-data?agent=MARKET_AGENT`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
    }
  })
    .then(response => {
      if (response.ok) {
        return response.json()
      }
      throw new Error('Market data fetch failed')
    })
    .then(data => {
      const bubbles = data.bubbles || []
      
      // Convert timestamp strings to Date objects
      bubbles.forEach(bubble => {
        if (bubble.timestamp && typeof bubble.timestamp === 'string') {
          bubble.timestamp = new Date(bubble.timestamp)
        }
      })
      
      marketDataCache.value['MARKET_AGENT'] = bubbles
      
      // Cache the result
      if (bubbles.length > 0) {
        setDailyCache(marketCacheKey, bubbles)
        console.log('Market data cached asynchronously')
      }
    })
    .catch(error => {
      console.error('Error async loading market data:', error)
    })
}

// Data fetching with caching
const fetchDataBubbles = async () => {
  // Build cache key
  const cacheKey = props.viewMode === 'MARKET' 
    ? `research_market_${props.activeAgent}`
    : `research_company_${props.ticker}_${props.activeAgent}`
  
  // Check cache first
  const cached = getDailyCache(cacheKey)
  if (cached) {
    console.log('Using cached data for:', cacheKey)
    dataBubbles.value = cached
    return
  }
  
  if (props.viewMode === 'MARKET') {
    // Market mode - fetch market data based on active agent
    try {
      console.log('Fetching market data for agent:', props.activeAgent)
      const response = await fetch(`http://localhost:8000/api/research/market-data?agent=${props.activeAgent}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        console.log('Market data response:', data)
        const bubbles = data.bubbles || []
        
        // Convert timestamp strings to Date objects
        bubbles.forEach(bubble => {
          if (bubble.timestamp && typeof bubble.timestamp === 'string') {
            bubble.timestamp = new Date(bubble.timestamp)
          }
        })
        
        dataBubbles.value = bubbles
        
        // Cache the result
        if (bubbles.length > 0) {
          setDailyCache(cacheKey, bubbles)
        }
      } else {
        console.error('Market data fetch failed:', response.status, response.statusText)
        dataBubbles.value = []
      }
    } catch (error) {
      console.error('Error fetching market data:', error)
      dataBubbles.value = []
    }
  } else {
    // Company mode - fetch data based on active agent
    if (!props.ticker) {
      dataBubbles.value = []
      return
    }
    
    try {
      console.log('Fetching company data for:', props.ticker, 'agent:', props.activeAgent)
      const response = await fetch(`http://localhost:8000/api/research/company-data/${props.ticker}?agent=${props.activeAgent}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        console.log('Company data response:', data)
        const bubbles = data.bubbles || []
        
        // Convert timestamp strings to Date objects
        bubbles.forEach(bubble => {
          if (bubble.timestamp && typeof bubble.timestamp === 'string') {
            bubble.timestamp = new Date(bubble.timestamp)
          }
        })
        
        dataBubbles.value = bubbles
        
        // Cache the result
        if (bubbles.length > 0) {
          setDailyCache(cacheKey, bubbles)
        }
        
        // Async load market data in background
        loadMarketDataAsync()
      } else {
        console.error('Company data fetch failed:', response.status, response.statusText)
        dataBubbles.value = []
      }
    } catch (error) {
      console.error('Error fetching company data:', error)
      dataBubbles.value = []
    }
  }
}

const generateMockBubbles = () => {
  if (props.viewMode === 'COMPANY') {
    return [
      {
        id: 'income-1',
        type: 'income',
        category: 'YAHOO FINANCE',
        icon: '📊',
        title: 'YAHOO FINANCE: INCOME STATEMENT',
        subtitle: props.ticker,
        timestamp: new Date(),
        data: {
          'TOTAL REVENUE': '307.39B',
          'COST OF REVENUE': '133.40B',
          'GROSS PROFIT': '173.99B',
          'OPERATING EXPE...': '84.50B'
        }
      },
      {
        id: 'balance-1',
        type: 'balance',
        category: 'YAHOO FINANCE',
        icon: '⚖️',
        title: 'YAHOO FINANCE: BALANCE SHEET',
        subtitle: props.ticker,
        timestamp: new Date(),
        data: {
          'TOTAL ASSETS': '426.60B',
          'TOTAL LIABILITIES': '100.20B',
          'TOTAL EQUITY': '326.40B',
          'CASH & EQUIVAL...': '108.60B'
        }
      },
      {
        id: 'cashflow-1',
        type: 'cashflow',
        category: 'YAHOO FINANCE',
        icon: '💰',
        title: 'YAHOO FINANCE: CASH FLOW',
        subtitle: props.ticker,
        timestamp: new Date(),
        data: {
          'OPERATING CAS...': '103.80B',
          'CAPITAL EXPENDI...': '-36.00B',
          'FREE CASH FLOW': '67.80B',
          'ISSUANCE OF DE...': '0.00B'
        }
      }
    ]
  } else {
    return [
      {
        id: 'sp500-1',
        type: 'equity',
        category: 'MARKET',
        icon: '📈',
        title: 'S&P 500 INDEX',
        subtitle: 'GLOBAL MARKET',
        timestamp: new Date(),
        data: {
          'PRICE': '5200.50',
          'PE RATIO': '23.5x',
          'TECHNOLOGY SE...': '+1.2%',
          'FINANCIALS SEC...': '+0.8%'
        }
      },
      {
        id: 'vix-1',
        type: 'volatility',
        category: 'MARKET',
        icon: '📈',
        title: 'VIX VOLATILITY INDEX',
        subtitle: 'GLOBAL MARKET',
        timestamp: new Date(),
        data: {
          'VIX LEVEL': '14.50',
          'CHANGE (PTS)': '-0.75'
        }
      },
      {
        id: 'treasury-1',
        type: 'yield',
        category: 'MARKET',
        icon: '💵',
        title: 'US 10-YEAR TREASURY YIELD',
        subtitle: 'GLOBAL MARKET',
        timestamp: new Date(),
        data: {
          'YIELD %': '4.25%',
          'CHANGE (BPS)': '+2'
        }
      }
    ]
  }
}

// Utility functions
const formatTime = (date) => {
  const d = new Date(date)
  const hours = d.getHours()
  const minutes = d.getMinutes()
  const seconds = d.getSeconds()
  const ampm = hours >= 12 ? 'PM' : 'AM'
  const displayHours = hours % 12 || 12
  return `${displayHours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')} ${ampm}`
}

const formatValue = (value) => {
  if (typeof value === 'string') {
    if (value.startsWith('+') || value.startsWith('-')) {
      return value
    }
  }
  return value
}

const getValueClass = (value) => {
  if (typeof value === 'string') {
    if (value.startsWith('+')) return 'positive'
    if (value.startsWith('-')) return 'negative'
  }
  return ''
}

const toggleViewMode = () => {
  const newMode = props.viewMode === 'COMPANY' ? 'MARKET' : 'COMPANY'
  emit('update:view-mode', newMode)
}

const handleTickerSearch = () => {
  if (tickerInput.value.trim()) {
    emit('update:ticker', tickerInput.value.trim().toUpperCase())
    fetchDataBubbles()
  }
}

const clearEditor = () => {
  editorContent.value = ''
  if (editorRef.value) {
    editorRef.value.innerHTML = ''
  }
}

const auditReport = () => {
  // TODO: Implement audit functionality
  console.log('Audit report:', editorContent.value)
}

const refreshData = () => {
  fetchDataBubbles()
}

// Watchers
watch(() => props.viewMode, () => {
  // Reset agent to first available when mode changes
  if (availableAgents.value.length > 0) {
    emit('update:active-agent', availableAgents.value[0].id)
  }
  // fetchDataBubbles will be called by the activeAgent watcher
})

watch(() => props.activeAgent, () => {
  // Fetch data when agent changes
  fetchDataBubbles()
}, { immediate: false })

watch(() => props.ticker, () => {
  tickerInput.value = props.ticker
  if (props.viewMode === 'COMPANY') {
    fetchDataBubbles()
  }
})

onMounted(() => {
  fetchDataBubbles()
  // Load market data asynchronously if in company mode
  if (props.viewMode === 'COMPANY') {
    loadMarketDataAsync()
  }
})
</script>

<style scoped>
.research-edit-view {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #000000;
  color: #e5e5e5;
  font-family: 'Space Mono', monospace;
  position: relative;
}

/* Top Bar */
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #0a0a0a;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.top-bar-left {
  display: flex;
  align-items: center;
}

.logo-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.hexagon-logo {
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-text {
  display: flex;
  flex-direction: column;
}

.logo-title {
  font-family: 'Cinzel', serif;
  font-size: 1.2em;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 1px;
  line-height: 1.2;
}

.logo-subtitle {
  font-family: 'Space Mono', monospace;
  font-size: 0.7em;
  color: #737373;
  text-transform: uppercase;
  letter-spacing: 2px;
  margin-top: 2px;
}

.top-bar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.location-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  font-family: 'Space Mono', monospace;
  font-size: 0.75em;
}

.location-label {
  color: #737373;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 2px;
}

.location-value {
  color: #e5e5e5;
  font-weight: 600;
}

.location-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #737373;
  border: 2px solid rgba(255, 255, 255, 0.1);
}

/* Header */
.editor-header {
  padding: 20px 24px;
  background: #0a0a0a;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.header-title {
  font-family: 'Cinzel', serif;
  font-size: 2em;
  font-weight: 700;
  color: #ffffff;
  margin: 0;
  letter-spacing: 1px;
  white-space: nowrap;
}

/* Mode Toggle Switch */
.mode-toggle-switch {
  cursor: pointer;
  user-select: none;
}

.switch-track {
  display: flex;
  width: 90px;
  height: 40px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 20px;
  overflow: hidden;
  position: relative;
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.switch-section {
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  position: relative;
}

.company-section {
  flex: 1.2;
  background: transparent;
  border-radius: 20px 0 0 20px;
}

.company-section.active {
  background: #f59e0b;
  border-radius: 20px 0 0 20px;
  flex: 1.2;
}

.company-section.active svg {
  color: #000000;
  stroke: #000000;
  stroke-width: 2.5;
}

.company-section:not(.active) {
  flex: 0.8;
  background: rgba(0, 0, 0, 0.3);
}

.company-section:not(.active) svg {
  color: #737373;
  stroke: #737373;
  opacity: 0.5;
}

.market-section {
  flex: 0.8;
  background: transparent;
  border-radius: 0 20px 20px 0;
}

.market-section.active {
  background: #22d3ee;
  border-radius: 0 20px 20px 0;
  flex: 1.2;
}

.market-section.active svg {
  color: #000000;
  stroke: #000000;
}

.market-section:not(.active) {
  flex: 0.8;
  background: rgba(0, 0, 0, 0.3);
}

.market-section:not(.active) svg {
  color: #737373;
  stroke: #737373;
  opacity: 0.5;
}

.search-container {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  padding: 0 16px;
}

.search-input {
  background: transparent;
  border: none;
  padding: 10px 0;
  color: #e5e5e5;
  font-family: 'Space Mono', monospace;
  font-size: 0.9em;
  width: 140px;
  outline: none;
}

.search-input::placeholder {
  color: #737373;
}

.icon-group {
  display: flex;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  padding: 4px;
  gap: 4px;
}

.icon-btn {
  width: 32px;
  height: 32px;
  background: transparent;
  border: none;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #737373;
  transition: all 0.2s;
}

.icon-btn:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #e5e5e5;
}

.icon-btn.active {
  background: #f59e0b;
  color: #000000;
}

.research-edit-view.market-mode .icon-btn.active {
  background: #22d3ee;
  color: #000000;
}

.agent-icon-emoji {
  font-size: 1.2em;
  line-height: 1;
}

.header-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  font-family: 'Space Mono', monospace;
  font-size: 0.85em;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  background: transparent;
}

.clear-btn {
  color: #737373;
}

.clear-btn:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.2);
  color: #e5e5e5;
}

.audit-btn {
  background: #f59e0b;
  border-color: #f59e0b;
  color: #000000;
  font-weight: 600;
}

.research-edit-view.market-mode .audit-btn {
  background: #22d3ee;
  border-color: #22d3ee;
}

.audit-btn:hover {
  background: #fbbf24;
  transform: scale(1.02);
}

.research-edit-view.market-mode .audit-btn:hover {
  background: #38bdf8;
}

.active-agent-display {
  font-family: 'Space Mono', monospace;
  font-size: 0.85em;
  color: #737373;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.agent-name-highlight {
  color: #f59e0b;
  font-weight: 700;
}

.research-edit-view.market-mode .agent-name-highlight {
  color: #22d3ee;
}

/* Editor Container */
.editor-container {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* Editor Panel */
.editor-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 40px;
  overflow-y: auto;
  position: relative;
}

.editor-content {
  flex: 1;
  min-height: 400px;
  padding: 20px;
  background: transparent;
  border: none;
  color: #e5e5e5;
  font-family: 'Lora', serif;
  font-size: 1em;
  line-height: 1.8;
  outline: none;
  transition: all 0.3s ease;
}

.editor-content.has-content {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

.editor-content.drag-active {
  border: 2px dashed rgba(245, 158, 11, 0.5);
  background: rgba(245, 158, 11, 0.05);
}

.research-edit-view.market-mode .editor-content.drag-active {
  border-color: rgba(34, 211, 238, 0.5);
  background: rgba(34, 211, 238, 0.05);
}

.editor-placeholder {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: left;
  pointer-events: none;
  opacity: 0.7;
}

.placeholder-title {
  font-family: 'Cinzel', serif;
  font-size: 1.8em;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 30px;
  letter-spacing: 0.5px;
}

.placeholder-instructions {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.instruction-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-family: 'Lora', serif;
  font-size: 1.1em;
  color: #a3a3a3;
}

.instruction-number {
  color: #f59e0b;
  font-weight: 700;
  font-family: 'Space Mono', monospace;
}

.research-edit-view.market-mode .instruction-number {
  color: #22d3ee;
}

/* Data Sidebar */
.data-sidebar {
  width: 380px;
  background: rgba(10, 10, 10, 0.8);
  border-left: 1px solid rgba(255, 255, 255, 0.1);
  padding: 20px;
  overflow-y: auto;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: 'Cinzel', serif;
  font-size: 1em;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 10px;
  letter-spacing: 1px;
}

.sidebar-title svg {
  color: #e5e5e5;
}

.sidebar-stream {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: 'Space Mono', monospace;
  font-size: 0.8em;
  color: #737373;
}

.sidebar-stream svg {
  color: #737373;
}

.refresh-btn {
  background: transparent;
  border: none;
  color: #737373;
  cursor: pointer;
  padding: 4px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.refresh-btn:hover {
  color: #f59e0b;
  transform: rotate(180deg);
}

.research-edit-view.market-mode .refresh-btn:hover {
  color: #22d3ee;
}

/* Data Bubbles */
.data-bubbles {
  display: flex;
  flex-direction: column;
  gap: 15px;
  flex: 1;
}

.data-bubble {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 18px;
  cursor: grab;
  transition: all 0.3s ease;
}

.data-bubble:hover {
  border-color: rgba(245, 158, 11, 0.4);
  background: rgba(255, 255, 255, 0.05);
  transform: translateY(-2px);
}

.research-edit-view.market-mode .data-bubble:hover {
  border-color: rgba(34, 211, 238, 0.4);
}

.data-bubble:active {
  cursor: grabbing;
  transform: scale(0.98);
}

.bubble-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.bubble-icon {
  font-size: 1.5em;
}

.bubble-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.bubble-category-badge {
  font-family: 'Space Mono', monospace;
  font-size: 0.7em;
  color: #a3a3a3;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.05);
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.bubble-time {
  font-family: 'Space Mono', monospace;
  font-size: 0.7em;
  color: #525252;
}

.bubble-title {
  font-family: 'Cinzel', serif;
  font-size: 0.9em;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 5px;
  letter-spacing: 0.5px;
}

.bubble-subtitle {
  font-family: 'Space Mono', monospace;
  font-size: 0.8em;
  color: #a3a3a3;
  margin-bottom: 15px;
}

.bubble-data {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.bubble-data-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  background: rgba(255, 255, 255, 0.03);
  padding: 10px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.data-label {
  font-family: 'Space Mono', monospace;
  font-size: 0.7em;
  color: #737373;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.data-value {
  font-family: 'Space Mono', monospace;
  font-size: 0.9em;
  font-weight: 700;
  color: #ffffff;
}

.data-value.positive {
  color: #10b981;
}

.data-value.negative {
  color: #ef4444;
}

.no-bubbles {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  flex: 1;
}

.lock-icon {
  font-size: 4em;
  margin-bottom: 10px;
  opacity: 0.6;
}

.folder-icon {
  font-size: 3em;
  margin-bottom: 20px;
  opacity: 0.5;
}

.no-data-text {
  font-family: 'Space Mono', monospace;
  font-size: 0.85em;
  color: #737373;
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* Sidebar Footer */
.sidebar-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 15px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  margin-top: auto;
}

.encryption-text {
  font-family: 'Space Mono', monospace;
  font-size: 0.75em;
  color: #737373;
}

.sync-status {
  padding: 2px 8px;
  border-radius: 4px;
  font-family: 'Space Mono', monospace;
  font-size: 0.75em;
  font-weight: 600;
}

.sync-status.synced {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

/* Status Bar */
.status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: rgba(10, 10, 10, 0.9);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  font-family: 'Space Mono', monospace;
  font-size: 0.8em;
  color: #737373;
}

.status-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-separator {
  color: #525252;
}

.status-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-right svg {
  color: #737373;
}

/* Scrollbar Styling */
.editor-panel::-webkit-scrollbar,
.data-sidebar::-webkit-scrollbar {
  width: 6px;
}

.editor-panel::-webkit-scrollbar-track,
.data-sidebar::-webkit-scrollbar-track {
  background: transparent;
}

.editor-panel::-webkit-scrollbar-thumb,
.data-sidebar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

.editor-panel::-webkit-scrollbar-thumb:hover,
.data-sidebar::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}
</style>
