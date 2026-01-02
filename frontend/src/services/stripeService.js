import { loadStripe } from '@stripe/stripe-js'

// Singleton state
let stripePromise = null
let checkoutInstance = null
let currentMountId = 0

const STRIPE_KEY = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY

// Initialize Stripe Promise once
const getStripe = () => {
    if (!stripePromise) {
        if (!STRIPE_KEY) {
            console.error('Stripe Publishable Key is missing')
            return Promise.reject(new Error('Stripe not configured'))
        }
        stripePromise = loadStripe(STRIPE_KEY)
    }
    return stripePromise
}

export const StripeCheckoutService = {
    /**
     * Mounts the Stripe Embedded Checkout to the given element ID.
     * Guaranteed to destroy any previous instance first.
     * @param {string} elementId - The DOM ID to mount to (e.g. '#checkout')
     * @param {Function} fetchClientSecret - Async function returning clientSecret
     */
    async mount(elementId, fetchClientSecret) {
        // Increment ID to identify this specific request
        const myId = ++currentMountId

        // 1. Destroy existing instance if any
        if (checkoutInstance) {
            try {
                await checkoutInstance.destroy()
            } catch (e) {
                console.warn('StripeService: Failed to destroy previous instance', e)
            }
            checkoutInstance = null
        }

        // 2. Load Stripe
        const stripe = await getStripe()

        // check staleness (if another mount was requested while we awaited)
        if (myId !== currentMountId) {
            return
        }

        // 3. Initialize Checkouts
        const instance = await stripe.initEmbeddedCheckout({
            fetchClientSecret
        })

        // check staleness again
        if (myId !== currentMountId) {
            instance.destroy()
            return
        }

        // 4. Mount
        checkoutInstance = instance
        instance.mount(elementId)

        return instance
    },

    /**
     * Force destroy the current instance.
     * Useful for unmounting components.
     */
    async destroy() {
        // Increment ID to prevent pending mounts from succeeding
        currentMountId++

        if (checkoutInstance) {
            try {
                await checkoutInstance.destroy()
            } catch (e) {
                // ignore
            }
            checkoutInstance = null
        }
    }
}
