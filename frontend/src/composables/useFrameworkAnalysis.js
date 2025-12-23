import { computed } from 'vue'
import {
    calculateRevenueGrowth,
    calculateGrossMargin,
    calculateOperatingMargin,
    calculateNetMargin
} from '@/utils/financialUtils'

export function useFrameworkAnalysis(incomeData, cashFlowData) {
    // --- Data Computations ---

    // Pricing Power Data
    const pricingPowerData = computed(() => {
        if (!incomeData.value || incomeData.value.length === 0) return null

        return {
            dates: incomeData.value.map(d => d.date).reverse(),
            revenueGrowth: incomeData.value.map((d, i) => {
                if (i < incomeData.value.length - 1) {
                    const growth = calculateRevenueGrowth(d.revenue, incomeData.value[i + 1].revenue)
                    return growth ? growth * 100 : null
                }
                return null
            }).reverse(),
            grossMargin: incomeData.value.map(d => {
                const margin = calculateGrossMargin(d.grossProfit, d.revenue)
                return margin ? margin * 100 : null
            }).reverse(),
            operatingMargin: incomeData.value.map(d => {
                const margin = calculateOperatingMargin(d.ebitda, d.revenue)
                return margin ? margin * 100 : null
            }).reverse()
        }
    })

    // Financial Health Data
    const financialHealthData = computed(() => {
        if (!cashFlowData.value || cashFlowData.value.length === 0) return null

        return {
            dates: cashFlowData.value.map(d => d.date).reverse(),
            netIncome: cashFlowData.value.map(d => d.netIncome).reverse(),
            operatingCashFlow: cashFlowData.value.map(d => d.netCashProvidedByOperatingActivities).reverse(),
            freeCashFlow: cashFlowData.value.map(d => d.freeCashFlow).reverse(),
            capex: cashFlowData.value.map(d => Math.abs(d.capitalExpenditure || 0)).reverse()
        }
    })

    // Working Capital Data
    const workingCapitalData = computed(() => {
        if (!cashFlowData.value || cashFlowData.value.length === 0) return null

        const getGrowth = (arr, key, i) => {
            if (i < arr.length - 1) {
                const current = arr[i][key]
                const prev = arr[i + 1][key]
                const growth = calculateRevenueGrowth(current, prev)
                return growth ? growth * 100 : null
            }
            return null
        }

        return {
            dates: cashFlowData.value.map(d => d.date).reverse(),
            accountsReceivablesGrowth: cashFlowData.value.map((d, i) => getGrowth(cashFlowData.value, 'accountsReceivables', i)).reverse(),
            netIncomeGrowth: cashFlowData.value.map((d, i) => getGrowth(cashFlowData.value, 'netIncome', i)).reverse(),
            inventoryGrowth: cashFlowData.value.map((d, i) => getGrowth(cashFlowData.value, 'inventory', i)).reverse(),
            accountsPayablesGrowth: cashFlowData.value.map((d, i) => getGrowth(cashFlowData.value, 'accountsPayables', i)).reverse()
        }
    })

    // CapEx Analysis Data
    const capexAnalysisData = computed(() => {
        if (!cashFlowData.value || cashFlowData.value.length === 0 ||
            !incomeData.value || incomeData.value.length === 0) return null

        const minLength = Math.min(cashFlowData.value.length, incomeData.value.length)
        const cfSlice = cashFlowData.value.slice(0, minLength)
        const incSlice = incomeData.value.slice(0, minLength)

        return {
            dates: cfSlice.map(d => d.date).reverse(),
            capexGrowth: cfSlice.map((d, i) => {
                if (i < cfSlice.length - 1) {
                    const growth = calculateRevenueGrowth(d.capitalExpenditure, cfSlice[i + 1].capitalExpenditure)
                    return growth ? growth * 100 : null
                }
                return null
            }).reverse(),
            revenueGrowth: incSlice.map((d, i) => {
                if (i < incSlice.length - 1) {
                    const growth = calculateRevenueGrowth(d.revenue, incSlice[i + 1].revenue)
                    return growth ? growth * 100 : null
                }
                return null
            }).reverse()
        }
    })

    // --- Chart Configurations ---

    const pricingPowerChartConfig = computed(() => {
        if (!pricingPowerData.value) return null
        return {
            type: 'line',
            data: {
                labels: pricingPowerData.value.dates,
                datasets: [
                    { label: 'Revenue Growth Rate (%)', data: pricingPowerData.value.revenueGrowth, borderColor: 'rgb(59, 130, 246)', backgroundColor: 'rgba(59, 130, 246, 0.1)', yAxisID: 'y' },
                    { label: 'Gross Margin (%)', data: pricingPowerData.value.grossMargin, borderColor: 'rgb(16, 185, 129)', backgroundColor: 'rgba(16, 185, 129, 0.1)', yAxisID: 'y' },
                    { label: 'Operating Margin (%)', data: pricingPowerData.value.operatingMargin, borderColor: 'rgb(245, 158, 11)', backgroundColor: 'rgba(245, 158, 11, 0.1)', yAxisID: 'y' }
                ]
            },
            options: {
                interaction: { mode: 'index', intersect: false },
                scales: { y: { type: 'linear', display: true, position: 'left', title: { display: true, text: 'Percentage (%)' } } }
            }
        }
    })

    const incomeVsCashFlowChartConfig = computed(() => {
        if (!financialHealthData.value) return null
        return {
            type: 'bar',
            data: {
                labels: financialHealthData.value.dates,
                datasets: [
                    { label: 'Net Income', data: financialHealthData.value.netIncome, backgroundColor: 'rgba(59, 130, 246, 0.7)', borderColor: 'rgb(59, 130, 246)', borderWidth: 1 },
                    { label: 'Operating Cash Flow', data: financialHealthData.value.operatingCashFlow, backgroundColor: 'rgba(16, 185, 129, 0.7)', borderColor: 'rgb(16, 185, 129)', borderWidth: 1 }
                ]
            },
            options: { scales: { y: { beginAtZero: true, title: { display: true, text: 'Amount ($)' } } } }
        }
    })

    const freeCashFlowChartConfig = computed(() => {
        if (!financialHealthData.value) return null
        return {
            type: 'line',
            data: {
                labels: financialHealthData.value.dates,
                datasets: [{ label: 'Free Cash Flow', data: financialHealthData.value.freeCashFlow, borderColor: 'rgb(139, 92, 246)', backgroundColor: 'rgba(139, 92, 246, 0.1)', fill: true }]
            },
            options: { scales: { y: { beginAtZero: true, title: { display: true, text: 'Amount ($)' } } } }
        }
    })

    const capexChartConfig = computed(() => {
        if (!financialHealthData.value) return null
        return {
            type: 'bar',
            data: {
                labels: financialHealthData.value.dates,
                datasets: [{ label: 'Capital Expenditure', data: financialHealthData.value.capex, backgroundColor: 'rgba(239, 68, 68, 0.7)', borderColor: 'rgb(239, 68, 68)', borderWidth: 1 }]
            },
            options: { scales: { y: { beginAtZero: true, title: { display: true, text: 'Amount ($)' } } } }
        }
    })

    const arVsNiGrowthChartConfig = computed(() => {
        if (!workingCapitalData.value) return null
        return {
            type: 'line',
            data: {
                labels: workingCapitalData.value.dates,
                datasets: [
                    { label: 'Accounts Receivables Growth (%)', data: workingCapitalData.value.accountsReceivablesGrowth, borderColor: 'rgb(59, 130, 246)', backgroundColor: 'rgba(59, 130, 246, 0.1)', fill: false },
                    { label: 'Net Income Growth (%)', data: workingCapitalData.value.netIncomeGrowth, borderColor: 'rgb(16, 185, 129)', backgroundColor: 'rgba(16, 185, 129, 0.1)', fill: false }
                ]
            },
            options: { interaction: { mode: 'index', intersect: false }, scales: { y: { title: { display: true, text: 'Growth Rate (%)' } } } }
        }
    })

    const inventoryGrowthChartConfig = computed(() => {
        if (!workingCapitalData.value) return null
        return {
            type: 'bar',
            data: {
                labels: workingCapitalData.value.dates,
                datasets: [{ label: 'Inventory Growth (%)', data: workingCapitalData.value.inventoryGrowth, backgroundColor: 'rgba(139, 92, 246, 0.7)', borderColor: 'rgb(139, 92, 246)', borderWidth: 1 }]
            },
            options: { scales: { y: { title: { display: true, text: 'Growth Rate (%)' } } } }
        }
    })

    const apGrowthChartConfig = computed(() => {
        if (!workingCapitalData.value) return null
        return {
            type: 'bar',
            data: {
                labels: workingCapitalData.value.dates,
                datasets: [{ label: 'Accounts Payables Growth (%)', data: workingCapitalData.value.accountsPayablesGrowth, backgroundColor: 'rgba(245, 158, 11, 0.7)', borderColor: 'rgb(245, 158, 11)', borderWidth: 1 }]
            },
            options: { scales: { y: { title: { display: true, text: 'Growth Rate (%)' } } } }
        }
    })

    const capexAnalysisChartConfig = computed(() => {
        if (!capexAnalysisData.value) return null
        return {
            type: 'line',
            data: {
                labels: capexAnalysisData.value.dates,
                datasets: [
                    { label: 'CapEx Growth (%)', data: capexAnalysisData.value.capexGrowth, borderColor: 'rgb(239, 68, 68)', backgroundColor: 'rgba(239, 68, 68, 0.1)', fill: false },
                    { label: 'Revenue Growth (%)', data: capexAnalysisData.value.revenueGrowth, borderColor: 'rgb(59, 130, 246)', backgroundColor: 'rgba(59, 130, 246, 0.1)', fill: false }
                ]
            },
            options: { interaction: { mode: 'index', intersect: false }, scales: { y: { title: { display: true, text: 'Growth Rate (%)' } } } }
        }
    })

    return {
        pricingPowerData,
        financialHealthData,
        workingCapitalData,
        capexAnalysisData,

        pricingPowerChartConfig,
        incomeVsCashFlowChartConfig,
        freeCashFlowChartConfig,
        capexChartConfig,
        arVsNiGrowthChartConfig,
        inventoryGrowthChartConfig,
        apGrowthChartConfig,
        capexAnalysisChartConfig
    }
}
