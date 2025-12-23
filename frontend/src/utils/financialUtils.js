// Format currency
export const formatCurrency = (value) => {
    if (value === null || value === undefined) return '-'
    const num = parseFloat(value)
    if (isNaN(num)) return '-'

    // Format in billions/millions
    if (Math.abs(num) >= 1e9) {
        return `$${(num / 1e9).toFixed(2)}B`
    } else if (Math.abs(num) >= 1e6) {
        return `$${(num / 1e6).toFixed(2)}M`
    } else if (Math.abs(num) >= 1e3) {
        return `$${(num / 1e3).toFixed(2)}K`
    }
    return `$${num.toFixed(2)}`
}

// Format value based on field type
export const formatValue = (key, value) => {
    // Date fields should be displayed as-is
    const dateFields = ['date', 'filingDate', 'acceptedDate', 'fillingDate', 'calendarYear', 'period']
    if (dateFields.includes(key)) {
        return value || '-'
    }

    // Everything else is currency
    return formatCurrency(value)
}

// Convert camelCase to Title Case
export const formatLineItemName = (name) => {
    // Add space before capital letters and capitalize first letter
    return name
        .replace(/([A-Z])/g, ' $1')
        .replace(/^./, (str) => str.toUpperCase())
        .trim()
}

// Format percentage
export const formatPercentage = (value) => {
    if (value === null || value === undefined || isNaN(value)) return '-'
    return `${(value * 100).toFixed(2)}%`
}

// Calculate Revenue Growth Rate (YoY)
export const calculateRevenueGrowth = (currentRevenue, previousRevenue) => {
    if (!previousRevenue || previousRevenue === 0) return null
    return (currentRevenue - previousRevenue) / previousRevenue
}

// Calculate Gross Margin
export const calculateGrossMargin = (grossProfit, revenue) => {
    if (!revenue || revenue === 0) return null
    return grossProfit / revenue
}

// Calculate Operating Profit Margin (EBITDA / Revenue)
export const calculateOperatingMargin = (ebitda, revenue) => {
    if (!revenue || revenue === 0) return null
    return ebitda / revenue
}

// Calculate Net Profit Margin
export const calculateNetMargin = (netIncome, revenue) => {
    if (!revenue || revenue === 0) return null
    return netIncome / revenue
}

// Calculate Cash Burn Rate (monthly)
export const calculateCashBurnRate = (cashBeginning, cashEnd, period) => {
    if (cashBeginning === null || cashBeginning === undefined ||
        cashEnd === null || cashEnd === undefined) return null

    const cashChange = cashBeginning - cashEnd
    // Determine number of months based on period
    const months = period === 'quarter' ? 3 : 12

    return cashChange / months
}

// Get revenue segment value for a specific date and product
export const getSegmentValue = (productName, date, revenueSegmentation) => {
    if (!revenueSegmentation || revenueSegmentation.length === 0) return null

    // Find the segment entry for this date
    const segmentEntry = revenueSegmentation.find(seg => seg.date === date)
    if (!segmentEntry || !segmentEntry.data) return null

    // Return the value for this product
    return segmentEntry.data[productName] || null
}
