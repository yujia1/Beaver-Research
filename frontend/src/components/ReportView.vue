<template>
  <div class="report-view">
    <h2>Reports</h2>
    
    <div class="content-container">
        <!-- Main Content Area -->
        <div class="main-report-area">
            <div class="upload-section" v-if="!report">
              <h3>Upload Document (PDF/HTML)</h3>
              <input type="file" @change="handleFileUpload" :disabled="loading" />
            </div>
            
            <div v-if="loading" class="loading">
              <p>{{ statusMessage }}</p>
            </div>
            
            <div v-else-if="error" class="error">{{ error }}</div>
            
            <!-- Generated Report (Immediate) -->
            <div class="report-content" v-if="report">
              <h3>Generated Report</h3>
              <div class="report-body" v-html="formattedReport"></div>
            </div>
        </div>

        <!-- Sidebar for Saved Reports (Right Side) -->
        <div class="reports-sidebar">
            <h3>Saved Reports</h3>
            <div v-if="loadingReports" class="loading-small">Loading...</div>
            <div v-else-if="savedReports.length === 0" class="no-reports">No saved reports</div>
            <ul v-else class="report-list">
                <li v-for="savedReport in savedReports" :key="savedReport.id" @click="selectReport(savedReport)" :class="{ active: selectedReportId === savedReport.id }">
                    <span class="report-ticker">{{ savedReport.ticker || savedReport.title }}</span>
                </li>
            </ul>
        </div>
    </div>

    <!-- Modal for Viewing Reports -->
    <div v-if="showModal" class="modal-overlay" @click="closeModal">
        <div class="modal-content" @click.stop>
            <div class="modal-header">
                <h3>{{ selectedReportTitle }}</h3>
                <button @click="closeModal" class="close-btn">Close</button>
            </div>
            <div class="modal-body">
                <div v-if="loadingModal" class="loading">Loading report...</div>
                <div v-else class="report-body" v-html="formattedModalReport"></div>
            </div>
        </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { marked } from 'marked';

// Main Report State (Generated)
const report = ref('');
const loading = ref(false);
const error = ref(null);
const statusMessage = ref('');

// Saved Reports State
const savedReports = ref([]);
const loadingReports = ref(false);
const selectedReportId = ref(null);
const selectedReportTitle = ref('');
const showModal = ref(false);

// Modal Report State
const modalReportContent = ref('');
const loadingModal = ref(false);

onMounted(() => {
    fetchReports();
});

const fetchReports = async () => {
    loadingReports.value = true;
    try {
        const response = await fetch('http://localhost:8000/api/reports/');
        if (response.ok) {
            savedReports.value = await response.json();
        }
    } catch (e) {
        console.error("Failed to fetch reports", e);
    } finally {
        loadingReports.value = false;
    }
};

const selectReport = async (savedReportSummary) => {
    selectedReportId.value = savedReportSummary.id;
    selectedReportTitle.value = savedReportSummary.title || savedReportSummary.ticker;
    loadingModal.value = true; // Use separate loading state
    showModal.value = true;
    
    try {
        const response = await fetch(`http://localhost:8000/api/reports/${savedReportSummary.id}`);
        if (!response.ok) throw new Error('Failed to fetch report content');
        const data = await response.json();
        modalReportContent.value = data.content;
    } catch (e) {
        console.error("Failed to load report", e);
        modalReportContent.value = "Failed to load report content.";
    } finally {
        loadingModal.value = false;
    }
};

const closeModal = () => {
    showModal.value = false;
    selectedReportId.value = null;
    selectedReportTitle.value = '';
    modalReportContent.value = '';
};

const formatDate = (dateString) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString() + ' ' + new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

// Formatter for Main Report
const formattedReport = computed(() => {
    try {
        return marked(report.value);
    } catch {
        return report.value.replace(/\n/g, '<br>');
    }
});

// Formatter for Modal Report
const formattedModalReport = computed(() => {
    try {
        return marked(modalReportContent.value);
    } catch {
        return modalReportContent.value.replace(/\n/g, '<br>');
    }
});

const handleFileUpload = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  loading.value = true;
  error.value = null;
  report.value = '';
  
  try {
    statusMessage.value = 'Uploading and extracting text...';
    const formData = new FormData();
    formData.append('file', file);
    
    const uploadResponse = await fetch('http://localhost:8000/api/external/upload', {
      method: 'POST',
      body: formData
    });
    
    if (!uploadResponse.ok) throw new Error('Upload failed');
    const uploadData = await uploadResponse.json();
    
    statusMessage.value = 'Generating AI Report...';
    const agentResponse = await fetch('http://localhost:8000/api/agent/generate_report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        data_context: uploadData.content_preview,
        prompt_customization: "Analyze this financial document and provide a summary."
      })
    });
    
    if (!agentResponse.ok) throw new Error('Report generation failed');
    const agentData = await agentResponse.json();
    report.value = agentData.report;

  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.report-view {
  padding: 20px;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.content-container {
    display: flex;
    gap: 20px;
    flex: 1;
    overflow: hidden;
}

.reports-sidebar {
    width: 250px; /* Reduced width for tickers */
    background: #f8f9fa;
    border-left: 1px solid #e0e0e0; /* Changed to border-left */
    padding: 15px;
    overflow-y: auto;
    border-radius: 8px;
    /* Order 2 to appear on right if we didn't swap HTML, but we swapped HTML so this is fine */
}

.report-list {
    list-style: none;
    padding: 0;
    margin: 0;
}

.report-list li {
    padding: 10px;
    border-bottom: 1px solid #eee;
    cursor: pointer;
    transition: background 0.2s;
    border-radius: 6px;
    margin-bottom: 5px;
}

.report-list li:hover {
    background: #e9ecef;
}

.report-list li.active {
    background: #e3f2fd;
    border-left: 4px solid #42b983;
}

.report-ticker {
    font-weight: 600;
    color: #2c3e50;
    display: block; /* Ensure it takes space */
}

.main-report-area {
    flex: 1;
    overflow-y: auto;
    padding-right: 10px;
}

.upload-section {
  margin-bottom: 20px;
  padding: 40px;
  border: 2px dashed #ccc;
  border-radius: 8px;
  text-align: center;
  background: #fafafa;
}

.loading {
  text-align: center;
  margin: 20px 0;
  color: #42b983;
}

.error {
  color: red;
  text-align: center;
  padding: 20px;
  background: #fff0f0;
  border-radius: 8px;
}

.report-content {
  background: #fff;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  color: #333;
}

.report-body {
    line-height: 1.6;
}

.report-body :deep(h1), .report-body :deep(h2), .report-body :deep(h3) {
    color: #2c3e50;
    margin-top: 1.5em;
}

.report-body :deep(ul), .report-body :deep(ol) {
    padding-left: 20px;
}

.report-body :deep(p) {
    margin-bottom: 1em;
}

/* Modal Styles */
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.modal-content {
    background: white;
    padding: 20px;
    border-radius: 8px;
    width: 80%;
    max-width: 900px;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
    border-bottom: 1px solid #eee;
    padding-bottom: 10px;
}

.modal-body {
    overflow-y: auto;
    flex: 1;
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

</style>
