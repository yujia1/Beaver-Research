// API Configuration - Runtime Detection
// Automatically uses the correct backend URL based on environment

function getApiBaseUrl() {
    // If running on localhost, use local backend
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return 'http://localhost:8000'
    }

    // If running on Railway production, use Railway backend
    if (window.location.hostname.includes('railway.app')) {
        return 'https://beaver-research-backend-production.up.railway.app'
    }

    // Fallback to localhost
    return 'http://localhost:8000'
}

const API_BASE_URL = getApiBaseUrl()

export default API_BASE_URL
