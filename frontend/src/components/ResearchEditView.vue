<template>
  <div class="research-edit-view" :class="{ 'preview-mode': viewMode === 'PREVIEW' }">
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
            <div class="logo-title">{{ t('research.title') }}</div>
            <div class="logo-subtitle">{{ t('research.subtitle') }}</div>
          </div>
        </div>
      </div>
      <div class="top-bar-right">
        <div class="location-info">
          <div class="location-label">{{ t('research.location') }}</div>
          <div class="location-value">{{ t('research.location_value') }}</div>
        </div>
        <div class="location-indicator"></div>
      </div>
    </div>

    <!-- Main Header Section -->
    <header class="editor-header">
      <div class="header-content">
        <!-- Report Name Input -->
        <input
          v-model="reportName"
          type="text"
          :placeholder="t('research.report_name_placeholder')"
          class="report-name-input"
        />
        
        <!-- Mode Toggle Switch (Edit / Preview) -->
        <div class="mode-toggle-switch" @click="toggleViewMode" :title="viewMode === 'EDIT' ? 'Switch to Preview' : 'Switch to Edit'">
          <div class="switch-track" :class="{ 'preview-active': viewMode === 'PREVIEW' }">
            <div class="switch-section edit-section" :class="{ 'active': viewMode === 'EDIT' }">
              <!-- Edit Icon -->
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
              </svg>
              <span style="font-size: 11px; margin-left: 4px; font-weight: 600;">Edit</span>
            </div>
            <div class="switch-section preview-section" :class="{ 'active': viewMode === 'PREVIEW' }">
              <!-- Preview Icon -->
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                <circle cx="12" cy="12" r="3"></circle>
              </svg>
              <span style="font-size: 11px; margin-left: 4px; font-weight: 600;">Preview</span>
            </div>
          </div>
        </div>
        
        <div style="flex: 1;"></div>

        <!-- Action Buttons -->
        <div class="header-actions">
          <button @click="showUploadModal = true" class="action-btn upload-header-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            <span>Upload</span>
          </button>
          <button @click="publishEditor" class="action-btn publish-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
            <span>{{ t('research.publish') }}</span>
          </button>

        </div>

        <!-- Report Type Selector -->
        <div class="report-type-selector">
          <button
            v-for="type in reportTypes"
            :key="type.value"
            @click="selectedReportType = type.value"
            :class="['report-type-btn', { active: selectedReportType === type.value }]"
          >
            {{ type.label }}
          </button>
        </div>
      </div>
    </header>

    <!-- Main Editor Area -->
    <div class="editor-container">
      <!-- Editor Panel -->
      <div class="editor-panel">
        <div v-if="editorContent.trim() === ''" class="editor-placeholder">
            <h2 class="placeholder-title">
              {{ t('research.editor_placeholder.title', { company: companyName || 'Company' }) }}
            </h2>
            <div class="placeholder-instructions">
              <div class="instruction-item">
                <span class="instruction-number">1.</span>
                <span>{{ t('research.editor_placeholder.step_1') }}</span>
              </div>
              <div class="instruction-item">
                <span class="instruction-number">2.</span>
                <span>{{ t('research.editor_placeholder.chat_instruction', 'Chat with the agent to generate analysis.') }}</span>
              </div>
            </div>
          </div>

        <div
          ref="editorRef"
          class="editor-content"
          :contenteditable="viewMode === 'EDIT'"
          @drop.prevent="handleDrop"
          @dragover.prevent="handleDragOver"
          @dragenter.prevent="handleDragEnter"
          @dragleave.prevent="handleDragLeave"
          @paste.prevent="handlePaste"
          :class="{ 'drag-active': isDragging, 'has-content': editorContent.trim() !== '' }"
          @input="handleEditorInput"
        ></div>
      </div>

      <!-- Data Stream Sidebar -->
      <!-- Resize Handle -->
      <div 
        class="resize-handle"
        @mousedown="startResize"
        :class="{ 'dragging': isResizing }"
      ></div>

      <!-- Data Stream Sidebar -->
      <ResearchChatSidebar 
        :active-agent="props.activeAgent"
        :ticker="props.ticker"
        :view-mode="props.viewMode"
        :style="{ width: sidebarWidth + 'px' }"
      />
    </div>

    <!-- Bottom Status Bar -->
    <div class="status-bar">
      <div class="status-left">
        <span>{{ t('research.chars') }}: {{ characterCount }}</span>
        <span class="status-separator">|</span>
        <span>{{ t('research.mode') }}: {{ viewMode }}</span>
      </div>
      <div class="status-right">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="7 10 12 15 17 10"></polyline>
          <line x1="12" y1="15" x2="12" y2="3"></line>
        </svg>
        <span>{{ t('research.autosave_on') }}</span>
      </div>
    </div>

    <!-- PDF Preview Modal -->
    <div v-if="showPreviewModal" class="modal-overlay" @click="closePreviewModal">
      <div class="modal-content preview-modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ t('research.preview_modal.title') }}</h3>
          <button @click="closePreviewModal" class="close-modal-btn">×</button>
        </div>
        <div class="modal-body preview-body">
          <div class="pdf-preview-container">
            <iframe 
              v-if="previewPdfUrl" 
              :src="previewPdfUrl" 
              class="pdf-preview-iframe"
              frameborder="0"
            ></iframe>
            <div v-else class="loading-pdf">{{ t('research.preview_modal.generating') }}</div>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="confirmPublish" class="modal-btn primary" :disabled="isPublishing">
            {{ isPublishing ? t('research.preview_modal.publishing') : t('research.preview_modal.confirm') }}
          </button>
          <button @click="closePreviewModal" class="modal-btn secondary" :disabled="isPublishing">{{ t('research.preview_modal.cancel') }}</button>
        </div>
      </div>
    </div>

    <!-- Upload Modal -->
    <div v-if="showUploadModal" class="modal-overlay" @click="closeUploadModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Upload Report</h3>
          <button @click="closeUploadModal" class="close-modal-btn">×</button>
        </div>
        <div class="modal-body">
             <div class="upload-form">
                <div class="form-group">
                    <label>Report Title</label>
                    <input v-model="uploadReportTitle" type="text" class="form-input" placeholder="Enter title">
                </div>
                <div class="form-group">
                    <label>Ticker</label>
                    <input v-model="uploadReportTicker" type="text" class="form-input" placeholder="e.g. TSLA">
                </div>
                <div class="form-group">
                    <label>Report Type</label>
                    <select v-model="uploadReportType" class="form-input">
                        <option value="">Select Type</option>
                        <option value="daily">Daily</option>
                        <option value="long">Long Position</option>
                        <option value="short">Short Position</option>
                        <option value="market">Market</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>File (PDF)</label>
                    <input type="file" accept=".pdf" @change="handleFileSelect" class="file-input">
                    <span v-if="selectedFile" class="file-name">{{ selectedFile.name }}</span>
                </div>
                
                <div v-if="uploadError" class="error-message">{{ uploadError }}</div>
                <div v-if="uploadSuccess" class="success-message">{{ uploadSuccess }}</div>
             </div>
        </div>
        <div class="modal-footer">
          <button @click="uploadReport" class="modal-btn primary" :disabled="!canUpload || uploadingReport">
            {{ uploadingReport ? 'Uploading...' : 'Upload' }}
          </button>
          <button @click="closeUploadModal" class="modal-btn secondary">Cancel</button>
        </div>
      </div>
    </div>

    <!-- Success Modal -->
    <div v-if="showSuccessModal" class="modal-overlay" @click="closeSuccessModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ t('research.success_modal.title') }}</h3>
        </div>
        <div class="modal-body">
          <div class="success-icon">✓</div>
          <p class="success-message">{{ t('research.success_modal.message') }}</p>
          <div class="success-details">
            <div class="detail-item">
              <span class="detail-label">{{ t('research.success_modal.type') }}</span>
              <span class="detail-value">{{ publishedReportType }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">{{ t('research.success_modal.ticker') }}</span>
              <span class="detail-value">{{ publishedReportTicker }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">{{ t('research.success_modal.date') }}</span>
              <span class="detail-value">{{ publishedReportDate }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">{{ t('research.success_modal.uuid') }}</span>
              <span class="detail-value uuid-value">{{ publishedReportUuid }}</span>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="redirectToReports" class="modal-btn primary">{{ t('research.success_modal.view_reports') }}</button>
          <button @click="closeSuccessModal" class="modal-btn secondary">{{ t('research.success_modal.close') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import API_BASE_URL from '@/config/api.js'
import ResearchChatSidebar from './ResearchChatSidebar.vue'

import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getDailyCache, setDailyCache } from '../utils/dailyCache.js'
import html2pdf from 'html2pdf.js'

const router = useRouter()
const { t } = useI18n()

const props = defineProps({
  viewMode: {
    type: String,
    required: true,
    validator: (value) => ['EDIT', 'PREVIEW'].includes(value)
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

// Sidebar state
const sidebarWidth = ref(380)
const isResizing = ref(false)

const startResize = () => {
  isResizing.value = true
  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
  document.body.style.userSelect = 'none'
}

const handleResize = (e) => {
  if (!isResizing.value) return
  const container = document.querySelector('.editor-container')
  if (!container) return
  
  const containerRect = container.getBoundingClientRect()
  const newWidth = containerRect.right - e.clientX
  
  // Constraints
  if (newWidth > 300 && newWidth < 800) {
    sidebarWidth.value = newWidth
  }
}

const stopResize = () => {
  isResizing.value = false
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
  document.body.style.userSelect = ''
}

onUnmounted(() => {
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
})

// Editor state
const editorRef = ref(null)
const editorContent = ref('')
const companyName = ref('Alphabet Inc.')

// Report type selection
const reportTypes = computed(() => [
  { label: t('research.report_types.daily'), value: 'daily' },
  { label: t('research.report_types.market'), value: 'market' },
  { label: t('research.report_types.long_position'), value: 'long' },
  { label: t('research.report_types.short_position'), value: 'short' }
])
const selectedReportType = ref('daily')

// Preview modal state
const showPreviewModal = ref(false)
const previewPdfUrl = ref(null)
const previewPdfBlob = ref(null)
const isPublishing = ref(false)

// Success modal state
const showSuccessModal = ref(false)
const publishedReportType = ref('')
const publishedReportTicker = ref('')
const publishedReportDate = ref('')
const publishedReportUuid = ref('')


// Upload Modal State
const showUploadModal = ref(false)
const uploadReportTitle = ref('')
const uploadReportTicker = ref('')
const uploadReportType = ref('')
const selectedFile = ref(null)
const uploadingReport = ref(false)
const uploadError = ref('')
const uploadSuccess = ref('')

const canUpload = computed(() => {
  return uploadReportTitle.value.trim() && uploadReportType.value && selectedFile.value
})

const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file && file.type === 'application/pdf') {
    selectedFile.value = file
    uploadError.value = ''
  } else {
    selectedFile.value = null
    uploadError.value = 'PDF files only'
  }
}

const closeUploadModal = () => {
    showUploadModal.value = false
    uploadReportTitle.value = ''
    uploadReportTicker.value = ''
    uploadReportType.value = ''
    selectedFile.value = null
    uploadSuccess.value = ''
    uploadError.value = ''
}

const uploadReport = async () => {
    if (!canUpload.value) return
    
    uploadingReport.value = true
    uploadError.value = ''
    uploadSuccess.value = ''
    
    try {
        const formData = new FormData()
        formData.append('pdf_file', selectedFile.value)
        formData.append('report_name', uploadReportTitle.value.trim())
        formData.append('ticker', uploadReportTicker.value.trim() || 'GENERAL')
        formData.append('report_type', uploadReportType.value)
        
        const token = localStorage.getItem('access_token')
        
        const response = await fetch(`${API_BASE_URL}/api/reports/publish`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        })
        
        if (!response.ok) {
            const errorData = await response.json()
            throw new Error(errorData.detail || 'Upload failed')
        }
        
        uploadSuccess.value = 'Report uploaded successfully'
        
        // Reset
        setTimeout(() => {
            closeUploadModal()
        }, 2000)
    } catch (err) {
        uploadError.value = err.message
    } finally {
        uploadingReport.value = false
    }
}

// Chatbox state for Research agent


// Character count
const characterCount = computed(() => {
  if (!editorRef.value) return 0
  const text = editorRef.value.innerText || ''
  return text.length
})

// Agent definitions
const companyAgents = computed(() => [
  { 
    id: 'FUNDAMENTAL_AGENT', 
    name: t('research.agents.financials'), 
    icon: '🀃', 
    focus: ['income', 'balance', 'cashflow', 'financial'],
    subAgents: ['FUNDAMENTAL_AGENT']
  },
  { 
    id: 'INSIDE_TRADING_ANALYST_AGENT', 
    name: t('research.agents.insider'), 
    icon: '♙', 
    focus: ['insider', 'trading', 'executive'],
    subAgents: ['INSIDE_TRADING_ANALYST_AGENT']
  },
  { 
    id: 'OPTION_ANALYST_AGENT', 
    name: t('research.agents.option'), 
    icon: '♘', 
    focus: ['option', 'options', 'chain', 'calls', 'puts'],
    subAgents: ['OPTION_ANALYST_AGENT']
  },
  { 
    id: 'POLYMARKET_AGENT', 
    name: t('research.agents.polymarket'), 
    icon: '⛪︎', 
    focus: ['polymarket', 'prediction', 'market'],
    subAgents: ['polymarket']
  },
  { 
    id: 'BOND_AGENT', 
    name: t('research.agents.bond'), 
    icon: '🀅', 
    focus: ['bond', 'credit', 'yield', 'treasury'],
    subAgents: ['BOND_ANALYST_AGENT', 'CREDIT_ANALYST_AGENT']
  },
  { 
    id: 'ECONOMICS_AGENT', 
    name: t('research.agents.economics'), 
    icon: '🀏', 
    focus: ['economics', 'cpi', 'macro', 'inflation'],
    subAgents: ['economics']
  },
  { 
    id: 'MANAGEMENT_AGENT', 
    name: t('research.agents.research'), 
    icon: '🀢', 
    focus: ['research', '10k', '10q', 'filing', 'management'],
    subAgents: ['management']
  }
])

const marketAgents = computed(() => [
  { id: 'EQUITY_AGENT', name: t('research.agents.equity_agent'), icon: '🀉', focus: ['equity', 'sector', 'sp500'], subAgents: ['sp500_index'] },
  { id: 'BOND_AGENT', name: t('research.agents.bond_agent'), icon: '🀅', focus: ['yield', 'treasury', 'rates'], subAgents: ['treasury_yield'] },
  { id: 'ECONOMICS_AGENT', name: t('research.agents.economics_agent'), icon: '🀏', focus: ['cpi', 'jobs', 'macro'], subAgents: ['cpi_inflation'] }
])

const availableAgents = computed(() => {
  return props.viewMode === 'COMPANY' ? companyAgents.value : marketAgents.value
})

const currentAgentName = computed(() => {
  if (!availableAgents.value || !Array.isArray(availableAgents.value)) return props.activeAgent
  const agent = availableAgents.value.find(a => a && a.id === props.activeAgent)
  return agent ? agent.name : props.activeAgent
})



// Drag and Drop handlers
const handleDragStart = (event) => {}

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
  
  // Check if files are being dropped (images)
  const files = event.dataTransfer.files
  if (files && files.length > 0) {
    // Handle file drops (images)
    await handleImageFiles(Array.from(files))
    return
  }
}

const insertInsight = (insight, range) => {
  if (!editorRef.value) return
  
  // Convert markdown to HTML for better formatting
  const htmlContent = convertMarkdownToHTML(insight)
  
  // Get the current selection/cursor position
  const selection = window.getSelection()
  let insertRange = range
  
  // If no range provided, try to get current selection
  if (!insertRange && selection.rangeCount > 0) {
    insertRange = selection.getRangeAt(0)
  }
  
  // Make sure we're working within the editor
  if (insertRange) {
    // Check if the range is actually inside the editor
    const rangeContainer = insertRange.commonAncestorContainer
    const isInEditor = editorRef.value.contains(rangeContainer.nodeType === Node.TEXT_NODE ? rangeContainer.parentNode : rangeContainer)
    
    if (!isInEditor) {
      insertRange = null
    }
  }
  
  if (insertRange) {
    // Insert at the cursor/drop position within editor
    try {
      insertRange.deleteContents()
      
      // Create a wrapper div to hold the content
      const wrapper = document.createElement('div')
      wrapper.innerHTML = htmlContent
      
      // Insert each child node
      const fragment = document.createDocumentFragment()
      while (wrapper.firstChild) {
        fragment.appendChild(wrapper.firstChild)
      }
      
      insertRange.insertNode(fragment)
      
      // Move cursor to end of inserted content
      insertRange.collapse(false)
      selection.removeAllRanges()
      selection.addRange(insertRange)
    } catch (error) {
      console.error('Error inserting at range:', error)
      // Fallback to append
      editorRef.value.innerHTML += htmlContent
    }
  } else {
    // Append to end of editor
    console.log('Appending to end of editor')
    editorRef.value.innerHTML += htmlContent
    
    // Move cursor to end
    const newRange = document.createRange()
    const sel = window.getSelection()
    newRange.selectNodeContents(editorRef.value)
    newRange.collapse(false)
    sel.removeAllRanges()
    sel.addRange(newRange)
  }
  
  // Update the content
  editorContent.value = editorRef.value.innerHTML
  console.log('Content inserted, editor HTML length:', editorRef.value.innerHTML.length)
}

// Convert simple markdown to HTML
const convertMarkdownToHTML = (markdown) => {
  let html = markdown
  
  // Convert headers (# Header -> <h1>Header</h1>)
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>')
  html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>')
  html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>')
  
  // Convert bold (**text** -> <strong>text</strong>)
  html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
  
  // Convert bullet points (- item -> <li>item</li>)
  html = html.replace(/^\- (.*$)/gim, '<li>$1</li>')
  
  // Wrap consecutive <li> items in <ul>
  html = html.replace(/(<li>.*<\/li>\n?)+/gim, '<ul>$&</ul>')
  
  // Convert line breaks to <br> or <p>
  // Split by double newlines for paragraphs
  const paragraphs = html.split('\n\n')
  html = paragraphs
    .map(p => {
      p = p.trim()
      if (!p) return ''
      // If it's already an HTML tag, don't wrap it
      if (p.startsWith('<h') || p.startsWith('<ul') || p.startsWith('<li')) {
        return p
      }
      // Otherwise wrap in paragraph
      return `<p>${p.replace(/\n/g, '<br>')}</p>`
    })
    .filter(p => p)
    .join('\n')
  
  return html
}

const handleEditorInput = () => {
  // Just sync the content without re-rendering
  // This prevents cursor from jumping
  if (editorRef.value) {
    editorContent.value = editorRef.value.innerHTML
  }
}

// Handle image paste and file drops
const handleImageFiles = async (files) => {
  const imageFiles = files.filter(file => file.type.startsWith('image/'))
  
  if (imageFiles.length === 0) {
    return
  }
  
  const selection = window.getSelection()
  const range = selection.rangeCount > 0 ? selection.getRangeAt(0) : null
  
  for (const file of imageFiles) {
    try {
      // Convert image to base64 data URL
      const reader = new FileReader()
      reader.onload = (e) => {
        const dataUrl = e.target.result
        insertImage(dataUrl, file.name, range)
      }
      reader.readAsDataURL(file)
    } catch (error) {
      console.error('Error processing image:', error)
      alert(t('research.alerts.image_error', { file: file.name }))
    }
  }
}

const insertImage = (dataUrl, altText, range) => {
  if (!editorRef.value) return
  
  const img = document.createElement('img')
  img.src = dataUrl
  img.alt = altText || 'Image'
  img.style.maxWidth = '100%'
  img.style.height = 'auto'
  img.style.display = 'block'
  img.style.margin = '10px 0'
  
  const selection = window.getSelection()
  let insertRange = range
  
  if (!insertRange && selection.rangeCount > 0) {
    insertRange = selection.getRangeAt(0)
  }
  
  if (insertRange) {
    insertRange.deleteContents()
    insertRange.insertNode(img)
    insertRange.setStartAfter(img)
    insertRange.collapse(false)
    selection.removeAllRanges()
    selection.addRange(insertRange)
  } else {
    // Append to end if no selection
    editorRef.value.appendChild(img)
    // Move cursor after image
    const newRange = document.createRange()
    const sel = window.getSelection()
    newRange.setStartAfter(img)
    newRange.collapse(true)
    sel.removeAllRanges()
    sel.addRange(newRange)
  }
  
  // Update content
  editorContent.value = editorRef.value.innerHTML
}

const handlePaste = async (event) => {
  const items = event.clipboardData?.items || []
  const imageFiles = []
  
  for (let i = 0; i < items.length; i++) {
    const item = items[i]
    if (item.type.indexOf('image') !== -1) {
      const file = item.getAsFile()
      if (file) {
        imageFiles.push(file)
      }
    }
  }
  
  if (imageFiles.length > 0) {
    event.preventDefault()
    await handleImageFiles(imageFiles)
    return
  }
  
  // Allow default paste behavior for text
  // We need to manually handle this to preserve cursor position
  const selection = window.getSelection()
  if (selection.rangeCount > 0) {
    const range = selection.getRangeAt(0)
    const text = event.clipboardData?.getData('text/plain') || ''
    
    if (text) {
      event.preventDefault()
      range.deleteContents()
      const textNode = document.createTextNode(text)
      range.insertNode(textNode)
      range.setStartAfter(textNode)
      range.collapse(false)
      selection.removeAllRanges()
      selection.addRange(range)
      editorContent.value = editorRef.value.innerHTML
    }
  }
}




const toggleViewMode = () => {
  const newMode = props.viewMode === 'EDIT' ? 'PREVIEW' : 'EDIT'
  emit('update:view-mode', newMode)
}



const generatePdfPreview = async () => {
  // Generate PDF from editor content
  if (!editorRef.value) {
    throw new Error('Editor not found')
  }
  
  // Create a temporary container for PDF generation
  const tempContainer = document.createElement('div')
  tempContainer.style.width = '210mm' // A4 width
  tempContainer.style.padding = '20mm'
  tempContainer.style.fontFamily = 'Arial, sans-serif'
  tempContainer.style.fontSize = '12pt'
  tempContainer.style.lineHeight = '1.6'
  tempContainer.innerHTML = editorRef.value.innerHTML
  
  // Copy styles from editor to temp container
  const editorStyles = window.getComputedStyle(editorRef.value)
  tempContainer.style.color = editorStyles.color
  tempContainer.style.backgroundColor = editorStyles.backgroundColor
  
  // Ensure images are properly sized in PDF
  const images = tempContainer.querySelectorAll('img')
  images.forEach(img => {
    img.style.maxWidth = '100%'
    img.style.height = 'auto'
    img.style.display = 'block'
    img.style.margin = '10px 0'
  })
  
  // Generate PDF
  const opt = {
    margin: [10, 10, 10, 10],
    filename: `report_${Date.now()}.pdf`,
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { 
      scale: 2,
      useCORS: true,
      logging: false
    },
    jsPDF: { 
      unit: 'mm', 
      format: 'a4', 
      orientation: 'portrait' 
    }
  }
  
  const pdfBlob = await html2pdf().set(opt).from(tempContainer).outputPdf('blob')
  return pdfBlob
}

  const publishEditor = async () => {
    // Publish the editor content
    if (!editorContent.value.trim()) {
      alert(t('research.alerts.empty_content'))
      return
    }
    
    // Ticker is required for all report types except "market"
    if (!props.ticker && selectedReportType.value !== 'market') {
      alert(t('research.alerts.ticker_required'))
      return
    }
    
    if (!selectedReportType.value) {
      alert(t('research.alerts.report_type_required'))
      return
    }
  
  try {
    // Generate PDF and show preview
    const pdfBlob = await generatePdfPreview()
    
    // Create object URL for preview
    const pdfUrl = URL.createObjectURL(pdfBlob)
    previewPdfUrl.value = pdfUrl
    previewPdfBlob.value = pdfBlob
    
    // Show preview modal
    showPreviewModal.value = true
  } catch (error) {
    console.error('Error generating PDF preview:', error)
    alert(t('research.alerts.pdf_error', { error: error.message }))
  }
}

const confirmPublish = async () => {
  if (!previewPdfBlob.value) {
    return
  }
  
  isPublishing.value = true
  
  try {
    const token = localStorage.getItem('access_token')
    if (!token) {
      alert(t('research.alerts.login_required'))
      closePreviewModal()
      return
    }
    
    // Create FormData to send PDF file
    const formData = new FormData()
    formData.append('pdf_file', previewPdfBlob.value, `report.pdf`)
    formData.append('ticker', props.ticker || 'MARKET')
    formData.append('view_mode', props.viewMode)
    formData.append('active_agent', props.activeAgent || '')
    formData.append('report_type', selectedReportType.value)
    formData.append('report_name', reportName.value || 'Untitled Report')
    
    const response = await fetch(`${API_BASE_URL}/api/reports/publish`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
        // Don't set Content-Type, let browser set it with boundary
      },
      body: formData
    })
    
    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Failed to publish report')
    }
    
    const result = await response.json()
    
    // Close preview modal
    closePreviewModal()
    
    // Show success modal
    publishedReportType.value = reportTypes.value.find(t => t.value === selectedReportType.value)?.label || ''
    publishedReportTicker.value = result.ticker
    publishedReportDate.value = result.date
    publishedReportUuid.value = result.uuid
    showSuccessModal.value = true
    
    // Dispatch event to notify other components (e.g., ReportView) that a new report was published
    window.dispatchEvent(new CustomEvent('report-published', {
      detail: {
        reportType: selectedReportType.value,
        ticker: result.ticker,
        date: result.date,
        uuid: result.uuid
      }
    }))
    
    console.log('Report published:', result)
  } catch (error) {
    console.error('Error publishing report:', error)
    alert(t('research.alerts.publish_error', { error: error.message }))
  } finally {
    isPublishing.value = false
  }
}

const closePreviewModal = () => {
  showPreviewModal.value = false
  // Clean up object URL to free memory
  if (previewPdfUrl.value) {
    URL.revokeObjectURL(previewPdfUrl.value)
    previewPdfUrl.value = null
  }
  previewPdfBlob.value = null
}

const closeSuccessModal = () => {
  showSuccessModal.value = false
}

const redirectToReports = () => {
  showSuccessModal.value = false
  router.push('/report')
}

const auditReport = () => {
  // TODO: Implement audit functionality
  console.log('Audit report:', editorContent.value)
}



onMounted(() => {
  // Initialize editor content only if it exists
  nextTick(() => {
    if (editorRef.value && editorContent.value && !editorRef.value.innerHTML) {
      editorRef.value.innerHTML = editorContent.value
    }
  })
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

.report-name-input {
  padding: 8px 16px;
  font-size: 1.2em;
  font-weight: 500;
  color: #000000;
  border: 2px solid #cccccc;
  border-radius: 6px;
  background: #ffffff;
  min-width: 200px;
  font-family: 'Arial', sans-serif;
}

.report-name-input:focus {
  outline: none;
  border-color: #3498db;
}

.report-name-input::placeholder {
  color: #999999;
}

.header-title {
  font-family: 'Cinzel', serif;
  font-size: 2em;
  font-weight: 700;
  color: #000000;
  margin: 0;
  letter-spacing: 1px;
  white-space: nowrap;
  display: none;
}

/* Mode Toggle Switch */
.mode-toggle-switch {
  cursor: pointer;
  user-select: none;
}

.switch-track {
  display: flex;
  width: 180px;
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

.edit-section {
  flex: 1.2;
  background: transparent;
  border-radius: 20px 0 0 20px;
}

.edit-section.active {
  background: #f59e0b;
  border-radius: 20px 0 0 20px;
  flex: 1.2;
}

.edit-section.active svg {
  color: #000000;
  stroke: #000000;
  stroke-width: 2.5;
}

.edit-section:not(.active) {
  flex: 0.8;
  background: rgba(0, 0, 0, 0.05);
}

.edit-section:not(.active) svg {
  color: #737373;
  stroke: #737373;
  opacity: 0.5;
}

.preview-section {
  flex: 0.8;
  background: transparent;
  border-radius: 0 20px 20px 0;
}

.preview-section.active {
  background: #22d3ee;
  border-radius: 0 20px 20px 0;
  flex: 1.2;
}

.preview-section.active svg {
  color: #000000;
  stroke: #000000;
}

.preview-section:not(.active) {
  flex: 0.8;
  background: rgba(0, 0, 0, 0.05);
}

.preview-section:not(.active) svg {
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

.publish-btn {
  background: #f59e0b;
  border-color: #f59e0b;
  color: #000000;
  font-weight: 600;
}

.research-edit-view.preview-mode .publish-btn {
  background: #22d3ee;
  border-color: #22d3ee;
}

.publish-btn:hover {
  background: #fbbf24;
  transform: scale(1.02);
}

.research-edit-view.preview-mode .publish-btn:hover {
  background: #38bdf8;
}



/* Report Type Selector */
.report-type-selector {
  display: flex;
  gap: 10px;
  align-items: center;
}

.report-type-btn {
  padding: 8px 20px;
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  background: #ffffff;
  color: #1a1a1a;
  font-family: 'Space Mono', monospace;
  font-size: 0.9em;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.report-type-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  border-color: rgba(0, 0, 0, 0.3);
}

.report-type-btn.active {
  background: #f59e0b;
  border-color: #f59e0b;
  color: #000000;
  font-weight: 600;
}

.research-edit-view.preview-mode .report-type-btn.active {
  background: #22d3ee;
  border-color: #22d3ee;
}

/* Editor Container */
.editor-container {
  display: flex;
  flex-direction: row;
  flex: 1;
  overflow: hidden;
}

.resize-handle {
  width: 5px;
  cursor: col-resize;
  background: transparent;
  transition: background 0.2s;
  z-index: 10;
  margin: 0 -2px;
  position: relative;
}

.resize-handle:hover,
.resize-handle.dragging {
  background: rgba(245, 158, 11, 0.5);
}

.research-edit-view.preview-mode .resize-handle:hover,
.research-edit-view.preview-mode .resize-handle.dragging {
  background: rgba(34, 211, 238, 0.5);
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

.research-edit-view.preview-mode .editor-content.drag-active {
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

.research-edit-view.preview-mode .instruction-number {
  color: #22d3ee;
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
.editor-panel::-webkit-scrollbar {
  width: 6px;
}

.editor-panel::-webkit-scrollbar-track {
  background: transparent;
}

.editor-panel::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.editor-panel::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.2);
}

/* Success Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  backdrop-filter: blur(4px);
}

.modal-content {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  animation: modalSlideIn 0.3s ease-out;
}

.preview-modal-content {
  max-width: 90%;
  width: 90%;
  max-height: 95vh;
  display: flex;
  flex-direction: column;
}

/* Upload Modal Form */
.upload-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 10px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-family: 'Space Mono', monospace;
  font-size: 0.85em;
  color: #525252;
  font-weight: 600;
}

.form-input, .file-input {
  padding: 10px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 6px;
  font-family: 'Space Mono', monospace;
  font-size: 0.9em;
  width: 100%;
}

.form-input:focus {
  outline: none;
  border-color: #f59e0b;
}

.file-name {
  font-size: 0.85em;
  color: #10b981;
  margin-top: 4px;
}

.error-message {
  color: #ef4444;
  font-size: 0.9em;
  margin-top: 10px;
}

.success-message {
  color: #10b981;
  font-size: 0.9em;
  margin-top: 10px;
}

.upload-header-btn {
  background: #f59e0b;
  border-color: #f59e0b;
  color: #000000;
  font-weight: 600;
}
.upload-header-btn:hover {
  background: #fbbf24;
  transform: scale(1.02);
}
.research-edit-view.preview-mode .upload-header-btn {
  background: #22d3ee;
  border-color: #22d3ee;
}
.research-edit-view.preview-mode .upload-header-btn:hover {
  background: #38bdf8;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  padding: 24px 24px 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.close-modal-btn {
  background: none;
  border: none;
  font-size: 28px;
  color: #666;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.close-modal-btn:hover {
  background: rgba(0, 0, 0, 0.1);
  color: #000;
}

.modal-header h3 {
  margin: 0;
  font-family: 'Cinzel', serif;
  font-size: 1.5em;
  font-weight: 600;
  color: #000000;
}

.modal-body {
  padding: 24px;
  text-align: center;
}

.preview-body {
  padding: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.pdf-preview-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: #f5f5f5;
}

.pdf-preview-iframe {
  width: 100%;
  flex: 1;
  border: none;
  min-height: 600px;
}

.loading-pdf {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #666;
  font-size: 16px;
}

.success-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: #10b981;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2em;
  font-weight: bold;
  margin: 0 auto 20px;
  animation: successPulse 0.5s ease-out;
}

@keyframes successPulse {
  0% {
    transform: scale(0);
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
  }
}

.success-message {
  font-family: 'Lora', serif;
  font-size: 1.1em;
  color: #1a1a1a;
  margin-bottom: 24px;
}

.success-details {
  text-align: left;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
  padding: 20px;
  margin-top: 20px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-label {
  font-family: 'Space Mono', monospace;
  font-size: 0.85em;
  color: #737373;
  font-weight: 500;
}

.detail-value {
  font-family: 'Space Mono', monospace;
  font-size: 0.9em;
  color: #1a1a1a;
  font-weight: 600;
}

.uuid-value {
  font-size: 0.75em;
  word-break: break-all;
  text-align: right;
  max-width: 60%;
}

.modal-footer {
  padding: 16px 24px 24px;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

.modal-btn {
  padding: 10px 20px;
  border-radius: 6px;
  font-family: 'Space Mono', monospace;
  font-size: 0.9em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid;
}

.modal-btn.primary {
  background: #f59e0b;
  border-color: #f59e0b;
  color: #000000;
}

.research-edit-view.market-mode .modal-btn.primary {
  background: #22d3ee;
  border-color: #22d3ee;
}

.modal-btn.primary:hover {
  background: #fbbf24;
  transform: scale(1.02);
}

.research-edit-view.market-mode .modal-btn.primary:hover {
  background: #38bdf8;
}

.modal-btn.secondary {
  background: transparent;
  border-color: rgba(0, 0, 0, 0.2);
  color: #1a1a1a;
}

.modal-btn.secondary:hover {
  background: rgba(0, 0, 0, 0.05);
}

.modal-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  pointer-events: none;
}
</style>
