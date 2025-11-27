<template>
  <div class="login-view">
    <div class="login-container">
      <div class="login-card">
        <h1>Login</h1>
        <p class="subtitle">Sign in to your account</p>
        
        <form @submit.prevent="handleLogin" class="login-form">
          <div class="form-group">
            <label for="username">Username</label>
            <input
              id="username"
              v-model="username"
              type="text"
              required
              placeholder="Enter your username"
              :disabled="loading"
            />
          </div>
          
          <div class="form-group">
            <label for="password">Password</label>
            <input
              id="password"
              v-model="password"
              type="password"
              required
              placeholder="Enter your password"
              :disabled="loading"
            />
          </div>
          
          <div v-if="error" class="error-message">{{ error }}</div>
          
          <button type="submit" class="submit-btn" :disabled="loading">
            {{ loading ? 'Logging in...' : 'Login' }}
          </button>
        </form>
        
        <div class="signup-link">
          <p>Don't have an account? <router-link to="/signup">Sign up</router-link></p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref(null)

const handleLogin = async () => {
  loading.value = true
  error.value = null
  
  try {
    const response = await fetch('http://localhost:8000/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username: username.value,
        password: password.value
      })
    })
    
    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Login failed')
    }
    
    const data = await response.json()
    
    // Store token in localStorage
    localStorage.setItem('access_token', data.access_token)
    
    // Fetch user info to get role
    try {
      const userResponse = await fetch('http://localhost:8000/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${data.access_token}`
        }
      })
      if (userResponse.ok) {
        const userData = await userResponse.json()
        localStorage.setItem('user', JSON.stringify(userData))
      }
    } catch (err) {
      console.error('Failed to fetch user info:', err)
    }
    
    // Dispatch custom event to notify App.vue of login
    window.dispatchEvent(new CustomEvent('user-logged-in'))
    
    // Redirect to home page
    router.push('/')
  } catch (err) {
    error.value = err.message || 'An error occurred during login'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-view {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8f9fa;
  padding: 20px;
}

.login-container {
  width: 100%;
  max-width: 400px;
}

.login-card {
  background: #ffffff;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid #cccccc;
}

.login-card h1 {
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

.login-form {
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

.error-message {
  background: #fff0f0;
  color: #e74c3c;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid #e74c3c;
  font-size: 0.9em;
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

.signup-link {
  margin-top: 20px;
  text-align: center;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

.signup-link p {
  margin: 0;
  color: #666666;
  font-size: 0.9em;
}

.signup-link a {
  color: #3498db;
  text-decoration: none;
  font-weight: 500;
}

.signup-link a:hover {
  text-decoration: underline;
}
</style>

