<template>
  <div class="short-interest-view">
    <div class="page-header">
      <h1>Short Interest</h1>
    </div>

    <div class="category-tabs">
      <button 
        v-for="category in categories" 
        :key="category.value" 
        :class="{ active: activeCategory === category.value }"
        @click="activeCategory = category.value; currentPage = 1; fetchData(1)"
      >
        {{ category.label }}
      </button>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>Loading short interest data...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p class="error-message">{{ error }}</p>
      <button @click="fetchData" class="retry-btn">Retry</button>
    </div>

    <div v-else class="content-section">
      <div class="table-container">
        <table class="short-interest-table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Current Short Int.</th>
              <th>Previous Short Int.</th>
              <th>Short Int. Change</th>
              <th>Short Int. % Change</th>
              <th>Days to Cover</th>
              <th>Shares Short Value</th>
              <th>Avg Daily Volume</th>
              <th>Market Cap</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in tableData" :key="index">
              <td class="symbol-cell">
                <strong>{{ row.symbol }}</strong>
              </td>
              <td>{{ formatPercentage(row.current_short_int) }}</td>
              <td>{{ formatPercentage(row.previous_short_int) }}</td>
              <td>{{ formatNumber(row.short_int_change) }}</td>
              <td :class="getChangeClass(row.short_int_pct_change)">
                {{ formatPercentage(row.short_int_pct_change) }}
              </td>
              <td>{{ formatNumber(row.days_to_cover) }}</td>
              <td>{{ row.shares_short_value || '-' }}</td>
              <td>{{ row.avg_daily_volume || '-' }}</td>
              <td>{{ row.market_cap || '-' }}</td>
            </tr>
            <tr v-if="tableData.length === 0">
              <td colspan="9" class="no-data">No data available</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination Controls -->
      <div v-if="totalPages > 1" class="pagination-container">
        <div class="pagination">
          <button 
            @click="goToPage(currentPage - 1)" 
            :disabled="currentPage === 1"
            class="pagination-btn"
          >
            &lt;
          </button>
          
          <template v-for="pageNum in visiblePages" :key="pageNum">
            <button
              v-if="pageNum !== '...'"
              @click="goToPage(pageNum)"
              :class="{ active: currentPage === pageNum }"
              class="pagination-btn page-number"
            >
              {{ pageNum }}
            </button>
            <span v-else class="pagination-ellipsis">...</span>
          </template>
          
          <button 
            @click="goToPage(currentPage + 1)" 
            :disabled="currentPage === totalPages"
            class="pagination-btn"
          >
            &gt;
          </button>
        </div>
        
        <div class="pagination-info">
          <span>100 / page</span>
        </div>
      </div>

      <div v-if="updatedAt" class="data-footer">
        <p class="update-time">Last updated: {{ formatDate(updatedAt) }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'

const activeCategory = ref('most-shorted')
const loading = ref(false)
const error = ref(null)
const tableData = ref([])
const updatedAt = ref(null)
const currentPage = ref(1)
const totalPages = ref(20) // Maximum 20 pages as per backend
const itemsPerPage = 100

const categories = [
  { label: 'Most Shorted', value: 'most-shorted' },
  { label: 'Largest Increase', value: 'largest-increase' },
  { label: 'Largest Decrease', value: 'largest-decrease' }
]

const fetchData = async (page = null) => {
  loading.value = true
  error.value = null
  
  try {
    const token = localStorage.getItem('access_token')
    if (!token) {
      error.value = 'Please login to view short interest data'
      loading.value = false
      return
    }

    let endpoint = ''
    switch (activeCategory.value) {
      case 'most-shorted':
        endpoint = '/api/short-interest/most-shorted'
        break
      case 'largest-increase':
        endpoint = '/api/short-interest/largest-increase'
        break
      case 'largest-decrease':
        endpoint = '/api/short-interest/largest-decrease'
        break
      default:
        endpoint = '/api/short-interest/most-shorted'
    }

    // Add page parameter if specified
    const pageToFetch = page !== null ? page : currentPage.value
    const url = pageToFetch ? `${endpoint}?page=${pageToFetch}` : endpoint

    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch data' }))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }

    const data = await response.json()
    tableData.value = data.data || []
    updatedAt.value = data.updated_at || null
    
    // If we got less than itemsPerPage, we've reached the last page
    if (tableData.value.length < itemsPerPage && pageToFetch < totalPages.value) {
      totalPages.value = pageToFetch
    }
  } catch (err) {
    console.error('Error fetching short interest data:', err)
    error.value = err.message || 'Failed to load short interest data'
    tableData.value = []
  } finally {
    loading.value = false
  }
}

const goToPage = (page) => {
  if (page < 1 || page > totalPages.value || page === currentPage.value) {
    return
  }
  currentPage.value = page
  fetchData(page)
}

const visiblePages = computed(() => {
  const pages = []
  const maxVisible = 7 // Show up to 7 page numbers
  
  if (totalPages.value <= maxVisible) {
    // Show all pages if total is less than max visible
    for (let i = 1; i <= totalPages.value; i++) {
      pages.push(i)
    }
  } else {
    // Show first page
    pages.push(1)
    
    if (currentPage.value <= 3) {
      // Near the beginning
      for (let i = 2; i <= 5; i++) {
        pages.push(i)
      }
      pages.push('...')
      pages.push(totalPages.value)
    } else if (currentPage.value >= totalPages.value - 2) {
      // Near the end
      pages.push('...')
      for (let i = totalPages.value - 4; i <= totalPages.value; i++) {
        pages.push(i)
      }
    } else {
      // In the middle
      pages.push('...')
      for (let i = currentPage.value - 1; i <= currentPage.value + 1; i++) {
        pages.push(i)
      }
      pages.push('...')
      pages.push(totalPages.value)
    }
  }
  
  return pages
})

const formatPercentage = (value) => {
  if (value === null || value === undefined) return '-'
  return `${value.toFixed(2)}%`
}

const formatNumber = (value) => {
  if (value === null || value === undefined) return '-'
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(2)}M`
  } else if (value >= 1000) {
    return `${(value / 1000).toFixed(2)}K`
  }
  return value.toFixed(2)
}

const getChangeClass = (value) => {
  if (value === null || value === undefined) return ''
  if (value > 0) return 'positive-change'
  if (value < 0) return 'negative-change'
  return ''
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  try {
    const date = new Date(dateString)
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (e) {
    return dateString
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.short-interest-view {
  min-height: 100vh;
  padding: 2rem;
  background: #ffffff;
  color: #000000;
}

.page-header {
  margin-bottom: 2rem;
}

.page-header h1 {
  font-size: 2rem;
  font-weight: 700;
  color: #000000;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #666666;
  font-size: 1rem;
  margin-bottom: 1.5rem;
}

.category-tabs {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  border-bottom: 2px solid #e5e5e5;
}

.category-tabs button {
  padding: 0.75rem 1.5rem;
  background: transparent;
  border: none;
  border-bottom: 3px solid transparent;
  color: #666666;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: -2px;
}

.category-tabs button:hover {
  color: #000000;
  background: rgba(0, 0, 0, 0.02);
}

.category-tabs button.active {
  color: #3498db;
  border-bottom-color: #3498db;
  font-weight: 600;
}

.content-section {
  background: #ffffff;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
  padding: 1.5rem;
  overflow-x: auto;
}

.table-container {
  overflow-x: auto;
  overflow-y: auto;
  max-height: 600px;
  width: 100%;
  position: relative;
}

.short-interest-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.short-interest-table thead {
  background-color: #f8f9fa;
  border-bottom: 2px solid #e5e5e5;
  position: sticky;
  top: 0;
  z-index: 10;
}

.short-interest-table th {
  padding: 1rem 0.75rem;
  text-align: left;
  font-weight: 600;
  color: #000000;
  white-space: nowrap;
  border-right: 1px solid #e5e5e5;
}

.short-interest-table th:last-child {
  border-right: none;
}

.short-interest-table tbody tr {
  border-bottom: 1px solid #e5e5e5;
  transition: background-color 0.15s ease;
}

.short-interest-table tbody tr:hover {
  background-color: #f8f9fa;
}

.short-interest-table td {
  padding: 0.875rem 0.75rem;
  color: #000000;
  border-right: 1px solid #e5e5e5;
  white-space: nowrap;
}

.short-interest-table td:last-child {
  border-right: none;
}

.symbol-cell {
  font-weight: 600;
}

.positive-change {
  color: #e74c3c;
  font-weight: 500;
}

.negative-change {
  color: #27ae60;
  font-weight: 500;
}

.no-data {
  text-align: center;
  padding: 2rem;
  color: #666666;
  font-style: italic;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  color: #666666;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e5e5e5;
  border-top-color: #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-state {
  text-align: center;
  padding: 3rem 2rem;
  color: #e74c3c;
}

.error-message {
  font-size: 1.1rem;
  margin-bottom: 1rem;
}

.retry-btn {
  padding: 0.75rem 1.5rem;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.retry-btn:hover {
  background: #2980b9;
}

.data-footer {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e5e5e5;
  text-align: center;
  color: #666666;
  font-size: 0.9rem;
}

.data-footer p {
  margin: 0.25rem 0;
}

.update-time {
  font-size: 0.85rem;
  color: #999999;
}

.pagination-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e5e5e5;
}

.pagination {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.pagination-btn {
  padding: 0.5rem 0.75rem;
  background: #ffffff;
  border: 1px solid #e5e5e5;
  border-radius: 4px;
  color: #000000;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pagination-btn:hover:not(:disabled) {
  background: #f8f9fa;
  border-color: #3498db;
  color: #3498db;
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination-btn.active {
  background: #3498db;
  border-color: #3498db;
  color: #ffffff;
  font-weight: 600;
}

.pagination-btn.active:hover {
  background: #2980b9;
  border-color: #2980b9;
}

.pagination-ellipsis {
  padding: 0 0.5rem;
  color: #666666;
  font-size: 0.9rem;
}

.pagination-info {
  color: #666666;
  font-size: 0.9rem;
}
</style>
