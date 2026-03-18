import React, { ComponentProps } from 'react'
// @ts-ignore
import makeAsyncScriptLoader from 'react-async-script'
import ConfigProvider from 'common/providers/ConfigProvider'
import Utils from 'common/utils/utils'
// @ts-ignore
import firstpromoter from 'project/firstPromoter'
import { Payment } from './Payment'

type PaymentLoadParams = {
  errored: boolean
}

export const onPaymentLoad = ({ errored }: PaymentLoadParams) => {
  if (errored) {
    // TODO: no error details are available https://github.com/dozoisch/react-async-script/issues/58
    console.error('failed to load chargebee')
    return
  }
  if (!Project.chargebee?.site) {
    return
  }
  const planId = API.getCookie('plan')
  let link: HTMLAnchorElement | undefined

  if (planId && Utils.getFlagsmithHasFeature('payments_enabled')) {
    // Create a link element with data-cb-plan-id attribute
    link = document.createElement('a')
    link.setAttribute('data-cb-type', 'checkout')
    link.setAttribute('data-cb-plan-id', planId)
    link.setAttribute('href', 'javascript:void(0)')
    // Append the link to the body
    document.body.appendChild(link)
  }

  Chargebee.init({
    site: Project.chargebee.site,
  })
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

const WrappedPayment = makeAsyncScriptLoader(
  'https://js.chargebee.com/v2/chargebee.js',
  {
    removeOnUnmount: true,
  },
)(ConfigProvider(Payment))

export default (props: ComponentProps<typeof Payment>) => (
  <WrappedPayment {...props} asyncScriptOnLoad={onPaymentLoad} />
)
