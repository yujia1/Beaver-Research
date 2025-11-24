<template>
  <div class="productivity-view">
    <h2>Productivity</h2>
    
    <div class="content-section">
      <div class="info-card">
        <h3>📊 Productivity Metrics</h3>
        <p>This section will display productivity-related economic indicators and metrics.</p>
        <p class="coming-soon">Coming soon: Labor productivity, GDP per capita, manufacturing productivity, and more.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
// Component logic will be added here
</script>

<style scoped>
.productivity-view {
  padding: 30px 30px 30px 0;
  max-width: 1600px;
  margin: 0 auto;
}

.productivity-view h2 {
  margin: 0 0 24px 0;
  font-size: 2em;
  color: #ecf0f1;
  text-align: center;
}

.content-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.info-card {
  border: 1px solid #34495e;
  padding: 30px;
  border-radius: 12px;
  background: #2c3e50;
  color: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.info-card h3 {
  margin: 0 0 16px 0;
  font-size: 1.5em;
  color: #42b983;
}

.info-card p {
  margin: 12px 0;
  line-height: 1.6;
  color: #bdc3c7;
}

.coming-soon {
  font-style: italic;
  color: #95a5a6;
  margin-top: 20px;
}
</style>

