<template>
  <div class="signup-view">
    <div class="signup-container">
      <div class="signup-card">
        <h1>{{ t('auth.signup_title') }}</h1>
        <p class="subtitle">{{ t('auth.signup_subtitle') }}</p>
        
        <form @submit.prevent="handleSignup" class="signup-form">
          <div class="form-group">
            <label for="email">{{ t('auth.email') }}</label>
            <input
              id="email"
              v-model="email"
              type="email"
              required
              :placeholder="t('auth.email_placeholder')"
              :disabled="loading"
              @blur="validateEmail"
              :class="{ 'invalid': emailError }"
            />
            <div v-if="emailError" class="validation-error">{{ emailError }}</div>
          </div>
          
          <div class="form-group">
            <label for="password">{{ t('auth.password') }}</label>
            <input
              id="password"
              v-model="password"
              type="password"
              required
              :placeholder="t('auth.password_hint')"
              :disabled="loading"
              minlength="6"
              maxlength="20"
            />
          </div>
          
          <div class="form-group">
            <label for="confirmPassword">{{ t('auth.confirm_password') }}</label>
            <input
              id="confirmPassword"
              v-model="confirmPassword"
              type="password"
              required
              :placeholder="t('auth.confirm_password_placeholder')"
              :disabled="loading"
            />
          </div>
          
          <div v-if="error" class="error-message">{{ error }}</div>
          <div v-if="success" class="success-message">{{ success }}</div>
          
          <button type="submit" class="submit-btn" :disabled="loading || !isFormValid">
            {{ loading ? t('auth.creating_account') : t('auth.signup_action') }}
          </button>
          
          <div v-if="password && password.length < 6" class="password-mismatch">
            {{ t('auth.password_min_length_error') }}
          </div>
          <div v-if="password && password.length > 20" class="password-mismatch">
            {{ t('auth.password_length_error') }}
          </div>
          <div v-if="password && confirmPassword && password !== confirmPassword" class="password-mismatch">
            {{ t('auth.password_mismatch') }}
          </div>
        </form>
        
        <div class="login-link">
          <p>{{ t('auth.already_have_account') }} <router-link to="/login">{{ t('auth.login') }}</router-link></p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import API_BASE_URL from '@/config/api.js'

import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const router = useRouter()
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const error = ref(null)
const success = ref(null)
const emailError = ref(null)

// Email validation function
const validateEmail = () => {
  emailError.value = null
  if (!email.value) {
    return
  }
  
  // Basic email format validation
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(email.value)) {
    emailError.value = t('auth.email_invalid')
    return false
  }
  
  // Additional validation: check for common issues
  if (email.value.includes('..')) {
    emailError.value = t('auth.email_dots_error')
    return false
  }
  
  if (email.value.startsWith('.') || email.value.endsWith('.')) {
    emailError.value = t('auth.email_start_end_error')
    return false
  }
  
  return true
}

// Computed property to check if form is valid
const isFormValid = computed(() => {
  return email.value && 
         !emailError.value && 
         password.value.length >= 6 && 
         password.value.length <= 20 && 
         password.value === confirmPassword.value
})

const handleSignup = async () => {
  // Validate email before submitting
  if (!validateEmail()) {
    error.value = emailError.value || t('auth.email_invalid')
    return
  }
  
  if (password.value !== confirmPassword.value) {
    error.value = t('auth.password_mismatch')
    return
  }
  
  if (password.value.length < 6 || password.value.length > 20) {
    error.value = t('auth.password_length_error')
    return
  }
  
  loading.value = true
  error.value = null
  success.value = null
  
  try {
    // Create AbortController for timeout
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 10000) // 10 second timeout
    
    const response = await fetch(`${API_BASE_URL}/api/auth/signup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email: email.value,
        username: email.value, // Use email as username
        password: password.value
      }),
      signal: controller.signal
    })
    
    clearTimeout(timeoutId)
    
    if (!response.ok) {
      let errorMessage = t('auth.signup_failed')
      try {
        const errorData = await response.json()
        errorMessage = errorData.detail || errorMessage
        if (errorMessage && errorMessage.includes('password cannot be longer than 72 bytes')) {
          errorMessage = t('auth.password_too_long')
        }
      } catch (e) {
        errorMessage = `${t('auth.server_error')}: ${response.status} ${response.statusText}`
      }
      throw new Error(errorMessage)
    }
    
    const data = await response.json()
    success.value = t('auth.signup_success')
    
    // Redirect to login after 2 seconds
    setTimeout(() => {
      router.push('/login')
    }, 2000)
  } catch (err) {
    if (err.name === 'AbortError') {
      error.value = `Request timed out. Please check if the backend server is running on ${API_BASE_URL}`
    } else if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
      error.value = `Cannot connect to server. Please ensure the backend is running on ${API_BASE_URL}`
    } else {
      error.value = err.message || t('auth.signup_failed')
    }
    console.error('Signup error:', err)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.signup-view {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8f9fa;
  padding: 20px;
}

.signup-container {
  width: 100%;
  max-width: 400px;
}

.signup-card {
  background: #ffffff;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid #cccccc;
}

.signup-card h1 {
  margin: 0 0 10px 0;
  color: #000000;
  font-weight: 600;
  font-size: 2em;
  text-align: center;
}

.subtitle {
  text-align: center;
  color: #666666;
  margin: 0 0 30px 0;
  font-size: 0.95em;
}

.signup-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  color: #000000;
  font-weight: 500;
  font-size: 0.9em;
}

.form-group input {
  padding: 12px;
  border: 1px solid #cccccc;
  border-radius: 6px;
  font-size: 1em;
  background: #ffffff;
  color: #000000;
  transition: border-color 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #3498db;
}

.form-group input:disabled {
  background: #f8f9fa;
  cursor: not-allowed;
}

.form-group input::placeholder {
  color: #999999;
}

.form-group input.invalid {
  border-color: #e74c3c;
}

.validation-error {
  color: #e74c3c;
  font-size: 0.85em;
  margin-top: -5px;
}

.error-message {
  background: #fff0f0;
  color: #e74c3c;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid #e74c3c;
  font-size: 0.9em;
}

.success-message {
  background: #e8f5e9;
  color: #42b983;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid #42b983;
  font-size: 0.9em;
}

.password-mismatch {
  color: #e74c3c;
  font-size: 0.85em;
  margin-top: -10px;
}

.submit-btn {
  padding: 12px 24px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1em;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
  margin-top: 10px;
}

.submit-btn:hover:not(:disabled) {
  background: #2980b9;
}

.submit-btn:disabled {
  background: #95a5a6;
  cursor: not-allowed;
}

.login-link {
  margin-top: 20px;
  text-align: center;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

.login-link p {
  margin: 0;
  color: #666666;
  font-size: 0.9em;
}

.login-link a {
  color: #3498db;
  text-decoration: none;
  font-weight: 500;
}

.login-link a:hover {
  text-decoration: underline;
}
</style>

