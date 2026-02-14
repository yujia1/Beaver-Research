<template>
  <div class="flagged-companies-view">

    
    <!-- Filter Panel -->
    <div class="filter-panel">
      <div class="filter-group">
        <label>Strategy Filter</label>
        <select v-model="filters.strategy" @change="fetchFlaggedCompanies">
          <option value="all">All Strategies</option>
          <option value="Cash Flow Sustainability">Cash Flow Sustainability</option>
          <option value="Balance Sheet Stress">Balance Sheet Stress</option>
          <option value="Working Capital Anomalies">Working Capital Anomalies</option>
          <option value="Valuation Dislocation">Valuation Dislocation</option>
        </select>
      </div>
      
      <div class="filter-group">
        <label>Search Ticker</label>
        <input 
          v-model="filters.searchTicker" 
          type="text"
          placeholder="e.g., PLTR"
          @input="onSearchInput"
        />
      </div>
      
      <div class="filter-group">
        <label>Sort By</label>
        <select v-model="sortBy" @change="sortCompanies">
          <option value="red_flags_count">Red Flags Count</option>
          <option value="ticker">Ticker</option>
          <option value="screening_date">Screening Date</option>
        </select>
      </div>
      
      <button @click="fetchFlaggedCompanies" class="refresh-button" :disabled="loading">
        <span v-if="!loading">Refresh</span>
        <span v-else class="loading-spinner"></span>
        Refresh
      </button>
    </div>
    

    
    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner large"></div>
      <p>Loading flagged companies...</p>
    </div>
    
    <!-- Error State -->
    <div v-else-if="error" class="error-alert">
      <span class="error-icon">Error</span>
      <span>{{ error }}</span>
      <button @click="fetchFlaggedCompanies" class="retry-button">Retry</button>
    </div>
    
    <!-- Flagged Companies Table -->
    <div v-else-if="displayedCompanies.length > 0" class="table-container">
      <table class="flagged-table">
        <thead>
          <tr>
            <th @click="setSortBy('ticker')" class="sortable">
              Ticker
              <span v-if="sortBy === 'ticker'" class="sort-indicator">
                {{ sortDesc ? '↓' : '↑' }}
              </span>
            </th>
            <th>Company Name</th>
            <th @click="setSortBy('red_flags_count')" class="sortable">
              Red Flags
              <span v-if="sortBy === 'red_flags_count'" class="sort-indicator">
                {{ sortDesc ? '↓' : '↑' }}
              </span>
            </th>
            <th>Strategies Flagged</th>
            <th @click="setSortBy('screening_date')" class="sortable">
              Screening Date
              <span v-if="sortBy === 'screening_date'" class="sort-indicator">
                {{ sortDesc ? '↓' : '↑' }}
              </span>
            </th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="company in displayedCompanies" 
            :key="company.id"
            class="company-row"
          >
            <td class="ticker-cell">
              <button @click="openDetailModal(company)" class="ticker-button">
                {{ company.ticker }}
              </button>
            </td>
            <td class="company-name">{{ company.company_name || 'N/A' }}</td>
            <td class="red-flags-cell">
              <span class="red-flags-badge">
                {{ company.red_flags?.length || 0 }}
              </span>
            </td>
            <td class="strategies-cell">
              <div class="strategy-chips">
                <span 
                  v-for="strategy in company.strategies_flagged" 
                  :key="strategy"
                  class="strategy-chip"
                >
                  {{ strategy }}
                </span>
              </div>
            </td>
            <td class="date-cell">
              {{ formatDate(company.screening_date) }}
            </td>
            <td class="actions-cell">
              <button @click="openDetailModal(company)" class="action-button">
                View Details
              </button>
              <button @click="exportCompany(company)" class="action-button secondary">
                Export
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      
      <!-- Pagination -->
      <div class="pagination">
        <button 
          @click="previousPage" 
          :disabled="page === 1"
          class="page-button"
        >
          ← Previous
        </button>
        <span class="page-info">
          Page {{ page }} of {{ totalPages }}
        </span>
        <button 
          @click="nextPage" 
          :disabled="page >= totalPages"
          class="page-button"
        >
          Next →
        </button>
      </div>
    </div>
    
    <!-- Empty State -->
    <div v-else class="empty-state">
      <!-- <div class="empty-icon">📭</div> -->
      <h3>No Flagged Companies</h3>
      <p>No companies match your current filters</p>
      <button @click="resetFilters" class="reset-button">Reset Filters</button>
    </div>
    
    <!-- Detail Modal -->
    <div v-if="showDetailModal" class="modal-overlay" @click="closeDetailModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>{{ selectedCompany?.ticker }} - Detailed Metrics</h2>
          <button @click="closeDetailModal" class="close-button">×</button>
        </div>
        
        <div class="modal-body">
          <!-- Company Info -->
          <div class="company-info">
            <h3>{{ selectedCompany?.company_name || selectedCompany?.ticker }}</h3>
            <p>Screened on: {{ formatDate(selectedCompany?.screening_date) }}</p>
          </div>
          
          <!-- Red Flags Summary -->
          <div class="modal-section">
            <h4>Red Flags ({{ selectedCompany?.red_flags?.length || 0 }})</h4>
            <div class="red-flags-list">
              <div 
                v-for="(flag, index) in selectedCompany?.red_flags" 
                :key="index"
                class="flag-item"
              >
                <RedFlagBadge :reason="flag.reason" />
                <span class="flag-metric">{{ flag.metric }}</span>
              </div>
            </div>
          </div>
          
          <!-- Strategies Flagged -->
          <div class="modal-section">
            <h4>Strategies Flagged</h4>
            <div class="strategy-chips">
              <span 
                v-for="strategy in selectedCompany?.strategies_flagged" 
                :key="strategy"
                class="strategy-chip large"
              >
                {{ strategy }}
              </span>
            </div>
          </div>
          
          <!-- Metrics Table -->
          <div class="modal-section">
            <h4>All Metrics</h4>
            <ScreenerMetricsTable 
              v-if="selectedCompany?.metrics"
              :metrics="selectedCompany.metrics"
              :show-trend="false"
            />
          </div>
        </div>
        
        <div class="modal-footer">
          <button @click="exportCompany(selectedCompany)" class="export-button">
            Export to PDF
          </button>
          <button @click="closeDetailModal" class="close-modal-button">
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import ScreenerMetricsTable from '@/components/quant/ScreenerMetricsTable.vue'
import RedFlagBadge from '@/components/quant/RedFlagBadge.vue'

export default {
  name: 'FlaggedCompaniesView',
  components: {
    ScreenerMetricsTable,
    RedFlagBadge
  },
  data() {
    return {
      flaggedCompanies: [],
      filters: {
        strategy: 'all',
        searchTicker: ''
      },
      sortBy: 'red_flags_count',
      sortDesc: true,
      page: 1,
      limit: 50,
      totalCount: 0,
      loading: false,
      error: null,
      
      // Modal
      selectedCompany: null,
      showDetailModal: false,
      
      // Debounce timer
      searchTimer: null
    }
  },
  computed: {
    filteredCompanies() {
      let companies = [...this.flaggedCompanies]
      
      // Filter by strategy
      if (this.filters.strategy !== 'all') {
        companies = companies.filter(c => 
          c.strategies_flagged?.includes(this.filters.strategy)
        )
      }
      
      // Filter by ticker search
      if (this.filters.searchTicker) {
        const search = this.filters.searchTicker.toLowerCase()
        companies = companies.filter(c => 
          c.ticker.toLowerCase().includes(search)
        )
      }
      
      return companies
    },
    
    sortedCompanies() {
      const companies = [...this.filteredCompanies]
      
      companies.sort((a, b) => {
        let aVal, bVal
        
        switch (this.sortBy) {
          case 'red_flags_count':
            aVal = a.red_flags?.length || 0
            bVal = b.red_flags?.length || 0
            break
          case 'ticker':
            aVal = a.ticker
            bVal = b.ticker
            break
          case 'screening_date':
            aVal = new Date(a.screening_date)
            bVal = new Date(b.screening_date)
            break
          default:
            return 0
        }
        
        if (aVal < bVal) return this.sortDesc ? 1 : -1
        if (aVal > bVal) return this.sortDesc ? -1 : 1
        return 0
      })
      
      return companies
    },
    
    displayedCompanies() {
      const start = (this.page - 1) * this.limit
      const end = start + this.limit
      return this.sortedCompanies.slice(start, end)
    },
    
    filteredCount() {
      return this.filteredCompanies.length
    },
    
    totalPages() {
      return Math.ceil(this.filteredCount / this.limit)
    },
    
    averageRedFlags() {
      if (this.filteredCompanies.length === 0) return 0
      const total = this.filteredCompanies.reduce((sum, c) => sum + (c.red_flags?.length || 0), 0)
      return (total / this.filteredCompanies.length).toFixed(1)
    }
  },
  mounted() {
    this.fetchFlaggedCompanies()
  },
  methods: {
    async fetchFlaggedCompanies() {
      this.loading = true
      this.error = null
      
      try {
        const params = {}
        
        if (this.filters.strategy !== 'all') {
          params.strategy = this.filters.strategy
        }
        
        const response = await axios.get('/api/quant/screener/flagged', { params })
        this.flaggedCompanies = response.data
        this.totalCount = response.data.length
        this.page = 1 // Reset to first page
      } catch (err) {
        console.error('Error fetching flagged companies:', err)
        this.error = err.response?.data?.detail || err.message || 'Failed to fetch flagged companies'
      } finally {
        this.loading = false
      }
    },
    
    onSearchInput() {
      // Debounce search
      clearTimeout(this.searchTimer)
      this.searchTimer = setTimeout(() => {
        this.page = 1
      }, 300)
    },
    
    setSortBy(field) {
      if (this.sortBy === field) {
        this.sortDesc = !this.sortDesc
      } else {
        this.sortBy = field
        this.sortDesc = true
      }
    },
    
    sortCompanies() {
      this.page = 1
    },
    
    previousPage() {
      if (this.page > 1) {
        this.page--
        window.scrollTo({ top: 0, behavior: 'smooth' })
      }
    },
    
    nextPage() {
      if (this.page < this.totalPages) {
        this.page++
        window.scrollTo({ top: 0, behavior: 'smooth' })
      }
    },
    
    resetFilters() {
      this.filters.strategy = 'all'
      this.filters.searchTicker = ''
      this.page = 1
    },
    
    openDetailModal(company) {
      this.selectedCompany = company
      this.showDetailModal = true
      document.body.style.overflow = 'hidden'
    },
    
    closeDetailModal() {
      this.showDetailModal = false
      this.selectedCompany = null
      document.body.style.overflow = 'auto'
    },
    
    exportCompany(company) {
      // Export to CSV/PDF
      console.log('Exporting company:', company.ticker)
      
      // Simple CSV export
      const csv = [
        ['Metric', 'Value', 'Red Flag', 'Reason'],
        ...Object.entries(company.metrics || {}).map(([key, metric]) => [
          metric.name,
          metric.latest_value,
          metric.is_red_flag ? 'Yes' : 'No',
          metric.red_flag_reason || ''
        ])
      ].map(row => row.join(',')).join('\n')
      
      const blob = new Blob([csv], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${company.ticker}_metrics.csv`
      a.click()
      window.URL.revokeObjectURL(url)
    },
    
    formatDate(dateString) {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }
  }
}
</script>

<style scoped>
.flagged-companies-view {
  max-width: 1600px;
  margin: 0 auto;
  padding: 2rem;
}

/* Header */


/* Filter Panel */
.filter-panel {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  align-items: end;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-group label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

.filter-group select,
.filter-group input {
  padding: 0.75rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.filter-group select:focus,
.filter-group input:focus {
  outline: none;
  border-color: #ef4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
}

.refresh-button {
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.refresh-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
}

.refresh-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}



/* Loading & Error States */
.loading-state {
  text-align: center;
  padding: 4rem 2rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
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
  border-top-color: #ef4444;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-alert {
  background-color: #fef2f2;
  border-left: 4px solid #ef4444;
  padding: 1.5rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.error-icon {
  font-size: 1.5rem;
}

.retry-button {
  margin-left: auto;
  padding: 0.5rem 1rem;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

/* Table */
.table-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.flagged-table {
  width: 100%;
  border-collapse: collapse;
}

.flagged-table thead {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
}

.flagged-table th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.flagged-table th.sortable {
  cursor: pointer;
  user-select: none;
}

.flagged-table th.sortable:hover {
  background: rgba(255, 255, 255, 0.1);
}

.sort-indicator {
  margin-left: 0.25rem;
}

.flagged-table tbody tr {
  border-bottom: 1px solid #e5e7eb;
  transition: background-color 0.2s;
}

.flagged-table tbody tr:hover {
  background-color: #f9fafb;
}

.flagged-table td {
  padding: 1rem;
  font-size: 0.875rem;
}

.ticker-button {
  background: none;
  border: none;
  color: #667eea;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  text-decoration: underline;
}

.ticker-button:hover {
  color: #764ba2;
}

.company-name {
  color: #6b7280;
}

.red-flags-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  height: 32px;
  padding: 0 0.75rem;
  background: #fef2f2;
  color: #dc2626;
  border-radius: 9999px;
  font-weight: 700;
}

.strategy-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.strategy-chip {
  padding: 0.25rem 0.75rem;
  background: #fef2f2;
  color: #dc2626;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
  white-space: nowrap;
}

.strategy-chip.large {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
}

.date-cell {
  color: #6b7280;
  font-size: 0.8125rem;
}

.actions-cell {
  display: flex;
  gap: 0.5rem;
}

.action-button {
  padding: 0.5rem 1rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.action-button:hover {
  background: #764ba2;
}

.action-button.secondary {
  background: #e5e7eb;
  color: #374151;
}

.action-button.secondary:hover {
  background: #d1d5db;
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  background: #f9fafb;
}

.page-button {
  padding: 0.5rem 1rem;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.page-button:hover:not(:disabled) {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.page-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: #6b7280;
  font-weight: 500;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-state h3 {
  font-size: 1.5rem;
  color: #374151;
  margin-bottom: 0.5rem;
}

.empty-state p {
  color: #6b7280;
  margin-bottom: 2rem;
}

.reset-button {
  padding: 0.75rem 1.5rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.reset-button:hover {
  background: #764ba2;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 2rem;
}

.modal-content {
  background: white;
  border-radius: 12px;
  max-width: 900px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #374151;
}

.close-button {
  background: none;
  border: none;
  font-size: 2rem;
  color: #6b7280;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  line-height: 1;
}

.close-button:hover {
  color: #374151;
}

.modal-body {
  padding: 2rem;
}

.company-info {
  margin-bottom: 2rem;
}

.company-info h3 {
  font-size: 1.25rem;
  color: #374151;
  margin-bottom: 0.5rem;
}

.company-info p {
  color: #6b7280;
}

.modal-section {
  margin-bottom: 2rem;
}

.modal-section h4 {
  font-size: 1.125rem;
  color: #374151;
  margin-bottom: 1rem;
}

.red-flags-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.flag-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  background: #fef2f2;
  border-radius: 8px;
}

.flag-metric {
  font-weight: 500;
  color: #374151;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem 2rem;
  border-top: 1px solid #e5e7eb;
}

.export-button,
.close-modal-button {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.export-button {
  background: #667eea;
  color: white;
}

.export-button:hover {
  background: #764ba2;
}

.close-modal-button {
  background: #e5e7eb;
  color: #374151;
}

.close-modal-button:hover {
  background: #d1d5db;
}

/* Responsive */
@media (max-width: 768px) {
  .flagged-companies-view {
    padding: 1rem;
  }
  
  .filter-panel {
    grid-template-columns: 1fr;
  }
  
  .flagged-table {
    font-size: 0.75rem;
  }
  
  .flagged-table th,
  .flagged-table td {
    padding: 0.75rem 0.5rem;
  }
  
  .actions-cell {
    flex-direction: column;
  }
  
  .modal-overlay {
    padding: 1rem;
  }
}
</style>
