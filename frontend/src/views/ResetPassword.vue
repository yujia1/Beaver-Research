<template>
  <div class="auth-container">
    <div class="auth-card">
      <h2>Reset Password</h2>
      <p>Enter your new password below.</p>
      
      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="password">New Password</label>
          <input 
            type="password" 
            id="password" 
            v-model="password" 
            required 
            placeholder="At least 6 characters"
            minlength="6"
          >
        </div>

        <div class="form-group">
          <label for="confirmPassword">Confirm Password</label>
          <input 
            type="password" 
            id="confirmPassword" 
            v-model="confirmPassword" 
            required 
            placeholder="Confirm new password"
            minlength="6"
          >
        </div>

        <button type="submit" :disabled="loading" class="submit-btn">
          {{ loading ? 'Updating...' : 'Set New Password' }}
        </button>
      </form>

      <div v-if="message" class="message success">
        {{ message }}
      </div>
      <div v-if="error" class="message error">
        {{ error }}
      </div>

      <div class="links" v-if="message">
        <router-link to="/login">Click here to Login</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import API_BASE_URL from '@/config/api';

const route = useRoute();
const password = ref('');
const confirmPassword = ref('');
const loading = ref(false);
const message = ref('');
const error = ref('');
const token = ref('');

onMounted(() => {
    token.value = route.query.token;
    if (!token.value) {
        error.value = "Invalid reset link. No token provided.";
    }
});

const handleSubmit = async () => {
  if (password.value !== confirmPassword.value) {
      error.value = "Passwords do not match";
      return;
  }
  
  if (!token.value) {
      error.value = "Missing reset token.";
      return;
  }

  loading.value = true;
  message.value = '';
  error.value = '';

  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/reset-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
          token: token.value, 
          new_password: password.value 
      })
    });

    if (!response.ok) {
       const errData = await response.json();
       throw new Error(errData.detail || 'Failed to reset password');
    }

    const data = await response.json();
    message.value = data.message;
    password.value = '';
    confirmPassword.value = '';
    
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
/* Reuse styles from ForgotPassword or common auth styles */
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
  padding: 1rem;
}

.auth-card {
  background: #1f2937;
  padding: 2.5rem;
  border-radius: 1rem;
  width: 100%;
  max-width: 400px;
  border: 1px solid #374151;
}

h2 {
  color: #f3f4f6;
  margin-bottom: 0.5rem;
  text-align: center;
}

p {
  color: #9ca3af;
  margin-bottom: 2rem;
  text-align: center;
  font-size: 0.9rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  color: #d1d5db;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

input {
  width: 100%;
  padding: 0.75rem;
  background: #374151;
  border: 1px solid #4b5563;
  border-radius: 0.5rem;
  color: white;
  transition: border-color 0.2s;
}

input:focus {
  outline: none;
  border-color: #60a5fa;
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
  background: #4b5563;
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
  background: #064e3b;
  color: #34d399;
}

.message.error {
  background: #7f1d1d;
  color: #fca5a5;
}

.links {
  margin-top: 1.5rem;
  text-align: center;
}

.links a {
  color: #60a5fa;
  text-decoration: none;
  font-size: 0.9rem;
}

.links a:hover {
  text-decoration: underline;
}
</style>
