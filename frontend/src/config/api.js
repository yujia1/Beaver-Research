// API Configuration
// Uses relative URLs when deployed together with backend
// Falls back to localhost for local development

const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : '' // Empty string means relative URLs (same origin)

export default API_BASE_URL


