<template>
  <div class="auth-container">
    <div class="auth-card">
      <h2>{{ t('auth.verify_email_title') }}</h2>
      
      <div v-if="loading" class="status">
        <div class="spinner"></div>
        <p>{{ t('auth.verifying') }}</p>
      </div>

      <div v-else-if="success" class="status success">
        <div class="icon">✓</div>
        <p>{{ t('auth.verify_success') }}</p>
        <router-link to="/dashboard" class="action-btn">{{ t('auth.go_to_dashboard') }}</router-link>
      </div>

      <div v-else class="status error">
        <div class="icon">✕</div>
        <p>{{ t('auth.verify_failed') }}</p>
        <p class="error-detail">{{ error }}</p>
        <router-link to="/login" class="action-btn secondary">{{ t('auth.back_to_login') }}</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import API_BASE_URL from '@/config/api';

const route = useRoute();
const { t } = useI18n();
const loading = ref(true);
const success = ref(false);
const error = ref('');

onMounted(async () => {
    const token = route.query.token;
    if (!token) {
        error.value = t('auth.no_token');
        loading.value = false;
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/verify-email?token=${token}`);
        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || t('common.error'));
        }
        success.value = true;
    } catch (e) {
        error.value = e.message;
    } finally {
        loading.value = false;
    }
});
</script>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
  padding: 1rem;
}

.auth-card {
  background: #1f2937;
  padding: 3rem;
  border-radius: 1rem;
  width: 100%;
  max-width: 450px;
  border: 1px solid #374151;
  text-align: center;
}

h2 {
  color: #f3f4f6;
  margin-bottom: 2rem;
}

.status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #374151;
  border-top: 4px solid #60a5fa;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  color: white;
}

.success .icon {
  background: #059669;
}

.error .icon {
  background: #dc2626;
}

p {
  color: #d1d5db;
  font-size: 1.1rem;
}

.error-detail {
  color: #fca5a5;
  font-size: 0.9rem;
}

.action-btn {
  background: #2563eb;
  color: white;
  padding: 0.75rem 2rem;
  border-radius: 0.5rem;
  text-decoration: none;
  font-weight: 600;
  transition: background 0.2s;
}

.action-btn:hover {
  background: #1d4ed8;
}

.action-btn.secondary {
  background: #4b5563;
}

.action-btn.secondary:hover {
  background: #374151;
}
</style>
