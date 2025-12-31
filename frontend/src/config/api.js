// API Configuration - Runtime Detection
// Detects the correct backend URL based on the current hostname

function getApiBaseUrl() {
    const hostname = window.location.hostname
    console.log('Detected hostname:', hostname)

    // Local development
    if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '0.0.0.0') {
        return 'http://localhost:8000'
    }

    // Railway staging
    if (hostname.includes('stage')) {
        return 'https://api-stage.beaver-research.cloud'
    }

    // Railway production (default)
    if (hostname.includes('railway.app')) {
        return 'https://beaver-research-backend-production.up.railway.app'
    }

    // Fallback
    return 'http://localhost:8000'
}

const API_BASE_URL = getApiBaseUrl()

export default API_BASE_URL
