import React, { FC, ReactNode } from 'react'
import { usePaymentState, useChargebeeCheckout } from './hooks'

type PaymentButtonProps = {
  'data-cb-plan-id'?: string
  className?: string
  children?: ReactNode
  isDisableAccount?: string
}

export const PaymentButton: FC<PaymentButtonProps> = ({
  children,
  className,
  isDisableAccount,
  ...rest
}) => {
  const planId = rest['data-cb-plan-id']
  const { hasActiveSubscription, organisation } = usePaymentState()
  const { isLoading, openCheckout } = useChargebeeCheckout({
    onSuccess: isDisableAccount
      ? () => {
          window.location.href = '/organisations'
        }
      : undefined,
    organisationId: organisation?.id,
  })

  if (hasActiveSubscription) {
    return (
      <button
        onClick={() => planId && openCheckout(planId)}
        className={className}
        type='button'
        disabled={isLoading}
      >
        {isLoading ? 'Processing...' : children}
      </button>
    )
  }

  return (
    <button
      type='button'
      data-cb-type='checkout'
      data-cb-plan-id={planId}
      className={className}
    >
      {children}
    </button>
  )
}
