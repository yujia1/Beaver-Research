<template>
  <div class="report-view">
    <h2>Reports</h2>
    
    <div class="category-tabs">
      <button 
        v-for="category in categories" 
        :key="category.value" 
        :class="{ active: activeCategory === category.value }"
        @click="activeCategory = category.value"
      >
        {{ category.label }}
      </button>
    </div>

    <div class="content-container">
        <div class="main-report-area">
            <div v-if="loadingReports" class="loading">Loading reports...</div>
            <div v-else>
                <!-- Long Position Reports -->
                <div v-if="activeCategory === 'long'" class="report-category">
                    <div v-if="longReports.length === 0" class="no-reports">No long position reports</div>
                    <ul v-else class="report-list">
                        <li v-for="savedReport in longReports" :key="savedReport.id" :class="{ active: expandedReportIds.has(savedReport.id) }">
                            <div class="report-item-header" @click="toggleReport(savedReport)">
                                <span class="report-ticker">{{ savedReport.ticker }} - {{ new Date(savedReport.created_at).toLocaleDateString('en-US', { year: 'numeric', month: '2-digit', day: '2-digit' }) }}</span>
                                <span class="report-date">{{ formatDate(savedReport.created_at) }}</span>
                            </div>
                            <div v-if="expandedReportIds.has(savedReport.id)" class="report-item-content">
                                <div v-if="loadingReportsById[savedReport.id]" class="loading">Loading report...</div>
                                <div v-else class="report-body" v-html="getReportContent(savedReport)"></div>
                            </div>
                        </li>
                    </ul>
                </div>

                <!-- Daily Reports -->
                <div v-if="activeCategory === 'daily'" class="report-category">
                    <div v-if="dailyReports.length === 0" class="no-reports">No daily reports</div>
                    <ul v-else class="report-list">
                        <li v-for="savedReport in dailyReports" :key="savedReport.id" :class="{ active: expandedReportIds.has(savedReport.id) }">
                            <div class="report-item-header" @click="toggleReport(savedReport)">
                                <span class="report-ticker">{{ savedReport.ticker }} - {{ new Date(savedReport.created_at).toLocaleDateString('en-US', { year: 'numeric', month: '2-digit', day: '2-digit' }) }}</span>
                                <span class="report-date">{{ formatDate(savedReport.created_at) }}</span>
                            </div>
                            <div v-if="expandedReportIds.has(savedReport.id)" class="report-item-content">
                                <div v-if="loadingReportsById[savedReport.id]" class="loading">Loading report...</div>
                                <div v-else class="report-body" v-html="getReportContent(savedReport)"></div>
                            </div>
                        </li>
                    </ul>
                </div>

                <!-- Short Position Reports -->
                <div v-if="activeCategory === 'short'" class="report-category">
                    <div v-if="shortReports.length === 0" class="no-reports">No short position reports</div>
                    <ul v-else class="report-list">
                        <li v-for="savedReport in shortReports" :key="savedReport.id" :class="{ active: expandedReportIds.has(savedReport.id) }">
                            <div class="report-item-header" @click="toggleReport(savedReport)">
                                <span class="report-ticker">{{ savedReport.ticker }} - {{ new Date(savedReport.created_at).toLocaleDateString('en-US', { year: 'numeric', month: '2-digit', day: '2-digit' }) }}</span>
                                <span class="report-date">{{ formatDate(savedReport.created_at) }}</span>
                            </div>
                            <div v-if="expandedReportIds.has(savedReport.id)" class="report-item-content">
                                <div v-if="loadingReportsById[savedReport.id]" class="loading">Loading report...</div>
                                <div v-else class="report-body" v-html="getReportContent(savedReport)"></div>
                            </div>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { marked } from 'marked';

// Saved Reports State
const savedReports = ref([]);
const loadingReports = ref(false);
const expandedReportIds = ref(new Set()); // Track multiple expanded reports
const activeCategory = ref('long');

// Report Content State - store content by report ID
const reportContents = ref({});
const loadingReportsById = ref({}); // Track loading state per report

// Mock data for daily reports
const mockDailyReports = [
  {
    id: 'mock-daily-1',
    ticker: 'AAPL',
    title: 'AAPL - 2024-01-15',
    report_type: 'daily',
    created_at: '2024-01-15T09:00:00',
    content: `# Daily Report: Apple Inc. (AAPL)
## Date: January 15, 2024

### Market Overview
Apple Inc. (AAPL) showed strong performance today with the stock closing at $185.50, up 2.3% from the previous day's close. Trading volume was above average at 65 million shares.

### Key Highlights
- **Price Movement**: Stock gained $4.15 (2.3%) during the trading session
- **Volume**: 65M shares traded, 15% above 30-day average
- **Market Cap**: $2.89 trillion
- **52-Week Range**: $164.08 - $198.23

### Technical Analysis
The stock broke through the $185 resistance level with strong momentum. RSI indicator shows 68, indicating bullish sentiment but approaching overbought territory. Support level is now at $182.

### News & Events
- Apple announced new AI features for iPhone
- Analysts upgraded price target to $210
- Strong holiday sales reported

### Outlook
Short-term outlook remains positive with continued momentum expected. Investors should monitor the $190 resistance level.`
  },
  {
    id: 'mock-daily-2',
    ticker: 'MSFT',
    title: 'MSFT - 2024-01-15',
    report_type: 'daily',
    created_at: '2024-01-15T09:00:00',
    content: `# Daily Report: Microsoft Corporation (MSFT)
## Date: January 15, 2024

### Market Overview
Microsoft Corporation (MSFT) closed at $378.85, up 1.8% on the day. The stock saw increased buying interest following positive earnings guidance.

### Key Highlights
- **Price Movement**: Stock gained $6.70 (1.8%) during the trading session
- **Volume**: 28M shares traded, 8% above average
- **Market Cap**: $2.81 trillion
- **52-Week Range**: $309.45 - $384.30

### Technical Analysis
MSFT is trading near its 52-week high with strong upward momentum. The stock is well above all major moving averages. MACD shows bullish crossover signal.

### News & Events
- Azure cloud services revenue exceeded expectations
- New AI integration in Office 365 announced
- Partnership with major enterprise clients

### Outlook
Positive momentum expected to continue. Next resistance at $385. Support level at $375.`
  },
  {
    id: 'mock-daily-3',
    ticker: 'GOOGL',
    title: 'GOOGL - 2024-01-14',
    report_type: 'daily',
    created_at: '2024-01-14T09:00:00',
    content: `# Daily Report: Alphabet Inc. (GOOGL)
## Date: January 14, 2024

### Market Overview
Alphabet Inc. (GOOGL) closed at $142.50, down 0.5% from the previous day. The stock experienced some profit-taking after recent gains.

### Key Highlights
- **Price Movement**: Stock declined $0.72 (0.5%) during the trading session
- **Volume**: 32M shares traded, near average
- **Market Cap**: $1.78 trillion
- **52-Week Range**: $115.55 - $151.55

### Technical Analysis
The stock is consolidating near recent highs. RSI at 55 indicates neutral momentum. Key support at $140, resistance at $145.

### News & Events
- Google Cloud revenue growth accelerated
- New AI search features launched
- Regulatory concerns in EU markets

### Outlook
Neutral to slightly bullish. Watch for breakout above $145 for continued upward movement.`
  },
  {
    id: 'mock-daily-4',
    ticker: 'TSLA',
    title: 'TSLA - 2024-01-14',
    report_type: 'daily',
    created_at: '2024-01-14T09:00:00',
    content: `# Daily Report: Tesla Inc. (TSLA)
## Date: January 14, 2024

### Market Overview
Tesla Inc. (TSLA) closed at $248.50, up 3.2% on strong delivery numbers. The stock outperformed the broader market.

### Key Highlights
- **Price Movement**: Stock gained $7.70 (3.2%) during the trading session
- **Volume**: 125M shares traded, 45% above average
- **Market Cap**: $789 billion
- **52-Week Range**: $152.37 - $299.29

### Technical Analysis
Strong breakout above $245 resistance level. Volume surge confirms bullish sentiment. RSI at 72, approaching overbought but momentum remains strong.

### News & Events
- Q4 delivery numbers exceeded expectations
- New Model 3 refresh announced
- Supercharger network expansion plans

### Outlook
Very bullish short-term outlook. Next target at $260. Support at $240.`
  },
  {
    id: 'mock-daily-5',
    ticker: 'NVDA',
    title: 'NVDA - 2024-01-13',
    report_type: 'daily',
    created_at: '2024-01-13T09:00:00',
    content: `# Daily Report: NVIDIA Corporation (NVDA)
## Date: January 13, 2024

### Market Overview
NVIDIA Corporation (NVDA) closed at $522.50, up 4.1% following strong AI chip demand forecasts. The stock led the tech sector higher.

### Key Highlights
- **Price Movement**: Stock gained $20.60 (4.1%) during the trading session
- **Volume**: 58M shares traded, 25% above average
- **Market Cap**: $1.29 trillion
- **52-Week Range**: $385.30 - $502.66

### Technical Analysis
Breakout above $500 psychological level with strong momentum. All technical indicators are bullish. Stock is in strong uptrend.

### News & Events
- AI chip demand forecast raised by 30%
- New data center partnerships announced
- Analyst upgrades across the board

### Outlook
Extremely bullish. Stock targeting $550 next. Support at $500.`
  },
  {
    id: 'mock-daily-6',
    ticker: 'AMZN',
    title: 'AMZN - 2024-01-13',
    report_type: 'daily',
    created_at: '2024-01-13T09:00:00',
    content: `# Daily Report: Amazon.com Inc. (AMZN)
## Date: January 13, 2024

### Market Overview
Amazon.com Inc. (AMZN) closed at $151.20, up 1.5% on positive holiday sales data. The e-commerce giant showed resilience.

### Key Highlights
- **Price Movement**: Stock gained $2.23 (1.5%) during the trading session
- **Volume**: 42M shares traded, 12% above average
- **Market Cap**: $1.56 trillion
- **52-Week Range**: $101.15 - $155.63

### Technical Analysis
Stock is approaching 52-week high with steady momentum. RSI at 65 indicates healthy bullish trend. Support at $148.

### News & Events
- Record holiday sales reported
- AWS cloud services growth accelerated
- Prime membership numbers increased

### Outlook
Positive outlook with potential to break above $155. Support at $148.`
  }
];

// Mock data for long position reports
const mockLongReports = [
  {
    id: 'mock-long-1',
    ticker: 'AAPL',
    title: 'AAPL - 2024-01-10',
    report_type: 'long',
    created_at: '2024-01-10T09:00:00',
    content: `# Long Position Report: Apple Inc. (AAPL)
## Date: January 10, 2024

### Investment Thesis
Apple Inc. represents a compelling long-term investment opportunity with strong fundamentals, innovative product pipeline, and robust ecosystem. The company's market position and financial strength support a bullish outlook.

### Key Strengths
- **Market Leadership**: Dominant position in premium smartphone and tablet markets
- **Ecosystem Lock-in**: Strong customer loyalty and high switching costs
- **Services Growth**: Expanding high-margin services revenue (App Store, iCloud, Apple Music)
- **Financial Health**: Strong cash position ($165B) and consistent dividend payments
- **Innovation**: Continuous product innovation and R&D investment

### Financial Metrics
- **Current Price**: $185.50
- **Target Price**: $210 (13% upside)
- **P/E Ratio**: 30.5 (reasonable for growth stock)
- **Dividend Yield**: 0.5%
- **Revenue Growth**: 8% YoY
- **Profit Margin**: 25.3%

### Risk Factors
- Market saturation in smartphone segment
- Regulatory scrutiny in key markets
- Supply chain dependencies
- Competition from Android ecosystem

### Recommendation
**BUY** - Strong long-term hold with 12-18 month price target of $210. Suitable for growth-oriented portfolios.`
  },
  {
    id: 'mock-long-2',
    ticker: 'MSFT',
    title: 'MSFT - 2024-01-08',
    report_type: 'long',
    created_at: '2024-01-08T09:00:00',
    content: `# Long Position Report: Microsoft Corporation (MSFT)
## Date: January 8, 2024

### Investment Thesis
Microsoft is well-positioned for long-term growth driven by cloud transformation, AI integration, and enterprise software dominance. The company's diversified revenue streams provide stability and growth potential.

### Key Strengths
- **Azure Cloud**: Second-largest cloud provider with 23% market share
- **Office 365**: Recurring revenue from subscription model
- **Enterprise Focus**: Strong relationships with Fortune 500 companies
- **AI Leadership**: Strategic investments in OpenAI and AI capabilities
- **Dividend Growth**: Consistent dividend increases for 18+ years

### Financial Metrics
- **Current Price**: $378.85
- **Target Price**: $420 (11% upside)
- **P/E Ratio**: 35.2
- **Dividend Yield**: 0.7%
- **Revenue Growth**: 13% YoY
- **Cloud Revenue Growth**: 28% YoY

### Risk Factors
- Cloud competition from AWS and Google
- Economic sensitivity in enterprise spending
- Regulatory concerns in EU
- Currency headwinds

### Recommendation
**BUY** - Excellent long-term hold with strong cloud and AI tailwinds. Target price $420 over 12-18 months.`
  },
  {
    id: 'mock-long-3',
    ticker: 'NVDA',
    title: 'NVDA - 2024-01-05',
    report_type: 'long',
    created_at: '2024-01-05T09:00:00',
    content: `# Long Position Report: NVIDIA Corporation (NVDA)
## Date: January 5, 2024

### Investment Thesis
NVIDIA is the clear leader in AI chip technology with dominant market position in data center GPUs. The AI revolution provides massive tailwinds for long-term growth.

### Key Strengths
- **AI Leadership**: 80%+ market share in AI training chips
- **Data Center Growth**: Explosive demand from cloud providers and enterprises
- **Software Moat**: CUDA platform creates switching costs
- **Gaming Segment**: Strong position in gaming GPU market
- **Innovation**: Continuous advancement in chip technology

### Financial Metrics
- **Current Price**: $522.50
- **Target Price**: $600 (15% upside)
- **P/E Ratio**: 65.3 (high but justified by growth)
- **Revenue Growth**: 206% YoY
- **Data Center Revenue**: $14.5B (up 279% YoY)
- **Gross Margin**: 76.0%

### Risk Factors
- High valuation multiples
- Cyclical nature of chip industry
- Competition from AMD and custom chips
- Regulatory restrictions in China

### Recommendation
**BUY** - High-growth opportunity with significant upside. Target $600 over 12-18 months. Suitable for aggressive growth portfolios.`
  },
  {
    id: 'mock-long-4',
    ticker: 'GOOGL',
    title: 'GOOGL - 2024-01-03',
    report_type: 'long',
    created_at: '2024-01-03T09:00:00',
    content: `# Long Position Report: Alphabet Inc. (GOOGL)
## Date: January 3, 2024

### Investment Thesis
Alphabet offers attractive valuation with strong search dominance and growing cloud/AI businesses. The stock trades at a discount to peers despite solid fundamentals.

### Key Strengths
- **Search Monopoly**: 92% market share in search advertising
- **YouTube**: Dominant video platform with growing ad revenue
- **Google Cloud**: Rapidly growing cloud business (now profitable)
- **AI Innovation**: Leading AI research and product integration
- **Valuation**: Trading at reasonable P/E of 24.5

### Financial Metrics
- **Current Price**: $142.50
- **Target Price**: $165 (16% upside)
- **P/E Ratio**: 24.5 (attractive vs peers)
- **Revenue Growth**: 11% YoY
- **Cloud Revenue**: $8.4B (up 22% YoY)
- **Operating Margin**: 28.5%

### Risk Factors
- Regulatory pressure in EU and US
- Competition in search from AI assistants
- Cloud market share challenges
- Antitrust concerns

### Recommendation
**BUY** - Undervalued with strong fundamentals. Target $165 over 12-18 months. Good value play in tech sector.`
  }
];

// Mock data for short position reports
const mockShortReports = [
  {
    id: 'mock-short-1',
    ticker: 'TSLA',
    title: 'TSLA - 2024-01-12',
    report_type: 'short',
    created_at: '2024-01-12T09:00:00',
    content: `# Short Position Report: Tesla Inc. (TSLA)
## Date: January 12, 2024

### Short Thesis
Tesla faces significant headwinds including valuation concerns, increasing competition, and execution risks. The stock appears overvalued relative to fundamentals.

### Key Concerns
- **Valuation**: Trading at 60x P/E despite slowing growth
- **Competition**: EV market becoming increasingly competitive
- **Price Cuts**: Aggressive price reductions eroding margins
- **Execution Risk**: Production delays and quality issues
- **Cybertruck**: Uncertain demand and production challenges

### Financial Metrics
- **Current Price**: $248.50
- **Target Price**: $180 (28% downside)
- **P/E Ratio**: 60.2 (extremely high)
- **Revenue Growth**: 3% YoY (slowing)
- **Operating Margin**: 8.2% (declining from 17% peak)
- **Free Cash Flow**: Negative in recent quarters

### Risk Factors
- High short interest (could cause squeeze)
- Strong brand and fanbase
- Potential new product launches
- Government EV incentives

### Recommendation
**SHORT** - Overvalued with fundamental deterioration. Target $180 over 6-12 months. High risk/reward ratio.`
  },
  {
    id: 'mock-short-2',
    ticker: 'RIVN',
    title: 'RIVN - 2024-01-11',
    report_type: 'short',
    created_at: '2024-01-11T09:00:00',
    content: `# Short Position Report: Rivian Automotive (RIVN)
## Date: January 11, 2024

### Short Thesis
Rivian faces significant challenges including cash burn, production scaling issues, and intense competition. The path to profitability remains uncertain.

### Key Concerns
- **Cash Burn**: Burning $1.5B+ per quarter
- **Production**: Struggling to scale production efficiently
- **Competition**: Established automakers entering EV market
- **Valuation**: Market cap of $15B with minimal revenue
- **Demand**: Questionable demand for premium EV trucks

### Financial Metrics
- **Current Price**: $15.20
- **Target Price**: $8 (47% downside)
- **Revenue**: $1.3B (annualized)
- **Losses**: -$5.4B (TTM)
- **Cash Position**: $9.2B (will last ~18 months at current burn)
- **Production**: 50K units/year (below targets)

### Risk Factors
- Amazon partnership provides stability
- Strong product reviews
- Potential acquisition target
- Government EV subsidies

### Recommendation
**SHORT** - High cash burn and execution risks. Target $8 over 6-12 months. Monitor cash position closely.`
  },
  {
    id: 'mock-short-3',
    ticker: 'PLTR',
    title: 'PLTR - 2024-01-09',
    report_type: 'short',
    created_at: '2024-01-09T09:00:00',
    content: `# Short Position Report: Palantir Technologies (PLTR)
## Date: January 9, 2024

### Short Thesis
Palantir trades at extreme valuation multiples despite slowing growth and customer concentration risks. The stock appears disconnected from fundamentals.

### Key Concerns
- **Valuation**: Trading at 20x revenue with slowing growth
- **Customer Concentration**: Top 3 customers = 40% of revenue
- **Competition**: Increasing competition in data analytics
- **Stock-Based Compensation**: High dilution from SBC
- **Profitability**: Only recently profitable, margins remain thin

### Financial Metrics
- **Current Price**: $18.50
- **Target Price**: $12 (35% downside)
- **P/S Ratio**: 20.3 (extremely high)
- **Revenue Growth**: 16% YoY (slowing from 30%+)
- **Operating Margin**: 5.2% (thin)
- **SBC**: 15% of revenue (high dilution)

### Risk Factors
- Government contracts provide stability
- AI narrative could drive momentum
- Potential new large contracts
- Short squeeze risk

### Recommendation
**SHORT** - Overvalued with fundamental concerns. Target $12 over 6-12 months. High risk due to volatility.`
  },
  {
    id: 'mock-short-4',
    ticker: 'NIO',
    title: 'NIO - 2024-01-07',
    report_type: 'short',
    created_at: '2024-01-07T09:00:00',
    content: `# Short Position Report: NIO Inc. (NIO)
## Date: January 7, 2024

### Short Thesis
NIO faces severe headwinds including intense competition in China, cash burn concerns, and geopolitical risks. The company's path to profitability is uncertain.

### Key Concerns
- **Competition**: Fierce competition from BYD, Tesla, and local Chinese EV makers
- **Cash Burn**: Burning $500M+ per quarter
- **Market Share**: Declining market share in China EV market
- **Geopolitical Risk**: US-China tensions affecting sentiment
- **Valuation**: Market cap of $8B with negative margins

### Financial Metrics
- **Current Price**: $6.80
- **Target Price**: $4 (41% downside)
- **Revenue**: $7.2B (annualized)
- **Losses**: -$2.1B (TTM)
- **Cash Position**: $5.5B (limited runway)
- **Market Share**: 2.1% in China (declining)

### Risk Factors
- Strong brand in China
- Battery swap technology differentiation
- Potential government support
- Short squeeze risk

### Recommendation
**SHORT** - Competitive pressures and cash concerns. Target $4 over 6-12 months. Monitor cash position and market share trends.`
  }
];

// Categories for tabs
const categories = [
  { label: 'Daily Report', value: 'daily' },
  { label: 'Long Position Report', value: 'long' },
  { label: 'Short Position Report', value: 'short' }
];

// Filtered reports by category
const longReports = computed(() => {
    // Combine API reports with mock data
    const apiLongReports = savedReports.value.filter(report => 
        report.report_type && report.report_type.toLowerCase().includes('long')
    );
    // Sort by date, newest first
    return [...mockLongReports, ...apiLongReports].sort((a, b) => 
        new Date(b.created_at) - new Date(a.created_at)
    );
});

const shortReports = computed(() => {
    // Combine API reports with mock data
    const apiShortReports = savedReports.value.filter(report => 
        report.report_type && report.report_type.toLowerCase().includes('short')
    );
    // Sort by date, newest first
    return [...mockShortReports, ...apiShortReports].sort((a, b) => 
        new Date(b.created_at) - new Date(a.created_at)
    );
});

const dailyReports = computed(() => {
    // Combine API reports with mock data
    const apiDailyReports = savedReports.value.filter(report => 
        report.report_type && report.report_type.toLowerCase().includes('daily')
    );
    // Sort by date, newest first
    return [...mockDailyReports, ...apiDailyReports].sort((a, b) => 
        new Date(b.created_at) - new Date(a.created_at)
    );
});

onMounted(() => {
    fetchReports();
});

const fetchReports = async () => {
    loadingReports.value = true;
    try {
        const response = await fetch('http://localhost:8000/api/reports/');
        if (response.ok) {
            savedReports.value = await response.json();
        }
    } catch (e) {
        console.error("Failed to fetch reports", e);
    } finally {
        loadingReports.value = false;
    }
};

const toggleReport = async (savedReportSummary) => {
    // If clicking an expanded report, collapse it
    if (expandedReportIds.value.has(savedReportSummary.id)) {
        expandedReportIds.value.delete(savedReportSummary.id);
        return;
    }
    
    // Otherwise, expand the clicked report
    expandedReportIds.value.add(savedReportSummary.id);
    
    // If content is already loaded, don't fetch again
    if (reportContents.value[savedReportSummary.id]) {
        return;
    }
    
    loadingReportsById.value[savedReportSummary.id] = true;
    
    try {
        // Check if it's a mock report (has content already)
        if (savedReportSummary.content) {
            reportContents.value[savedReportSummary.id] = savedReportSummary.content;
            loadingReportsById.value[savedReportSummary.id] = false;
        } else {
            // Fetch from API
            const response = await fetch(`http://localhost:8000/api/reports/${savedReportSummary.id}`);
            if (!response.ok) throw new Error('Failed to fetch report content');
            const data = await response.json();
            reportContents.value[savedReportSummary.id] = data.content;
        }
    } catch (e) {
        console.error("Failed to load report", e);
        reportContents.value[savedReportSummary.id] = "Failed to load report content.";
    } finally {
        loadingReportsById.value[savedReportSummary.id] = false;
    }
};

const getReportContent = (savedReportSummary) => {
    const content = reportContents.value[savedReportSummary.id];
    if (!content) return '';
    
    try {
        return marked(content);
    } catch {
        return content.replace(/\n/g, '<br>');
    }
};

const formatDate = (dateString) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString() + ' ' + new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

</script>

<style scoped>
.report-view {
  padding: 20px;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.report-view h2 {
  color: #000000;
}

.category-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 30px;
  justify-content: center;
  flex-wrap: nowrap;
  border-bottom: 2px solid #cccccc;
  padding-bottom: 12px;
  overflow-x: auto;
}

.category-tabs button {
  background: transparent;
  border: none;
  color: #666666;
  padding: 12px 20px;
  border-radius: 6px 6px 0 0;
  cursor: pointer;
  font-size: 0.95em;
  font-weight: 500;
  transition: all 0.2s;
  border-bottom: 3px solid transparent;
}

.category-tabs button.active {
  color: #000000;
  border-bottom-color: #3498db;
  background: rgba(52, 152, 219, 0.1);
  font-weight: 600;
}

.category-tabs button:hover {
  color: #000000;
  background: rgba(0, 0, 0, 0.05);
}

.content-container {
    flex: 1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}

.main-report-area {
    flex: 1;
    overflow-y: auto;
    padding-right: 10px;
    min-height: 0;
}

.report-list {
    list-style: none;
    padding: 0;
    margin: 0;
}

.report-list li {
    border-bottom: 1px solid #eee;
    border-radius: 6px;
    margin-bottom: 5px;
    overflow: hidden;
}

.report-item-header {
    padding: 12px;
    cursor: pointer;
    transition: background 0.2s;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.report-item-header:hover {
    background: #e9ecef;
}

.report-list li.active .report-item-header {
    background: #e3f2fd;
    border-left: 4px solid #42b983;
}

.report-item-content {
    border-top: 1px solid #e0e0e0;
    animation: slideDown 0.3s ease-out;
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    margin: 10px 0;
    max-height: 600px;
    overflow-y: auto;
}

.report-item-content .report-body {
    padding: 20px;
    color: #000000;
    font-size: 0.95em;
    line-height: 1.8;
}

@keyframes slideDown {
    from {
        opacity: 0;
        max-height: 0;
    }
    to {
        opacity: 1;
        max-height: 600px;
    }
}

.report-ticker {
    font-weight: 600;
    color: #000000;
    flex: 1;
}

.report-date {
    font-size: 0.85em;
    color: #000000;
    margin-left: 10px;
}

.report-category {
    margin-top: 20px;
}

.loading {
  text-align: center;
  margin: 20px 0;
  color: #42b983;
}

.report-body {
    line-height: 1.6;
    color: #000000;
}

.report-body :deep(h1), .report-body :deep(h2), .report-body :deep(h3), .report-body :deep(h4), .report-body :deep(h5), .report-body :deep(h6) {
    color: #000000;
    margin-top: 1.5em;
}

.report-body :deep(ul), .report-body :deep(ol) {
    padding-left: 20px;
    color: #000000;
}

.report-body :deep(p) {
    margin-bottom: 1em;
    color: #000000;
}

.report-body :deep(li) {
    color: #000000;
}

.report-body :deep(strong), .report-body :deep(b) {
    color: #000000;
}

.report-body :deep(*) {
    color: #000000;
}


.close-btn {
    padding: 6px 12px;
    background: #95a5a6;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

.close-btn:hover {
    background: #7f8c8d;
}

.no-reports {
    color: black;
    font-style: italic;
    text-align: center;
    margin-top: 20px;
}

</style>
