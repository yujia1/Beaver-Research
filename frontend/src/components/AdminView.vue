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
        :class="{ active: activeTab === 'reports' }"
        @click="activeTab = 'reports'"
      >
        Report Management
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
import { ref, computed, onMounted, watch } from 'vue'
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

    const response = await fetch('http://localhost:8000/api/auth/users', {
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

    const response = await fetch('http://localhost:8000/api/auth/update-payment-status', {
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

    const response = await fetch(`http://localhost:8000/api/auth/users/${userToDelete.value.id}`, {
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

    const response = await fetch('http://localhost:8000/api/reports/', {
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
    const response = await fetch(`http://localhost:8000/api/reports/${reportToDelete.value.id}`, {
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

// Watch for tab changes to load reports
watch(activeTab, (newTab) => {
  if (newTab === 'reports' && reports.value.length === 0) {
    loadReports()
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
}

.category-tabs button.active {
  color: #000000;
  border-bottom-color: #3498db;
  background: rgba(52, 152, 219, 0.1);
  font-weight: 600;
}

.category-tabs button:hover {
  color: #000000;
  background: rgba(0, 0, 0, 0.05);
}

.admin-header h1 {
  font-size: 2rem;
  font-weight: 700;
  color: #000000;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #666666;
  font-size: 1rem;
}

.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  gap: 1rem;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e5e5e5;
  border-top-color: #000000;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-message {
  color: #dc2626;
  font-size: 1rem;
}

.retry-button {
  padding: 0.5rem 1rem;
  background: #000000;
  color: #ffffff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
}

.retry-button:hover {
  background: #333333;
}

.admin-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.stats-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.stat-card {
  background: #f5f5f5;
  padding: 1.5rem;
  border-radius: 8px;
  text-align: center;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #000000;
  margin-bottom: 0.5rem;
}

.stat-label {
  color: #666666;
  font-size: 0.875rem;
}

.filters-section {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.search-input,
.filter-select {
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 1rem;
  background: #ffffff;
  color: #000000;
}

.search-input {
  flex: 1;
  min-width: 250px;
}

.filter-select {
  min-width: 150px;
}

.search-input:focus,
.filter-select:focus {
  outline: none;
  border-color: #000000;
  box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.1);
}

.users-table-container {
  overflow-x: auto;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
  background: #ffffff;
}

.users-table thead {
  background: #f5f5f5;
}

.users-table th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  color: #000000;
  border-bottom: 2px solid #e5e5e5;
  font-size: 0.875rem;
  text-transform: uppercase;
}

.users-table td {
  padding: 1rem;
  border-bottom: 1px solid #e5e5e5;
  color: #000000;
  font-size: 0.875rem;
}

.user-row:hover {
  background: #f9f9f9;
}

.report-details {
  color: #666666;
  font-size: 0.9em;
  margin: 0.5rem 0;
}

.role-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.role-admin {
  background: #fee2e2;
  color: #991b1b;
}

.role-creator {
  background: #dbeafe;
  color: #1e40af;
}

.role-contributor {
  background: #f3e8ff;
  color: #6b21a8;
}

.role-user {
  background: #f3f4f6;
  color: #374151;
}

.role-daily,
.role-long,
.role-short,
.role-market,
.role-research {
  background: #3498db;
  color: #ffffff;
}

.payment-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.payment-badge.paid {
  background: #d1fae5;
  color: #065f46;
}

.payment-badge.unpaid {
  background: #fee2e2;
  color: #991b1b;
}

.transaction-id {
  font-family: monospace;
  font-size: 0.75rem;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.payment-date,
.created-date {
  font-size: 0.75rem;
  color: #666666;
}

.actions-cell {
  white-space: nowrap;
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.action-button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.action-button.verify {
  background: #10b981;
  color: #ffffff;
}

.action-button.verify:hover:not(:disabled) {
  background: #059669;
}

.action-button.unverify {
  background: #ef4444;
  color: #ffffff;
}

.action-button.unverify:hover:not(:disabled) {
  background: #dc2626;
}

.action-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.action-button.delete {
  background: #dc2626;
  color: #ffffff;
}

.action-button.delete:hover:not(:disabled) {
  background: #b91c1c;
}

.no-results {
  text-align: center;
  padding: 3rem;
  color: #666666;
}

.message {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  padding: 1rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
}

.message.success {
  background: #10b981;
  color: #ffffff;
}

.message.error {
  background: #ef4444;
  color: #ffffff;
}

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
  z-index: 2000;
}

.modal-content {
  background: #ffffff;
  padding: 2rem;
  border-radius: 8px;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.modal-content h2 {
  margin: 0 0 1rem 0;
  color: #000000;
  font-size: 1.5rem;
  font-weight: 700;
}

.modal-content p {
  margin: 0.5rem 0;
  color: #000000;
  line-height: 1.5;
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
</style>

