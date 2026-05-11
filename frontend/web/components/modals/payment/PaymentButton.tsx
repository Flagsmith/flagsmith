import React, { FC, ReactNode } from 'react'
import { useChargebeeCheckout } from './hooks'

type PaymentButtonProps = {
  'data-cb-plan-id'?: string
  className?: string
  children?: ReactNode
  isDisableAccount?: string
  hasActiveSubscription: boolean
  organisationId: number
}

export const PaymentButton: FC<PaymentButtonProps> = ({
  children,
  className,
  hasActiveSubscription,
  isDisableAccount,
  organisationId,
  ...rest
}) => {
  const planId = rest['data-cb-plan-id']
  const { isLoading, openCheckout } = useChargebeeCheckout({
    onSuccess: isDisableAccount
      ? () => {
          window.location.href = '/organisations'
        }
      : undefined,
    organisationId,
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
