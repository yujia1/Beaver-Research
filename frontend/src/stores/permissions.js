// Centralized permission store
// Load once on login, reuse everywhere
let cachedPermissions = null
let permissionsPromise = null

export const permissionStore = {
    // Get permissions (from cache or localStorage)
    get() {
        if (cachedPermissions) {
            return cachedPermissions
        }

        // Try to load from localStorage
        try {
            const stored = localStorage.getItem('user_permissions')
            if (stored) {
                cachedPermissions = JSON.parse(stored)
                return cachedPermissions
            }
        } catch (e) {
            console.error('Error loading permissions from localStorage:', e)
        }

        return []
    },

    // Set permissions (called after login or API fetch)
    set(permissions) {
        cachedPermissions = permissions
        try {
            localStorage.setItem('user_permissions', JSON.stringify(permissions))
        } catch (e) {
            console.error('Error saving permissions to localStorage:', e)
        }
    },

    // Clear permissions (on logout)
    clear() {
        cachedPermissions = null
        localStorage.removeItem('user_permissions')
    },

    // Fetch from API (with deduplication)
    async fetch(apiBaseUrl) {
        // If already fetching, return that promise
        if (permissionsPromise) {
            return permissionsPromise
        }

        const token = localStorage.getItem('access_token')
        if (!token) {
            return []
        }

        permissionsPromise = (async () => {
            try {
                const response = await fetch(`${apiBaseUrl}/api/auth/my-permissions`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                })

                if (response.ok) {
                    const permissions = await response.json()
                    this.set(permissions)
                    return permissions
                }
                return []
            } catch (e) {
                console.error('Error fetching permissions:', e)
                return []
            } finally {
                permissionsPromise = null
            }
        })()

        return permissionsPromise
    },

    // Check if user has access to a resource
    hasAccess(resource) {
        const permissions = this.get()
        return permissions.includes(resource)
    }
}
