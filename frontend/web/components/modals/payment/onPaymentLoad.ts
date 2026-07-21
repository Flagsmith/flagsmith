// @ts-ignore
import firstpromoter from 'project/firstPromoter'
import Utils from 'common/utils/utils'

type OnPaymentLoadArgs = {
  errored?: boolean
}

export const onPaymentLoad = ({ errored }: OnPaymentLoadArgs) => {
  if (errored) return
  if (!Project.chargebee?.site) return

  const planId = API.getCookie('plan')
  let link: HTMLAnchorElement | undefined
  if (planId && Utils.getFlagsmithHasFeature('payments_enabled')) {
    link = document.createElement('a')
    link.setAttribute('data-cb-type', 'checkout')
    link.setAttribute('data-cb-plan-id', planId)
    link.setAttribute('href', 'javascript:void(0)')
    document.body.appendChild(link)
  }

  Chargebee.init({ site: Project.chargebee.site })
  Chargebee.registerAgain()
  firstpromoter()
  Chargebee.getInstance().setCheckoutCallbacks?.(() => ({
    success: (hostedPageId: string) => {
      AppActions.updateSubscription(hostedPageId)
    },
  }))

  if (link) {
    link.click()
    document.body.removeChild(link)
    API.setCookie('plan', null)
  }
}
