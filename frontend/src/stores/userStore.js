import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { usePermissionStore } from './permissionStore'
import router from '@/router'

export const useUserStore = defineStore('user', () => {
    const user = ref(null)
    const token = ref(localStorage.getItem('access_token') || null)
    const isAuthenticated = computed(() => !!token.value)

    // Permission store dependency
    const permissionStore = usePermissionStore()

    function setUser(userData) {
        user.value = userData
        localStorage.setItem('user', JSON.stringify(userData))
    }

    function setToken(newToken) {
        token.value = newToken
        localStorage.setItem('access_token', newToken)
    }

    async function fetchUser(apiBaseUrl) {
        if (!token.value) return null

        try {
            const response = await fetch(`${apiBaseUrl}/api/auth/me`, {
                headers: { 'Authorization': `Bearer ${token.value}` }
            })

            if (response.ok) {
                const userData = await response.json()
                setUser(userData)
                return userData
            } else {
                logout() // Invalid token
            }
        } catch (e) {
            console.error('Error fetching user:', e)
        }
        return null
    }

    async function login(username, password, apiBaseUrl) {
        try {
            const response = await fetch(`${apiBaseUrl}/api/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            })

            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.detail || 'Login failed')
            }

            const data = await response.json()
            setToken(data.access_token)

            // Fetch user info
            await fetchUser(apiBaseUrl)

            // Fetch permissions
            await permissionStore.fetch(apiBaseUrl)

            return true
        } catch (e) {
            throw e
        }
    }

    function logout() {
        token.value = null
        user.value = null
        localStorage.removeItem('access_token')
        localStorage.removeItem('user')
        permissionStore.clear()
        router.push('/login')
    }

    // Init from localStorage
    const savedUser = localStorage.getItem('user')
    if (savedUser) {
        try {
            user.value = JSON.parse(savedUser)
        } catch (e) {
            console.error(e)
        }
    }

    return {
        user,
        token,
        isAuthenticated,
        login,
        logout,
        fetchUser
    }
})
