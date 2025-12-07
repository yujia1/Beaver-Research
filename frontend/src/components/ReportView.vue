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
                                <div v-else class="report-body" v-html="getReportContent(savedReport)"></div>
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
                                <div v-else class="report-body" v-html="getReportContent(savedReport)"></div>
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
                                <div v-else class="report-body" v-html="getReportContent(savedReport)"></div>
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

// Mock data removed - using only API data from MinIO
const mockDailyReports = []

const mockLongReports = []

const mockShortReports = []

// Categories for tabs
const categories = [
  { label: 'Market Report', value: 'market' },
  { label: 'Daily Report', value: 'daily' },
  { label: 'Long Position Report', value: 'long' },
  { label: 'Short Position Report', value: 'short' }
];

// Filtered reports by category
const longReports = computed(() => {
    // Combine API reports with mock data
    const apiLongReports = savedReports.value.filter(report => 
        report.report_type && report.report_type.toLowerCase().includes('long')
    );
    // Sort by date, newest first
    return [...mockLongReports, ...apiLongReports].sort((a, b) => {
        const dateA = new Date(a.created_at || a.date || a.timestamp || 0);
        const dateB = new Date(b.created_at || b.date || b.timestamp || 0);
        return dateB - dateA;
    });
});

const shortReports = computed(() => {
    // Combine API reports with mock data
    const apiShortReports = savedReports.value.filter(report => 
        report.report_type && report.report_type.toLowerCase().includes('short')
    );
    // Sort by date, newest first
    return [...mockShortReports, ...apiShortReports].sort((a, b) => {
        const dateA = new Date(a.created_at || a.date || a.timestamp || 0);
        const dateB = new Date(b.created_at || b.date || b.timestamp || 0);
        return dateB - dateA;
    });
});

const dailyReports = computed(() => {
    // Combine API reports with mock data
    const apiDailyReports = savedReports.value.filter(report => 
        report.report_type && report.report_type.toLowerCase().includes('daily')
    );
    // Sort by date, newest first
    return [...mockDailyReports, ...apiDailyReports].sort((a, b) => {
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
    const response = await fetch('http://localhost:8000/api/auth/payment-status', {
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
            fetch('http://localhost:8000/api/reports/minio/daily', {
                headers: { 'Authorization': `Bearer ${token}` }
            }),
            fetch('http://localhost:8000/api/reports/minio/market', {
                headers: { 'Authorization': `Bearer ${token}` }
            }),
            fetch('http://localhost:8000/api/reports/minio/long', {
                headers: { 'Authorization': `Bearer ${token}` }
            }),
            fetch('http://localhost:8000/api/reports/minio/short', {
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
    
    // If content is already loaded, don't fetch again
    if (reportContents.value[reportId]) {
        return;
    }
    
    loadingReportsById.value[reportId] = true;
    
    try {
        // Check if it's a report from MinIO (has content already)
        if (savedReportSummary.content) {
            reportContents.value[reportId] = savedReportSummary.content;
            loadingReportsById.value[reportId] = false;
        } else if (savedReportSummary.id) {
            // Fetch from database API if it has a numeric ID
        const response = await fetch(`http://localhost:8000/api/reports/${savedReportSummary.id}`);
        if (!response.ok) throw new Error('Failed to fetch report content');
        const data = await response.json();
            reportContents.value[reportId] = data.content;
        } else {
            reportContents.value[reportId] = "Report content not available.";
        }
    } catch (e) {
        console.error("Failed to load report", e);
        reportContents.value[reportId] = "Failed to load report content.";
    } finally {
        loadingReportsById.value[reportId] = false;
    }
};

const getReportContent = (savedReportSummary) => {
    // If content is already in the report object (from MinIO), use it
    if (savedReportSummary.content) {
        try {
            return marked(savedReportSummary.content);
        } catch {
            return savedReportSummary.content.replace(/\n/g, '<br>');
        }
    }
    // Otherwise, use cached content
    const content = reportContents.value[savedReportSummary.id];
    if (!content) return '';
    
    try {
        return marked(content);
    } catch {
        return content.replace(/\n/g, '<br>');
    }
};

const formatDate = (dateString) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString() + ' ' + new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

</script>

<style scoped>
.report-view {
  padding: 20px;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.report-view h2 {
  color: #000000;
}

.category-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 30px;
  justify-content: center;
  flex-wrap: nowrap;
  border-bottom: 2px solid #cccccc;
  padding-bottom: 12px;
  overflow-x: auto;
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

.content-container {
    flex: 1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}

.main-report-area {
    flex: 1;
    overflow-y: auto;
    padding-right: 10px;
    min-height: 0;
}

.report-list {
    list-style: none;
    padding: 0;
    margin: 0;
}

.report-list li {
    border-bottom: 1px solid #eee;
    border-radius: 6px;
    margin-bottom: 5px;
    overflow: hidden;
}

.report-item-header {
    padding: 12px;
    cursor: pointer;
    transition: background 0.2s;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.report-item-header:hover {
    background: #e9ecef;
}

.report-list li.active .report-item-header {
    background: #e3f2fd;
    border-left: 4px solid #42b983;
}

.report-item-content {
    border-top: 1px solid #e0e0e0;
    animation: slideDown 0.3s ease-out;
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    margin: 10px 0;
    max-height: 600px;
    overflow-y: auto;
}

.report-item-content .report-body {
    padding: 20px;
    color: #000000;
    font-size: 0.95em;
    line-height: 1.8;
}

@keyframes slideDown {
    from {
        opacity: 0;
        max-height: 0;
    }
    to {
        opacity: 1;
        max-height: 600px;
    }
}

.report-ticker {
    font-weight: 600;
    color: #000000;
    flex: 1;
}

.report-date {
    font-size: 0.85em;
    color: #000000;
    margin-left: 10px;
}

.report-category {
    margin-top: 20px;
}

.loading {
  text-align: center;
  margin: 20px 0;
  color: #42b983;
}

.report-body {
    line-height: 1.6;
    color: #000000;
}

.report-body :deep(h1), .report-body :deep(h2), .report-body :deep(h3), .report-body :deep(h4), .report-body :deep(h5), .report-body :deep(h6) {
    color: #000000;
    margin-top: 1.5em;
}

.report-body :deep(ul), .report-body :deep(ol) {
    padding-left: 20px;
    color: #000000;
}

.report-body :deep(p) {
    margin-bottom: 1em;
    color: #000000;
}

.report-body :deep(li) {
    color: #000000;
}

.report-body :deep(strong), .report-body :deep(b) {
    color: #000000;
}

.report-body :deep(*) {
    color: #000000;
}


.close-btn {
    padding: 6px 12px;
    background: #95a5a6;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

.close-btn:hover {
    background: #7f8c8d;
}

.no-reports {
    color: black;
    font-style: italic;
    text-align: center;
    margin-top: 20px;
}

.loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    gap: 1rem;
}

.loading-container p {
    color: #a8a29e;
    font-size: 1rem;
}

.loading-spinner {
    width: 40px;
    height: 40px;
    border: 4px solid rgba(255, 255, 255, 0.1);
    border-top-color: #42b983;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

</style>
