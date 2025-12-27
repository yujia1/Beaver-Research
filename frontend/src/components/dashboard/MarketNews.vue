<template>
  <div class="market-news-container">
    <div class="news-header">
      <div class="title-container">
        <h3>{{ t('dashboard.market_news.title') }}</h3>
        <span class="pulse-dot"></span>
      </div>
      <div class="header-actions">
        <button class="action-btn">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
        </button>
        <button class="action-btn">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
        </button>
      </div>
    </div>

    <div class="news-list">
      <div v-for="item in newsItems" :key="item.id" class="news-item">
        <div class="news-meta">
          <span class="news-time">{{ item.time }}</span>
          <div class="news-trending" :class="item.sentiment">
            <svg v-if="item.sentiment === 'positive'" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"></polyline><polyline points="17 18 23 18 23 12"></polyline></svg>
          </div>
        </div>

        <div class="news-content">
          <div class="news-tags">
            <span v-for="tag in item.tags" :key="tag" class="news-tag">{{ tag }}</span>
          </div>
          <h4 class="news-headline">{{ item.headline }}</h4>
          <p class="news-summary">{{ item.summary }}</p>
        </div>

        <div class="news-thumbnail">
           <!-- Using placeholder images or colored blocks since we don't have real images -->
           <div class="thumbnail-placeholder" :style="{ backgroundColor: item.color }"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const newsItems = ref([
  {
    id: 1,
    time: "05:50:10 PM",
    sentiment: "negative",
    tags: ["MARKETS", "$TLX"],
    headline: "$TLX Telix Pharmaceuticals Plunges 21% on SEC Subpoena and FDA Manufacturing Rejection",
    summary: "Shares cratered following a devastating Complete Response Letter from the FDA and a concurrent SEC subpoena regarding disclosures for its prostate cancer drug candidates. The regulatory setbacks have triggered a wave of securities class action filings...",
    color: "#e5e7eb"
  },
  {
    id: 2,
    time: "05:50:10 PM",
    sentiment: "positive",
    tags: ["MARKETS", "$TGT"],
    headline: "$TGT Target Shares Rally as Activist Investor Reports New Multi-Million Dollar Stake",
    summary: "The retail giant saw a late-session surge in interest following reports that an activist investor is building a position to push for structural changes. Analysts anticipate immediate pressure on management to address margin compression and inventory...",
    color: "#d1d5db"
  },
  {
    id: 3,
    time: "05:50:10 PM",
    sentiment: "negative",
    tags: ["MARKETS", "$BTC", "$ETH"],
    headline: "$BTC / $ETH Crypto Markets Slide as Bitcoin Loses $90,000 Support Level Amid Risk-Off Sentiment",
    summary: "Major digital assets are experiencing broad-based selling pressure, with Bitcoin retreating toward the $87,000 mark as year-end profit-taking and ETF outflows accelerate. The global crypto market cap fell 1.19% in the last few hours as traders rotate out of high...",
    color: "#e5e7eb"
  },
  {
    id: 4,
    time: "05:50:10 PM",
    sentiment: "positive",
    tags: ["MARKETS", "$NVDA"],
    headline: "$NVDA Nvidia Finalizes $20 Billion Licensing Agreement with AI Accelerator Startup Groq",
    summary: "The deal grants the chip giant access to specialized LPU (Language Processing Unit) technology to bolster its AI inference capabilities against rising competition from custom ASIC manufacturers. Market analysts view the move as a strategic hedge to...",
    color: "#4b5563"
  }
]);
</script>

<style scoped>
.market-news-container {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1.5rem;
  margin-top: 2rem;
  font-family: 'Inter', sans-serif;
}

.news-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #f3f4f6;
}

.title-container {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.news-header h3 {
  font-size: 1.25rem;
  font-weight: 800;
  color: #111827;
  text-transform: uppercase;
  margin: 0;
  letter-spacing: 0.5px;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background-color: #3b82f6;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 1; box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7); }
  50% { transform: scale(1); opacity: 0.7; box-shadow: 0 0 0 4px rgba(59, 130, 246, 0); }
  100% { transform: scale(1); opacity: 1; box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); }
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #9ca3af;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
}

.action-btn:hover {
  color: #111827;
  background-color: #f3f4f6;
}

.news-list {
  display: flex;
  flex-direction: column;
}

.news-item {
  display: flex;
  gap: 1.5rem;
  padding: 1.5rem 0;
  border-bottom: 1px solid #f3f4f6;
}

.news-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.news-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  min-width: 80px;
  gap: 0.5rem;
}

.news-time {
  font-size: 0.75rem;
  color: #9ca3af;
  font-weight: 600;
  font-family: 'Courier New', monospace;
  white-space: pre-wrap;
  width: 60px;
  line-height: 1.2;
}

.news-trending {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.news-trending.positive {
  background-color: #ecfdf5;
  color: #10b981;
}

.news-trending.negative {
  background-color: #fef2f2;
  color: #ef4444;
}

.news-content {
  flex: 1;
}

.news-tags {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.news-tag {
  font-size: 0.7rem;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  background-color: #f3f4f6;
  color: #4b5563;
  text-transform: uppercase;
}

.news-tag:first-child {
  background-color: #eff6ff;
  color: #2563eb;
}

.news-headline {
  font-size: 1rem;
  font-weight: 700;
  color: #111827;
  margin: 0 0 0.5rem 0;
  line-height: 1.4;
}

.news-summary {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
  line-height: 1.5;
}

.news-thumbnail {
  width: 96px;
  height: 64px;
  flex-shrink: 0;
}

.thumbnail-placeholder {
  width: 100%;
  height: 100%;
  border-radius: 4px;
  background-color: #e5e7eb;
}
</style>
