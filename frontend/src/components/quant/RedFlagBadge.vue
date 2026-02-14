<template>
  <div class="red-flag-badge" v-tooltip="reason">
    <span class="icon">⚠️</span>
    <span class="text">Red Flag</span>
  </div>
</template>

<script>
export default {
  name: 'RedFlagBadge',
  props: {
    reason: {
      type: String,
      required: true
    }
  }
}
</script>

<style scoped>
.red-flag-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.75rem;
  background-color: #fef2f2;
  color: #dc2626;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: help;
  transition: all 0.2s;
}

.red-flag-badge:hover {
  background-color: #fee2e2;
  transform: scale(1.05);
}

.red-flag-badge .icon {
  font-size: 1rem;
}

.red-flag-badge .text {
  white-space: nowrap;
}
</style>
