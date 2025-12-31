<template>
  <div class="security-view">
    <h2>{{ t('security.title') }}</h2>
    
    <div class="content-section">
      <div class="info-card">
        <h3>{{ t('security.section_title') }}</h3>
        <p>{{ t('security.description') }}</p>
        <p class="coming-soon">{{ t('security.coming_soon') }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n';
const { t } = useI18n();
</script>

<style scoped>
.security-view {
  padding: 30px 30px 30px 0;
  max-width: 1600px;
  margin: 0 auto;
}

.security-view h2 {
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


