<template>
  <div class="report-view">
    <h2>AI Reports</h2>
    <div class="upload-section">
      <h3>Upload Document (PDF/HTML)</h3>
      <input type="file" @change="handleFileUpload" :disabled="loading" />
    </div>
    
    <div v-if="loading" class="loading">
      <p>{{ statusMessage }}</p>
    </div>
    
    <div v-else-if="error" class="error">{{ error }}</div>
    
    <div class="report-content" v-if="report">
      <h3>Generated Report</h3>
      <div class="report-body" v-html="formattedReport"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { marked } from 'marked'; // Need to install marked or just display plain text

const report = ref('');
const loading = ref(false);
const error = ref(null);
const statusMessage = ref('');

// Simple markdown formatter if marked is not available, or just use pre-wrap
const formattedReport = computed(() => {
    // For now, just wrap in pre tags or basic formatting
    return report.value.replace(/\n/g, '<br>');
});

const handleFileUpload = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  loading.value = true;
  error.value = null;
  report.value = '';
  
  try {
    // 1. Upload File
    statusMessage.value = 'Uploading and extracting text...';
    const formData = new FormData();
    formData.append('file', file);
    
    const uploadResponse = await fetch('http://localhost:8000/api/external/upload', {
      method: 'POST',
      body: formData
    });
    
    if (!uploadResponse.ok) throw new Error('Upload failed');
    const uploadData = await uploadResponse.json();
    
    // 2. Generate Report
    statusMessage.value = 'Generating AI Report...';
    const agentResponse = await fetch('http://localhost:8000/api/agent/generate_report', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        data_context: uploadData.content_preview, // Sending preview for now to avoid token limits, or full text if needed
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
  padding: 20px 20px 20px 0;
}
.upload-section {
  margin-bottom: 20px;
  padding: 20px;
  border: 2px dashed #ccc;
  border-radius: 8px;
  text-align: center;
}
.loading {
  text-align: center;
  margin: 20px 0;
  color: #42b983;
}
.error {
  color: red;
  text-align: center;
}
.report-content {
  background: #f9f9f9;
  padding: 20px;
  border-radius: 8px;
  color: #333;
}
.report-body {
    white-space: pre-wrap;
    font-family: sans-serif;
}
</style>
