import { ref, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import API_BASE_URL from '@/config/api.js'

export function usePayment() {
    const router = useRouter()
    const hasPaid = ref(false)
    const loading = ref(true)

    const checkPaymentStatus = async (redirectOnFail = true) => {
        const token = localStorage.getItem('access_token')
        if (!token) {
            if (redirectOnFail) router.push('/login')
            return false
        }

        try {
            // In a real app we would call the endpoint.
            // For now, mirroring ResearchView logic:
            const response = await fetch(`${API_BASE_URL}/api/auth/payment-status`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            })

            if (response.ok) {
                const status = await response.json()
                // Grant access if paid OR if user is admin/creator
                if (status.role === 'admin' || status.role === 'creator') {
                    hasPaid.value = true
                } else {
                    hasPaid.value = status.has_paid || false
                }
            } else if (response.status === 401) {
                // Token expired or invalid
                localStorage.removeItem('access_token')
                localStorage.removeItem('user')
                if (redirectOnFail) router.push('/login')
                hasPaid.value = false
            }
        } catch (error) {
            console.error('Error checking payment status:', error)
            // On error, allow access (fail open) - as per original file
            hasPaid.value = true
        } finally {
            loading.value = false
        }
        return hasPaid.value
    }

    const setupPaymentListeners = () => {
        const handleVerify = () => checkPaymentStatus(false)
        window.addEventListener('payment-verified', handleVerify)
        onUnmounted(() => {
            window.removeEventListener('payment-verified', handleVerify)
        })
    }

    return {
        hasPaid,
        loading,
        checkPaymentStatus,
        setupPaymentListeners
    }
}
