import { useState } from 'react'
// @ts-ignore
import _data from 'common/data/base/_data'

type UseChargebeeCheckoutParams = {
  organisationId: number | undefined
  onSuccess?: () => void
}

export const useChargebeeCheckout = ({
  onSuccess,
  organisationId,
}: UseChargebeeCheckoutParams) => {
  const [isLoading, setIsLoading] = useState(false)

  const openCheckout = (planId: string) => {
    if (!organisationId) return

    setIsLoading(true)
    Chargebee.getInstance().openCheckout({
      close: () => {
        setIsLoading(false)
      },
      hostedPage() {
        return _data.post(
          `${Project.api}organisations/${organisationId}/get-hosted-page-url-for-subscription-upgrade/`,
          { plan_id: planId },
        )
      },
      success: (res: any) => {
        AppActions.updateSubscription(res)
        onSuccess?.()
      },
    })
  }

  return { isLoading, openCheckout }
}
