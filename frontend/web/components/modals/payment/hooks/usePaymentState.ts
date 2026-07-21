import { useState } from 'react'
import { Organisation } from 'common/types/responses'

type UsePaymentStateParams = {
  organisation: Organisation
}

export const usePaymentState = ({ organisation }: UsePaymentStateParams) => {
  const [yearly, setYearly] = useState(true)

  const plan = organisation.subscription.plan ?? ''
  const isAWS = organisation.subscription.payment_method === 'AWS_MARKETPLACE'
  const hasActiveSubscription = !!organisation.subscription.subscription_id

  return {
    hasActiveSubscription,
    isAWS,
    plan,
    setYearly,
    yearly,
  }
}
