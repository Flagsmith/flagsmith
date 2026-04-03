// @ts-ignore
import firstpromoter from 'project/firstPromoter'

let initialised = false

type InitChargebeeParams = {
  isPaymentsEnabled: boolean
}

export const initChargebee = ({ isPaymentsEnabled }: InitChargebeeParams) => {
  if (initialised || !Project.chargebee?.site) return

  Chargebee.init({ site: Project.chargebee.site })
  Chargebee.registerAgain()
  firstpromoter()
  Chargebee.getInstance().setCheckoutCallbacks?.(() => ({
    success: (hostedPageId: string) => {
      AppActions.updateSubscription(hostedPageId)
    },
  }))

  // Handle plan cookie from signup flow
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

  initialised = true
}
