import { ref } from 'vue'
import API_BASE_URL from '@/config/api.js'

export function useFinancialData() {
    const loading = ref(false)
    const error = ref(null)

    // Data refs
    const incomeData = ref([])
    const cashFlowData = ref([])
    const balanceSheetData = ref([])
    const revenueSegmentation = ref([])
    const employeeCount = ref([])
    const mergersAcquisitions = ref([])
    const filings = ref([])
    const keyMetrics = ref([])
    const financialRatios = ref([])
    const earnings = ref([])
    const dividends = ref([])
    const splits = ref([])
    const insiderTrading = ref([])
    const businessDescription = ref('')
    const historicalPrice = ref([])
    const senateTrades = ref([])
    const houseTrades = ref([])

    const politicianTrades = ref([]) // For detail view

    const fetchFinancialData = async (tickerValue, periodValue) => {
        if (!tickerValue || String(tickerValue).trim() === '') {
            error.value = 'Please enter a ticker symbol'
            return
        }

        loading.value = true
        error.value = null

        try {
            const token = localStorage.getItem('access_token')
            const headers = token ? { 'Authorization': `Bearer ${token}` } : {}

            const response = await fetch(
                `${API_BASE_URL}/api/framework/all/${String(tickerValue).toUpperCase()}?period=${periodValue}&limit=5`,
                { headers }
            )

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch data' }))
                throw new Error(errorData.detail || 'Failed to fetch financial data')
            }

            const data = await response.json()
            incomeData.value = data.income_statement || []
            cashFlowData.value = data.cash_flow || []
            balanceSheetData.value = data.balance_sheet || []
            revenueSegmentation.value = data.revenue_segmentation || []
            employeeCount.value = data.employee_count || []
            mergersAcquisitions.value = data.mergers_acquisitions || []
            filings.value = data.filings || []
            keyMetrics.value = data.key_metrics || []
            financialRatios.value = data.financial_ratios || []
            earnings.value = data.earnings || []
            dividends.value = data.dividends || []
            splits.value = data.splits || []
            insiderTrading.value = data.insider_trading || []
            senateTrades.value = data.senate_trades || []
            houseTrades.value = data.house_trades || []
            businessDescription.value = data.business_description || ''
            historicalPrice.value = data.historical_price || []
        } catch (err) {
            error.value = err.message
            console.error('Error fetching financial data:', err)
        } finally {
            loading.value = false
        }
    }

    const fetchPoliticianTrades = async (name, chamber) => {
        if (!name) return

        loading.value = true
        // Keep main error separate, or reuse? Let's reuse for simplicity but careful not to block main view
        // Maybe better to have local error for modal or just log it.

        try {
            const token = localStorage.getItem('access_token')
            const headers = token ? { 'Authorization': `Bearer ${token}` } : {}

            const endpoint = chamber === 'senate' ? 'senate-trades-by-name' : 'house-trades-by-name'

            const response = await fetch(
                `${API_BASE_URL}/api/framework/${endpoint}?name=${encodeURIComponent(name)}`,
                { headers }
            )

            if (!response.ok) {
                throw new Error('Failed to fetch politician trades')
            }

            const data = await response.json()
            politicianTrades.value = data.data || []
        } catch (err) {
            console.error('Error fetching politician trades:', err)
            politicianTrades.value = []
        } finally {
            loading.value = false
        }
    }


    const fetchFinancialRatiosComparison = async (tickers) => {
        if (!tickers || tickers.length === 0) return

        loading.value = true
        // don't clear error here to avoid flashing if it's separate part

        try {
            const token = localStorage.getItem('access_token')
            const headers = {
                'Content-Type': 'application/json',
                ...(token ? { 'Authorization': `Bearer ${token}` } : {})
            }

            const response = await fetch(
                `${API_BASE_URL}/api/framework/financial-ratios-comparison`,
                {
                    method: 'POST',
                    headers,
                    body: JSON.stringify({ tickers })
                }
            )

            if (!response.ok) {
                throw new Error('Failed to fetch financial ratios comparison')
            }

            const data = await response.json()
            financialRatios.value = data
        } catch (err) {
            console.error('Error fetching financial ratios:', err)
            // Optional: set error state
        } finally {
            loading.value = false
        }
    }

    return {
        loading,
        error,
        incomeData,
        cashFlowData,
        balanceSheetData,
        revenueSegmentation,
        employeeCount,
        mergersAcquisitions,
        filings,
        keyMetrics,
        financialRatios,
        earnings,
        dividends,
        splits,
        insiderTrading,
        senateTrades,
        houseTrades,
        politicianTrades,
        businessDescription,
        historicalPrice,
        fetchFinancialData,
        fetchPoliticianTrades,
        fetchFinancialRatiosComparison
    }
}
