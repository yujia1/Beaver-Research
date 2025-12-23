<template>
  <div class="data-table-wrapper">
    <table class="data-table">
      <thead>
        <tr>
          <th class="line-item-header">{{ t('framework.line_item') }}</th>
          <th v-for="periodDate in periods" :key="periodDate" class="period-header">
            {{ periodDate }}
          </th>
        </tr>
      </thead>
      <tbody>
        <!-- Categorized view -->
        <template v-if="categorizedItems.length > 0">
          <template v-for="category in categorizedItems" :key="category.name">
            <!-- Category Header Row -->
            <tr class="category-header-row" @click="toggleCategory(category.name)">
              <td class="category-header-cell" :colspan="periods.length + 1">
                <div class="category-header-content">
                  <svg 
                    class="category-icon" 
                    :class="{ expanded: isCategoryExpanded(category.name) }"
                    xmlns="http://www.w3.org/2000/svg" 
                    width="16" 
                    height="16" 
                    viewBox="0 0 24 24" 
                    fill="none" 
                    stroke="currentColor" 
                    stroke-width="2" 
                    stroke-linecap="round" 
                    stroke-linejoin="round"
                  >
                    <polyline points="9 18 15 12 9 6"></polyline>
                  </svg>
                  <span class="category-name">{{ category.name }}</span>
                </div>
              </td>
            </tr>
            
            <!-- Category Content -->
            <template v-if="isCategoryExpanded(category.name)">
                <!-- Subcategories -->
                <template v-if="category.subcategories && category.subcategories.length > 0">
                   <template v-for="subcategory in category.subcategories" :key="subcategory.name">
                      <!-- Subcategory Header -->
                      <tr class="subcategory-header-row" @click.stop="toggleCategory(subcategory.name)">
                         <td class="subcategory-header-cell" :colspan="periods.length + 1">
                            <div class="subcategory-header-content">
                               <svg class="category-icon subcategory-icon" :class="{ expanded: isCategoryExpanded(subcategory.name) }" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
                               <span class="subcategory-name">{{ subcategory.name }}</span>
                            </div>
                         </td>
                      </tr>
                      <!-- Subcategory Fields -->
                      <template v-if="isCategoryExpanded(subcategory.name)">
                         <tr v-for="field in subcategory.fields" :key="field" class="data-row subcategory-data-row">
                            <td class="line-item-cell subcategory-item">{{ formatLineItemName(field) }}</td>
                            <td v-for="(val, index) in data" :key="index" class="data-cell">
                               {{ formatValue(field, val[field]) }}
                            </td>
                         </tr>
                      </template>
                   </template>
                </template>

                <!-- Direct Fields -->
                <template v-for="(field) in category.fields" :key="field">
                    <tr class="data-row">
                       <td class="line-item-cell">{{ formatLineItemName(field) }}</td>
                       <td v-for="(val, index) in data" :key="index" class="data-cell">
                          {{ formatValue(field, val[field]) }}
                       </td>
                    </tr>

                    <!-- Revenue Segmentation -->
                    <template v-if="field === 'revenue' && activeTab === 'income' && productNames.length > 0">
                       <tr v-for="productName in productNames" :key="productName" class="segmentation-row">
                          <td class="line-item-cell segmentation-item">{{ productName }}</td>
                          <td v-for="(val, index) in data" :key="index" class="data-cell">
                             {{ formatCurrency(getSegmentValue(productName, val.date)) }}
                          </td>
                       </tr>
                    </template>

                    <!-- Calculated Metrics -->
                    <template v-if="activeTab === 'income'">
                      <!-- Revenue Growth -->
                      <tr v-if="field === 'revenue'" class="calculated-metric-row">
                        <td class="line-item-cell calculated-metric">Revenue Growth Rate ({{ period === 'annual' ? 'YoY' : 'QoQ' }})</td>
                        <td v-for="(val, index) in data" :key="`growth-${index}`" class="data-cell calculated-value">
                           {{ index < data.length - 1 ? formatPercentage(calculateRevenueGrowth(val.revenue, data[index + 1].revenue)) : '-' }}
                        </td>
                      </tr>
                      <!-- Gross Margin -->
                      <tr v-if="field === 'grossProfit'" class="calculated-metric-row">
                        <td class="line-item-cell calculated-metric">Gross Margin</td>
                         <td v-for="(val, index) in data" :key="`gm-${index}`" class="data-cell calculated-value">
                            {{ formatPercentage(calculateGrossMargin(val.grossProfit, val.revenue)) }}
                         </td>
                      </tr>
                      <!-- Operating Margin -->
                      <tr v-if="field === 'ebitda'" class="calculated-metric-row">
                         <td class="line-item-cell calculated-metric">Operating Profit Margin</td>
                         <td v-for="(val, index) in data" :key="`opm-${index}`" class="data-cell calculated-value">
                            {{ formatPercentage(calculateOperatingMargin(val.ebitda, val.revenue)) }}
                         </td>
                      </tr>
                      <!-- Net Margin -->
                      <tr v-if="field === 'netIncome'" class="calculated-metric-row">
                         <td class="line-item-cell calculated-metric">Net Profit Margin</td>
                         <td v-for="(val, index) in data" :key="`npm-${index}`" class="data-cell calculated-value">
                            {{ formatPercentage(calculateNetMargin(val.netIncome, val.revenue)) }}
                         </td>
                      </tr>
                    </template>
                    
                    <template v-if="activeTab === 'cash_flow'">
                       <!-- Net Income Growth -->
                       <tr v-if="field === 'netIncome'" class="calculated-metric-row">
                          <td class="line-item-cell calculated-metric">Net Income Growth ({{ period === 'annual' ? 'YoY' : 'QoQ' }})</td>
                          <td v-for="(val, index) in data" :key="`ni-growth-${index}`" class="data-cell calculated-value">
                             {{ index < data.length - 1 ? formatPercentage(calculateRevenueGrowth(val.netIncome, data[index + 1].netIncome)) : '-' }}
                          </td>
                       </tr>
                       <!-- OCF Growth -->
                       <tr v-if="field === 'netCashProvidedByOperatingActivities'" class="calculated-metric-row">
                          <td class="line-item-cell calculated-metric">Operating Cash Flow Growth ({{ period === 'annual' ? 'YoY' : 'QoQ' }})</td>
                          <td v-for="(val, index) in data" :key="`ocf-growth-${index}`" class="data-cell calculated-value">
                             {{ index < data.length - 1 ? formatPercentage(calculateRevenueGrowth(val.netCashProvidedByOperatingActivities, data[index + 1].netCashProvidedByOperatingActivities)) : '-' }}
                          </td>
                       </tr>
                       <!-- AR Growth -->
                       <tr v-if="field === 'accountsReceivables'" class="calculated-metric-row">
                          <td class="line-item-cell calculated-metric">Accounts Receivables Growth ({{ period === 'annual' ? 'YoY' : 'QoQ' }})</td>
                          <td v-for="(val, index) in data" :key="`ar-growth-${index}`" class="data-cell calculated-value">
                             {{ index < data.length - 1 ? formatPercentage(calculateRevenueGrowth(val.accountsReceivables, data[index + 1].accountsReceivables)) : '-' }}
                          </td>
                       </tr>
                       <!-- Inventory Growth -->
                       <tr v-if="field === 'inventory'" class="calculated-metric-row">
                          <td class="line-item-cell calculated-metric">Inventory Growth ({{ period === 'annual' ? 'YoY' : 'QoQ' }})</td>
                          <td v-for="(val, index) in data" :key="`inv-growth-${index}`" class="data-cell calculated-value">
                             {{ index < data.length - 1 ? formatPercentage(calculateRevenueGrowth(val.inventory, data[index + 1].inventory)) : '-' }}
                          </td>
                       </tr>
                       <!-- AP Growth -->
                       <tr v-if="field === 'accountsPayables'" class="calculated-metric-row">
                          <td class="line-item-cell calculated-metric">Accounts Payables Growth ({{ period === 'annual' ? 'YoY' : 'QoQ' }})</td>
                          <td v-for="(val, index) in data" :key="`ap-growth-${index}`" class="data-cell calculated-value">
                             {{ index < data.length - 1 ? formatPercentage(calculateRevenueGrowth(val.accountsPayables, data[index + 1].accountsPayables)) : '-' }}
                          </td>
                       </tr>
                       <!-- Cash Burn -->
                       <tr v-if="field === 'cashAtEndOfPeriod'" class="calculated-metric-row">
                          <td class="line-item-cell calculated-metric">Cash Burn Rate (Monthly)</td>
                          <td v-for="(val, index) in data" :key="`burn-${index}`" class="data-cell calculated-value">
                             {{ formatCurrency(calculateCashBurnRate(val.cashAtBeginningOfPeriod, val.cashAtEndOfPeriod, period)) }}
                          </td>
                       </tr>
                       <!-- CapEx Growth -->
                       <tr v-if="field === 'capitalExpenditure'" class="calculated-metric-row">
                          <td class="line-item-cell calculated-metric">CapEx Growth Rate ({{ period === 'annual' ? 'YoY' : 'QoQ' }})</td>
                          <td v-for="(val, index) in data" :key="`capex-growth-${index}`" class="data-cell calculated-value">
                             {{ index < data.length - 1 ? formatPercentage(calculateRevenueGrowth(val.capitalExpenditure, data[index + 1].capitalExpenditure)) : '-' }}
                          </td>
                       </tr>
                    </template>
                </template>
            </template>
          </template>
        </template>
        
        <!-- Fallback -->
        <template v-else>
           <tr v-for="item in lineItems" :key="item">
              <td class="line-item-cell">{{ formatLineItemName(item) }}</td>
              <td v-for="(val, index) in data" :key="index" class="data-cell">
                 {{ formatValue(item, val[item]) }}
              </td>
           </tr>
        </template>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { 
  formatLineItemName, 
  formatValue, 
  formatCurrency, 
  formatPercentage, 
  calculateRevenueGrowth,
  calculateGrossMargin,
  calculateOperatingMargin,
  calculateNetMargin,
  calculateCashBurnRate,
  getSegmentValue as getSegmentValueUtil
} from '@/utils/financialUtils'

const props = defineProps({
  data: { type: Array, required: true },
  periods: { type: Array, required: true },
  categorizedItems: { type: Array, default: () => [] },
  activeTab: { type: String, required: true },
  period: { type: String, default: 'annual' },
  productNames: { type: Array, default: () => [] },
  lineItems: { type: Array, default: () => [] },
  revenueSegmentation: { type: Array, default: () => [] }
})

const { t } = useI18n()
const expandedCategories = ref(new Set(['Revenue & Direct Costs', 'Operating Activities (Cash from Operations)', 'Assets (What the Company Owns)']))

const toggleCategory = (name) => {
  if (expandedCategories.value.has(name)) {
    expandedCategories.value.delete(name)
  } else {
    expandedCategories.value.add(name)
  }
}

const isCategoryExpanded = (name) => expandedCategories.value.has(name)

// Note: getSegmentValue uses props.revenueSegmentation.
const getSegmentValue = (productName, date) => {
   return getSegmentValueUtil(productName, date, props.revenueSegmentation)
}
</script>

<style scoped>
.data-table-wrapper { overflow-x: auto; margin-top: 1.5rem; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.9375rem; }
.data-table thead { background: #f8f8f8; position: sticky; top: 0; z-index: 10; }
.data-table th { padding: 1rem; text-align: left; font-weight: 600; color: #000; border-bottom: 2px solid #e0e0e0; white-space: nowrap; }
.line-item-header { position: sticky; left: 0; background: #f8f8f8; z-index: 11; min-width: 250px; }
.period-header { text-align: left; min-width: 120px; }
.data-table tbody tr { border-bottom: 1px solid #f0f0f0; transition: background 0.2s; }
.data-table tbody tr:hover { background: #fafafa; }
.line-item-cell { padding: 1rem; font-weight: 500; color: #333; position: sticky; left: 0; background: #fff; border-right: 1px solid #f0f0f0; }
.data-table tbody tr:hover .line-item-cell { background: #fafafa; }
.data-cell { padding: 1rem; text-align: left; color: #666; font-family: 'Courier New', monospace; }
.category-header-row { background: #f8f8f8; cursor: pointer; transition: background 0.2s; border-top: 2px solid #e0e0e0; }
.category-header-row:hover { background: #f0f0f0; }
.category-header-cell { padding: 0.875rem 1rem !important; font-weight: 600; color: #000; text-align: left !important; }
.category-header-content { display: flex; align-items: center; gap: 0.5rem; }
.category-icon { color: #666; transition: transform 0.2s; flex-shrink: 0; }
.category-icon.expanded { transform: rotate(90deg); }
.category-name { font-size: 0.9375rem; text-transform: uppercase; letter-spacing: 0.5px; }
.subcategory-header-row { background: #fafafa; cursor: pointer; transition: background 0.2s; }
.subcategory-header-row:hover { background: #f5f5f5; }
.subcategory-header-cell { padding: 0.75rem 1rem 0.75rem 2.5rem !important; font-weight: 600; color: #333; text-align: left !important; }
.subcategory-header-content { display: flex; align-items: center; gap: 0.5rem; }
.subcategory-icon { width: 14px; height: 14px; }
.subcategory-name { font-size: 0.875rem; font-weight: 600; letter-spacing: 0.3px; }
.subcategory-data-row { background: #fcfcfc; }
.subcategory-data-row:hover { background: #f8f8f8; }
.subcategory-item { padding-left: 3.5rem !important; font-weight: 400; }
.calculated-metric-row { background: #f0f7ff; border-left: 3px solid #3b82f6; }
.calculated-metric-row:hover { background: #e6f2ff; }
.calculated-metric { font-style: italic; color: #1e40af; font-weight: 500; }
.calculated-value { color: #1e40af; font-weight: 600; }
.segmentation-row { background: #fef3c7; border-left: 3px solid #f59e0b; }
.segmentation-row:hover { background: #fde68a; }
.segmentation-item { padding-left: 2.5rem !important; font-style: italic; color: #92400e; font-weight: 500; font-size: 0.875rem; }
</style>
