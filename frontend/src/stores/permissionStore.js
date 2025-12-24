import { defineStore } from 'pinia'
import { ref } from 'vue'

export const usePermissionStore = defineStore('permissions', () => {
    const permissions = ref([])
    const isFetching = ref(false)

    // Load from localStorage on init
    try {
        const stored = localStorage.getItem('user_permissions')
        if (stored) {
            permissions.value = JSON.parse(stored)
        }
    } catch (e) {
        console.error('Error loading permissions:', e)
    }

    function set(newPermissions) {
        permissions.value = newPermissions
        localStorage.setItem('user_permissions', JSON.stringify(newPermissions))
    }

    function clear() {
        permissions.value = []
        localStorage.removeItem('user_permissions')
    }

    async function fetchPermissions(apiBaseUrl) {
        if (isFetching.value) return

        const token = localStorage.getItem('access_token')
        if (!token) return

        isFetching.value = true
        try {
            const response = await fetch(`${apiBaseUrl}/api/auth/my-permissions`, {
                headers: { 'Authorization': `Bearer ${token}` }
            })

            if (response.ok) {
                const data = await response.json()
                set(data)
            }
        } catch (e) {
            console.error('Error fetching permissions:', e)
        } finally {
            isFetching.value = false
        }
    }

    function hasAccess(resource) {
        return permissions.value.includes(resource)
    }

    return {
        permissions,
        set,
        clear,
        fetch: fetchPermissions,
        hasAccess
    }
})
