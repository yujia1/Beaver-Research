<template>
  <div class="success-container">
    <div class="success-card">
      <div class="icon-circle">
        ✓
      </div>
      <h1>{{ t('payment.success_title') }}</h1>
      <p>{{ t('payment.success_message') }}</p>
      
      <div class="actions">
        <button @click="router.push('/dashboard')" class="dashboard-btn">
          {{ t('payment.go_to_dashboard') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/stores/userStore';
import { useI18n } from 'vue-i18n';
import API_BASE_URL from '@/config/api';

const router = useRouter();
const userStore = useUserStore();
const { t } = useI18n();

onMounted(async () => {
  // Force refresh user data to update permission/payment status
  if (userStore.isAuthenticated) {
    await userStore.fetchUser(API_BASE_URL);
    // Also refresh permissions
    // Note: You might need to import permissionStore or just let app logic handle it
    // userStore.fetchUser typically updates the user object which includes has_paid
  }
});
</script>

<style scoped>
.success-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
  padding: 2rem;
}

.success-card {
  background: #1f2937;
  padding: 3rem;
  border-radius: 1rem;
  text-align: center;
  max-width: 500px;
  border: 1px solid #374151;
}

.icon-circle {
  width: 80px;
  height: 80px;
  background: #059669;
  color: white;
  font-size: 3rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 2rem auto;
}

h1 {
  color: #f3f4f6;
  margin-bottom: 1rem;
}

p {
  color: #9ca3af;
  margin-bottom: 2rem;
  line-height: 1.6;
}

.dashboard-btn {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.dashboard-btn:hover {
  background: #1d4ed8;
}
</style>
