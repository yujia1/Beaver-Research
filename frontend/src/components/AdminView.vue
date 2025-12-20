<template>
  <div class="admin-view">
    <div class="admin-header">
      <h1>Admin Panel</h1>
      <p class="subtitle">Manage users and reports</p>
    </div>

    <!-- Tabs -->
    <div class="category-tabs">
      <button 
        :class="{ active: activeTab === 'users' }"
        @click="activeTab = 'users'"
      >
        User Management
      </button>     
      <button 
        :class="{ active: activeTab === 'access' }"
        @click="activeTab = 'access'; loadPermissions()"
      >
        Access Management
      </button>
      <button 
        :class="{ active: activeTab === 'reports' }"
        @click="activeTab = 'reports'"
      >
        Report Management
      </button>
      <button 
        :class="{ active: activeTab === 'batch' }"
        @click="activeTab = 'batch'"
      >
        Batch Management
      </button>
      <button 
        :class="{ active: activeTab === 'health' }"
        @click="activeTab = 'health'"
      >
        Health Management
      </button> 
      <button 
        :class="{ active: activeTab === 'database' }"
        @click="activeTab = 'database'; loadTables()"
      >
        Database Management
      </button>
    </div>

    <!-- User Management Tab -->
    <div v-if="activeTab === 'users'">
      <div v-if="loading" class="loading-container">
        <div class="loading-spinner"></div>
        <p>Loading users...</p>
      </div>

      <div v-else-if="error" class="error-container">
        <p class="error-message">{{ error }}</p>
        <button @click="loadUsers" class="retry-button">Retry</button>
      </div>

      <div v-else class="admin-content">
      <div class="stats-section">
        <div class="stat-card">
          <div class="stat-value">{{ users.length }}</div>
          <div class="stat-label">Total Users</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ paidUsersCount }}</div>
          <div class="stat-label">Paid Users</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ unpaidUsersCount }}</div>
          <div class="stat-label">Unpaid Users</div>
        </div>
      </div>

      <div class="filters-section">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search by username or email..."
          class="search-input"
        />
        <select v-model="roleFilter" class="filter-select">
          <option value="">All Roles</option>
          <option value="admin">Admin</option>
          <option value="creator">Creator</option>
          <option value="contributor">Contributor</option>
          <option value="user">User</option>
        </select>
        <select v-model="paymentFilter" class="filter-select">
          <option value="">All Payment Status</option>
          <option value="paid">Paid</option>
          <option value="unpaid">Unpaid</option>
        </select>
      </div>

      <div class="users-table-container">
        <table class="users-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Username</th>
              <th>Email</th>
              <th>Role</th>
              <th>Payment Status</th>
              <th>Transaction ID</th>
              <th>Payment Date</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in filteredUsers" :key="user.id" class="user-row">
              <td>{{ user.id }}</td>
              <td>{{ user.username }}</td>
              <td>{{ user.email }}</td>
              <td>
                <span :class="['role-badge', `role-${user.role}`]">
                  {{ user.role }}
                </span>
              </td>
              <td>
                <span :class="['payment-badge', user.has_paid ? 'paid' : 'unpaid']">
                  {{ user.has_paid ? '✓ Paid' : '✗ Unpaid' }}
                </span>
              </td>
              <td class="transaction-id">
                {{ user.payment_transaction_id || '-' }}
              </td>
              <td class="payment-date">
                {{ formatDate(user.payment_date) }}
              </td>
              <td class="created-date">
                {{ formatDate(user.created_at) }}
              </td>
              <td class="actions-cell">
                <div class="action-buttons">
                  <button
                    @click="togglePaymentStatus(user)"
                    :class="['action-button', user.has_paid ? 'unverify' : 'verify']"
                    :disabled="updatingUserId === user.id"
                  >
                    {{ updatingUserId === user.id ? 'Updating...' : (user.has_paid ? 'Unverify' : 'Verify Payment') }}
                  </button>
                  <button
                    @click="confirmDelete(user)"
                    class="action-button delete"
                    :disabled="deletingUserId === user.id || isCurrentUser(user)"
                    :title="isCurrentUser(user) ? 'Cannot delete your own account' : 'Delete user'"
                  >
                    {{ deletingUserId === user.id ? 'Deleting...' : 'Delete' }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="filteredUsers.length === 0" class="no-results">
        <p>No users found matching your filters.</p>
      </div>
      </div>
    </div>

    <!-- Health Management Tab -->
    <div v-if="activeTab === 'health'">
      <div class="admin-content">
        <div class="health-section">
          <h2>System Health</h2>
          <p class="subtitle">Monitor system status and services</p>
          
          <div class="health-cards">
            <div class="health-card">
              <h3>Backend API</h3>
              <div class="health-status" :class="backendHealth.status">
                <span class="status-indicator"></span>
                <span>{{ backendHealth.status === 'healthy' ? 'Healthy' : 'Unhealthy' }}</span>
              </div>
              <p v-if="backendHealth.message" class="health-message">{{ backendHealth.message }}</p>
            </div>
            
            <div class="health-card">
              <h3>Database</h3>
              <div class="health-status" :class="databaseHealth.status">
                <span class="status-indicator"></span>
                <span>{{ databaseHealth.status === 'healthy' ? 'Healthy' : 'Unhealthy' }}</span>
              </div>
              <p v-if="databaseHealth.message" class="health-message">{{ databaseHealth.message }}</p>
            </div>
            
            <div class="health-card">
              <h3>MinIO Storage</h3>
              <div class="health-status" :class="minioHealth.status">
                <span class="status-indicator"></span>
                <span>{{ minioHealth.status === 'healthy' ? 'Healthy' : 'Unhealthy' }}</span>
              </div>
              <p v-if="minioHealth.message" class="health-message">{{ minioHealth.message }}</p>
            </div>
          </div>
          
          <div class="health-actions">
            <button @click="checkHealth" class="action-button verify" :disabled="checkingHealth">
              {{ checkingHealth ? 'Checking...' : 'Refresh Health Status' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Batch Management Tab -->
    <div v-if="activeTab === 'batch'">
      <div class="admin-content">
        <div class="batch-section">
          <h2>Batch Job Management</h2>
          <p class="subtitle">Trigger and monitor batch processing jobs</p>
          
          <div class="batch-jobs">
            <!-- 13F Filing Processing Job -->
            <div class="batch-job-card">
              <div class="batch-job-header">
                <h3>13F Filing Processing</h3>
                <span class="job-status" :class="batchJobs.filing13f.status">
                  {{ batchJobs.filing13f.status === 'running' ? 'Running...' : batchJobs.filing13f.status === 'success' ? 'Completed' : batchJobs.filing13f.status === 'error' ? 'Failed' : 'Ready' }}
                </span>
              </div>
              <p class="job-description">
                Process 13F institutional holdings filings from SEC EDGAR. Fetches, parses, and stores holdings data with CUSIP-to-ticker mapping.
              </p>
              
              <div class="job-options">
                <div class="option-group">
                  <label>
                    <input type="checkbox" v-model="batchJobs.filing13f.forceReprocess" />
                    Force Reprocess (reprocess already processed filings)
                  </label>
                </div>
                <div class="option-group">
                  <label>Quarters (leave empty for all):</label>
                  <input 
                    type="text" 
                    v-model="batchJobs.filing13f.quarters" 
                    placeholder="e.g., 2025-Q3,2025-Q4"
                    class="quarters-input"
                  />
                  <small>Comma-separated list of quarters (e.g., 2025-Q3,2025-Q4)</small>
                </div>
              </div>
              
              <div class="job-actions">
                <button 
                  @click="trigger13FProcessing" 
                  class="action-button verify"
                  :disabled="batchJobs.filing13f.status === 'running'"
                >
                  {{ batchJobs.filing13f.status === 'running' ? 'Processing...' : 'Process 13F Filings' }}
                </button>
              </div>
              
              <div v-if="batchJobs.filing13f.result" class="job-result">
                <h4>Last Run Result:</h4>
                <div class="result-details">
                  <p><strong>Total Filings:</strong> {{ batchJobs.filing13f.result.total_filings || 0 }}</p>
                  <p><strong>Processed:</strong> {{ batchJobs.filing13f.result.processed || 0 }}</p>
                  <p><strong>Skipped:</strong> {{ batchJobs.filing13f.result.skipped || 0 }}</p>
                  <p><strong>Errors:</strong> {{ batchJobs.filing13f.result.errors || 0 }}</p>
                  <p v-if="batchJobs.filing13f.result.quarters"><strong>Quarters:</strong> {{ batchJobs.filing13f.result.quarters.join(', ') }}</p>
                </div>
              </div>
              
              <div v-if="batchJobs.filing13f.error" class="job-error">
                <strong>Error:</strong> {{ batchJobs.filing13f.error }}
              </div>
            </div>
            
            <!-- Add more batch jobs here in the future -->
          </div>
        </div>
      </div>
    </div>

    <!-- Access Management Tab -->
    <div v-if="activeTab === 'access'">
      <div v-if="loadingPermissions" class="loading-container">
        <div class="loading-spinner"></div>
        <p>Loading permissions...</p>
      </div>

      <div v-else-if="permissionsError" class="error-container">
        <p class="error-message">{{ permissionsError }}</p>
        <button @click="loadPermissions" class="retry-button">Retry</button>
        <button @click="initializePermissions" class="action-button verify" style="margin-left: 10px;">Initialize Defaults</button>
      </div>

      <div v-else class="admin-content">
        <div class="access-section">
          <h2>Access Management</h2>
          <p class="subtitle">Control which roles can access specific application routes</p>
          
          <div class="permissions-matrix">
            <table class="users-table">
              <thead>
                <tr>
                  <th>Resource / Route</th>
                  <th v-for="role in roles" :key="role">{{ role.charAt(0).toUpperCase() + role.slice(1) }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="resource in resourceTypes" :key="resource">
                  <td class="resource-name">{{ resource }}</td>
                  <td v-for="role in roles" :key="role" class="permission-cell">
                    <label class="toggle-switch">
                      <input 
                        type="checkbox" 
                        :checked="getPermission(role, resource)"
                        @change="updatePermission(role, resource, $event.target.checked)"
                        :disabled="role === 'admin'"
                      >
                      <span class="slider round"></span>
                    </label>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <div class="permission-legend">
            <p><small>* Admin role always has full access to all resources.</small></p>
            <p><small>* Changes take effect immediately but users may need to refresh for navigation updates.</small></p>
          </div>
        </div>
      </div>
    </div>

    <!-- Report Management Tab -->
    <div v-if="activeTab === 'reports'">
      <div v-if="loadingReports" class="loading-container">
        <div class="loading-spinner"></div>
        <p>Loading reports...</p>
      </div>

      <div v-else-if="reportsError" class="error-container">
        <p class="error-message">{{ reportsError }}</p>
        <button @click="loadReports" class="retry-button">Retry</button>
      </div>

      <div v-else class="admin-content">
        <div class="filters-section">
          <input
            v-model="reportSearchQuery"
            type="text"
            placeholder="Search by ticker or title..."
            class="search-input"
          />
          <select v-model="reportTypeFilter" class="filter-select">
            <option value="">All Types</option>
            <option value="daily">Daily</option>
            <option value="long">Long Position</option>
            <option value="short">Short Position</option>
            <option value="research">Research</option>
          </select>
        </div>

        <div class="users-table-container">
          <table class="users-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Title</th>
                <th>Ticker</th>
                <th>Type</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="report in filteredReports" :key="report.id" class="user-row">
                <td>{{ report.id }}</td>
                <td>{{ report.title }}</td>
                <td>{{ report.ticker || '-' }}</td>
                <td>
                  <span :class="['role-badge', `role-${report.report_type?.toLowerCase() || 'research'}`]">
                    {{ (report.report_type || 'research').toUpperCase() }}
                  </span>
                </td>
                <td class="created-date">
                  {{ formatDate(report.created_at) }}
                </td>
                <td class="actions-cell">
                  <button
                    @click="confirmDeleteReport(report)"
                    class="action-button delete"
                    :disabled="deletingReportId === report.id"
                  >
                    {{ deletingReportId === report.id ? 'Deleting...' : 'Delete' }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="filteredReports.length === 0" class="no-results">
          <p>No reports found matching your filters.</p>
        </div>
      </div>
    </div>

    <!-- Database Management Tab -->
    <div v-if="activeTab === 'database'">
      <div v-if="loadingTables" class="loading-container">
        <div class="loading-spinner"></div>
        <p>Loading database tables...</p>
      </div>

      <div v-else-if="tablesError" class="error-container">
        <p class="error-message">{{ tablesError }}</p>
        <button @click="loadTables" class="retry-button">Retry</button>
      </div>

      <div v-else class="admin-content">
        <div class="database-section">
          <h2>Database Management</h2>
          <p class="subtitle">Inspect database tables and data</p>
          
          <div class="table-selector">
            <label>Select Table:</label>
            <select v-model="selectedTable" @change="loadTableData">
              <option value="" disabled>Select a table</option>
              <option v-for="table in tables" :key="table" :value="table">{{ table }}</option>
            </select>
            <button @click="loadTableData" class="action-button verify" :disabled="!selectedTable || loadingTableData">
              {{ loadingTableData ? 'Loading...' : 'Refresh Data' }}
            </button>
          </div>
          
          <div v-if="tableData" class="data-view">
             <div class="table-info">
               <span><strong>Total Rows:</strong> {{ tableData.total_count }}</span>
               <span><strong>Showing:</strong> {{ tableData.rows.length }} rows</span>
             </div>
             
             <div class="users-table-container db-table-container">
               <table class="users-table">
                 <thead>
                   <tr>
                     <th v-for="col in tableData.columns" :key="col">{{ col }}</th>
                   </tr>
                 </thead>
                 <tbody>
                   <tr v-for="(row, idx) in tableData.rows" :key="idx">
                     <td v-for="col in tableData.columns" :key="col">{{ row[col] }}</td>
                   </tr>
                 </tbody>
               </table>
             </div>
             
             <div v-if="tableData.rows.length === 0" class="no-results">
                <p>No data found in this table.</p>
             </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="message" :class="['message', messageType]">
      {{ message }}
    </div>

    <!-- Delete User Confirmation Modal -->
    <div v-if="showDeleteConfirm" class="modal-overlay" @click="cancelDelete">
      <div class="modal-content" @click.stop>
        <h2>Confirm Delete</h2>
        <p>Are you sure you want to delete user <strong>{{ userToDelete?.username }}</strong> ({{ userToDelete?.email }})?</p>
        <p class="warning-text">This action cannot be undone.</p>
        <div class="modal-actions">
          <button @click="cancelDelete" class="modal-button cancel">Cancel</button>
          <button @click="deleteUser" class="modal-button delete-confirm" :disabled="deletingUserId !== null">
            {{ deletingUserId !== null ? 'Deleting...' : 'Delete User' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Report Confirmation Modal -->
    <div v-if="showDeleteReportConfirm" class="modal-overlay" @click="cancelDeleteReport">
      <div class="modal-content" @click.stop>
        <h2>Confirm Delete Report</h2>
        <p>Are you sure you want to delete report <strong>{{ reportToDelete?.title }}</strong>?</p>
        <p v-if="reportToDelete?.ticker" class="report-details">Ticker: {{ reportToDelete.ticker }} | Type: {{ reportToDelete.report_type }}</p>
        <p class="warning-text">This action cannot be undone.</p>
        <div class="modal-actions">
          <button @click="cancelDeleteReport" class="modal-button cancel">Cancel</button>
          <button @click="deleteReport" class="modal-button delete-confirm" :disabled="deletingReportId !== null">
            {{ deletingReportId !== null ? 'Deleting...' : 'Delete Report' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import API_BASE_URL from '@/config/api.js'

import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const activeTab = ref('users')

// User Management State
const users = ref([])
const loading = ref(true)
const error = ref('')
const searchQuery = ref('')
const roleFilter = ref('')
const paymentFilter = ref('')
const updatingUserId = ref(null)
const deletingUserId = ref(null)
const userToDelete = ref(null)
const showDeleteConfirm = ref(false)

// Report Management State
const reports = ref([])
const loadingReports = ref(false)
const reportsError = ref('')
const reportSearchQuery = ref('')
const reportTypeFilter = ref('')
const deletingReportId = ref(null)
const reportToDelete = ref(null)
const showDeleteReportConfirm = ref(false)

// Health Management State
const checkingHealth = ref(false)
const backendHealth = ref({ status: 'unknown', message: '' })
const databaseHealth = ref({ status: 'unknown', message: '' })
const minioHealth = ref({ status: 'unknown', message: '' })

// Batch Management State

const batchJobs = ref({
  filing13f: {
    status: 'idle', // idle, running, success, error
    forceReprocess: false,
    quarters: '',
    result: null,
    error: null
  }
})

// Database Management State
const tables = ref([])
const loadingTables = ref(false)
const tablesError = ref('')
const selectedTable = ref('')
const tableData = ref(null)
const loadingTableData = ref(false)

// Access Management State
const permissions = ref([])
const loadingPermissions = ref(false)
const permissionsError = ref('')
const roles = ['admin', 'creator', 'contributor', 'user']
const resourceTypes = ['/research', '/alphatrade', '/report', '/investment', '/short-interest', '/whale-watching', '/agent']

// Message State
const message = ref('')
const messageType = ref('')

const paidUsersCount = computed(() => {
  return users.value.filter(u => u.has_paid).length
})

const unpaidUsersCount = computed(() => {
  return users.value.filter(u => !u.has_paid).length
})

const filteredUsers = computed(() => {
  let filtered = users.value

  // Search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(user =>
      user.username.toLowerCase().includes(query) ||
      user.email.toLowerCase().includes(query)
    )
  }

  // Role filter
  if (roleFilter.value) {
    filtered = filtered.filter(user => user.role === roleFilter.value)
  }

  // Payment filter
  if (paymentFilter.value === 'paid') {
    filtered = filtered.filter(user => user.has_paid)
  } else if (paymentFilter.value === 'unpaid') {
    filtered = filtered.filter(user => !user.has_paid)
  }

  return filtered
})

const filteredReports = computed(() => {
  let filtered = reports.value

  // Search filter
  if (reportSearchQuery.value) {
    const query = reportSearchQuery.value.toLowerCase()
    filtered = filtered.filter(report =>
      report.title.toLowerCase().includes(query) ||
      (report.ticker && report.ticker.toLowerCase().includes(query))
    )
  }

  // Type filter
  if (reportTypeFilter.value) {
    filtered = filtered.filter(report => report.report_type === reportTypeFilter.value)
  }

  return filtered
})

const loadUsers = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const token = localStorage.getItem('access_token')
    if (!token) {
      router.push('/login')
      return
    }

    const response = await fetch(`${API_BASE_URL}/api/auth/users`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (response.status === 403) {
      error.value = 'Access denied. Admin privileges required.'
      return
    }

    if (!response.ok) {
      throw new Error('Failed to load users')
    }

    users.value = await response.json()
  } catch (err) {
    console.error('Error loading users:', err)
    error.value = 'Failed to load users. Please try again.'
  } finally {
    loading.value = false
  }
}

const togglePaymentStatus = async (user) => {
  if (updatingUserId.value === user.id) return

  updatingUserId.value = user.id
  message.value = ''

  try {
    const token = localStorage.getItem('access_token')
    const newStatus = !user.has_paid

    const response = await fetch(`${API_BASE_URL}/api/auth/update-payment-status`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: user.id,
        has_paid: newStatus,
        transaction_id: user.payment_transaction_id || null
      })
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Failed to update payment status')
    }

    // Update local state
    user.has_paid = newStatus
    if (newStatus && !user.payment_date) {
      user.payment_date = new Date().toISOString()
    }

    message.value = `Payment status updated successfully for ${user.username}`
    messageType.value = 'success'

    setTimeout(() => {
      message.value = ''
    }, 3000)
  } catch (err) {
    console.error('Error updating payment status:', err)
    message.value = err.message || 'Failed to update payment status'
    messageType.value = 'error'

    setTimeout(() => {
      message.value = ''
    }, 5000)
  } finally {
    updatingUserId.value = null
  }
}



const loadTables = async () => {
  loadingTables.value = true
  tablesError.value = ''
  
  try {
    const token = localStorage.getItem('access_token')
    const response = await fetch(`${API_BASE_URL}/api/admin/db/tables`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    
    if (!response.ok) throw new Error('Failed to load tables')
    tables.value = await response.json()
  } catch (err) {
    console.error('Error loading tables:', err)
    tablesError.value = 'Failed to load tables'
  } finally {
    loadingTables.value = false
  }
}

const loadTableData = async () => {
  if (!selectedTable.value) return
  
  loadingTableData.value = true
  tableData.value = null
  
  try {
    const token = localStorage.getItem('access_token')
    const response = await fetch(`${API_BASE_URL}/api/admin/db/table/${selectedTable.value}?limit=100`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    
    if (!response.ok) throw new Error('Failed to load table data')
    tableData.value = await response.json()
  } catch (err) {
    console.error('Error loading table data:', err)
    message.value = 'Failed to load table data'
    messageType.value = 'error'
    setTimeout(() => { message.value = '' }, 3000)
  } finally {
    loadingTableData.value = false
  }
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return '-'
  }
}

const isCurrentUser = (user) => {
  const currentUserStr = localStorage.getItem('user')
  if (!currentUserStr) return false
  try {
    const currentUser = JSON.parse(currentUserStr)
    return currentUser.id === user.id
  } catch {
    return false
  }
}

const confirmDelete = (user) => {
  userToDelete.value = user
  showDeleteConfirm.value = true
}

const cancelDelete = () => {
  userToDelete.value = null
  showDeleteConfirm.value = false
}

const deleteUser = async () => {
  if (!userToDelete.value) return

  deletingUserId.value = userToDelete.value.id
  message.value = ''

  try {
    const token = localStorage.getItem('access_token')
    if (!token) {
      router.push('/login')
      return
    }

    const response = await fetch(`${API_BASE_URL}/api/auth/users/${userToDelete.value.id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Failed to delete user')
    }

    // Remove user from local state
    users.value = users.value.filter(u => u.id !== userToDelete.value.id)

    message.value = `User ${userToDelete.value.username} has been deleted successfully`
    messageType.value = 'success'

    // Close modal
    cancelDelete()

    setTimeout(() => {
      message.value = ''
    }, 3000)
  } catch (err) {
    console.error('Error deleting user:', err)
    message.value = err.message || 'Failed to delete user'
    messageType.value = 'error'

    setTimeout(() => {
      message.value = ''
    }, 5000)
  } finally {
    deletingUserId.value = null
  }
}

const loadReports = async () => {
  loadingReports.value = true
  reportsError.value = ''
  
  try {
    const token = localStorage.getItem('access_token')
    if (!token) {
      router.push('/login')
      return
    }

    const response = await fetch(`${API_BASE_URL}/api/reports/`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
      throw new Error('Failed to load reports')
    }

    reports.value = await response.json()
  } catch (err) {
    console.error('Error loading reports:', err)
    reportsError.value = 'Failed to load reports. Please try again.'
  } finally {
    loadingReports.value = false
  }
}

const confirmDeleteReport = (report) => {
  reportToDelete.value = report
  showDeleteReportConfirm.value = true
}

const cancelDeleteReport = () => {
  reportToDelete.value = null
  showDeleteReportConfirm.value = false
}

const deleteReport = async () => {
  if (!reportToDelete.value) return

  deletingReportId.value = reportToDelete.value.id
  message.value = ''

  try {
    const token = localStorage.getItem('access_token')
    const response = await fetch(`${API_BASE_URL}/api/reports/${reportToDelete.value.id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Failed to delete report')
    }

    message.value = `Report "${reportToDelete.value.title}" deleted successfully.`
    messageType.value = 'success'
    
    // Dispatch event to notify ReportView to refresh
    window.dispatchEvent(new CustomEvent('report-deleted', {
      detail: {
        reportId: reportToDelete.value.id,
        reportType: reportToDelete.value.report_type
      }
    }))
    
    loadReports() // Reload reports after deletion
    cancelDeleteReport()
  } catch (err) {
    console.error('Error deleting report:', err)
    message.value = err.message || 'Failed to delete report'
    messageType.value = 'error'
  } finally {
    deletingReportId.value = null
    setTimeout(() => { message.value = '' }, 3000)
  }
}

// Health Management Functions
const checkHealth = async () => {
  checkingHealth.value = true
  
  try {
    const token = localStorage.getItem('access_token')
    if (!token) {
      router.push('/login')
      return
    }

    // Check backend API
    try {
      const backendResponse = await fetch(`${API_BASE_URL}/`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      backendHealth.value = {
        status: backendResponse.ok ? 'healthy' : 'unhealthy',
        message: backendResponse.ok ? 'API is responding' : 'API is not responding'
      }
    } catch (err) {
      backendHealth.value = {
        status: 'unhealthy',
        message: 'Cannot reach backend API'
      }
    }

    // Check database (via a simple API call)
    try {
      const dbResponse = await fetch(`${API_BASE_URL}/api/auth/users`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      databaseHealth.value = {
        status: dbResponse.ok ? 'healthy' : 'unhealthy',
        message: dbResponse.ok ? 'Database connection working' : 'Database connection failed'
      }
    } catch (err) {
      databaseHealth.value = {
        status: 'unhealthy',
        message: 'Database connection error'
      }
    }

    // Check MinIO (via reports endpoint which uses MinIO)
    try {
      const minioResponse = await fetch(`${API_BASE_URL}/api/reports/`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      minioHealth.value = {
        status: minioResponse.ok ? 'healthy' : 'unhealthy',
        message: minioResponse.ok ? 'MinIO storage accessible' : 'MinIO storage error'
      }
    } catch (err) {
      minioHealth.value = {
        status: 'unhealthy',
        message: 'MinIO storage error'
      }
    }

  } catch (err) {
    console.error('Error checking system health:', err)
  } finally {
    checkingHealth.value = false
  }
}

// Access Management Functions
const loadPermissions = async () => {
  loadingPermissions.value = true
  permissionsError.value = ''
  
  try {
    const token = localStorage.getItem('access_token')
    if (!token) {
      router.push('/login')
      return
    }

    const response = await fetch(`${API_BASE_URL}/api/auth/permissions`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
        throw new Error('Failed to load permissions')
    }

    permissions.value = await response.json()
    
    // If empty, suggest initialization
    if (permissions.value.length === 0) {
        permissionsError.value = 'No permissions found. Please initialize defaults.'
    }
  } catch (err) {
    console.error('Error loading permissions:', err)
    permissionsError.value = 'Failed to load permissions. Please try again.'
  } finally {
    loadingPermissions.value = false
  }
}

const initializePermissions = async () => {
    try {
        const token = localStorage.getItem('access_token')
        const response = await fetch(`${API_BASE_URL}/api/auth/initialize-permissions`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        
        if (response.ok) {
            await loadPermissions()
            message.value = 'Default permissions initialized'
            messageType.value = 'success'
            setTimeout(() => { message.value = '' }, 3000)
        }
    } catch (err) {
        console.error('Error initializing permissions:', err)
        permissionsError.value = 'Failed to initialize permissions'
    }
}

const getPermission = (role, resource) => {
    if (role === 'admin') return true
    
    const perm = permissions.value.find(p => p.role === role && p.resource === resource)
    return perm ? perm.can_access : false
}

const updatePermission = async (role, resource, canAccess) => {
    try {
        const token = localStorage.getItem('access_token')
        const response = await fetch(`${API_BASE_URL}/api/auth/permissions`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                role,
                resource,
                can_access: canAccess
            })
        })

        if (!response.ok) {
            throw new Error('Failed to update permission')
        }
        
        const updatedPerm = await response.json()
        
        // Update local state
        const index = permissions.value.findIndex(p => p.role === role && p.resource === resource)
        if (index !== -1) {
            permissions.value[index] = updatedPerm
        } else {
            permissions.value.push(updatedPerm)
        }
        
        message.value = `Permission updated for ${role} on ${resource}`
        messageType.value = 'success'
        setTimeout(() => { message.value = '' }, 2000)
        
    } catch (err) {
        console.error('Error updating permission:', err)
        message.value = 'Failed to update permission'
        messageType.value = 'error'
        setTimeout(() => { message.value = '' }, 3000)
        
        // Revert UI change by reloading
        await loadPermissions()
    }
}



// Batch Management Functions
let pollingInterval = null

const pollJobStatus = async (jobId) => {
  const token = localStorage.getItem('access_token')
  if (!token) {
    router.push('/login')
    return
  }

  try {
    const response = await fetch(`/api/filing-13f/process/status/${jobId}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
      throw new Error('Failed to check job status')
    }

    const status = await response.json()
    
    if (status.status === 'completed') {
      // Stop polling
      if (pollingInterval) {
        clearInterval(pollingInterval)
        pollingInterval = null
      }
      
      batchJobs.value.filing13f.status = 'success'
      batchJobs.value.filing13f.result = status.result
      batchJobs.value.filing13f.error = null
      
      const result = status.result
      message.value = `13F processing completed: ${result.processed} processed, ${result.skipped} skipped`
      messageType.value = 'success'
      
      setTimeout(() => {
        message.value = ''
      }, 5000)
    } else if (status.status === 'error') {
      // Stop polling
      if (pollingInterval) {
        clearInterval(pollingInterval)
        pollingInterval = null
      }
      
      batchJobs.value.filing13f.status = 'error'
      batchJobs.value.filing13f.error = status.error || 'Processing failed'
      batchJobs.value.filing13f.result = null
      
      message.value = status.error || '13F processing failed'
      messageType.value = 'error'
      
      setTimeout(() => {
        message.value = ''
      }, 5000)
    } else if (status.status === 'running') {
      // Continue polling - job is still running
      batchJobs.value.filing13f.status = 'running'
    }
  } catch (err) {
    console.error('Error polling job status:', err)
    // Continue polling on error (might be temporary)
  }
}

const trigger13FProcessing = async () => {
  batchJobs.value.filing13f.status = 'running'
  batchJobs.value.filing13f.error = null
  batchJobs.value.filing13f.result = null
  
  // Clear any existing polling interval
  if (pollingInterval) {
    clearInterval(pollingInterval)
    pollingInterval = null
  }
  
  try {
    const token = localStorage.getItem('access_token')
    if (!token) {
      router.push('/login')
      return
    }

    const requestBody = {
      force_reprocess: batchJobs.value.filing13f.forceReprocess
    }
    
    // Parse quarters if provided
    if (batchJobs.value.filing13f.quarters.trim()) {
      requestBody.quarters = batchJobs.value.filing13f.quarters
        .split(',')
        .map(q => q.trim())
        .filter(q => q.length > 0)
    }

    const response = await fetch('/api/filing-13f/process', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Failed to trigger 13F processing')
    }

    const result = await response.json()
    
    // Start polling for job status
    message.value = result.message || '13F processing started...'
    messageType.value = 'info'
    
    // Poll every 2 seconds
    pollingInterval = setInterval(() => {
      pollJobStatus(result.job_id)
    }, 2000)
    
    // Initial poll
    pollJobStatus(result.job_id)
    
  } catch (err) {
    console.error('Error triggering 13F processing:', err)
    batchJobs.value.filing13f.error = err.message || 'Failed to trigger 13F processing'
    batchJobs.value.filing13f.status = 'error'
    
    message.value = err.message || 'Failed to trigger 13F processing'
    messageType.value = 'error'
    
    setTimeout(() => {
      message.value = ''
    }, 5000)
  }
}

// Watch for tab changes to load reports and health
watch(activeTab, (newTab) => {
  if (newTab === 'reports' && reports.value.length === 0) {
    loadReports()
  }
  if (newTab === 'health') {
    checkHealth()
  }
})

onUnmounted(() => {
  // Clean up polling interval when component unmounts
  if (pollingInterval) {
    clearInterval(pollingInterval)
    pollingInterval = null
  }
})

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.admin-view {
  min-height: 100vh;
  padding: 2rem;
  background: #ffffff;
  color: #000000;
}

.admin-header {
  margin-bottom: 20px;
}

.category-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 30px;
  justify-content: flex-start;
  flex-wrap: nowrap;
  border-bottom: 2px solid #cccccc;
  padding-bottom: 12px;
}

.category-tabs button {
  background: transparent;
  border: none;
  color: #666666;
  padding: 12px 20px;
  border-radius: 6px 6px 0 0;
  cursor: pointer;
  font-size: 0.95em;
  font-weight: 500;
  transition: all 0.2s;
  border-bottom: 3px solid transparent;
  white-space: nowrap;
}

.category-tabs button:hover {
  background: #ebebeb;
  color: #000;
}

.category-tabs button.active {
  background: #fff;
  color: #000;
  border-bottom-color: #000;
}

/* Content Sections */
.admin-content {
  background: #fff;
  animation: fadeIn 0.3s ease-out;
}

.stats-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  border: 1px solid #e0e0e0;
  border-radius: 4px; /* Sharper corners */
  padding: 1.25rem;
  background: #fafafa;
  transition: box-shadow 0.2s;
}

.stat-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #000;
  margin-bottom: 0.25rem;
}

.stat-label {
  font-size: 0.75rem;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Filters */
.filters-section {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  padding: 1rem;
  background: #fafafa;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
}

.search-input, .filter-select {
  padding: 0.5rem 0.75rem;
  border: 1px solid #d0d0d0;
  border-radius: 4px;
  font-size: 0.875rem;
  background: #fff;
  color: #000;
}

.search-input:focus, .filter-select:focus {
  outline: none;
  border-color: #000;
}

/* Tables matching AlphaTrade lots-table */
.users-table-container {
  overflow-x: auto;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.users-table th {
  text-align: left;
  padding: 0.75rem 1rem;
  font-size: 0.6875rem;
  font-weight: 600;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 2px solid #e0e0e0;
  background: #fafafa;
}

.users-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #e0e0e0;
  color: #333;
}

.user-row:hover {
  background: #f5f5f5;
}

/* Badges */
.role-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.role-admin { background: #000; color: #fff; }
.role-creator { background: #e0e0e0; color: #000; }
.role-user { background: #f5f5f5; color: #666; border: 1px solid #e0e0e0; }

.payment-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.payment-badge.paid { color: #10b981; background: rgba(16, 185, 129, 0.1); }
.payment-badge.unpaid { color: #666; background: rgba(0, 0, 0, 0.05); }

/* Buttons */
.action-button {
  padding: 0.375rem 0.75rem;
  border: none;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border: 1px solid transparent;
}

.action-button.verify {
  background: #fff;
  border-color: #000;
  color: #000;
}

.action-button.verify:hover {
  background: #000;
  color: #fff;
}

.action-button.unverify {
  background: #fff;
  border-color: #d0d0d0;
  color: #666;
}

.action-button.unverify:hover {
  border-color: #666;
  color: #000;
}

.action-button.delete {
  background: #fff;
  border-color: #ef4444;
  color: #ef4444;
}

.action-button.delete:hover {
  background: #ef4444;
  color: #fff;
}

/* Switches for Access Control - sharper */
.toggle-switch {
  position: relative;
  display: inline-block;
  width: 40px;
  height: 20px;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #e0e0e0;
  transition: .4s;
  border-radius: 20px; /* Keep somewhat rounded for mechanic implication, but cleaner colors */
}

.slider:before {
  position: absolute;
  content: "";
  height: 16px;
  width: 16px;
  left: 2px;
  bottom: 2px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

input:checked + .slider {
  background-color: #000; /* Black for active */
}

input:checked + .slider:before {
  transform: translateX(20px);
}

.modal-content strong {
  color: #000000;
  font-weight: 600;
}

.warning-text {
  color: #dc2626;
  font-weight: 600;
  margin-top: 1rem;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
  justify-content: flex-end;
}

.modal-button {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.modal-button.cancel {
  background: #f3f4f6;
  color: #000000;
}

.modal-button.cancel:hover {
  background: #e5e7eb;
}

.modal-button.delete-confirm {
  background: #dc2626;
  color: #ffffff;
}

.modal-button.delete-confirm:hover:not(:disabled) {
  background: #b91c1c;
}

  .modal-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

.health-section {
  padding: 1rem 0;
}

.health-section h2 {
  color: #000000;
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.health-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin: 2rem 0;
}

.health-card {
  background: #f5f5f5;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid #e5e5e5;
}

.health-card h3 {
  color: #000000;
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.health-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  display: inline-block;
}

.health-status.healthy {
  color: #065f46;
}

.health-status.healthy .status-indicator {
  background: #10b981;
}

.health-status.unhealthy {
  color: #991b1b;
}

.health-status.unhealthy .status-indicator {
  background: #ef4444;
}

.health-status.unknown {
  color: #666666;
}

.health-status.unknown .status-indicator {
  background: #9ca3af;
}

.health-message {
  color: #666666;
  font-size: 0.875rem;
  margin-top: 0.5rem;
}

.health-actions {
  margin-top: 2rem;
}

.batch-section {
  padding: 1rem 0;
}

.batch-section h2 {
  color: #000000;
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.batch-jobs {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  margin: 2rem 0;
}

.batch-job-card {
  background: #f5f5f5;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid #e5e5e5;
}

.batch-job-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.batch-job-header h3 {
  color: #000000;
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
}

.job-status {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.job-status.idle {
  background: #f3f4f6;
  color: #374151;
}

.job-status.running {
  background: #dbeafe;
  color: #1e40af;
}

.job-status.success {
  background: #d1fae5;
  color: #065f46;
}

.job-status.error {
  background: #fee2e2;
  color: #991b1b;
}

.job-description {
  color: #666666;
  font-size: 0.875rem;
  margin-bottom: 1.5rem;
  line-height: 1.5;
}

.job-options {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: #ffffff;
  border-radius: 6px;
  border: 1px solid #e5e5e5;
}

.option-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.option-group label {
  color: #000000;
  font-size: 0.875rem;
  font-weight: 500;
}

.option-group input[type="checkbox"] {
  margin-right: 0.5rem;
}

.quarters-input {
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
  background: #ffffff;
  color: #000000;
}

.quarters-input:focus {
  outline: none;
  border-color: #000000;
  box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.1);
}

.option-group small {
  color: #666666;
  font-size: 0.75rem;
}

.job-actions {
  margin-top: 1rem;
}

.job-result {
  margin-top: 1.5rem;
  padding: 1rem;
  background: #ffffff;
  border-radius: 6px;
  border: 1px solid #e5e5e5;
}

.job-result h4 {
  color: #000000;
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
}

.result-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0.75rem;
}

.result-details p {
  margin: 0;
  color: #000000;
  font-size: 0.875rem;
}

.result-details strong {
  font-weight: 600;
  margin-right: 0.5rem;
}

.job-error {
  margin-top: 1rem;
  padding: 1rem;
  background: #fee2e2;
  border-radius: 6px;
  border: 1px solid #fecaca;
  color: #991b1b;
  font-size: 0.875rem;
}

@media (max-width: 768px) {
  .admin-view {
    padding: 1rem;
  }

  .users-table-container {
    font-size: 0.75rem;
  }

  .users-table th,
  .users-table td {
    padding: 0.5rem;
  }

  .action-buttons {
    flex-direction: column;
    gap: 0.25rem;
  }

  .action-button {
    width: 100%;
    font-size: 0.75rem;
    padding: 0.4rem 0.8rem;
  }

  .modal-content {
    padding: 1.5rem;
  }
}

/* Access Management Styles */
.access-section {
    background: #ffffff;
    border-radius: 8px;
    padding: 20px;
}

.permissions-matrix {
    margin: 20px 0;
    overflow-x: auto;
}

.permissions-matrix .users-table {
    width: 100%;
}

.permissions-matrix th, 
.permissions-matrix td {
    text-align: center;
}

.permissions-matrix .resource-name {
    text-align: left;
    font-weight: 500;
}

.permission-cell {
    padding: 10px;
}

.permission-legend {
    margin-top: 20px;
    color: #666;
    font-style: italic;
}

/* Toggle Switch */
.toggle-switch {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 24px;
}

.toggle-switch input { 
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  -webkit-transition: .4s;
  transition: .4s;
}

.slider:before {
  position: absolute;
  content: "";
  height: 16px;
  width: 16px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  -webkit-transition: .4s;
  transition: .4s;
}

input:checked + .slider {
  background-color: #2196F3;
}

input:focus + .slider {
  box-shadow: 0 0 1px #2196F3;
}

input:checked + .slider:before {
  -webkit-transform: translateX(26px);
  -ms-transform: translateX(26px);
  transform: translateX(26px);
}

/* Rounded sliders */
.slider.round {
  border-radius: 34px;
}

.slider.round:before {
  border-radius: 50%;
}

input:disabled + .slider {
    background-color: #e0e0e0;
    cursor: not-allowed;
}
</style>

