<template>
  <div class="auth-container">
    <div class="auth-card">
      <h2>{{ t('auth.forgot_password_title') }}</h2>
      <p>{{ t('auth.forgot_password_subtitle') }}</p>
      
      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="email">{{ t('auth.email') }}</label>
          <input 
            type="email" 
            id="email" 
            v-model="email" 
            required 
            :placeholder="t('auth.email_placeholder')"
          >
        </div>

        <button type="submit" :disabled="loading" class="submit-btn">
          {{ loading ? t('auth.sending') : t('auth.send_reset_link') }}
        </button>
      </form>

      <div v-if="message" class="message success">
        {{ message }}
      </div>
      <div v-if="error" class="message error">
        {{ error }}
      </div>

      <div class="links">
        <router-link to="/login">{{ t('auth.back_to_login') }}</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import API_BASE_URL from '@/config/api';

const { t } = useI18n();
const email = ref('');
const loading = ref(false);
const message = ref('');
const error = ref('');

const handleSubmit = async () => {
  loading.value = true;
  message.value = '';
  error.value = '';

  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/forgot-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.value })
    });

    if (!response.ok) {
       // Even if failed, we might want to be vague for security, 
       // but here we trust the backend to always return success structure unless 500
       const errData = await response.json();
       throw new Error(errData.detail || t('common.error'));
    }

    const data = await response.json();
    message.value = data.message;
    email.value = ''; // clear input
    
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
};
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
  background: #ffffff;
  padding: 2.5rem;
  border-radius: 1rem;
  width: 100%;
  max-width: 400px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

h2 {
  color: #111827;
  margin-bottom: 0.5rem;
  text-align: center;
}

p {
  color: #6b7280;
  margin-bottom: 2rem;
  text-align: center;
  font-size: 0.9rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  color: #374151;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

input {
  width: 100%;
  padding: 0.75rem;
  background: #f9fafb;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  color: #111827;
  transition: border-color 0.2s;
}

input:focus {
  outline: none;
  border-color: #3b82f6;
  background: #ffffff;
}

.submit-btn {
  width: 100%;
  padding: 0.75rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.submit-btn:hover {
  background: #1d4ed8;
}

.submit-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.message {
  margin-top: 1rem;
  padding: 0.75rem;
  border-radius: 0.5rem;
  font-size: 0.9rem;
  text-align: center;
}

.message.success {
  background: #ecfdf5;
  color: #059669;
}

.message.error {
  background: #fef2f2;
  color: #dc2626;
}

.links {
  margin-top: 1.5rem;
  text-align: center;
}

.links a {
  color: #2563eb;
  text-decoration: none;
  font-size: 0.9rem;
}

.links a:hover {
  text-decoration: underline;
  color: #1d4ed8;
}
</style>
