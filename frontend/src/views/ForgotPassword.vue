<template>
  <div class="auth-container">
    <div class="auth-card">
      <h2>Forgot Password</h2>
      <p>Enter your email address and we'll send you a link to reset your password.</p>
      
      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="email">Email Address</label>
          <input 
            type="email" 
            id="email" 
            v-model="email" 
            required 
            placeholder="Enter your email"
          >
        </div>

        <button type="submit" :disabled="loading" class="submit-btn">
          {{ loading ? 'Sending...' : 'Send Reset Link' }}
        </button>
      </form>

      <div v-if="message" class="message success">
        {{ message }}
      </div>
      <div v-if="error" class="message error">
        {{ error }}
      </div>

      <div class="links">
        <router-link to="/login">Back to Login</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import API_BASE_URL from '@/config/api';

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
       throw new Error(errData.detail || 'An error occurred');
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
