<template>
  <div class="batch-screening-view">
    <!-- Header -->
    <div class="header">
      <h1>⚙️ Batch Screening Control</h1>
      <p>Admin interface for batch screening the entire U.S. market</p>
    </div>
    
    <!-- Control Panel -->
    <div class="control-panel">
      <h3>🚀 Start New Batch Screening</h3>
      
      <div class="config-grid">
        <div class="config-item">
          <label>Limit (for testing)</label>
          <input 
            v-model.number="config.limit" 
            type="number"
            placeholder="Leave empty for all stocks"
            :disabled="isRunning"
          />
          <span class="help-text">Leave empty to screen all stocks (~5000)</span>
        </div>
        
        <div class="config-item">
          <label>Batch Size</label>
          <input 
            v-model.number="config.batchSize" 
            type="number"
            min="1"
            max="10"
            :disabled="isRunning"
          />
          <span class="help-text">Stocks per batch (default: 5)</span>
        </div>
        
        <div class="config-item">
          <label>Delay (seconds)</label>
          <input 
            v-model.number="config.delaySeconds" 
            type="number"
            min="30"
            max="300"
            :disabled="isRunning"
          />
          <span class="help-text">Delay between batches (default: 60s)</span>
        </div>
        
        <div class="config-item checkbox">
          <label>
            <input 
              v-model="config.enablePeerComparison" 
              type="checkbox"
              :disabled="isRunning"
            />
            <span>Enable Peer Comparison</span>
          </label>
          <span class="help-text warning">⚠️ Not recommended for full market (very slow)</span>
        </div>
      </div>
      
      <div class="control-buttons">
        <button 
          @click="startBatchScreening" 
          :disabled="starting || isRunning"
          class="start-button"
        >
          <span v-if="starting" class="loading-spinner"></span>
          {{ starting ? 'Starting...' : 'Start Batch Screening' }}
        </button>
        
        <button 
          @click="updateStockUniverse" 
          :disabled="updatingUniverse || isRunning"
          class="update-button"
        >
          <span v-if="updatingUniverse" class="loading-spinner"></span>
          {{ updatingUniverse ? 'Updating...' : 'Update Stock Universe' }}
        </button>
      </div>
      
      <div v-if="universeCount" class="universe-info">
        📊 Stock Universe: <strong>{{ universeCount.toLocaleString() }}</strong> stocks
      </div>
    </div>
    
    <!-- Active Run Monitor -->
    <div v-if="batchStatus" class="active-run-monitor">
      <div class="monitor-header">
        <h3>📊 Active Screening Run #{{ batchStatus.run_id }}</h3>
        <span class="status-badge" :class="batchStatus.status">
          {{ batchStatus.status }}
        </span>
      </div>
      
      <!-- Progress Bar -->
      <div class="progress-section">
        <div class="progress-bar-container">
          <div 
            class="progress-bar" 
            :style="{ width: progressPercent + '%' }"
            :class="{ complete: batchStatus.status === 'completed' }"
          ></div>
        </div>
        <div class="progress-text">
          {{ progressPercent }}% Complete
        </div>
      </div>
      
      <!-- Stats Grid -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon">📈</div>
          <div class="stat-value">{{ batchStatus.total_stocks || 0 }}</div>
          <div class="stat-label">Total Stocks</div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon">✅</div>
          <div class="stat-value">{{ batchStatus.processed || 0 }}</div>
          <div class="stat-label">Processed</div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon">🚩</div>
          <div class="stat-value">{{ batchStatus.flagged || 0 }}</div>
          <div class="stat-label">Flagged</div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon">⏱️</div>
          <div class="stat-value">{{ estimatedTimeRemaining }}</div>
          <div class="stat-label">Est. Time Remaining</div>
        </div>
      </div>
      
      <!-- Action Buttons -->
      <div v-if="isRunning" class="run-actions">
        <button @click="refreshStatus" class="refresh-status-button">
          🔄 Refresh Status
        </button>
      </div>
      
      <!-- Completion Message -->
      <div v-if="batchStatus.status === 'completed'" class="completion-message">
        <span class="check-icon">✓</span>
        <span>Batch screening completed successfully!</span>
        <button @click="viewFlaggedCompanies" class="view-results-button">
          View Flagged Companies →
        </button>
      </div>
      
      <!-- Error Message -->
      <div v-if="batchStatus.status === 'failed'" class="error-message">
        <span class="error-icon">⚠️</span>
        <span>Batch screening failed</span>
        <p v-if="batchStatus.error_log">{{ batchStatus.error_log }}</p>
      </div>
    </div>
    
    <!-- Screening Run History -->
    <div class="run-history">
      <div class="history-header">
        <h3>📜 Screening Run History</h3>
        <button @click="fetchRunHistory" class="refresh-history-button">
          🔄 Refresh
        </button>
      </div>
      
      <div v-if="loadingHistory" class="loading-state">
        <div class="loading-spinner large"></div>
        <p>Loading history...</p>
      </div>
      
      <div v-else-if="runHistory.length > 0" class="history-table-container">
        <table class="history-table">
          <thead>
            <tr>
              <th>Run ID</th>
              <th>Start Time</th>
              <th>Duration</th>
              <th>Processed</th>
              <th>Flagged</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="run in runHistory" :key="run.id">
              <td class="run-id">#{{ run.id }}</td>
              <td>{{ formatDateTime(run.run_date) }}</td>
              <td>{{ formatDuration(run.duration_seconds) }}</td>
              <td>{{ run.total_stocks_processed || 0 }}</td>
              <td>
                <span class="flagged-badge">{{ run.total_flagged || 0 }}</span>
              </td>
              <td>
                <span class="status-badge" :class="run.status">
                  {{ run.status }}
                </span>
              </td>
              <td>
                <button 
                  @click="viewRunDetails(run)" 
                  class="action-button"
                >
                  View Details
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <div v-else class="empty-history">
        <p>No screening runs yet</p>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'BatchScreeningView',
  data() {
    return {
      // Configuration
      config: {
        limit: null,
        batchSize: 5,
        delaySeconds: 60,
        enablePeerComparison: false
      },
      
      // Active run
      activeRunId: null,
      batchStatus: null,
      pollInterval: null,
      
      // History
      runHistory: [],
      
      // Loading states
      starting: false,
      updatingUniverse: false,
      loadingHistory: false,
      
      // Stock universe
      universeCount: null
    }
  },
  computed: {
    isRunning() {
      return this.batchStatus?.status === 'running'
    },
    
    progressPercent() {
      if (!this.batchStatus || !this.batchStatus.total_stocks) return 0
      const percent = (this.batchStatus.processed / this.batchStatus.total_stocks) * 100
      return Math.min(Math.round(percent), 100)
    },
    
    estimatedTimeRemaining() {
      if (!this.batchStatus || !this.isRunning) return 'N/A'
      
      const processed = this.batchStatus.processed || 0
      const total = this.batchStatus.total_stocks || 0
      const remaining = total - processed
      
      if (remaining <= 0) return '0m'
      
      // Estimate based on batch size and delay
      const batchesRemaining = Math.ceil(remaining / this.config.batchSize)
      const secondsRemaining = batchesRemaining * this.config.delaySeconds
      
      const hours = Math.floor(secondsRemaining / 3600)
      const minutes = Math.floor((secondsRemaining % 3600) / 60)
      
      if (hours > 0) {
        return `${hours}h ${minutes}m`
      }
      return `${minutes}m`
    }
  },
  mounted() {
    this.fetchRunHistory()
    this.fetchUniverseCount()
    this.startPolling()
  },
  beforeUnmount() {
    this.stopPolling()
  },
  methods: {
    async startBatchScreening() {
      this.starting = true
      
      try {
        const payload = {
          batch_size: this.config.batchSize,
          delay_seconds: this.config.delaySeconds,
          enable_peer_comparison: this.config.enablePeerComparison
        }
        
        if (this.config.limit) {
          payload.limit = this.config.limit
        }
        
        const response = await axios.post('/api/quant/screener/batch-screen', payload)
        
        this.activeRunId = response.data.run_id
        await this.fetchBatchStatus()
        
        // Show success message
        alert(`Batch screening started! Run ID: ${this.activeRunId}`)
      } catch (error) {
        console.error('Error starting batch screening:', error)
        alert(error.response?.data?.detail || 'Failed to start batch screening')
      } finally {
        this.starting = false
      }
    },
    
    async fetchBatchStatus() {
      if (!this.activeRunId) return
      
      try {
        const response = await axios.get(`/api/quant/screener/batch-status/${this.activeRunId}`)
        this.batchStatus = response.data
        
        // If completed or failed, stop polling and refresh history
        if (['completed', 'failed'].includes(this.batchStatus.status)) {
          this.stopPolling()
          this.fetchRunHistory()
        }
      } catch (error) {
        console.error('Error fetching batch status:', error)
      }
    },
    
    async refreshStatus() {
      await this.fetchBatchStatus()
    },
    
    async updateStockUniverse() {
      this.updatingUniverse = true
      
      try {
        const response = await axios.post('/api/quant/screener/update-stock-universe')
        this.universeCount = response.data.count
        alert(`Stock universe updated! Total stocks: ${this.universeCount}`)
      } catch (error) {
        console.error('Error updating stock universe:', error)
        alert(error.response?.data?.detail || 'Failed to update stock universe')
      } finally {
        this.updatingUniverse = false
      }
    },
    
    async fetchRunHistory() {
      this.loadingHistory = true
      
      try {
        // Note: This endpoint doesn't exist yet, would need to be added
        // For now, we'll just show empty or use a mock
        // const response = await axios.get('/api/quant/screener/runs')
        // this.runHistory = response.data
        
        // Mock data for now
        this.runHistory = []
      } catch (error) {
        console.error('Error fetching run history:', error)
      } finally {
        this.loadingHistory = false
      }
    },
    
    async fetchUniverseCount() {
      try {
        const response = await axios.get('/api/quant/screener/stock-universe/count')
        this.universeCount = response.data.count
      } catch (error) {
        console.error('Error fetching universe count:', error)
      }
    },
    
    startPolling() {
      this.pollInterval = setInterval(() => {
        if (this.activeRunId && this.isRunning) {
          this.fetchBatchStatus()
        }
      }, 5000) // Poll every 5 seconds
    },
    
    stopPolling() {
      if (this.pollInterval) {
        clearInterval(this.pollInterval)
        this.pollInterval = null
      }
    },
    
    viewFlaggedCompanies() {
      this.$router.push('/quant/flagged')
    },
    
    viewRunDetails(run) {
      console.log('Viewing run details:', run)
      // Could open a modal or navigate to details page
    },
    
    formatDateTime(dateString) {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    },
    
    formatDuration(seconds) {
      if (!seconds) return 'N/A'
      const hours = Math.floor(seconds / 3600)
      const minutes = Math.floor((seconds % 3600) / 60)
      
      if (hours > 0) {
        return `${hours}h ${minutes}m`
      }
      return `${minutes}m`
    }
  }
}
</script>

<style scoped>
.batch-screening-view {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

/* Header */
.header {
  text-align: center;
  margin-bottom: 2rem;
}

.header h1 {
  font-size: 2.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 0.5rem;
}

.header p {
  color: #6b7280;
  font-size: 1.125rem;
}

/* Control Panel */
.control-panel {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

.control-panel h3 {
  margin: 0 0 1.5rem 0;
  font-size: 1.25rem;
  color: #374151;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.config-item label {
  display: block;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.5rem;
}

.config-item input[type="number"],
.config-item input[type="text"] {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.2s;
}

.config-item input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.config-item input:disabled {
  background: #f3f4f6;
  cursor: not-allowed;
}

.config-item.checkbox label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.config-item.checkbox input[type="checkbox"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.help-text {
  display: block;
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.help-text.warning {
  color: #f59e0b;
  font-weight: 500;
}

.control-buttons {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.start-button,
.update-button {
  flex: 1;
  padding: 1rem 2rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.start-button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.start-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.update-button {
  background: #10b981;
  color: white;
}

.update-button:hover:not(:disabled) {
  background: #059669;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
}

.start-button:disabled,
.update-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

.loading-spinner.large {
  width: 48px;
  height: 48px;
  border: 4px solid #e5e7eb;
  border-top-color: #667eea;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.universe-info {
  text-align: center;
  padding: 1rem;
  background: #f0fdf4;
  border-radius: 8px;
  color: #065f46;
  font-size: 1rem;
}

/* Active Run Monitor */
.active-run-monitor {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

.monitor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.monitor-header h3 {
  margin: 0;
  font-size: 1.5rem;
  color: #374151;
}

.status-badge {
  padding: 0.5rem 1rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.status-badge.running {
  background: #dbeafe;
  color: #1e40af;
}

.status-badge.completed {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.failed {
  background: #fee2e2;
  color: #991b1b;
}

/* Progress Bar */
.progress-section {
  margin-bottom: 2rem;
}

.progress-bar-container {
  width: 100%;
  height: 24px;
  background: #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  transition: width 0.5s ease;
  border-radius: 12px;
}

.progress-bar.complete {
  background: linear-gradient(90deg, #10b981 0%, #059669 100%);
}

.progress-text {
  text-align: center;
  font-weight: 600;
  color: #374151;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: #f9fafb;
  padding: 1.5rem;
  border-radius: 12px;
  text-align: center;
}

.stat-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #374151;
  margin-bottom: 0.5rem;
}

.stat-label {
  color: #6b7280;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Run Actions */
.run-actions {
  display: flex;
  justify-content: center;
  margin-bottom: 1rem;
}

.refresh-status-button {
  padding: 0.75rem 1.5rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-status-button:hover {
  background: #764ba2;
}

/* Completion/Error Messages */
.completion-message,
.error-message {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  border-radius: 8px;
}

.completion-message {
  background: #d1fae5;
  color: #065f46;
}

.error-message {
  background: #fee2e2;
  color: #991b1b;
}

.check-icon {
  font-size: 2rem;
}

.error-icon {
  font-size: 2rem;
}

.view-results-button {
  margin-left: auto;
  padding: 0.75rem 1.5rem;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.view-results-button:hover {
  background: #059669;
}

/* Run History */
.run-history {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.history-header h3 {
  margin: 0;
  font-size: 1.5rem;
  color: #374151;
}

.refresh-history-button {
  padding: 0.5rem 1rem;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.refresh-history-button:hover {
  background: #e5e7eb;
}

.loading-state {
  text-align: center;
  padding: 3rem;
}

.history-table-container {
  overflow-x: auto;
}

.history-table {
  width: 100%;
  border-collapse: collapse;
}

.history-table thead {
  background: #f9fafb;
}

.history-table th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  font-size: 0.875rem;
  color: #374151;
  border-bottom: 2px solid #e5e7eb;
}

.history-table tbody tr {
  border-bottom: 1px solid #e5e7eb;
}

.history-table tbody tr:hover {
  background: #f9fafb;
}

.history-table td {
  padding: 1rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.run-id {
  font-weight: 600;
  color: #374151;
}

.flagged-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  padding: 0.25rem 0.75rem;
  background: #fef2f2;
  color: #dc2626;
  border-radius: 9999px;
  font-weight: 600;
}

.action-button {
  padding: 0.5rem 1rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.action-button:hover {
  background: #764ba2;
}

.empty-history {
  text-align: center;
  padding: 3rem;
  color: #6b7280;
  font-style: italic;
}

/* Responsive */
@media (max-width: 768px) {
  .batch-screening-view {
    padding: 1rem;
  }
  
  .config-grid {
    grid-template-columns: 1fr;
  }
  
  .control-buttons {
    flex-direction: column;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
