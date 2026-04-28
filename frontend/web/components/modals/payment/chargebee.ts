// @ts-ignore
import firstpromoter from 'project/firstPromoter'

let initialised = false

type BindChargebeeButtonsParams = {
  isPaymentsEnabled: boolean
}

const initChargebee = ({
  isPaymentsEnabled,
}: BindChargebeeButtonsParams) => {
  Chargebee.init({ site: Project.chargebee.site })
  firstpromoter()
  Chargebee.getInstance().setCheckoutCallbacks?.(() => ({
    success: (hostedPageId: string) => {
      AppActions.updateSubscription(hostedPageId)
    },
  }))

  const planId = API.getCookie('plan')
  if (planId && isPaymentsEnabled) {
    const link = document.createElement('a')
    link.setAttribute('data-cb-type', 'checkout')
    link.setAttribute('data-cb-plan-id', planId)
    link.setAttribute('href', '#')
    document.body.appendChild(link)
    Chargebee.registerAgain()
    link.click()
    document.body.removeChild(link)
    API.setCookie('plan', null)
  }
}

export const bindChargebeeButtons = ({
  isPaymentsEnabled,
}: BindChargebeeButtonsParams) => {
  if (!Project.chargebee?.site) return

  if (!initialised) {
    initChargebee({ isPaymentsEnabled })
    initialised = true
  }

  // Re-scan the DOM so buttons rendered after the initial mount
  // (e.g. after toggling the yearly/monthly switch) get wired up.
  Chargebee.registerAgain()
}
