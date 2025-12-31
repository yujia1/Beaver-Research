<template>
  <div class="data-sidebar">
    <div class="sidebar-header">
      <div class="sidebar-title">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h9l2 3h9a2 2 0 0 1 2 2z"></path>
        </svg>
        <span>{{ t('research.sidebar.title') }}</span>
      </div>
    </div>

    <!-- Chatbox -->
    <div class="research-chatbox">
      <div class="chatbox-messages" ref="chatContainerRef">
        <div
          v-for="(message, index) in chatMessages"
          :key="index"
          class="chat-message"
          :class="{ 'user-message': message.role === 'user', 'assistant-message': message.role === 'assistant' }"
        >
          <div class="message-content" v-html="renderMarkdown(message.content)"></div>
          <div class="message-time">{{ formatTime(message.timestamp) }}</div>
        </div>
        <div v-if="isChatLoading" class="chat-message assistant-message">
           <div class="message-content">...</div>
        </div>
      </div>
      <div class="chatbox-input">
        <input
          v-model="chatInput"
          @keyup.enter="sendChatMessage"
          type="text"
          :placeholder="t('research.chat.placeholder')"
          class="chat-input"
          :disabled="isChatLoading"
        />
        <button @click="sendChatMessage" class="chat-send-btn" :disabled="isChatLoading">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </button>
      </div>
    </div>

    <div class="sidebar-footer">
      <span class="encryption-text">{{ t('research.sidebar.encryption') }}</span>
      <span class="sync-status synced">{{ t('research.sidebar.synced') }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import API_BASE_URL from '@/config/api.js'

const props = defineProps({
  activeAgent: String,
  ticker: String,
  viewMode: String
})

const { t } = useI18n()
const chatMessages = ref([
  {
    role: 'assistant',
    content: t('research.chat.intro', { ticker: props.ticker || 'companies' }),
    timestamp: new Date()
  }
])
const chatInput = ref('')
const isChatLoading = ref(false)
const chatContainerRef = ref(null)

const formatTime = (date) => {
  if (!date) return ''
  return new Date(date).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
}

const sendChatMessage = async () => {
  if (!chatInput.value.trim() || isChatLoading.value) return
  
  const userMsg = chatInput.value.trim()
  chatInput.value = ''
  
  chatMessages.value.push({
    role: 'user',
    content: userMsg,
    timestamp: new Date()
  })
  
  isChatLoading.value = true
  
  nextTick(() => {
    if (chatContainerRef.value) {
      chatContainerRef.value.scrollTop = chatContainerRef.value.scrollHeight
    }
  })
  
  try {
    const token = localStorage.getItem('access_token')
    const history = chatMessages.value.map(m => ({ role: m.role, content: m.content })).slice(-10)
    
    const response = await fetch(`${API_BASE_URL}/api/research/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        message: userMsg,
        agent_id: props.activeAgent,
        ticker: props.ticker,
        view_mode: props.viewMode,
        history: history
      })
    })
    
    if (!response.ok) {
        try {
            const err = await response.json()
            throw new Error(err.detail || 'Chat failed')
        } catch (e) {
            throw new Error('Chat failed with status: ' + response.status)
        }
    }
    
    const data = await response.json()
    
    chatMessages.value.push({
      role: 'assistant',
      content: data.response,
      timestamp: new Date()
    })
    
  } catch (error) {
    console.error('Chat error:', error)
    chatMessages.value.push({
      role: 'assistant',
      content: t('research.chat.error'),
      timestamp: new Date()
    })
  } finally {
    isChatLoading.value = false
      nextTick(() => {
        if (chatContainerRef.value) {
            chatContainerRef.value.scrollTop = chatContainerRef.value.scrollHeight
        }
    })
  }
}

// Markdown Rendering
import { marked } from 'marked'

const renderMarkdown = (text) => {
  if (!text) return ''
  return marked.parse(text)
}
</script>

<style scoped>
.data-sidebar {
  width: 380px;
  background: rgba(255, 255, 255, 0.8);
  border-left: 1px solid rgba(0, 0, 0, 0.1);
  padding: 20px;
  overflow-y: hidden; /* Changed to hidden to let inner containers handle scroll */
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  font-family: 'Space Mono', monospace;
}

.sidebar-header {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  flex-shrink: 0;
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

.research-chatbox {
  display: flex;
  flex-direction: column;
  height: 100%;
  flex: 1;
  min-height: 0;
  overflow: hidden; /* Ensure it stays within parent */
}

.chatbox-messages {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 10px 0;
  margin-bottom: 15px;
  padding-right: 5px; /* Space for scrollbar */
}

.chat-message {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  border-radius: 8px;
  max-width: 90%; /* Increased width slightly */
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
  width: 100%; /* Take available width up to max-width */
}

.message-content {
  font-family: 'Lora', serif;
  font-size: 0.9em;
  color: #1a1a1a;
  line-height: 1.5;
  overflow-wrap: break-word;
}

/* Embedded scrollable feature for Assistant messages */
.assistant-message .message-content {
  max-height: 400px;
  overflow-y: auto;
  padding-right: 8px; /* Avoid scrollbar covering text */
}

/* Markdown Styles within Message Content */
.message-content :deep(h1), 
.message-content :deep(h2), 
.message-content :deep(h3) {
  font-family: 'Cinzel', serif;
  margin-top: 10px;
  margin-bottom: 5px;
  font-size: 1.1em;
  font-weight: 600;
}

.message-content :deep(p) {
  margin-bottom: 8px;
}

.message-content :deep(ul), 
.message-content :deep(ol) {
  margin-left: 20px;
  margin-bottom: 8px;
}

.message-content :deep(li) {
  margin-bottom: 4px;
}

.message-content :deep(strong) {
  font-weight: 600;
  color: #000;
}

.message-content :deep(code) {
  font-family: 'Space Mono', monospace;
  background: rgba(0,0,0,0.05);
  padding: 2px 4px;
  border-radius: 4px;
  font-size: 0.9em;
}

.message-content :deep(pre) {
  background: #f4f4f4;
  padding: 10px;
  border-radius: 6px;
  overflow-x: auto;
  margin-bottom: 10px;
}

.message-content :deep(pre code) {
  background: transparent;
  padding: 0;
}

.message-time {
  font-family: 'Space Mono', monospace;
  font-size: 0.7em;
  color: #737373;
  margin-top: 4px;
  align-self: flex-end; /* Align time to right */
}

.chatbox-input {
  display: flex;
  gap: 8px;
  padding-top: 15px;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  flex-shrink: 0;
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

.sidebar-footer {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.7em;
  color: #737373;
  font-family: 'Space Mono', monospace;
}

.encryption-text {
  opacity: 0.7;
}

.sync-status {
  display: flex;
  align-items: center;
  gap: 6px;
}

.sync-status::before {
  content: '';
  display: block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10b981;
}

/* Scrollbar */
.data-sidebar::-webkit-scrollbar,
.chatbox-messages::-webkit-scrollbar {
  width: 6px;
}

.data-sidebar::-webkit-scrollbar-track,
.chatbox-messages::-webkit-scrollbar-track {
  background: transparent;
}

.data-sidebar::-webkit-scrollbar-thumb,
.chatbox-messages::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.data-sidebar::-webkit-scrollbar-thumb:hover,
.chatbox-messages::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.2);
}
</style>
