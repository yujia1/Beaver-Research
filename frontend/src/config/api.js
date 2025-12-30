// API Configuration
// Uses VITE_API_URL environment variable set in Railway/deployment platform

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default API_BASE_URL

