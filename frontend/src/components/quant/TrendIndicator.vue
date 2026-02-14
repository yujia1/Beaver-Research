<template>
  <div class="trend-indicator" :class="trendClass">
    <span class="arrow">{{ trendArrow }}</span>
    <span class="direction">{{ trendText }}</span>
  </div>
</template>

<script>
export default {
  name: 'TrendIndicator',
  props: {
    trend: {
      type: Object,
      required: true,
      validator: (value) => {
        return value && typeof value.direction === 'string'
      }
    }
  },
  computed: {
    trendClass() {
      if (!this.trend || !this.trend.direction) return 'neutral'
      return this.trend.direction.toLowerCase()
    },
    trendArrow() {
      const direction = this.trend?.direction?.toLowerCase()
      if (direction === 'improving') return '↗'
      if (direction === 'declining') return '↘'
      return '→'
    },
    trendText() {
      if (!this.trend || !this.trend.direction) return 'Stable'
      return this.trend.direction.charAt(0).toUpperCase() + this.trend.direction.slice(1)
    }
  }
}
</script>

<style scoped>
.trend-indicator {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.875rem;
  font-weight: 500;
}

.trend-indicator .arrow {
  font-size: 1.25rem;
  font-weight: bold;
}

.trend-indicator.improving {
  color: #10b981;
}

.trend-indicator.declining {
  color: #ef4444;
}

.trend-indicator.stable,
.trend-indicator.neutral {
  color: #6b7280;
}
</style>
