// API Configuration
// Uses VITE_API_URL environment variable for Railway deployment
// Falls back to localhost for local development

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

console.log('API_BASE_URL:', API_BASE_URL) // Debug log to verify

export default API_BASE_URL
