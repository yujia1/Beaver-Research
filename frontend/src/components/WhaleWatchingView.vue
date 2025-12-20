<template>
  <div class="whale-watching-view">
    <div class="page-header">
      <div>
        <h1>Whale Watching</h1>
        <p class="subtitle">Track major institutional position changes from 13F filings</p>
      </div>
    </div>

    <!-- Summary Cards -->
    <div v-if="!loading && summary" class="summary-cards">
      <div class="summary-card">
        <div class="card-icon">🚨</div>
        <div class="card-content">
          <div class="card-value">{{ summary.high_severity_unread }}</div>
          <div class="card-label">High Severity Alerts</div>
        </div>
      </div>
      <div class="summary-card">
        <div class="card-icon">📊</div>
        <div class="card-content">
          <div class="card-value">{{ summary.unread_alerts }}</div>
          <div class="card-label">Unread Alerts</div>
        </div>
      </div>
      <div class="summary-card">
        <div class="card-icon">🐋</div>
        <div class="card-content">
          <div class="card-value">{{ summary.whale_position_changes }}</div>
          <div class="card-label">Whale Moves</div>
        </div>
      </div>
      <div class="summary-card">
        <div class="card-icon">📈</div>
        <div class="card-content">
          <div class="card-value">{{ summary.total_position_changes }}</div>
          <div class="card-label">Total Changes</div>
        </div>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters-section">
      <div class="filter-group">
        <label>Ticker:</label>
        <input v-model="filters.ticker" type="text" placeholder="e.g., AAPL" @input="fetchAlerts" />
      </div>
      <div class="filter-group">
        <label>Severity:</label>
        <select v-model="filters.severity" @change="fetchAlerts">
          <option value="">All</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>
      </div>
      <div class="filter-group">
        <label>Change Type:</label>
        <select v-model="filters.changeType" @change="fetchAlerts">
          <option value="">All</option>
          <option value="NEW">New Position</option>
          <option value="CLOSED">Closed Position</option>
          <option value="INCREASED">Increased</option>
          <option value="DECREASED">Decreased</option>
        </select>
      </div>
      <div class="filter-group">
        <label>
          <input type="checkbox" v-model="filters.whalesOnly" @change="fetchAlerts" />
          Whales Only (Top 50)
        </label>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Loading whale watching data...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-message">
      <p>{{ error }}</p>
    </div>

    <!-- Alerts List -->
    <div v-else-if="alerts && alerts.length > 0" class="alerts-container">
      <h2>Recent Whale Alerts</h2>
      <div class="alerts-list">
        <div 
          v-for="alert in alerts" 
          :key="alert.id" 
          class="alert-card"
          :class="[`severity-${alert.severity.toLowerCase()}`, { 'unread': !alert.is_read }]"
        >
          <div class="alert-header">
            <div class="alert-badge" :class="`badge-${alert.severity.toLowerCase()}`">
              {{ alert.severity }}
            </div>
            <div class="alert-type">{{ formatAlertType(alert.alert_type) }}</div>
            <div class="alert-date">{{ formatDate(alert.created_at) }}</div>
          </div>
          <div class="alert-body">
            <div class="alert-message">{{ alert.message }}</div>
            <div class="alert-details">
              <span class="detail-item">
                <strong>Ticker:</strong> {{ alert.ticker }}
              </span>
              <span class="detail-item">
                <strong>Institution:</strong> {{ alert.institution_name }}
              </span>
              <span class="detail-item" v-if="alert.percent_change">
                <strong>Change:</strong> {{ alert.percent_change.toFixed(1) }}%
              </span>
              <span class="detail-item">
                <strong>Quarter:</strong> {{ alert.quarter }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="empty-state">
      <div class="empty-icon">🔍</div>
      <h3>No Whale Alerts Found</h3>
      <p>No institutional position changes match your current filters.</p>
    </div>
  </div>
</template>

<script setup>
import API_BASE_URL from '@/config/api.js'

import { ref, onMounted } from 'vue'

const loading = ref(true)
const error = ref(null)
const alerts = ref([])
const summary = ref(null)

const filters = ref({
  ticker: '',
  severity: '',
  changeType: '',
  whalesOnly: true
})

const formatAlertType = (type) => {
  const types = {
    'WHALE_NEW': '🆕 New Position',
    'WHALE_EXIT': '🚪 Position Exit',
    'WHALE_INCREASE': '📈 Position Increased',
    'WHALE_DECREASE': '📉 Position Decreased'
  }
  return types[type] || type
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric', 
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const fetchSummary = async () => {
  try {
    const token = localStorage.getItem('access_token')
    if (!token) {
      error.value = 'Please login to view whale watching data'
      loading.value = false
      return
    }

    const response = await fetch(`${API_BASE_URL}/api/whale-watching/summary`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (response.ok) {
      summary.value = await response.json()
    } else if (response.status === 401) {
      error.value = 'Please login to view whale watching data'
    } else {
      error.value = 'Failed to load summary data'
    }
  } catch (err) {
    console.error('Error fetching summary:', err)
    error.value = err.message || 'Failed to load summary data'
  }
}

const fetchAlerts = async () => {
  try {
    loading.value = true
    error.value = null

    const token = localStorage.getItem('access_token')
    if (!token) {
      error.value = 'Please login to view whale watching data'
      loading.value = false
      return
    }

    // Build query params
    const params = new URLSearchParams()
    if (filters.value.ticker) params.append('ticker', filters.value.ticker.toUpperCase())
    if (filters.value.severity) params.append('severity', filters.value.severity)
    params.append('limit', '50')

    const url = `${API_BASE_URL}/api/whale-watching/alerts?${params.toString()}`
    
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (response.ok) {
      alerts.value = await response.json()
    } else if (response.status === 401) {
      error.value = 'Please login to view whale watching data'
    } else {
      error.value = 'Failed to load whale alerts'
    }
  } catch (err) {
    console.error('Error fetching whale alerts:', err)
    error.value = err.message || 'Failed to load whale alerts'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await fetchSummary()
  await fetchAlerts()
})
</script>

<style scoped>
.whale-watching-view {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 32px;
}

.page-header h1 {
  font-size: 32px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 8px 0;
}

.subtitle {
  font-size: 16px;
  color: #666;
  margin: 0;
}

/* Summary Cards */
.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.summary-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.card-icon {
  font-size: 36px;
}

.card-content {
  flex: 1;
}

.card-value {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 4px;
}

.card-label {
  font-size: 14px;
  opacity: 0.9;
}

/* Filters */
.filters-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-group label {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.filter-group input[type="text"],
.filter-group select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  min-width: 150px;
}

.filter-group input[type="checkbox"] {
  margin-right: 8px;
}

/* Alerts */
.alerts-container h2 {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 20px;
}

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.alert-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border-left: 4px solid #ddd;
  transition: all 0.2s;
}

.alert-card.unread {
  background: #f8f9ff;
  border-left-color: #667eea;
}

.alert-card.severity-high {
  border-left-color: #ef4444;
}

.alert-card.severity-medium {
  border-left-color: #f59e0b;
}

.alert-card.severity-low {
  border-left-color: #10b981;
}

.alert-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.alert-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.alert-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.badge-high {
  background: #fee2e2;
  color: #dc2626;
}

.badge-medium {
  background: #fef3c7;
  color: #d97706;
}

.badge-low {
  background: #d1fae5;
  color: #059669;
}

.alert-type {
  font-weight: 600;
  color: #333;
  flex: 1;
}

.alert-date {
  font-size: 13px;
  color: #666;
}

.alert-message {
  font-size: 16px;
  color: #1a1a1a;
  margin-bottom: 12px;
  line-height: 1.5;
}

.alert-details {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 14px;
}

.detail-item {
  color: #666;
}

.detail-item strong {
  color: #333;
  margin-right: 4px;
}

/* Loading */
.loading {
  text-align: center;
  padding: 60px 20px;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Error */
.error-message {
  background: #fee2e2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 16px;
  color: #dc2626;
  text-align: center;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 20px;
  color: #333;
  margin-bottom: 8px;
}

.empty-state p {
  color: #666;
  font-size: 14px;
}
</style>
