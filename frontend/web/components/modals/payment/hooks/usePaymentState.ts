import { useState } from 'react'
import AccountStore from 'common/stores/account-store'

type PaymentState = {
  organisation: any
  plan: string
  isAWS: boolean
  hasActiveSubscription: boolean
  yearly: boolean
  setYearly: (yearly: boolean) => void
}

export const usePaymentState = (): PaymentState => {
  const [yearly, setYearly] = useState(true)

  const organisation = AccountStore.getOrganisation()
  const plan = organisation?.subscription?.plan ?? ''
  const isAWS = organisation?.subscription?.payment_method === 'AWS_MARKETPLACE'
  const hasActiveSubscription = !!AccountStore.getOrganisationPlan(
    organisation?.id,
  )

  return {
    hasActiveSubscription,
    isAWS,
    organisation,
    plan,
    setYearly,
    yearly,
  }
}
