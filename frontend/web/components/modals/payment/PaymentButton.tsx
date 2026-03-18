import React, { FC, ReactNode } from 'react'
import { usePaymentState } from './hooks'
import { useChargebeeCheckout } from './hooks'

type PaymentButtonProps = {
  'data-cb-plan-id'?: string
  className?: string
  children?: ReactNode
  isDisableAccount?: string
}

export const PaymentButton: FC<PaymentButtonProps> = (props) => {
  const { hasActiveSubscription, organisation } = usePaymentState()
  const { openCheckout } = useChargebeeCheckout({
    onSuccess: props.isDisableAccount
      ? () => {
          window.location.href = '/organisations'
        }
      : undefined,
    organisationId: organisation?.id,
  })

  if (hasActiveSubscription) {
    return (
      <a
        onClick={() => {
          const planId = props['data-cb-plan-id']
          if (planId) {
            openCheckout(planId)
          }
        }}
        className={props.className}
        href='#'
      >
        {props.children}
      </a>
    )
  }

  return (
    <a
      href='javascript:void(0)'
      data-cb-type='checkout'
      data-cb-plan-id={props['data-cb-plan-id']}
      className={props.className}
    >
      {props.children}
    </a>
  )
}
