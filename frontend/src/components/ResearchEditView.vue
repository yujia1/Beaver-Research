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

        <!-- Chatbox for Research Agent -->
        <div v-if="props.activeAgent === 'MANAGEMENT_AGENT'" class="research-chatbox">
          <div class="chatbox-messages">
            <div
              v-for="(message, index) in chatMessages"
              :key="index"
              class="chat-message"
              :class="{ 'user-message': message.role === 'user', 'assistant-message': message.role === 'assistant' }"
            >
              <div class="message-content">{{ message.content }}</div>
              <div class="message-time">{{ formatTime(message.timestamp) }}</div>
            </div>
          </div>
          <div class="chatbox-input">
            <input
              v-model="chatInput"
              @keyup.enter="sendChatMessage"
              type="text"
              placeholder="Ask about research, filings, or analysis..."
              class="chat-input"
            />
            <button @click="sendChatMessage" class="chat-send-btn">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            </button>
          </div>
        </div>

        <!-- Data Bubbles for other agents -->
        <div v-else class="data-bubbles">
          <div
            v-for="bubble in filteredBubbles"
            :key="bubble.id"
            :draggable="true"
            @dragstart="handleDragStart($event, bubble)"
            class="data-bubble"
            :class="`bubble-${bubble.type}`"
          >
            <div class="bubble-header" v-if="!isFinancialStatementBubble(bubble)">
              <div class="bubble-icon">{{ bubble.icon }}</div>
              <div class="bubble-meta">
                <span class="bubble-category-badge">{{ bubble.category }}</span>
                <span class="bubble-time">{{ formatTime(bubble.timestamp) }}</span>
              </div>
            </div>
            <div class="bubble-title">{{ bubble.title }}</div>
            
            <!-- Period Toggle Row for Financial Statements (Income, Balance, Cash Flow) -->
            <div v-if="isFinancialStatementBubble(bubble)" class="bubble-period-row">
              <div class="period-toggle">
                <button
                  :class="{ active: getBubblePeriod(bubble.id) === 'Annually' }"
                  @click="setBubblePeriod(bubble.id, 'Annually')"
                  class="period-btn"
                >
                  Annually
                </button>
                <button
                  :class="{ active: getBubblePeriod(bubble.id) === 'Quarterly' }"
                  @click="setBubblePeriod(bubble.id, 'Quarterly')"
                  class="period-btn"
                >
                  Quarterly
                </button>
              </div>
              <div class="bubble-meta-right">
                <span class="bubble-category-badge">{{ bubble.category }}</span>
                <span class="bubble-time">{{ formatTime(bubble.timestamp) }}</span>
              </div>
            </div>
            
            <div class="bubble-data">
              <template v-if="isFinancialStatementBubble(bubble) && hasPeriodData(bubble)">
                <!-- Financial statement with period data -->
                <div
                  v-for="(value, key) in getPeriodDataMetrics(bubble)"
                  :key="key"
                  class="bubble-data-item"
                >
                  <span class="data-label">{{ key }}</span>
                  <span class="data-value" :class="getValueClass(value)">{{ formatValue(value) }}</span>
                </div>
              </template>
              <template v-else>
                <!-- Regular bubble data -->
                <div
                  v-for="(value, key) in (bubble.data?.data_metrics || bubble.data || {})"
                  :key="key"
                  class="bubble-data-item"
                >
                  <span class="data-label">{{ key }}</span>
                  <span class="data-value" :class="getValueClass(value)">{{ formatValue(value) }}</span>
                </div>
              </template>
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

// Chatbox state for Research agent
const chatMessages = ref([
  {
    role: 'assistant',
    content: 'Hello! I can help you research company filings, analyze financial data, and answer questions about ' + (props.ticker || 'companies') + '. What would you like to know?',
    timestamp: new Date()
  }
])
const chatInput = ref('')

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
    name: 'Financials', 
    icon: '📊', 
    focus: ['income', 'balance', 'cashflow'],
    subAgents: ['INCOME_ANALYST_AGENT', 'BALANCE_ANALYST_AGENT', 'CASHFLOW_ANALYST_AGENT']
  },
  { 
    id: 'TECHNICAL_ANALYST_AGENT', 
    name: 'Technical', 
    icon: '📈', 
    focus: ['technical', 'rsi', 'macd', 'moving average'],
    subAgents: ['TECHNICAL_ANALYST_AGENT']
  },
  { 
    id: 'INSIDE_TRADING_ANALYST_AGENT', 
    name: 'Insider', 
    icon: '👤', 
    focus: ['insider', 'trading', 'executive'],
    subAgents: ['INSIDE_TRADING_ANALYST_AGENT']
  },
  { 
    id: 'OPTION_ANALYST_AGENT', 
    name: 'Option', 
    icon: '📈', 
    focus: ['option', 'options', 'chain', 'calls', 'puts'],
    subAgents: ['OPTION_ANALYST_AGENT']
  },
  { 
    id: 'POLYMARKET_AGENT', 
    name: 'PolyMarket', 
    icon: '📊', 
    focus: ['polymarket', 'prediction', 'market'],
    subAgents: ['polymarket']
  },
  { 
    id: 'BOND_AGENT', 
    name: 'Bond', 
    icon: '💵', 
    focus: ['bond', 'credit', 'yield', 'treasury'],
    subAgents: ['BOND_ANALYST_AGENT', 'CREDIT_ANALYST_AGENT']
  },
  { 
    id: 'ECONOMICS_AGENT', 
    name: 'Economics', 
    icon: '🌐', 
    focus: ['economics', 'cpi', 'macro', 'inflation'],
    subAgents: ['economics']
  },
  { 
    id: 'MANAGEMENT_AGENT', 
    name: 'Research', 
    icon: '📝', 
    focus: ['research', '10k', '10q', 'filing', 'management'],
    subAgents: ['management']
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

// Period selection state for financial statement bubbles (Annually/Quarterly)
const bubblePeriods = ref({}) // { bubbleId: 'Annually' | 'Quarterly' }

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
    // Decode the encoded_output from insights
    let insights = null
    
    if (isFinancialStatementBubble(draggedBubble.value) && hasPeriodData(draggedBubble.value)) {
      // For financial statement bubbles, get insights from the selected period
      const period = getBubblePeriod(draggedBubble.value.id)
      const periodData = draggedBubble.value.data[period]
      insights = periodData?.insights || null
    } else {
      // For other bubbles, get insights directly
      insights = draggedBubble.value.data?.insights || null
    }
    
    // Decode the encoded_output if available
    let insight = null
    if (insights && insights.encoded_output) {
      try {
        // Decode base64 string
        const decodedJson = atob(insights.encoded_output)
        const decodedData = JSON.parse(decodedJson)
        
        // Format as markdown
        insight = formatDecodedInsight(decodedData, draggedBubble.value)
      } catch (decodeError) {
        console.error('Error decoding encoded_output:', decodeError)
        // Fallback to using insights directly if decoding fails
        insight = formatInsightsAsMarkdown(insights, draggedBubble.value)
      }
    } else if (insights) {
      // If no encoded_output, use insights directly
      insight = formatInsightsAsMarkdown(insights, draggedBubble.value)
    } else {
      // Fallback to generating basic insight
      insight = generateFallbackInsight(draggedBubble.value)
    }
    
    // Insert insight into editor
    insertInsight(insight, range)
    
    draggedBubble.value = null
  } catch (error) {
    console.error('Error processing drop:', error)
    alert('Failed to process data. Please try again.')
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
    const response = await fetch(`http://localhost:8000/api/research/process?data-agent=${props.activeAgent}`, {
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
  
  // Handle financial statement bubbles with period data
  let metrics = {}
  let insights = null
  
  if (isFinancialStatementBubble(bubble) && hasPeriodData(bubble)) {
    const period = getBubblePeriod(bubble.id)
    const periodData = bubble.data[period]
    metrics = periodData?.data_metrics || {}
    insights = periodData?.insights || null
  } else {
    metrics = bubble.data?.data_metrics || bubble.data || {}
    insights = bubble.data?.insights || null
  }
  
  Object.entries(metrics).forEach(([key, value]) => {
    table += `| ${key} | ${formatValue(value)} |\n`
  })
  
  // Include insights if available
  if (insights) {
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
  // Mock data - no async loading needed
  if (props.viewMode !== 'COMPANY') return
  console.log('Mock mode: Skipping async market data load')
}

// Data fetching with caching
// Generate mock data based on agent type
const generateMockBubbles = () => {
  const now = new Date()
  
  if (props.viewMode === 'MARKET') {
    // Market mode mock data
    if (props.activeAgent === 'EQUITY_AGENT') {
      return [
        {
          id: 'sp500-mock-1',
          type: 'sp500',
          category: 'MARKET',
          title: 'S&P 500 INDEX',
          timestamp: now,
          data: {
            data_metrics: {
              'current price': '5200.50',
              'pe ratio': '23.5x',
              'technology sector': '+1.2%',
              'financials sector': '+0.8%'
            },
            insights: {
              analysis: 'The S&P 500 continues to show strong performance with technology and financial sectors leading gains.',
              bullet_points: [
                'Technology sector up 1.2%',
                'Financials sector up 0.8%',
                'Market sentiment remains positive',
                'PE ratio at 23.5x indicates fair valuation'
              ],
              encoded_output: btoa(JSON.stringify({
                analysis: 'The S&P 500 continues to show strong performance with technology and financial sectors leading gains.',
                bullet_points: [
                  'Technology sector up 1.2%',
                  'Financials sector up 0.8%',
                  'Market sentiment remains positive',
                  'PE ratio at 23.5x indicates fair valuation'
                ],
                period: 'current',
                agent: 'EQUITY_AGENT'
              }))
            }
          }
        }
      ]
    } else if (props.activeAgent === 'BOND_AGENT') {
      return [
        {
          id: 'treasury-mock-1',
          type: 'treasury_yield',
          category: 'MARKET',
          title: 'US 10-YEAR TREASURY YIELD',
          timestamp: now,
          data: {
            data_metrics: {
              'yield %': '4.25%',
              'change (bps)': '+2',
              '2s10s spread': '0.45%',
              '10s30s spread': '0.12%'
            },
            insights: {
              analysis: 'Treasury yields remain stable with slight upward movement indicating market confidence.',
              bullet_points: [
                '10-year yield at 4.25%',
                'Positive spread indicates healthy yield curve',
                'Market expectations for stable monetary policy'
              ],
              encoded_output: btoa(JSON.stringify({
                analysis: 'Treasury yields remain stable with slight upward movement indicating market confidence.',
                bullet_points: [
                  '10-year yield at 4.25%',
                  'Positive spread indicates healthy yield curve',
                  'Market expectations for stable monetary policy'
                ],
                period: 'current',
                agent: 'BOND_AGENT'
              }))
            }
          }
        }
      ]
    } else if (props.activeAgent === 'ECONOMICS_AGENT') {
      return [
        {
          id: 'cpi-mock-1',
          type: 'cpi',
          category: 'MARKET',
          title: 'CPI INFLATION',
          timestamp: now,
          data: {
            data_metrics: {
              'current cpi': '310.25',
              'yoy change %': '3.2%',
              'mom change %': '0.2%'
            },
            insights: {
              analysis: 'CPI shows moderate inflation with year-over-year growth at 3.2%, indicating stable economic conditions.',
              bullet_points: [
                'Year-over-year inflation at 3.2%',
                'Month-over-month change at 0.2%',
                'Inflation trending towards target range'
              ],
              encoded_output: btoa(JSON.stringify({
                analysis: 'CPI shows moderate inflation with year-over-year growth at 3.2%, indicating stable economic conditions.',
                bullet_points: [
                  'Year-over-year inflation at 3.2%',
                  'Month-over-month change at 0.2%',
                  'Inflation trending towards target range'
                ],
                period: 'current',
                agent: 'ECONOMICS_AGENT'
              }))
            }
          }
        }
      ]
    }
    return []
  } else {
    // Company mode mock data
    if (!props.ticker) {
      return []
    }
    
    if (props.activeAgent === 'FUNDAMENTAL_AGENT') {
      // Create mock data for Income Statement, Balance Sheet, and Cash Flow
      const createEncodedOutput = (period, agent, analysis, bullets) => {
        return btoa(JSON.stringify({
          analysis,
          bullet_points: bullets,
          period,
          agent,
          timestamp: now.toISOString(),
          ticker: props.ticker
        }))
      }
      
      return [
        {
          id: `income-${props.ticker}-${now.getTime()}`,
          type: 'INCOME_ANALYST_AGENT',
          category: 'FINANCIAL',
          title: 'INCOME STATEMENT',
          timestamp: now,
          data: {
            Annually: {
              data_metrics: {
                'total revenue': '100.38B',
                'cost of revenue': '79.38B',
                'gross profit': '21.46B',
                'operating expense': '9.02B',
                'net income': '15.00B',
                'ebitda': '14.80B'
              },
              insights: {
                analysis: 'Tesla demonstrates strong revenue growth with total revenue reaching $100.38B annually. The company maintains healthy gross margins at 21.4%, indicating efficient cost management. Operating expenses are well-controlled at $9.02B, contributing to robust EBITDA of $14.80B. Net income of $15.00B reflects strong profitability and operational efficiency.',
                bullet_points: [
                  'Total revenue reached $100.38B, showing strong growth trajectory',
                  'Gross profit margin at 21.4% indicates healthy pricing power',
                  'Operating expenses well-managed at $9.02B',
                  'EBITDA of $14.80B demonstrates strong operational cash generation',
                  'Net income of $15.00B reflects efficient capital allocation'
                ],
                encoded_output: createEncodedOutput(
                  'annual',
                  'INCOME_ANALYST_AGENT',
                  'Tesla demonstrates strong revenue growth with total revenue reaching $100.38B annually. The company maintains healthy gross margins at 21.4%, indicating efficient cost management. Operating expenses are well-controlled at $9.02B, contributing to robust EBITDA of $14.80B. Net income of $15.00B reflects strong profitability and operational efficiency.',
                  [
                    'Total revenue reached $100.38B, showing strong growth trajectory',
                    'Gross profit margin at 21.4% indicates healthy pricing power',
                    'Operating expenses well-managed at $9.02B',
                    'EBITDA of $14.80B demonstrates strong operational cash generation',
                    'Net income of $15.00B reflects efficient capital allocation'
                  ]
                )
              }
            },
            Quarterly: {
              data_metrics: {
                'total revenue': '25.17B',
                'cost of revenue': '19.85B',
                'gross profit': '5.32B',
                'operating expense': '2.26B',
                'net income': '3.75B',
                'ebitda': '3.70B'
              },
              insights: {
                analysis: 'Tesla\'s quarterly performance shows consistent revenue generation with $25.17B in the latest quarter. Gross profit of $5.32B represents a 21.1% margin, maintaining strong profitability. Operating expenses of $2.26B are well-contained, supporting quarterly EBITDA of $3.70B. Net income of $3.75B indicates strong quarterly earnings momentum.',
                bullet_points: [
                  'Quarterly revenue of $25.17B shows consistent growth',
                  'Gross profit margin maintained at 21.1%',
                  'Operating expenses controlled at $2.26B per quarter',
                  'Quarterly EBITDA of $3.70B demonstrates operational strength',
                  'Net income of $3.75B reflects strong quarterly profitability'
                ],
                encoded_output: createEncodedOutput(
                  'quarterly',
                  'INCOME_ANALYST_AGENT',
                  'Tesla\'s quarterly performance shows consistent revenue generation with $25.17B in the latest quarter. Gross profit of $5.32B represents a 21.1% margin, maintaining strong profitability. Operating expenses of $2.26B are well-contained, supporting quarterly EBITDA of $3.70B. Net income of $3.75B indicates strong quarterly earnings momentum.',
                  [
                    'Quarterly revenue of $25.17B shows consistent growth',
                    'Gross profit margin maintained at 21.1%',
                    'Operating expenses controlled at $2.26B per quarter',
                    'Quarterly EBITDA of $3.70B demonstrates operational strength',
                    'Net income of $3.75B reflects strong quarterly profitability'
                  ]
                )
              }
            }
          }
        },
        {
          id: `balance-${props.ticker}-${now.getTime()}`,
          type: 'BALANCE_ANALYST_AGENT',
          category: 'FINANCIAL',
          title: 'BALANCE SHEET',
          timestamp: now,
          data: {
            Annually: {
              data_metrics: {
                'total assets': '106.62B',
                'total liabilities': '28.69B',
                'total equity': '77.93B',
                'cash & equivalents': '29.09B',
                'total debt': '9.57B',
                'current ratio': '1.95'
              },
              insights: {
                analysis: 'Tesla maintains a strong balance sheet with total assets of $106.62B. The company has a healthy equity position of $77.93B, representing 73% of total assets. Cash and equivalents of $29.09B provide significant liquidity. Total debt of $9.57B is manageable relative to equity, and the current ratio of 1.95 indicates strong short-term liquidity.',
                bullet_points: [
                  'Total assets of $106.62B demonstrate strong financial position',
                  'Equity of $77.93B represents 73% of total assets',
                  'Cash and equivalents of $29.09B provide strong liquidity',
                  'Total debt of $9.57B is well-managed',
                  'Current ratio of 1.95 indicates strong short-term liquidity'
                ],
                encoded_output: createEncodedOutput(
                  'annual',
                  'BALANCE_ANALYST_AGENT',
                  'Tesla maintains a strong balance sheet with total assets of $106.62B. The company has a healthy equity position of $77.93B, representing 73% of total assets. Cash and equivalents of $29.09B provide significant liquidity. Total debt of $9.57B is manageable relative to equity, and the current ratio of 1.95 indicates strong short-term liquidity.',
                  [
                    'Total assets of $106.62B demonstrate strong financial position',
                    'Equity of $77.93B represents 73% of total assets',
                    'Cash and equivalents of $29.09B provide strong liquidity',
                    'Total debt of $9.57B is well-managed',
                    'Current ratio of 1.95 indicates strong short-term liquidity'
                  ]
                )
              }
            },
            Quarterly: {
              data_metrics: {
                'total assets': '106.62B',
                'total liabilities': '28.69B',
                'total equity': '77.93B',
                'cash & equivalents': '29.09B',
                'total debt': '9.57B',
                'current ratio': '1.95'
              },
              insights: {
                analysis: 'Tesla\'s quarterly balance sheet shows consistent strength with total assets of $106.62B. The company maintains a solid equity position of $77.93B. Cash and equivalents of $29.09B provide ample liquidity for operations and growth. The current ratio of 1.95 indicates strong short-term financial flexibility.',
                bullet_points: [
                  'Quarterly assets remain strong at $106.62B',
                  'Equity position stable at $77.93B',
                  'Cash position of $29.09B supports operations',
                  'Debt levels manageable at $9.57B',
                  'Current ratio of 1.95 shows healthy liquidity'
                ],
                encoded_output: createEncodedOutput(
                  'quarterly',
                  'BALANCE_ANALYST_AGENT',
                  'Tesla\'s quarterly balance sheet shows consistent strength with total assets of $106.62B. The company maintains a solid equity position of $77.93B. Cash and equivalents of $29.09B provide ample liquidity for operations and growth. The current ratio of 1.95 indicates strong short-term financial flexibility.',
                  [
                    'Quarterly assets remain strong at $106.62B',
                    'Equity position stable at $77.93B',
                    'Cash position of $29.09B supports operations',
                    'Debt levels manageable at $9.57B',
                    'Current ratio of 1.95 shows healthy liquidity'
                  ]
                )
              }
            }
          }
        },
        {
          id: `cashflow-${props.ticker}-${now.getTime()}`,
          type: 'CASHFLOW_ANALYST_AGENT',
          category: 'FINANCIAL',
          title: 'CASH FLOW',
          timestamp: now,
          data: {
            Annually: {
              data_metrics: {
                'free cash flow': '3.58B',
                'capital expenditure': '-11.34B',
                'issuance of debt': '5.74B',
                'repayment of debt': '-2.88B',
                'end cash position': '17.04B',
                'changes in cash': '-0.01B'
              },
              insights: {
                analysis: 'Tesla demonstrates strong cash generation capabilities with free cash flow of $3.58B annually. Capital expenditures of $11.34B reflect significant investment in growth and capacity expansion. The company issued $5.74B in debt while repaying $2.88B, showing active capital management. The ending cash position of $17.04B provides substantial liquidity for future investments and operations.',
                bullet_points: [
                  'Free cash flow of $3.58B demonstrates strong cash generation',
                  'Capital expenditures of $11.34B indicate growth investments',
                  'Debt issuance of $5.74B supports strategic initiatives',
                  'Debt repayment of $2.88B shows active capital management',
                  'Ending cash position of $17.04B provides strong liquidity'
                ],
                encoded_output: createEncodedOutput(
                  'annual',
                  'CASHFLOW_ANALYST_AGENT',
                  'Tesla demonstrates strong cash generation capabilities with free cash flow of $3.58B annually. Capital expenditures of $11.34B reflect significant investment in growth and capacity expansion. The company issued $5.74B in debt while repaying $2.88B, showing active capital management. The ending cash position of $17.04B provides substantial liquidity for future investments and operations.',
                  [
                    'Free cash flow of $3.58B demonstrates strong cash generation',
                    'Capital expenditures of $11.34B indicate growth investments',
                    'Debt issuance of $5.74B supports strategic initiatives',
                    'Debt repayment of $2.88B shows active capital management',
                    'Ending cash position of $17.04B provides strong liquidity'
                  ]
                )
              }
            },
            Quarterly: {
              data_metrics: {
                'free cash flow': '3.99B',
                'capital expenditure': '-2.25B',
                'issuance of debt': '1.18B',
                'repayment of debt': '-0.69B',
                'end cash position': '19.58B',
                'changes in cash': '-0.01B'
              },
              insights: {
                analysis: 'Tesla\'s quarterly cash flow shows robust performance with free cash flow of $3.99B in the latest quarter. Capital expenditures of $2.25B reflect ongoing investment in production capacity and technology. The company issued $1.18B in debt while repaying $0.69B, maintaining balanced capital structure. The ending cash position of $19.58B demonstrates strong quarterly liquidity.',
                bullet_points: [
                  'Quarterly free cash flow of $3.99B shows strong cash generation',
                  'Capital expenditures of $2.25B support growth initiatives',
                  'Debt issuance of $1.18B provides capital flexibility',
                  'Debt repayment of $0.69B maintains balanced leverage',
                  'Ending cash position of $19.58B indicates strong liquidity'
                ],
                encoded_output: createEncodedOutput(
                  'quarterly',
                  'CASHFLOW_ANALYST_AGENT',
                  'Tesla\'s quarterly cash flow shows robust performance with free cash flow of $3.99B in the latest quarter. Capital expenditures of $2.25B reflect ongoing investment in production capacity and technology. The company issued $1.18B in debt while repaying $0.69B, maintaining balanced capital structure. The ending cash position of $19.58B demonstrates strong quarterly liquidity.',
                  [
                    'Quarterly free cash flow of $3.99B shows strong cash generation',
                    'Capital expenditures of $2.25B support growth initiatives',
                    'Debt issuance of $1.18B provides capital flexibility',
                    'Debt repayment of $0.69B maintains balanced leverage',
                    'Ending cash position of $19.58B indicates strong liquidity'
                  ]
                )
              }
            }
          }
        }
      ]
    } else if (props.activeAgent === 'TECHNICAL_ANALYST_AGENT') {
      const createEncodedOutput = (agent, analysis, bullets) => {
        return btoa(JSON.stringify({ analysis, bullet_points: bullets, period: 'current', agent, ticker: props.ticker }))
      }
      
      return [
        {
          id: `macd-${props.ticker}-${now.getTime()}`,
          type: 'TECHNICAL_ANALYST_AGENT',
          category: 'TECHNICAL',
          title: 'MACD',
          timestamp: now,
          data: {
            data_metrics: {
              'macd line': '2.45',
              'signal line': '1.85',
              'histogram': '0.60',
              'trend': 'Bullish'
            },
            insights: {
              analysis: 'MACD indicator shows bullish momentum with MACD line at 2.45 above signal line at 1.85. The positive histogram of 0.60 indicates strengthening upward momentum.',
              bullet_points: ['MACD line above signal line indicates bullish trend', 'Positive histogram shows increasing momentum', 'Current reading suggests continued upward movement'],
              encoded_output: createEncodedOutput('TECHNICAL_ANALYST_AGENT', 'MACD indicator shows bullish momentum with MACD line at 2.45 above signal line at 1.85. The positive histogram of 0.60 indicates strengthening upward momentum.', ['MACD line above signal line indicates bullish trend', 'Positive histogram shows increasing momentum', 'Current reading suggests continued upward movement'])
            }
          }
        },
        {
          id: `trending-${props.ticker}-${now.getTime()}`,
          type: 'TECHNICAL_ANALYST_AGENT',
          category: 'TECHNICAL',
          title: 'TRENDING',
          timestamp: now,
          data: {
            data_metrics: {
              'trend direction': 'Uptrend',
              'trend strength': 'Strong',
              'support level': '240.00',
              'resistance level': '260.00'
            },
            insights: {
              analysis: 'Tesla is in a strong uptrend with clear support at $240.00 and resistance at $260.00. The trend strength is strong, indicating sustained buying pressure.',
              bullet_points: ['Strong uptrend confirmed', 'Support level at $240.00', 'Resistance level at $260.00', 'Sustained buying pressure'],
              encoded_output: createEncodedOutput('TECHNICAL_ANALYST_AGENT', 'Tesla is in a strong uptrend with clear support at $240.00 and resistance at $260.00. The trend strength is strong, indicating sustained buying pressure.', ['Strong uptrend confirmed', 'Support level at $240.00', 'Resistance level at $260.00', 'Sustained buying pressure'])
            }
          }
        },
        {
          id: `rsi-${props.ticker}-${now.getTime()}`,
          type: 'TECHNICAL_ANALYST_AGENT',
          category: 'TECHNICAL',
          title: 'RSI',
          timestamp: now,
          data: {
            data_metrics: {
              'rsi': '58.5',
              'rsi status': 'Neutral',
              'overbought threshold': '70',
              'oversold threshold': '30'
            },
            insights: {
              analysis: 'RSI reading of 58.5 indicates neutral momentum, neither overbought nor oversold. The indicator suggests the stock has room to move in either direction.',
              bullet_points: ['RSI at 58.5 indicates neutral momentum', 'Not in overbought or oversold territory', 'Room for movement in either direction'],
              encoded_output: createEncodedOutput('TECHNICAL_ANALYST_AGENT', 'RSI reading of 58.5 indicates neutral momentum, neither overbought nor oversold. The indicator suggests the stock has room to move in either direction.', ['RSI at 58.5 indicates neutral momentum', 'Not in overbought or oversold territory', 'Room for movement in either direction'])
            }
          }
        }
      ]
    } else if (props.activeAgent === 'INSIDE_TRADING_ANALYST_AGENT') {
      const createEncodedOutput = (agent, analysis, bullets) => {
        return btoa(JSON.stringify({ analysis, bullet_points: bullets, period: 'current', agent, ticker: props.ticker }))
      }
      
      return [
        {
          id: `institution-${props.ticker}-${now.getTime()}`,
          type: 'INSIDE_TRADING_ANALYST_AGENT',
          category: 'INSIDER',
          title: 'INSTITUTION HOLDING',
          timestamp: now,
          data: {
            data_metrics: {
              'total institutions': '2,145',
              'total shares held': '1.25B',
              'institutional ownership %': '42.5%',
              'net change (qoq)': '+2.3%'
            },
            insights: {
              analysis: 'Institutional ownership stands at 42.5% with 2,145 institutions holding 1.25B shares. Quarterly net change of +2.3% indicates increasing institutional interest.',
              bullet_points: ['42.5% institutional ownership', '2,145 institutions holding shares', 'Quarterly increase of 2.3%', 'Strong institutional support'],
              encoded_output: createEncodedOutput('INSIDE_TRADING_ANALYST_AGENT', 'Institutional ownership stands at 42.5% with 2,145 institutions holding 1.25B shares. Quarterly net change of +2.3% indicates increasing institutional interest.', ['42.5% institutional ownership', '2,145 institutions holding shares', 'Quarterly increase of 2.3%', 'Strong institutional support'])
            }
          }
        },
        {
          id: `insider-trading-${props.ticker}-${now.getTime()}`,
          type: 'INSIDE_TRADING_ANALYST_AGENT',
          category: 'INSIDER',
          title: 'INSIDER TRADING',
          timestamp: now,
          data: {
            data_metrics: {
              'insider transactions (6m)': '24',
              'total value': '$125.5M',
              'buy transactions': '8',
              'sell transactions': '16'
            },
            insights: {
              analysis: 'Over the past 6 months, there were 24 insider transactions totaling $125.5M. With 8 buys and 16 sells, insider activity shows a net selling trend, though this is common for executives exercising options.',
              bullet_points: ['24 insider transactions in 6 months', 'Total value of $125.5M', 'Net selling trend observed', 'Common for option exercises'],
              encoded_output: createEncodedOutput('INSIDE_TRADING_ANALYST_AGENT', 'Over the past 6 months, there were 24 insider transactions totaling $125.5M. With 8 buys and 16 sells, insider activity shows a net selling trend, though this is common for executives exercising options.', ['24 insider transactions in 6 months', 'Total value of $125.5M', 'Net selling trend observed', 'Common for option exercises'])
            }
          }
        }
      ]
    } else if (props.activeAgent === 'OPTION_ANALYST_AGENT') {
      const createEncodedOutput = (agent, analysis, bullets) => {
        return btoa(JSON.stringify({ analysis, bullet_points: bullets, period: 'current', agent, ticker: props.ticker }))
      }
      
      return [
        {
          id: `open-interest-${props.ticker}-${now.getTime()}`,
          type: 'OPTION_ANALYST_AGENT',
          category: 'OPTION',
          title: 'OPEN INTEREST',
          timestamp: now,
          data: {
            data_metrics: {
              'total open interest': '8.5M',
              'calls open interest': '4.8M',
              'puts open interest': '3.7M',
              'call/put ratio': '1.30'
            },
            insights: {
              analysis: 'Total open interest of 8.5M contracts shows strong options activity. Calls dominate with 4.8M vs 3.7M puts, resulting in a call/put ratio of 1.30, indicating bullish sentiment.',
              bullet_points: ['Total open interest of 8.5M contracts', 'Calls outnumber puts 4.8M to 3.7M', 'Call/put ratio of 1.30 indicates bullish sentiment', 'Strong options market activity'],
              encoded_output: createEncodedOutput('OPTION_ANALYST_AGENT', 'Total open interest of 8.5M contracts shows strong options activity. Calls dominate with 4.8M vs 3.7M puts, resulting in a call/put ratio of 1.30, indicating bullish sentiment.', ['Total open interest of 8.5M contracts', 'Calls outnumber puts 4.8M to 3.7M', 'Call/put ratio of 1.30 indicates bullish sentiment', 'Strong options market activity'])
            }
          }
        },
        {
          id: `put-volume-${props.ticker}-${now.getTime()}`,
          type: 'OPTION_ANALYST_AGENT',
          category: 'OPTION',
          title: 'PUT OPTION VOLUME',
          timestamp: now,
          data: {
            data_metrics: {
              'put volume (today)': '1.2M',
              'put volume (avg)': '850K',
              'volume ratio': '1.41',
              'most active strike': '240'
            },
            insights: {
              analysis: 'Put option volume of 1.2M today exceeds the 850K average, with a volume ratio of 1.41. The most active strike is $240, suggesting traders are hedging or speculating at this level.',
              bullet_points: ['Put volume of 1.2M exceeds average', 'Volume ratio of 1.41 indicates increased activity', 'Most active strike at $240', 'Potential hedging or speculation'],
              encoded_output: createEncodedOutput('OPTION_ANALYST_AGENT', 'Put option volume of 1.2M today exceeds the 850K average, with a volume ratio of 1.41. The most active strike is $240, suggesting traders are hedging or speculating at this level.', ['Put volume of 1.2M exceeds average', 'Volume ratio of 1.41 indicates increased activity', 'Most active strike at $240', 'Potential hedging or speculation'])
            }
          }
        },
        {
          id: `call-volume-${props.ticker}-${now.getTime()}`,
          type: 'OPTION_ANALYST_AGENT',
          category: 'OPTION',
          title: 'CALL OPTION VOLUME',
          timestamp: now,
          data: {
            data_metrics: {
              'call volume (today)': '1.8M',
              'call volume (avg)': '1.1M',
              'volume ratio': '1.64',
              'most active strike': '250'
            },
            insights: {
              analysis: 'Call option volume of 1.8M today significantly exceeds the 1.1M average, with a volume ratio of 1.64. The most active strike is $250, indicating strong bullish sentiment and expectations for upward price movement.',
              bullet_points: ['Call volume of 1.8M well above average', 'Volume ratio of 1.64 shows strong activity', 'Most active strike at $250', 'Strong bullish sentiment'],
              encoded_output: createEncodedOutput('OPTION_ANALYST_AGENT', 'Call option volume of 1.8M today significantly exceeds the 1.1M average, with a volume ratio of 1.64. The most active strike is $250, indicating strong bullish sentiment and expectations for upward price movement.', ['Call volume of 1.8M well above average', 'Volume ratio of 1.64 shows strong activity', 'Most active strike at $250', 'Strong bullish sentiment'])
            }
          }
        },
        {
          id: `put-call-ratio-${props.ticker}-${now.getTime()}`,
          type: 'OPTION_ANALYST_AGENT',
          category: 'OPTION',
          title: 'PUT/CALL RATIO',
          timestamp: now,
          data: {
            data_metrics: {
              'put/call ratio': '0.67',
              'calls volume': '1.8M',
              'puts volume': '1.2M',
              'sentiment': 'Bullish'
            },
            insights: {
              analysis: 'Put/call ratio of 0.67 indicates bullish sentiment, as calls significantly outnumber puts. With 1.8M calls vs 1.2M puts, the market shows strong optimism for price appreciation.',
              bullet_points: ['Put/call ratio of 0.67 indicates bullish sentiment', 'Calls outnumber puts 1.8M to 1.2M', 'Strong market optimism', 'Expectations for price appreciation'],
              encoded_output: createEncodedOutput('OPTION_ANALYST_AGENT', 'Put/call ratio of 0.67 indicates bullish sentiment, as calls significantly outnumber puts. With 1.8M calls vs 1.2M puts, the market shows strong optimism for price appreciation.', ['Put/call ratio of 0.67 indicates bullish sentiment', 'Calls outnumber puts 1.8M to 1.2M', 'Strong market optimism', 'Expectations for price appreciation'])
            }
          }
        }
      ]
    } else if (props.activeAgent === 'POLYMARKET_AGENT') {
      const createEncodedOutput = (agent, analysis, bullets) => {
        return btoa(JSON.stringify({ analysis, bullet_points: bullets, period: 'current', agent, ticker: props.ticker }))
      }
      
      return [
        {
          id: `polymarket-${props.ticker}-${now.getTime()}`,
          type: 'POLYMARKET_AGENT',
          category: 'POLYMARKET',
          title: 'What will Tesla (TSLA) hit before 2026?',
          timestamp: now,
          data: {
            data_metrics: {
              '$300+ odds': '45%',
              '$350+ odds': '28%',
              '$400+ odds': '15%',
              '$500+ odds': '8%'
            },
            insights: {
              analysis: 'PolyMarket prediction markets show 45% odds that Tesla will hit $300+ before 2026, with 28% for $350+, 15% for $400+, and 8% for $500+. These odds reflect market sentiment and probability assessments from prediction market participants.',
              bullet_points: ['45% odds for $300+ before 2026', '28% odds for $350+', '15% odds for $400+', '8% odds for $500+', 'Based on prediction market sentiment'],
              encoded_output: createEncodedOutput('POLYMARKET_AGENT', 'PolyMarket prediction markets show 45% odds that Tesla will hit $300+ before 2026, with 28% for $350+, 15% for $400+, and 8% for $500+. These odds reflect market sentiment and probability assessments from prediction market participants.', ['45% odds for $300+ before 2026', '28% odds for $350+', '15% odds for $400+', '8% odds for $500+', 'Based on prediction market sentiment'])
            }
          }
        }
      ]
    } else if (props.activeAgent === 'BOND_AGENT') {
      const createEncodedOutput = (agent, analysis, bullets) => {
        return btoa(JSON.stringify({ analysis, bullet_points: bullets, period: 'current', agent, ticker: props.ticker }))
      }
      
      return [
        {
          id: `bond-3m-${now.getTime()}`,
          type: 'BOND_ANALYST_AGENT',
          category: 'BOND',
          title: '3 MONTHS',
          timestamp: now,
          data: {
            data_metrics: {
              'yield': '5.25%',
              'change (bps)': '+5',
              'trend': 'Rising'
            },
            insights: {
              analysis: '3-month Treasury yield at 5.25% shows a +5 bps increase, indicating rising short-term rates. This reflects market expectations for monetary policy.',
              bullet_points: ['3-month yield at 5.25%', 'Rising trend with +5 bps change', 'Reflects short-term rate expectations'],
              encoded_output: createEncodedOutput('BOND_ANALYST_AGENT', '3-month Treasury yield at 5.25% shows a +5 bps increase, indicating rising short-term rates. This reflects market expectations for monetary policy.', ['3-month yield at 5.25%', 'Rising trend with +5 bps change', 'Reflects short-term rate expectations'])
            }
          }
        },
        {
          id: `bond-3y-${now.getTime()}`,
          type: 'BOND_ANALYST_AGENT',
          category: 'BOND',
          title: '3 YEARS',
          timestamp: now,
          data: {
            data_metrics: {
              'yield': '4.75%',
              'change (bps)': '+3',
              'trend': 'Stable'
            },
            insights: {
              analysis: '3-year Treasury yield at 4.75% with a +3 bps change indicates stable intermediate-term rates. The yield curve remains relatively flat in this segment.',
              bullet_points: ['3-year yield at 4.75%', 'Stable trend with +3 bps change', 'Intermediate-term rate stability'],
              encoded_output: createEncodedOutput('BOND_ANALYST_AGENT', '3-year Treasury yield at 4.75% with a +3 bps change indicates stable intermediate-term rates. The yield curve remains relatively flat in this segment.', ['3-year yield at 4.75%', 'Stable trend with +3 bps change', 'Intermediate-term rate stability'])
            }
          }
        },
        {
          id: `bond-5y-${now.getTime()}`,
          type: 'BOND_ANALYST_AGENT',
          category: 'BOND',
          title: '5 YEARS',
          timestamp: now,
          data: {
            data_metrics: {
              'yield': '4.50%',
              'change (bps)': '+2',
              'trend': 'Stable'
            },
            insights: {
              analysis: '5-year Treasury yield at 4.50% shows minimal change of +2 bps, indicating stable medium-term expectations. The yield remains in a tight range.',
              bullet_points: ['5-year yield at 4.50%', 'Minimal change of +2 bps', 'Stable medium-term expectations'],
              encoded_output: createEncodedOutput('BOND_ANALYST_AGENT', '5-year Treasury yield at 4.50% shows minimal change of +2 bps, indicating stable medium-term expectations. The yield remains in a tight range.', ['5-year yield at 4.50%', 'Minimal change of +2 bps', 'Stable medium-term expectations'])
            }
          }
        },
        {
          id: `bond-10y-${now.getTime()}`,
          type: 'BOND_ANALYST_AGENT',
          category: 'BOND',
          title: '10 YEARS',
          timestamp: now,
          data: {
            data_metrics: {
              'yield': '4.25%',
              'change (bps)': '+2',
              'trend': 'Stable'
            },
            insights: {
              analysis: '10-year Treasury yield at 4.25% with a +2 bps change reflects stable long-term rate expectations. This is a key benchmark for mortgage rates and corporate borrowing costs.',
              bullet_points: ['10-year yield at 4.25%', 'Key benchmark rate', 'Stable long-term expectations', 'Impacts mortgage and corporate rates'],
              encoded_output: createEncodedOutput('BOND_ANALYST_AGENT', '10-year Treasury yield at 4.25% with a +2 bps change reflects stable long-term rate expectations. This is a key benchmark for mortgage rates and corporate borrowing costs.', ['10-year yield at 4.25%', 'Key benchmark rate', 'Stable long-term expectations', 'Impacts mortgage and corporate rates'])
            }
          }
        },
        {
          id: `bond-30y-${now.getTime()}`,
          type: 'BOND_ANALYST_AGENT',
          category: 'BOND',
          title: '30 YEARS',
          timestamp: now,
          data: {
            data_metrics: {
              'yield': '4.40%',
              'change (bps)': '+1',
              'trend': 'Stable'
            },
            insights: {
              analysis: '30-year Treasury yield at 4.40% shows minimal change of +1 bps, indicating very stable ultra-long-term rate expectations. The yield curve shows slight inversion in this segment.',
              bullet_points: ['30-year yield at 4.40%', 'Minimal change of +1 bps', 'Ultra-long-term rate stability', 'Slight yield curve inversion'],
              encoded_output: createEncodedOutput('BOND_ANALYST_AGENT', '30-year Treasury yield at 4.40% shows minimal change of +1 bps, indicating very stable ultra-long-term rate expectations. The yield curve shows slight inversion in this segment.', ['30-year yield at 4.40%', 'Minimal change of +1 bps', 'Ultra-long-term rate stability', 'Slight yield curve inversion'])
            }
          }
        }
      ]
    } else if (props.activeAgent === 'ECONOMICS_AGENT') {
      const createEncodedOutput = (agent, analysis, bullets) => {
        return btoa(JSON.stringify({ analysis, bullet_points: bullets, period: 'current', agent, ticker: props.ticker }))
      }
      
      return [
        {
          id: `cpi-${now.getTime()}`,
          type: 'ECONOMICS_AGENT',
          category: 'ECONOMICS',
          title: 'CPI',
          timestamp: now,
          data: {
            data_metrics: {
              'current cpi': '310.25',
              'yoy change %': '3.2%',
              'mom change %': '0.2%',
              'core cpi': '4.1%'
            },
            insights: {
              analysis: 'CPI shows moderate inflation with year-over-year growth at 3.2% and month-over-month change of 0.2%. Core CPI at 4.1% indicates underlying inflation pressures remain above target.',
              bullet_points: ['Year-over-year inflation at 3.2%', 'Month-over-month change of 0.2%', 'Core CPI at 4.1%', 'Inflation trending towards target'],
              encoded_output: createEncodedOutput('ECONOMICS_AGENT', 'CPI shows moderate inflation with year-over-year growth at 3.2% and month-over-month change of 0.2%. Core CPI at 4.1% indicates underlying inflation pressures remain above target.', ['Year-over-year inflation at 3.2%', 'Month-over-month change of 0.2%', 'Core CPI at 4.1%', 'Inflation trending towards target'])
            }
          }
        },
        {
          id: `unemployment-${now.getTime()}`,
          type: 'ECONOMICS_AGENT',
          category: 'ECONOMICS',
          title: 'UNEMPLOYMENT',
          timestamp: now,
          data: {
            data_metrics: {
              'unemployment rate': '3.8%',
              'change (pp)': '-0.1',
              'labor force participation': '62.8%',
              'nonfarm payrolls': '+185K'
            },
            insights: {
              analysis: 'Unemployment rate at 3.8% shows a slight improvement of -0.1 percentage points. Labor force participation at 62.8% and nonfarm payrolls adding 185K jobs indicate a healthy labor market.',
              bullet_points: ['Unemployment rate at 3.8%', 'Slight improvement of -0.1 pp', 'Labor force participation at 62.8%', 'Strong job growth of 185K'],
              encoded_output: createEncodedOutput('ECONOMICS_AGENT', 'Unemployment rate at 3.8% shows a slight improvement of -0.1 percentage points. Labor force participation at 62.8% and nonfarm payrolls adding 185K jobs indicate a healthy labor market.', ['Unemployment rate at 3.8%', 'Slight improvement of -0.1 pp', 'Labor force participation at 62.8%', 'Strong job growth of 185K'])
            }
          }
        },
        {
          id: `house-permit-${now.getTime()}`,
          type: 'ECONOMICS_AGENT',
          category: 'ECONOMICS',
          title: 'HOUSE PERMIT',
          timestamp: now,
          data: {
            data_metrics: {
              'building permits (saar)': '1.45M',
              'yoy change %': '+5.2%',
              'housing starts (saar)': '1.38M',
              'trend': 'Expanding'
            },
            insights: {
              analysis: 'Building permits at 1.45M (seasonally adjusted annual rate) show a 5.2% year-over-year increase. Housing starts at 1.38M indicate an expanding housing market with strong construction activity.',
              bullet_points: ['Building permits at 1.45M SAAR', 'Year-over-year increase of 5.2%', 'Housing starts at 1.38M', 'Expanding housing market'],
              encoded_output: createEncodedOutput('ECONOMICS_AGENT', 'Building permits at 1.45M (seasonally adjusted annual rate) show a 5.2% year-over-year increase. Housing starts at 1.38M indicate an expanding housing market with strong construction activity.', ['Building permits at 1.45M SAAR', 'Year-over-year increase of 5.2%', 'Housing starts at 1.38M', 'Expanding housing market'])
            }
          }
        }
      ]
    } else if (props.activeAgent === 'MANAGEMENT_AGENT') {
      // Research agent - return empty array, will show chatbox instead
      return []
    } else {
      // Other agents - return empty or basic mock data
      return []
    }
  }
}

const fetchDataBubbles = async () => {
  // Use mock data instead of calling backend
  console.log('Using mock data for:', props.viewMode, props.activeAgent, props.ticker)
  const mockBubbles = generateMockBubbles()
  dataBubbles.value = mockBubbles
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

// Check if bubble is a financial statement (Income, Balance, Cash Flow)
const isFinancialStatementBubble = (bubble) => {
  const financialTypes = ['INCOME_ANALYST_AGENT', 'BALANCE_ANALYST_AGENT', 'CASHFLOW_ANALYST_AGENT']
  return financialTypes.includes(bubble.type) || 
         bubble.title === 'INCOME STATEMENT' || 
         bubble.title === 'BALANCE SHEET' || 
         bubble.title === 'CASH FLOW'
}

// Check if bubble has period data (Annually/Quarterly structure)
const hasPeriodData = (bubble) => {
  return bubble.data && (bubble.data.Annually || bubble.data.Quarterly)
}

// Get the selected period for a bubble (default to 'Annually')
const getBubblePeriod = (bubbleId) => {
  return bubblePeriods.value[bubbleId] || 'Annually'
}

// Set the period for a bubble
const setBubblePeriod = (bubbleId, period) => {
  bubblePeriods.value[bubbleId] = period
}

// Get data metrics for the selected period
const getPeriodDataMetrics = (bubble) => {
  const period = getBubblePeriod(bubble.id)
  if (bubble.data && bubble.data[period]) {
    return bubble.data[period].data_metrics || {}
  }
  return {}
}

// Get insights for the selected period (for drag and drop)
const getPeriodInsights = (bubble) => {
  const period = getBubblePeriod(bubble.id)
  if (bubble.data && bubble.data[period]) {
    return bubble.data[period].insights || {}
  }
  return {}
}

// Format decoded insight data as markdown
const formatDecodedInsight = (decodedData, bubble) => {
  let markdown = `## ${bubble.title}\n\n`
  
  // Get data metrics from bubble's period data (for financial statements) or direct data
  let metrics = {}
  if (isFinancialStatementBubble(bubble) && hasPeriodData(bubble)) {
    const period = getBubblePeriod(bubble.id)
    const periodData = bubble.data[period]
    metrics = periodData?.data_metrics || {}
  } else {
    metrics = bubble.data?.data_metrics || bubble.data || {}
  }
  
  // Add data metrics table if available
  if (Object.keys(metrics).length > 0) {
    markdown += '| Metric | Value |\n'
    markdown += '|--------|-------|\n'
    Object.entries(metrics).forEach(([key, value]) => {
      markdown += `| ${key} | ${formatValue(value)} |\n`
    })
    markdown += '\n'
  }
  
  // Add analysis if available
  if (decodedData.analysis) {
    markdown += `**Analysis:**\n\n${decodedData.analysis}\n\n`
  }
  
  // Add bullet points if available
  if (decodedData.bullet_points && decodedData.bullet_points.length > 0) {
    markdown += '**Key Points:**\n\n'
    decodedData.bullet_points.forEach(point => {
      markdown += `- ${point}\n`
    })
  }
  
  return markdown
}

// Format insights object as markdown (when encoded_output is not available)
const formatInsightsAsMarkdown = (insights, bubble) => {
  let markdown = `## ${bubble.title}\n\n`
  
  // Add data metrics if available
  if (bubble.data && bubble.data.data_metrics) {
    const metrics = bubble.data.data_metrics
    if (Object.keys(metrics).length > 0) {
      markdown += '| Metric | Value |\n'
      markdown += '|--------|-------|\n'
      Object.entries(metrics).forEach(([key, value]) => {
        markdown += `| ${key} | ${formatValue(value)} |\n`
      })
      markdown += '\n'
    }
  }
  
  // Add analysis if available
  if (insights.analysis) {
    markdown += `**Analysis:**\n\n${insights.analysis}\n\n`
  }
  
  // Add bullet points if available
  if (insights.bullet_points && insights.bullet_points.length > 0) {
    markdown += '**Key Points:**\n\n'
    insights.bullet_points.forEach(point => {
      markdown += `- ${point}\n`
    })
  }
  
  return markdown
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

const refreshData = async () => {
  // Refresh mock data (just regenerate)
  console.log('Refreshing mock data')
  fetchDataBubbles()
}

// Chatbox functions for Research agent
const sendChatMessage = () => {
  if (!chatInput.value.trim()) return
  
  // Add user message
  chatMessages.value.push({
    role: 'user',
    content: chatInput.value.trim(),
    timestamp: new Date()
  })
  
  const userMessage = chatInput.value.trim()
  chatInput.value = ''
  
  // Simulate assistant response (mock)
  setTimeout(() => {
    const responses = [
      `Based on the latest filings for ${props.ticker}, I can help you analyze the key financial metrics and trends.`,
      `The 10-K filing shows significant growth in revenue and strong cash flow generation. Would you like me to dive deeper into any specific section?`,
      `I've reviewed the management discussion and analysis. The company highlights several key strategic initiatives. What aspect interests you most?`,
      `The financial statements indicate healthy margins and efficient capital allocation. I can provide more detailed analysis on any specific metric.`
    ]
    const randomResponse = responses[Math.floor(Math.random() * responses.length)]
    
    chatMessages.value.push({
      role: 'assistant',
      content: randomResponse,
      timestamp: new Date()
    })
  }, 500)
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
})
</script>

<style scoped>
.research-edit-view {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  color: #1a1a1a;
  font-family: 'Space Mono', monospace;
  position: relative;
}

/* Top Bar */
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #ffffff;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
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
  color: #000000;
  letter-spacing: 1px;
  line-height: 1.2;
}

.logo-subtitle {
  font-family: 'Space Mono', monospace;
  font-size: 0.7em;
  color: #525252;
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
  color: #1a1a1a;
  font-weight: 600;
}

.location-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #525252;
  border: 2px solid rgba(0, 0, 0, 0.1);
}

/* Header */
.editor-header {
  padding: 20px 24px;
  background: #ffffff;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
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
  color: #000000;
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
  background: rgba(0, 0, 0, 0.05);
  border-radius: 20px;
  overflow: hidden;
  position: relative;
  transition: all 0.3s ease;
  border: 1px solid rgba(0, 0, 0, 0.1);
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
  background: rgba(0, 0, 0, 0.05);
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
  background: rgba(0, 0, 0, 0.05);
}

.market-section:not(.active) svg {
  color: #737373;
  stroke: #737373;
  opacity: 0.5;
}

.search-container {
  display: flex;
  align-items: center;
  background: rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 6px;
  padding: 0 16px;
}

.search-input {
  background: transparent;
  border: none;
  padding: 10px 0;
  color: #1a1a1a;
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
  background: rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.1);
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
  background: rgba(0, 0, 0, 0.05);
  color: #1a1a1a;
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
  border: 1px solid rgba(0, 0, 0, 0.1);
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
  background: rgba(0, 0, 0, 0.05);
  border-color: rgba(0, 0, 0, 0.2);
  color: #1a1a1a;
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
  color: #1a1a1a;
  font-family: 'Lora', serif;
  font-size: 1em;
  line-height: 1.8;
  outline: none;
  transition: all 0.3s ease;
}

.editor-content.has-content {
  background: rgba(0, 0, 0, 0.02);
  border: 1px solid rgba(0, 0, 0, 0.05);
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
  color: #000000;
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
  color: #525252;
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
  background: rgba(255, 255, 255, 0.8);
  border-left: 1px solid rgba(0, 0, 0, 0.1);
  padding: 20px;
  overflow-y: auto;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.sidebar-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: 'Cinzel', serif;
  font-size: 1em;
  font-weight: 600;
  color: #000000;
  margin-bottom: 10px;
  letter-spacing: 1px;
}

.sidebar-title svg {
  color: #1a1a1a;
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
  background: rgba(0, 0, 0, 0.03);
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  padding: 18px;
  cursor: grab;
  transition: all 0.3s ease;
}

.data-bubble:hover {
  border-color: rgba(245, 158, 11, 0.4);
  background: rgba(0, 0, 0, 0.05);
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
  color: #000000;
  margin-bottom: 12px;
  letter-spacing: 0.5px;
}

/* Period Toggle Row for Financial Statements */
.bubble-period-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.period-toggle {
  display: flex;
  gap: 8px;
}

.bubble-meta-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.period-btn {
  font-family: 'Space Mono', monospace;
  font-size: 0.75em;
  font-weight: 600;
  padding: 6px 16px;
  border: 1px solid rgba(0, 0, 0, 0.3);
  border-radius: 20px;
  background: transparent;
  color: #10b981;
  cursor: pointer;
  transition: all 0.3s ease;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.period-btn:hover {
  border-color: rgba(0, 0, 0, 0.5);
  background: rgba(0, 0, 0, 0.05);
}

.period-btn.active {
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.5);
  color: #10b981;
}

.bubble-subtitle {
  font-family: 'Space Mono', monospace;
  font-size: 0.8em;
  color: #525252;
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
  background: rgba(0, 0, 0, 0.03);
  padding: 10px;
  border-radius: 6px;
  border: 1px solid rgba(0, 0, 0, 0.05);
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
  color: #000000;
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

/* Research Chatbox */
.research-chatbox {
  display: flex;
  flex-direction: column;
  height: 100%;
  flex: 1;
  min-height: 0;
}

.chatbox-messages {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 10px 0;
  margin-bottom: 15px;
}

.chat-message {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  border-radius: 8px;
  max-width: 85%;
}

.user-message {
  align-self: flex-end;
  background: rgba(245, 158, 11, 0.1);
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.assistant-message {
  align-self: flex-start;
  background: rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.message-content {
  font-family: 'Lora', serif;
  font-size: 0.9em;
  color: #1a1a1a;
  line-height: 1.5;
}

.message-time {
  font-family: 'Space Mono', monospace;
  font-size: 0.7em;
  color: #737373;
  margin-top: 4px;
}

.chatbox-input {
  display: flex;
  gap: 8px;
  padding-top: 15px;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

.chat-input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 6px;
  font-family: 'Space Mono', monospace;
  font-size: 0.85em;
  color: #1a1a1a;
  background: rgba(0, 0, 0, 0.02);
  outline: none;
}

.chat-input:focus {
  border-color: rgba(245, 158, 11, 0.4);
  background: rgba(0, 0, 0, 0.03);
}

.chat-input::placeholder {
  color: #737373;
}

.chat-send-btn {
  padding: 10px 14px;
  background: #f59e0b;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #000000;
  transition: all 0.2s;
}

.chat-send-btn:hover {
  background: #fbbf24;
  transform: scale(1.05);
}

.chat-send-btn:active {
  transform: scale(0.98);
}

/* Sidebar Footer */
.sidebar-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 15px;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
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
  background: rgba(255, 255, 255, 0.9);
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  font-family: 'Space Mono', monospace;
  font-size: 0.8em;
  color: #525252;
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
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.editor-panel::-webkit-scrollbar-thumb:hover,
.data-sidebar::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.2);
}
</style>
