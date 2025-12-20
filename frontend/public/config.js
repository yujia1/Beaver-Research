// Runtime API configuration
// This file is replaced at runtime with the actual backend URL
window.API_CONFIG = {
    baseURL: import.meta.env.VITE_API_URL || window.location.origin.replace('frontend', 'backend').replace(':5173', ':8000')
}
