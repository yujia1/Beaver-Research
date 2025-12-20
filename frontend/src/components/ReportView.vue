<template>
  <div class="report-view">
    <PaymentGate v-if="!hasPaid && !loading" />
    <div v-else-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Checking access...</p>
    </div>
    <div v-else>
    <h2>Reports</h2>
    
      <div class="category-tabs">
        <button 
          v-for="category in categories" 
          :key="category.value" 
          :class="{ active: activeCategory === category.value }"
          @click="activeCategory = category.value"
        >
          {{ category.label }}
        </button>
            </div>
            
      <div class="content-container">
          <div class="main-report-area">
              <div v-if="loadingReports" class="loading">Loading reports...</div>
              <div v-else>
                <!-- Long Position Reports -->
                <div v-if="activeCategory === 'long'" class="report-category">
                    <div v-if="longReports.length === 0" class="no-reports">No long position reports</div>
                    <ul v-else class="report-list">
                        <li v-for="savedReport in longReports" :key="savedReport.id || savedReport.uuid" :class="{ active: expandedReportIds.has(savedReport.id || savedReport.uuid) }">
                            <div class="report-item-header" @click="toggleReport(savedReport)">
                                <span class="report-ticker">{{ savedReport.ticker }} - {{ new Date(savedReport.created_at || savedReport.date || savedReport.timestamp).toLocaleDateString('en-US', { year: 'numeric', month: '2-digit', day: '2-digit' }) }}</span>
                                <span class="report-date">{{ formatDate(savedReport.created_at || savedReport.date || savedReport.timestamp) }}</span>
                            </div>
                            <div v-if="expandedReportIds.has(savedReport.id || savedReport.uuid)" class="report-item-content">
                                <div v-if="loadingReportsById[savedReport.id || savedReport.uuid]" class="loading">Loading report...</div>
                                <div v-else class="report-body">
                                    <iframe 
                                        v-if="getReportPdfUrl(savedReport)" 
                                        :src="getReportPdfUrl(savedReport)" 
                                        class="pdf-viewer"
                                        frameborder="0"
                                    ></iframe>
                                    <div v-else class="report-error">PDF not available</div>
                                </div>
                            </div>
                        </li>
                    </ul>
            </div>
            
                <!-- Daily Reports -->
                <div v-if="activeCategory === 'daily'" class="report-category">
                    <div v-if="dailyReports.length === 0" class="no-reports">No daily reports</div>
                    <ul v-else class="report-list">
                        <li v-for="savedReport in dailyReports" :key="savedReport.id || savedReport.uuid" :class="{ active: expandedReportIds.has(savedReport.id || savedReport.uuid) }">
                            <div class="report-item-header" @click="toggleReport(savedReport)">
                                <span class="report-ticker">{{ savedReport.ticker }} - {{ new Date(savedReport.created_at || savedReport.date || savedReport.timestamp).toLocaleDateString('en-US', { year: 'numeric', month: '2-digit', day: '2-digit' }) }}</span>
                                <span class="report-date">{{ formatDate(savedReport.created_at || savedReport.date || savedReport.timestamp) }}</span>
                            </div>
                            <div v-if="expandedReportIds.has(savedReport.id || savedReport.uuid)" class="report-item-content">
                                <div v-if="loadingReportsById[savedReport.id || savedReport.uuid]" class="loading">Loading report...</div>
                                <div v-else class="report-body" v-html="getReportContent(savedReport)"></div>
            </div>
                        </li>
                    </ul>
        </div>

                <!-- Market Reports -->
                <div v-if="activeCategory === 'market'" class="report-category">
                    <div v-if="marketReports.length === 0" class="no-reports">No market reports</div>
                    <ul v-else class="report-list">
                        <li v-for="savedReport in marketReports" :key="savedReport.id || savedReport.uuid" :class="{ active: expandedReportIds.has(savedReport.id || savedReport.uuid) }">
                            <div class="report-item-header" @click="toggleReport(savedReport)">
                                <span class="report-ticker">{{ savedReport.ticker }} - {{ new Date(savedReport.created_at || savedReport.date || savedReport.timestamp).toLocaleDateString('en-US', { year: 'numeric', month: '2-digit', day: '2-digit' }) }}</span>
                                <span class="report-date">{{ formatDate(savedReport.created_at || savedReport.date || savedReport.timestamp) }}</span>
                            </div>
                            <div v-if="expandedReportIds.has(savedReport.id || savedReport.uuid)" class="report-item-content">
                                <div v-if="loadingReportsById[savedReport.id || savedReport.uuid]" class="loading">Loading report...</div>
                                <div v-else class="report-body">
                                    <iframe 
                                        v-if="getReportPdfUrl(savedReport)" 
                                        :src="getReportPdfUrl(savedReport)" 
                                        class="pdf-viewer"
                                        frameborder="0"
                                    ></iframe>
                                    <div v-else class="report-error">PDF not available</div>
                                </div>
                            </div>
                        </li>
                    </ul>
        </div>

                <!-- Short Position Reports -->
                <div v-if="activeCategory === 'short'" class="report-category">
                    <div v-if="shortReports.length === 0" class="no-reports">No short position reports</div>
            <ul v-else class="report-list">
                        <li v-for="savedReport in shortReports" :key="savedReport.id || savedReport.uuid" :class="{ active: expandedReportIds.has(savedReport.id || savedReport.uuid) }">
                            <div class="report-item-header" @click="toggleReport(savedReport)">
                                <span class="report-ticker">{{ savedReport.ticker }} - {{ new Date(savedReport.created_at || savedReport.date || savedReport.timestamp).toLocaleDateString('en-US', { year: 'numeric', month: '2-digit', day: '2-digit' }) }}</span>
                                <span class="report-date">{{ formatDate(savedReport.created_at || savedReport.date || savedReport.timestamp) }}</span>
                            </div>
                            <div v-if="expandedReportIds.has(savedReport.id || savedReport.uuid)" class="report-item-content">
                                <div v-if="loadingReportsById[savedReport.id || savedReport.uuid]" class="loading">Loading report...</div>
                                <div v-else class="report-body">
                                    <iframe 
                                        v-if="getReportPdfUrl(savedReport)" 
                                        :src="getReportPdfUrl(savedReport)" 
                                        class="pdf-viewer"
                                        frameborder="0"
                                    ></iframe>
                                    <div v-else class="report-error">PDF not available</div>
                                </div>
                            </div>
                </li>
            </ul>
        </div>
    </div>
            </div>
        </div>
    </div>
  </div>
</template>

<script setup>
import API_BASE_URL from '@/config/api.js'

import { ref, computed, onMounted, onUnmounted } from 'vue';
import { marked } from 'marked';
import { useRouter } from 'vue-router';
import PaymentGate from './PaymentGate.vue';

const router = useRouter();

// Payment State
const hasPaid = ref(false);
const loading = ref(true);

// Saved Reports State
const savedReports = ref([]);
const loadingReports = ref(false);
const expandedReportIds = ref(new Set()); // Track multiple expanded reports
const activeCategory = ref('long');

// Report Content State - store content by report ID
const reportContents = ref({});
const loadingReportsById = ref({}); // Track loading state per report



// Categories for tabs
const categories = [
  { label: 'Market Report', value: 'market' },
  { label: 'Daily Report', value: 'daily' },
  { label: 'Long Position Report', value: 'long' },
  { label: 'Short Position Report', value: 'short' }
];

// Filtered reports by category
const longReports = computed(() => {
    const apiLongReports = savedReports.value.filter(report => 
        report.report_type && report.report_type.toLowerCase().includes('long')
    );
    // Sort by date, newest first
    return apiLongReports.sort((a, b) => {
        const dateA = new Date(a.created_at || a.date || a.timestamp || 0);
        const dateB = new Date(b.created_at || b.date || b.timestamp || 0);
        return dateB - dateA;
    });
});

const shortReports = computed(() => {
    const apiShortReports = savedReports.value.filter(report => 
        report.report_type && report.report_type.toLowerCase().includes('short')
    );
    // Sort by date, newest first
    return apiShortReports.sort((a, b) => {
        const dateA = new Date(a.created_at || a.date || a.timestamp || 0);
        const dateB = new Date(b.created_at || b.date || b.timestamp || 0);
        return dateB - dateA;
    });
});

const dailyReports = computed(() => {
    const apiDailyReports = savedReports.value.filter(report => 
        report.report_type && report.report_type.toLowerCase().includes('daily')
    );
    // Sort by date, newest first
    return apiDailyReports.sort((a, b) => {
        const dateA = new Date(a.created_at || a.date || a.timestamp || 0);
        const dateB = new Date(b.created_at || b.date || b.timestamp || 0);
        return dateB - dateA;
    });
});

const marketReports = computed(() => {
    // Filter market reports
    const apiMarketReports = savedReports.value.filter(report => 
        report.report_type && report.report_type.toLowerCase() === 'market'
    );
    // Sort by date, newest first
    return apiMarketReports.sort((a, b) => {
        const dateA = new Date(a.created_at || a.date || a.timestamp || 0);
        const dateB = new Date(b.created_at || b.date || b.timestamp || 0);
        return dateB - dateA;
    });
});

const checkPaymentStatus = async () => {
  const token = localStorage.getItem('access_token');
  if (!token) {
    router.push('/login');
    return;
  }
  
  try {
    const response = await fetch('${API_BASE_URL}/api/auth/payment-status', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (response.ok) {
      const status = await response.json();
      hasPaid.value = status.has_paid || false;
      // Fetch reports if user has paid
      if (hasPaid.value) {
        fetchReports();
      }
    } else if (response.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      router.push('/login');
    }
  } catch (error) {
    console.error('Error checking payment status:', error);
    // On error, deny access (fail closed for payment)
    hasPaid.value = false;
  } finally {
    loading.value = false;
  }
};

// Event handler functions
const handlePaymentVerified = () => {
  checkPaymentStatus();
};

const handleReportPublished = () => {
  if (hasPaid.value) {
    fetchReports();
  }
};

const handleReportDeleted = () => {
  if (hasPaid.value) {
    fetchReports(); // Refetch reports when one is deleted
  }
};

onMounted(() => {
  checkPaymentStatus();
  
  // Listen for payment verification events
  window.addEventListener('payment-verified', handlePaymentVerified);
  
  // Listen for report published events to refetch reports
  window.addEventListener('report-published', handleReportPublished);
  
  // Listen for report deleted events to refetch reports
  window.addEventListener('report-deleted', handleReportDeleted);
});

// Cleanup event listeners on unmount
onUnmounted(() => {
  window.removeEventListener('payment-verified', handlePaymentVerified);
  window.removeEventListener('report-published', handleReportPublished);
  window.removeEventListener('report-deleted', handleReportDeleted);
});

const fetchReports = async () => {
    loadingReports.value = true;
    try {
        const token = localStorage.getItem('access_token');
        if (!token) {
            router.push('/login');
            return;
        }
        
        // Fetch reports from MinIO for each category
        const [dailyResponse, marketResponse, longResponse, shortResponse] = await Promise.all([
            fetch('${API_BASE_URL}/api/reports/minio/daily', {
                headers: { 'Authorization': `Bearer ${token}` }
            }),
            fetch('${API_BASE_URL}/api/reports/minio/market', {
                headers: { 'Authorization': `Bearer ${token}` }
            }),
            fetch('${API_BASE_URL}/api/reports/minio/long', {
                headers: { 'Authorization': `Bearer ${token}` }
            }),
            fetch('${API_BASE_URL}/api/reports/minio/short', {
                headers: { 'Authorization': `Bearer ${token}` }
            })
        ]);
        
        const allReports = [];
        
        if (dailyResponse.ok) {
            const daily = await dailyResponse.json();
            allReports.push(...daily);
        }
        if (marketResponse.ok) {
            const market = await marketResponse.json();
            allReports.push(...market);
        }
        if (longResponse.ok) {
            const long = await longResponse.json();
            allReports.push(...long);
        }
        if (shortResponse.ok) {
            const short = await shortResponse.json();
            allReports.push(...short);
        }
        
        savedReports.value = allReports;
    } catch (e) {
        console.error("Failed to fetch reports", e);
    } finally {
        loadingReports.value = false;
    }
};

const toggleReport = async (savedReportSummary) => {
    const reportId = savedReportSummary.id || savedReportSummary.uuid;
    
    // If clicking an expanded report, collapse it
    if (expandedReportIds.value.has(reportId)) {
        expandedReportIds.value.delete(reportId);
        return;
    }
    
    // Otherwise, expand the clicked report
    expandedReportIds.value.add(reportId);
    
    // Mark as loaded (PDFs are loaded via iframe src, no need to fetch content)
    loadingReportsById.value[reportId] = false;
};

const getReportPdfUrl = (savedReportSummary) => {
    // Construct PDF URL from report metadata
    const reportType = savedReportSummary.report_type || 'daily';
    const ticker = savedReportSummary.ticker || 'MARKET';
    const date = savedReportSummary.date || new Date(savedReportSummary.created_at || savedReportSummary.timestamp).toISOString().split('T')[0];
    const uuid = savedReportSummary.uuid || savedReportSummary.id;
    
    if (!uuid || !date) {
        return null;
    }
    
    const token = localStorage.getItem('access_token');
    if (!token) {
        return null;
    }
    
    // Construct URL to backend PDF endpoint with token as query parameter
    // Encode the ticker and other path components to handle special characters
    const encodedTicker = encodeURIComponent(ticker);
    const encodedDate = encodeURIComponent(date);
    const encodedUuid = encodeURIComponent(uuid);
    const encodedReportType = encodeURIComponent(reportType);
    
    return `${API_BASE_URL}/api/reports/minio/pdf/${encodedReportType}/${encodedTicker}/${encodedDate}/${encodedUuid}?token=${encodeURIComponent(token)}`;
};

const formatDate = (dateString) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString() + ' ' + new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

</script>

<style scoped>
/* Page Layout - AlphaTrade Style */
.report-view {
  font-family: 'Inter', sans-serif;
  max-width: 1600px;
  margin: 0 auto;
  padding: 2rem;
  background-color: #ffffff;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.report-view h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #000000;
  margin: 0 0 2rem 0;
  text-transform: uppercase;
  letter-spacing: 1px;
  border-bottom: 3px solid #000;
  padding-bottom: 1rem;
}

/* Tabs - AlphaTrade Style */
.category-tabs {
  display: flex;
  background: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
  margin-bottom: 2rem;
  overflow-x: auto;
  justify-content: flex-start;
  padding-bottom: 0;
}

.category-tabs button {
  padding: 1rem 1.5rem;
  background: none;
  border: none;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  cursor: pointer;
  color: #666;
  transition: all 0.2s;
  border-bottom: 3px solid transparent;
  border-radius: 0;
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

/* Content Area */
.content-container {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.main-report-area {
  flex: 1;
  overflow-y: auto;
  padding-right: 0;
}

.report-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.report-list li {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
  background: #fafafa;
}

.report-item-header {
  padding: 1rem 1.25rem;
  cursor: pointer;
  transition: background 0.2s;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #ffffff;
}

.report-item-header:hover {
  background: #f5f5f5;
}

.report-list li.active .report-item-header {
  background: #f0f0f0;
  border-bottom: 1px solid #e0e0e0;
}

.report-ticker {
  font-weight: 700;
  color: #000000;
  flex: 1;
  font-size: 0.875rem;
  letter-spacing: 0.5px;
}

.report-date {
  font-size: 0.75rem;
  color: #666666;
  margin-left: 1rem;
  font-weight: 500;
}

.report-item-content {
  background: #ffffff;
  padding: 0;
  animation: slideDown 0.3s ease-out;
  border-top: 1px solid #e0e0e0;
}

.report-body {
  padding: 2rem;
  color: #000000;
  font-size: 0.95em;
  line-height: 1.8;
}

@keyframes slideDown {
  from { opacity: 0; max-height: 0; }
  to { opacity: 1; max-height: 800px; }
}

.report-category {
  margin-top: 0;
}

.loading {
  text-align: center;
  margin: 20px 0;
  color: #666;
  font-style: italic;
  font-size: 0.875rem;
}

.pdf-viewer {
  width: 100%;
  height: 800px;
  border: none;
  display: block;
}

.report-error {
  color: #ef4444;
  text-align: center;
  padding: 2rem;
  font-style: italic;
}

/* Markdown Styles within Reports */
.report-body :deep(h1), 
.report-body :deep(h2), 
.report-body :deep(h3) {
  color: #000000;
  margin-top: 1.5em;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.report-body :deep(h1) { font-size: 1.5rem; border-bottom: 2px solid #000; padding-bottom: 0.5rem; }
.report-body :deep(h2) { font-size: 1.25rem; border-bottom: 1px solid #e0e0e0; padding-bottom: 0.25rem; }
.report-body :deep(h3) { font-size: 1rem; }

.report-body :deep(ul), .report-body :deep(ol) {
  padding-left: 1.5rem;
  color: #000000;
}

.report-body :deep(p) {
  margin-bottom: 1rem;
  color: #333333;
}

.report-body :deep(li) {
  margin-bottom: 0.25rem;
}

.report-body :deep(strong), .report-body :deep(b) {
  color: #000000;
  font-weight: 700;
}

.no-reports {
  color: #666666;
  font-style: italic;
  text-align: center;
  padding: 3rem;
  background: #fafafa;
  border: 1px dashed #e0e0e0;
  border-radius: 4px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 50vh;
  gap: 1rem;
}

.loading-container p {
  color: #666666;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f0f0f0;
  border-top-color: #000000;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

</style>
