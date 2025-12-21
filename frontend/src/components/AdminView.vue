<template>
  <div class="admin-view">
    <div class="admin-header">
      <h1>{{ t('admin.header.title') }}</h1>
      <p class="subtitle">{{ t('admin.header.subtitle') }}</p>
    </div>

    <!-- Tabs -->
    <div class="category-tabs">
      <button 
        :class="{ active: activeTab === 'users' }"
        @click="activeTab = 'users'"
      >
        {{ t('admin.tabs.users') }}
      </button>     
      <button 
        :class="{ active: activeTab === 'access' }"
        @click="activeTab = 'access'; loadPermissions()"
      >
        {{ t('admin.tabs.access') }}
      </button>
      <button 
        :class="{ active: activeTab === 'reports' }"
        @click="activeTab = 'reports'"
      >
        {{ t('admin.tabs.reports') }}
      </button>
      <button 
        :class="{ active: activeTab === 'batch' }"
        @click="activeTab = 'batch'"
      >
        {{ t('admin.tabs.batch') }}
      </button>
      <button 
        :class="{ active: activeTab === 'health' }"
        @click="activeTab = 'health'"
      >
        {{ t('admin.tabs.health') }}
      </button> 
      <button 
        :class="{ active: activeTab === 'database' }"
        @click="activeTab = 'database'; loadTables()"
      >
        {{ t('admin.tabs.database') }}
      </button>
    </div>

    <!-- User Management Tab -->
    <div v-if="activeTab === 'users'">
      <div v-if="loading" class="loading-container">
        <div class="loading-spinner"></div>
        <p>{{ t('admin.users.loading') }}</p>
      </div>

      <div v-else-if="error" class="error-container">
        <p class="error-message">{{ error }}</p>
        <button @click="loadUsers" class="retry-button">{{ t('admin.errors.retry') }}</button>
      </div>

      <div v-else class="admin-content">
      <div class="stats-section">
        <div class="stat-card">
          <div class="stat-value">{{ users.length }}</div>
          <div class="stat-label">{{ t('admin.users.stats.total') }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ paidUsersCount }}</div>
          <div class="stat-label">{{ t('admin.users.stats.paid') }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ unpaidUsersCount }}</div>
          <div class="stat-label">{{ t('admin.users.stats.unpaid') }}</div>
        </div>
      </div>

      <div class="filters-section">
        <input
          v-model="searchQuery"
          type="text"
          :placeholder="t('admin.users.filters.search_placeholder')"
          class="search-input"
        />
        <select v-model="roleFilter" class="filter-select">
          <option value="">{{ t('admin.users.filters.all_roles') }}</option>
          <option value="admin">Admin</option>
          <option value="creator">Creator</option>
          <option value="contributor">Contributor</option>
          <option value="user">User</option>
        </select>
        <select v-model="paymentFilter" class="filter-select">
          <option value="">{{ t('admin.users.filters.all_payment') }}</option>
          <option value="paid">{{ t('admin.users.filters.paid') }}</option>
          <option value="unpaid">{{ t('admin.users.filters.unpaid') }}</option>
        </select>
      </div>

      <div class="users-table-container">
        <table class="users-table">
          <thead>
            <tr>
              <th>{{ t('admin.users.table.id') }}</th>
              <th>{{ t('admin.users.table.username') }}</th>
              <th>{{ t('admin.users.table.email') }}</th>
              <th>{{ t('admin.users.table.role') }}</th>
              <th>{{ t('admin.users.table.payment_status') }}</th>
              <th>{{ t('admin.users.table.transaction_id') }}</th>
              <th>{{ t('admin.users.table.payment_date') }}</th>
              <th>{{ t('admin.users.table.created') }}</th>
              <th>{{ t('admin.users.table.actions') }}</th>
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
                  {{ user.has_paid ? t('admin.users.badges.paid') : t('admin.users.badges.unpaid') }}
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
                    {{ updatingUserId === user.id ? t('admin.users.actions.updating') : (user.has_paid ? t('admin.users.actions.unverify') : t('admin.users.actions.verify')) }}
                  </button>
                  <button
                    @click="confirmDelete(user)"
                    class="action-button delete"
                    :disabled="deletingUserId === user.id || isCurrentUser(user)"
                    :title="isCurrentUser(user) ? t('admin.users.tooltips.cannot_delete_self') : t('admin.users.tooltips.delete_user')"
                  >
                    {{ deletingUserId === user.id ? t('admin.users.actions.deleting') : t('admin.users.actions.delete') }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="filteredUsers.length === 0" class="no-results">
        <p>{{ t('admin.users.no_results') }}</p>
      </div>
      </div>
    </div>

    <!-- Health Management Tab -->
    <div v-if="activeTab === 'health'">
      <div class="admin-content">
        <div class="health-section">
          <h2>{{ t('admin.health.title') }}</h2>
          <p class="subtitle">{{ t('admin.health.subtitle') }}</p>
          
          <div class="health-cards">
            <div class="health-card">
              <h3>{{ t('admin.health.backend') }}</h3>
              <div class="health-status" :class="backendHealth.status">
                <span class="status-indicator"></span>
                <span>{{ backendHealth.status === 'healthy' ? t('admin.health.status.healthy') : t('admin.health.status.unhealthy') }}</span>
              </div>
              <p v-if="backendHealth.message" class="health-message">{{ backendHealth.message }}</p>
            </div>
            
            <div class="health-card">
              <h3>{{ t('admin.health.database') }}</h3>
              <div class="health-status" :class="databaseHealth.status">
                <span class="status-indicator"></span>
                <span>{{ databaseHealth.status === 'healthy' ? t('admin.health.status.healthy') : t('admin.health.status.unhealthy') }}</span>
              </div>
              <p v-if="databaseHealth.message" class="health-message">{{ databaseHealth.message }}</p>
            </div>
            
            <div class="health-card">
              <h3>{{ t('admin.health.s3') }}</h3>
              <div class="health-status" :class="minioHealth.status">
                <span class="status-indicator"></span>
                <span>{{ minioHealth.status === 'healthy' ? t('admin.health.status.healthy') : t('admin.health.status.unhealthy') }}</span>
              </div>
              <p v-if="minioHealth.message" class="health-message">{{ minioHealth.message }}</p>
            </div>
          </div>
          
          <div class="health-actions">
            <button @click="checkHealth" class="action-button verify" :disabled="checkingHealth">
              {{ checkingHealth ? t('admin.health.actions.checking') : t('admin.health.actions.refresh') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Batch Management Tab -->
    <div v-if="activeTab === 'batch'">
      <div class="admin-content">
        <div class="batch-section">
          <h2>{{ t('admin.batch.title') }}</h2>
          <p class="subtitle">{{ t('admin.batch.subtitle') }}</p>
          
          <div class="batch-jobs">
            <!-- 13F Filing Processing Job -->
            <div class="batch-job-card">
              <div class="batch-job-header">
                <h3>{{ t('admin.batch.filing_13f.title') }}</h3>
                <span class="job-status" :class="batchJobs.filing13f.status">
                  {{ batchJobs.filing13f.status === 'running' ? t('admin.batch.filing_13f.status.running') : batchJobs.filing13f.status === 'success' ? t('admin.batch.filing_13f.status.completed') : batchJobs.filing13f.status === 'error' ? t('admin.batch.filing_13f.status.failed') : t('admin.batch.filing_13f.status.ready') }}
                </span>
              </div>
              <p class="job-description">
                {{ t('admin.batch.filing_13f.description') }}
              </p>
              
              <div class="job-options">
                <div class="option-group">
                  <label>
                    <input type="checkbox" v-model="batchJobs.filing13f.forceReprocess" />
                    {{ t('admin.batch.filing_13f.force_reprocess') }}
                  </label>
                </div>
                <div class="option-group">
                  <label>{{ t('admin.batch.filing_13f.quarters_label') }}</label>
                  <input 
                    type="text" 
                    v-model="batchJobs.filing13f.quarters" 
                    :placeholder="t('admin.batch.filing_13f.quarters_placeholder')"
                    class="quarters-input"
                  />
                  <small>{{ t('admin.batch.filing_13f.quarters_help') }}</small>
                </div>
              </div>
              
              <div class="job-actions">
                <button 
                  @click="trigger13FProcessing" 
                  class="action-button verify"
                  :disabled="batchJobs.filing13f.status === 'running'"
                >
                  {{ batchJobs.filing13f.status === 'running' ? t('admin.batch.filing_13f.processing_btn') : t('admin.batch.filing_13f.process_btn') }}
                </button>
              </div>
              
              <div v-if="batchJobs.filing13f.result" class="job-result">
                <h4>{{ t('admin.batch.filing_13f.result.title') }}</h4>
                <div class="result-details">
                  <p><strong>{{ t('admin.batch.filing_13f.result.total') }}</strong> {{ batchJobs.filing13f.result.total_filings || 0 }}</p>
                  <p><strong>{{ t('admin.batch.filing_13f.result.processed') }}</strong> {{ batchJobs.filing13f.result.processed || 0 }}</p>
                  <p><strong>{{ t('admin.batch.filing_13f.result.skipped') }}</strong> {{ batchJobs.filing13f.result.skipped || 0 }}</p>
                  <p><strong>{{ t('admin.batch.filing_13f.result.errors') }}</strong> {{ batchJobs.filing13f.result.errors || 0 }}</p>
                  <p v-if="batchJobs.filing13f.result.quarters"><strong>{{ t('admin.batch.filing_13f.result.quarters') }}</strong> {{ batchJobs.filing13f.result.quarters.join(', ') }}</p>
                </div>
              </div>
              
              <div v-if="batchJobs.filing13f.error" class="job-error">
                <strong>{{ t('admin.batch.filing_13f.error') }}</strong> {{ batchJobs.filing13f.error }}
              </div>
            </div>
            
            <!-- Add more batch jobs here in the future -->
          </div>
          
          <div class="scheduler-config-section">
            <h3 class="section-title">{{ t('admin.batch.scheduler.title') }}</h3>
            <div class="config-card">
              <div class="config-group">
                 <label class="toggle-switch">
                    <input 
                      type="checkbox" 
                      v-model="schedulerConfig.enabled"
                    >
                    <span class="slider round"></span>
                  </label>
                  <span class="config-label">{{ t('admin.batch.scheduler.enable_auto') }}</span>
              </div>
              
              <div class="config-group">
                <label>{{ t('admin.batch.scheduler.delay_days') }}</label>
                <input 
                  type="number" 
                  v-model.number="schedulerConfig.processing_delay_days"
                  min="0"
                  max="30"
                  class="days-input"
                />
                <small>{{ t('admin.batch.scheduler.delay_help') }}</small>
              </div>
              
              <div class="config-actions">
                <button 
                  @click="saveSchedulerConfig" 
                  class="action-button verify"
                  :disabled="savingSchedulerConfig"
                >
                  {{ savingSchedulerConfig ? t('admin.batch.scheduler.saving') : t('admin.batch.scheduler.save') }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Access Management Tab -->
    <div v-if="activeTab === 'access'">
      <div v-if="loadingPermissions" class="loading-container">
        <div class="loading-spinner"></div>
        <p>{{ t('admin.access.loading') }}</p>
      </div>

      <div v-else-if="permissionsError" class="error-container">
        <p class="error-message">{{ permissionsError }}</p>
        <button @click="loadPermissions" class="retry-button">{{ t('admin.errors.retry') }}</button>
        <button @click="initializePermissions" class="action-button verify" style="margin-left: 10px;">{{ t('admin.access.actions.initialize') }}</button>
      </div>

      <div v-else class="admin-content">
        <div class="access-section">
          <h2>{{ t('admin.access.title') }}</h2>
          <p class="subtitle">{{ t('admin.access.subtitle') }}</p>
          
          <div class="permissions-matrix">
            <table class="users-table">
              <thead>
                <tr>
                  <th>{{ t('admin.access.table.resource') }}</th>
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
            <p><small>{{ t('admin.access.legend.admin') }}</small></p>
            <p><small>{{ t('admin.access.legend.refresh') }}</small></p>
          </div>
        </div>
      </div>
    </div>

    <!-- Report Management Tab -->
    <div v-if="activeTab === 'reports'">
      <div v-if="loadingReports" class="loading-container">
        <div class="loading-spinner"></div>
        <p>{{ t('admin.reports.loading') }}</p>
      </div>

      <div v-else-if="reportsError" class="error-container">
        <p class="error-message">{{ reportsError }}</p>
        <button @click="loadReports" class="retry-button">{{ t('admin.errors.retry') }}</button>
      </div>

      <div v-else class="admin-content">
        <!-- Upload Report Section -->
        <div class="upload-section">
          <h3>{{ t('admin.reports.upload.title') }}</h3>
          <div class="upload-form">
            <div class="form-row">
              <div class="form-group">
                <label>{{ t('admin.reports.upload.report_title') }}</label>
                <input
                  v-model="uploadReportTitle"
                  type="text"
                  :placeholder="t('admin.reports.upload.report_title_placeholder')"
                  class="form-input"
                />
              </div>
              <div class="form-group">
                <label>{{ t('admin.reports.upload.ticker') }}</label>
                <input
                  v-model="uploadReportTicker"
                  type="text"
                  :placeholder="t('admin.reports.upload.ticker_placeholder')"
                  class="form-input"
                />
              </div>
              <div class="form-group">
                <label>{{ t('admin.reports.upload.type') }}</label>
                <select v-model="uploadReportType" class="form-input">
                  <option value="">{{ t('admin.reports.upload.select_type') }}</option>
                  <option value="daily">{{ t('report_types.daily') }}</option>
                  <option value="long">{{ t('report_types.long') }}</option>
                  <option value="short">{{ t('report_types.short') }}</option>
                  <option value="market">{{ t('report_types.market') }}</option>
                </select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group file-upload-group">
                <label>{{ t('admin.reports.upload.file') }}</label>
                <input
                  type="file"
                  accept=".pdf"
                  @change="handleFileSelect"
                  class="file-input"
                  ref="fileInput"
                />
                <span v-if="selectedFile" class="file-name">{{ selectedFile.name }}</span>
              </div>
              <div class="form-group upload-button-group">
                <button
                  @click="uploadReport"
                  :disabled="!canUpload || uploadingReport"
                  class="upload-button"
                >
                  {{ uploadingReport ? t('admin.reports.upload.btn_uploading') : t('admin.reports.upload.btn_upload') }}
                </button>
              </div>
            </div>
            <div v-if="uploadError" class="error-message">{{ uploadError }}</div>
            <div v-if="uploadSuccess" class="success-message">{{ uploadSuccess }}</div>
          </div>
        </div>

        <div class="filters-section">
          <input
            v-model="reportSearchQuery"
            type="text"
            :placeholder="t('admin.reports.filters.search_placeholder')"
            class="search-input"
          />
          <select v-model="reportTypeFilter" class="filter-select">
            <option value="">{{ t('admin.reports.filters.all_types') }}</option>
            <option value="daily">{{ t('report_types.daily') }}</option>
            <option value="long">{{ t('report_types.long') }}</option>
            <option value="short">{{ t('report_types.short') }}</option>
            <option value="research">{{ t('report_types.research') }}</option>
          </select>
        </div>

        <div class="users-table-container">
          <table class="users-table">
            <thead>
              <tr>
                <th>{{ t('admin.users.table.id') }}</th>
                <th>{{ t('admin.reports.table.title') }}</th>
                <th>{{ t('admin.reports.table.ticker') }}</th>
                <th>{{ t('admin.reports.table.type') }}</th>
                <th>{{ t('admin.reports.table.created') }}</th>
                <th>{{ t('admin.reports.table.actions') }}</th>
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
                    {{ deletingReportId === report.id ? t('admin.users.actions.deleting') : t('admin.users.actions.delete') }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="filteredReports.length === 0" class="no-results">
          <p>{{ t('admin.reports.no_results') }}</p>
        </div>
      </div>
    </div>

    <!-- Database Management Tab -->
    <div v-if="activeTab === 'database'">
      <div v-if="loadingTables" class="loading-container">
        <div class="loading-spinner"></div>
        <p>{{ t('admin.database.loading') }}</p>
      </div>

      <div v-else-if="tablesError" class="error-container">
        <p class="error-message">{{ tablesError }}</p>
        <button @click="loadTables" class="retry-button">{{ t('admin.errors.retry') }}</button>
      </div>

      <div v-else class="admin-content">
        <div class="database-section">
          <h2>{{ t('admin.database.title') }}</h2>
          <p class="subtitle">{{ t('admin.database.subtitle') }}</p>
          
          <div class="table-selector">
            <label>{{ t('admin.database.select_table') }}</label>
            <select v-model="selectedTable" @change="loadTableData">
              <option value="" disabled>{{ t('admin.database.select_placeholder') }}</option>
              <option v-for="table in tables" :key="table" :value="table">{{ table }}</option>
            </select>
            <button @click="loadTableData" class="action-button verify" :disabled="!selectedTable || loadingTableData">
              {{ loadingTableData ? t('admin.database.loading_btn') : t('admin.database.refresh_btn') }}
            </button>
          </div>
          
          <div v-if="tableData" class="data-view">
             <div class="table-info">
               <span><strong>{{ t('admin.database.info.total') }}</strong> {{ tableData.total_count }}</span>
               <span><strong>{{ t('admin.database.info.showing') }}</strong> {{ tableData.rows.length }} {{ t('admin.database.info.rows') }}</span>
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
                <p>{{ t('admin.database.no_results') }}</p>
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
        <h2>{{ t('admin.modals.delete_user.title') }}</h2>
        <p>{{ t('admin.modals.delete_user.message') }} <strong>{{ userToDelete?.username }}</strong> ({{ userToDelete?.email }})?</p>
        <p class="warning-text">{{ t('admin.modals.delete_user.warning') }}</p>
        <div class="modal-actions">
          <button @click="cancelDelete" class="modal-button cancel">{{ t('admin.modals.delete_user.cancel') }}</button>
          <button @click="deleteUser" class="modal-button delete-confirm" :disabled="deletingUserId !== null">
            {{ deletingUserId !== null ? t('admin.modals.delete_user.deleting') : t('admin.modals.delete_user.confirm') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Report Confirmation Modal -->
    <div v-if="showDeleteReportConfirm" class="modal-overlay" @click="cancelDeleteReport">
      <div class="modal-content" @click.stop>
        <h2>{{ t('admin.modals.delete_report.title') }}</h2>
        <p>{{ t('admin.modals.delete_report.message') }} <strong>{{ reportToDelete?.title }}</strong>?</p>
        <p v-if="reportToDelete?.ticker" class="report-details">{{ t('admin.modals.delete_report.ticker') }} {{ reportToDelete.ticker }} | {{ t('admin.modals.delete_report.type') }} {{ reportToDelete.report_type }}</p>
        <p class="warning-text">{{ t('admin.modals.delete_report.warning') }}</p>
        <div class="modal-actions">
          <button @click="cancelDeleteReport" class="modal-button cancel">{{ t('admin.modals.delete_report.cancel') }}</button>
          <button @click="deleteReport" class="modal-button delete-confirm" :disabled="deletingReportId !== null">
            {{ deletingReportId !== null ? t('admin.modals.delete_report.deleting') : t('admin.modals.delete_report.confirm') }}
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
import { useI18n } from 'vue-i18n'

const router = useRouter()
const { t } = useI18n()

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

// Upload Report State
const uploadReportTitle = ref('')
const uploadReportTicker = ref('')
const uploadReportType = ref('')
const selectedFile = ref(null)
const uploadingReport = ref(false)
const uploadError = ref('')
const uploadSuccess = ref('')
const fileInput = ref(null)

const canUpload = computed(() => {
  return uploadReportTitle.value.trim() && uploadReportType.value && selectedFile.value
})

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

// Scheduler Configuration State
const schedulerConfig = ref({
  enabled: true,
  processing_delay_days: 3
})
const savingSchedulerConfig = ref(false)

const loadSchedulerConfig = async () => {
  try {
    const token = localStorage.getItem('access_token')
    if (!token) return

    const response = await fetch(`${API_BASE_URL}/api/admin/scheduler/config`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (response.ok) {
      const data = await response.json()
      schedulerConfig.value = data
    }
  } catch (err) {
    console.error('Error loading scheduler config:', err)
  }
}

const saveSchedulerConfig = async () => {
  savingSchedulerConfig.value = true
  message.value = ''
  
  try {
    const token = localStorage.getItem('access_token')
    
    const response = await fetch(`${API_BASE_URL}/api/admin/scheduler/config`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(schedulerConfig.value)
    })

    if (!response.ok) {
      throw new Error(t('admin.errors.save_config'))
    }
    
    message.value = t('admin.messages.config_saved')
    messageType.value = 'success'
    setTimeout(() => { message.value = '' }, 3000)
    
  } catch (err) {
    console.error('Error saving scheduler config:', err)
    message.value = t('admin.errors.save_config')
    messageType.value = 'error'
  } finally {
    savingSchedulerConfig.value = false
  }
}

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
const resourceTypes = ['/research', '/alphatrade', '/report', '/investment', '/short-interest', '/whale-watching', '/agent', '/academy']

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
      error.value = t('admin.errors.access_denied')
      return
    }

    if (!response.ok) {
      throw new Error(t('admin.errors.load_users'))
    }

    users.value = await response.json()
  } catch (err) {
    console.error('Error loading users:', err)
    error.value = t('admin.errors.load_users')
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
      throw new Error(errorData.detail || t('admin.errors.update_payment'))
    }

    // Update local state
    user.has_paid = newStatus
    if (newStatus && !user.payment_date) {
      user.payment_date = new Date().toISOString()
    }

    message.value = t('admin.messages.payment_updated', { username: user.username })
    messageType.value = 'success'

    setTimeout(() => {
      message.value = ''
    }, 3000)
  } catch (err) {
    console.error('Error updating payment status:', err)
    message.value = err.message || t('admin.errors.update_payment')
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
    
    if (!response.ok) throw new Error(t('admin.errors.load_tables'))
    tables.value = await response.json()
  } catch (err) {
    console.error('Error loading tables:', err)
    tablesError.value = t('admin.errors.load_tables')
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
    
    if (!response.ok) throw new Error(t('admin.errors.load_table_data'))
    tableData.value = await response.json()
  } catch (err) {
    console.error('Error loading table data:', err)
    message.value = t('admin.errors.load_table_data')
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
      throw new Error(errorData.detail || t('admin.errors.delete_user'))
    }

    // Remove user from local state
    users.value = users.value.filter(u => u.id !== userToDelete.value.id)

    message.value = t('admin.messages.user_deleted', { username: userToDelete.value.username })
    messageType.value = 'success'

    // Close modal
    cancelDelete()

    setTimeout(() => {
      message.value = ''
    }, 3000)
  } catch (err) {
    console.error('Error deleting user:', err)
    message.value = err.message || t('admin.errors.delete_user')
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
      throw new Error(t('admin.errors.load_reports'))
    }

    reports.value = await response.json()
  } catch (err) {
    console.error('Error loading reports:', err)
    reportsError.value = t('admin.errors.load_reports')
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
      throw new Error(errorData.detail || t('admin.errors.delete_report'))
    }

    message.value = t('admin.messages.report_deleted', { title: reportToDelete.value.title })
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
    message.value = err.message || t('admin.errors.delete_report')
    messageType.value = 'error'
  } finally {
    deletingReportId.value = null
    setTimeout(() => { message.value = '' }, 3000)
  }
}

// Upload Report Functions
const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file && file.type === 'application/pdf') {
    selectedFile.value = file
    uploadError.value = ''
  } else {
    selectedFile.value = null
    uploadError.value = t('admin.errors.invalid_pdf')
  }
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
    const API_BASE_URL = window.location.hostname.includes('railway.app') 
      ? 'https://beaver-research-backend-production.up.railway.app'
      : 'http://localhost:8000'
    
    const response = await fetch(`${API_BASE_URL}/api/reports/publish`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    })
    
    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || t('admin.errors.upload_report'))
    }
    
    const result = await response.json()
    uploadSuccess.value = t('admin.messages.report_uploaded', { title: uploadReportTitle.value })
    
    // Reset form
    uploadReportTitle.value = ''
    uploadReportTicker.value = ''
    uploadReportType.value = ''
    selectedFile.value = null
    if (fileInput.value) {
      fileInput.value.value = ''
    }
    
    // Reload reports
    await loadReports()
    
    // Clear success message after 5 seconds
    setTimeout(() => {
      uploadSuccess.value = ''
    }, 5000)
  } catch (err) {
    console.error('Error uploading report:', err)
    uploadError.value = err.message || t('admin.errors.upload_report')
  } finally {
    uploadingReport.value = false
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
        message: backendResponse.ok ? t('admin.health.status.api_ok') : t('admin.health.status.api_error')
      }
    } catch (err) {
      backendHealth.value = {
        status: 'unhealthy',
        message: t('admin.health.status.api_error')
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
        message: dbResponse.ok ? t('admin.health.status.db_ok') : t('admin.health.status.db_error')
      }
    } catch (err) {
      databaseHealth.value = {
        status: 'unhealthy',
        message: t('admin.health.status.db_error')
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
        message: minioResponse.ok ? t('admin.health.status.s3_ok') : t('admin.health.status.s3_error')
      }
    } catch (err) {
      minioHealth.value = {
        status: 'unhealthy',
        message: t('admin.health.status.s3_error')
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
        throw new Error(t('admin.errors.load_permissions'))
    }

    permissions.value = await response.json()
    
    // If empty, suggest initialization
    if (permissions.value.length === 0) {
        permissionsError.value = t('admin.access.messages.no_permissions')
    }
  } catch (err) {
    console.error('Error loading permissions:', err)
    permissionsError.value = t('admin.errors.load_permissions')
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
            message.value = t('admin.access.messages.initialized')
            messageType.value = 'success'
            setTimeout(() => { message.value = '' }, 3000)
        }
    } catch (err) {
        console.error('Error initializing permissions:', err)
        permissionsError.value = t('admin.errors.init_permissions')
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
            throw new Error(t('admin.errors.update_permission'))
        }
        
        const updatedPerm = await response.json()
        
        // Update local state
        const index = permissions.value.findIndex(p => p.role === role && p.resource === resource)
        if (index !== -1) {
            permissions.value[index] = updatedPerm
        } else {
            permissions.value.push(updatedPerm)
        }
        
        message.value = t('admin.access.messages.updated', { role: role, resource: resource })
        messageType.value = 'success'
        setTimeout(() => { message.value = '' }, 2000)
        
    } catch (err) {
        console.error('Error updating permission:', err)
        message.value = t('admin.errors.update_permission')
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

  const API_BASE_URL = window.location.hostname.includes('railway.app') 
    ? 'https://beaver-research-backend-production.up.railway.app'
    : 'http://localhost:8000'

  try {
    const response = await fetch(`${API_BASE_URL}/api/filing-13f/process/status/${jobId}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
      throw new Error(t('admin.errors.check_job'))
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
      message.value = t('admin.messages.processing_completed', { processed: result.processed, skipped: result.skipped })
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
      batchJobs.value.filing13f.error = status.error || t('admin.messages.processing_failed')
      batchJobs.value.filing13f.result = null
      
      message.value = status.error || t('admin.messages.processing_failed')
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

    const API_BASE_URL = window.location.hostname.includes('railway.app') 
      ? 'https://beaver-research-backend-production.up.railway.app'
      : 'http://localhost:8000'

    const response = await fetch(`${API_BASE_URL}/api/filing-13f/process`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || t('admin.errors.trigger_job'))
    }

    const result = await response.json()
    
    // Start polling for job status
    message.value = result.message || t('admin.messages.processing_started')
    messageType.value = 'info'
    
    // Poll every 2 seconds
    pollingInterval = setInterval(() => {
      pollJobStatus(result.job_id)
    }, 2000)
    
    // Initial poll
    pollJobStatus(result.job_id)
    
  } catch (err) {
    console.error('Error triggering 13F processing:', err)
    batchJobs.value.filing13f.error = err.message || t('admin.errors.trigger_job')
    batchJobs.value.filing13f.status = 'error'
    
    message.value = err.message || t('admin.errors.trigger_job')
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
  const token = localStorage.getItem('access_token')
  if (!token) {
    router.push('/login')
    return
  }

  // Check if user is admin
  const userRole = localStorage.getItem('user_role')
  if (userRole !== 'admin') {
    loadingTables.value = false
    tablesError.value = t('admin.errors.access_denied')
  }

  // Load initial data based on active tab
  if (activeTab.value === 'users') {
    loadUsers()
  } else if (activeTab.value === 'batch') {
    loadSchedulerConfig()
  }
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

/* Upload Section */
.upload-section {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: #f5f9ff;
  border: 2px solid #3498db;
  border-radius: 8px;
}

.upload-section h3 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
  font-size: 1.2rem;
}

.upload-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-row {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.form-group {
  flex: 1;
  min-width: 200px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 600;
  color: #2c3e50;
  font-size: 0.9rem;
}

.form-input {
  padding: 0.75rem;
  border: 1px solid #d0d0d0;
  border-radius: 4px;
  font-size: 1rem;
}

.form-input:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.1);
}

.file-upload-group {
  flex: 2;
}

.file-input {
  padding: 0.5rem;
  border: 2px dashed #3498db;
  border-radius: 4px;
  background: white;
  cursor: pointer;
}

.file-name {
  display: inline-block;
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: #e8f4f8;
  border-radius: 4px;
  font-size: 0.9rem;
  color: #2c3e50;
}

.upload-button-group {
  display: flex;
  align-items: flex-end;
}

.upload-button {
  padding: 0.75rem 2rem;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
  white-space: nowrap;
}

.upload-button:hover:not(:disabled) {
  background: #2980b9;
}

.upload-button:disabled {
  background: #95a5a6;
  cursor: not-allowed;
}

.success-message {
  padding: 0.75rem;
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
  border-radius: 4px;
  margin-top: 0.5rem;
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

