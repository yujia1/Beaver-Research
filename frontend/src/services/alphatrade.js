// AlphaTrade API Service
const API_BASE = 'http://localhost:8000/api/alphatrade'

export const alphaTradeAPI = {
    // Positions
    async getPositions() {
        const response = await fetch(`${API_BASE}/positions`)
        if (!response.ok) throw new Error('Failed to fetch positions')
        return response.json()
    },

    async createPosition(ticker, sector) {
        const response = await fetch(`${API_BASE}/positions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker, sector })
        })
        if (!response.ok) throw new Error('Failed to create position')
        return response.json()
    },

    async deletePosition(ticker) {
        const response = await fetch(`${API_BASE}/positions/${ticker}`, {
            method: 'DELETE'
        })
        if (!response.ok) throw new Error('Failed to delete position')
        return response.json()
    },

    async updatePositionPrice(ticker) {
        const response = await fetch(`${API_BASE}/positions/${ticker}/price`, {
            method: 'PUT'
        })
        if (!response.ok) throw new Error('Failed to update position price')
        return response.json()
    },

    // Trade Lots
    async addLot(ticker, lotData) {
        const response = await fetch(`${API_BASE}/positions/${ticker}/lots`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(lotData)
        })
        if (!response.ok) throw new Error('Failed to add lot')
        return response.json()
    },

    async updateLot(lotId, lotData) {
        const response = await fetch(`${API_BASE}/lots/${lotId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(lotData)
        })
        if (!response.ok) throw new Error('Failed to update lot')
        return response.json()
    },

    async deleteLot(lotId) {
        const response = await fetch(`${API_BASE}/lots/${lotId}`, {
            method: 'DELETE'
        })
        if (!response.ok) throw new Error('Failed to delete lot')
        return response.json()
    },

    // Fundamental Analysis
    async updateAnalysis(ticker, questionId, data) {
        const response = await fetch(`${API_BASE}/positions/${ticker}/analysis`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ questionId, ...data })
        })
        if (!response.ok) throw new Error('Failed to update analysis')
        return response.json()
    },

    // Stock Data
    async getStockData(ticker) {
        const response = await fetch(`${API_BASE}/stock/${ticker}`)
        if (!response.ok) throw new Error('Failed to fetch stock data')
        return response.json()
    }
}
