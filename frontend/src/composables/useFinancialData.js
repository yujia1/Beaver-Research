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
    const businessDescription = ref('')
    const historicalPrice = ref([])
    const dailyHistoricalPrice = ref([]) // Cache for daily data

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
            businessDescription.value = data.business_description || ''
            historicalPrice.value = data.historical_price || []
            dailyHistoricalPrice.value = data.historical_price || []
        } catch (err) {
            error.value = err.message
            console.error('Error fetching financial data:', err)
        } finally {
            loading.value = false
        }
    }

    const fetchIntradayData = async (tickerValue, interval) => {
        if (!tickerValue) return

        loading.value = true
        // don't clear error/other data

        try {
            const token = localStorage.getItem('access_token')
            const headers = token ? { 'Authorization': `Bearer ${token}` } : {}

            const response = await fetch(
                `${API_BASE_URL}/api/framework/historical-chart/${interval}/${String(tickerValue).toUpperCase()}`,
                { headers }
            )

            if (!response.ok) {
                throw new Error('Failed to fetch intraday data')
            }

            const data = await response.json()
            // FMP returns list directly or { data: ... } depending on my backend wrapper?
            // Backend wrapper returns { data: [...] }
            historicalPrice.value = data.data || []

        } catch (err) {
            console.error('Error fetching intraday:', err)
            // Optional: set error
        } finally {
            loading.value = false
        }
    }

    const setChartPeriod = (period) => {
        // Helper to switch between daily cache and intraday fetch
        // BUT this requires ticker. 
        // We'll let the component call fetchIntradayData directly or expose this.
    }

    const resetToDailyPrice = () => {
        loading.value = true
        historicalPrice.value = [...dailyHistoricalPrice.value]
        loading.value = false
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
        dividends,
        splits,
        businessDescription,
        historicalPrice,
        dailyHistoricalPrice,
        fetchFinancialData,
        fetchIntradayData,
        resetToDailyPrice
    }
}
