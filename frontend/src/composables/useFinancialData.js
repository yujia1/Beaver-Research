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
    const dcfData = ref([])
    const earningsCalendar = ref([])
    const employeeCount = ref([])
    const mergersAcquisitions = ref([])

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
            dcfData.value = data.dcf || []
            earningsCalendar.value = data.earnings_calendar || []
            employeeCount.value = data.employee_count || []
            mergersAcquisitions.value = data.mergers_acquisitions || []
        } catch (err) {
            error.value = err.message
            console.error('Error fetching financial data:', err)
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
        dcfData,
        earningsCalendar,
        employeeCount,
        mergersAcquisitions,
        fetchFinancialData
    }
}
