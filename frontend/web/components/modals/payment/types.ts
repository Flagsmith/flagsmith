import { ReactNode } from 'react'

// ============================================================================
// Global Declarations
// ============================================================================

// Chargebee SDK - Global type declaration for the Chargebee payment integration
type ChargebeeInstance = {
  openCheckout: (config: {
    hostedPage: () => Promise<any>
    success: (res: any) => void
  }) => void
  setCheckoutCallbacks?: (fn: () => { success: (id: string) => void }) => void
  getCart: () => {
    setCustomer: (customer: { cf_tid?: string }) => void
  }
}

type ChargebeeSDK = {
  init: (config: { site: string }) => void
  registerAgain: () => void
  getInstance: () => ChargebeeInstance
}

declare global {
  const Chargebee: ChargebeeSDK
}

// ============================================================================
// Shared Types (used by multiple components)
// ============================================================================

export type PricingFeature = {
  icon?: string
  iconClass?: string
  text: ReactNode
}
