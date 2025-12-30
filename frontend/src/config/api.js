// API Configuration - Runtime Detection
// Detects the correct backend URL based on the current hostname

function getApiBaseUrl() {
    const hostname = window.location.hostname

    // Local development
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return 'http://localhost:8000'
    }

    // Railway staging
    if (hostname.includes('staging')) {
        return 'https://beaver-research-backend-stage-staging.up.railway.app'
    }

    // Railway production (default)
    if (hostname.includes('railway.app')) {
        return 'https://beaver-research-backend-production.up.railway.app'
    }

    // Fallback
    return 'http://localhost:8000'
}

const API_BASE_URL = getApiBaseUrl()

console.log('Frontend hostname:', window.location.hostname)
console.log('API_BASE_URL:', API_BASE_URL)

export default API_BASE_URL

