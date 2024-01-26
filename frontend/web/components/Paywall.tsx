import React, { FC, ReactNode } from 'react'
import Utils, { FeaturePermission, PlanName } from 'common/utils/utils'

type PaywallType = {
  feature: FeaturePermission
  children: ReactNode
}

export const MinimumPlan: FC<{ plan: PlanName }> = ({ plan }) => {
  if (global.flagsmithVersion?.backend?.is_saas) {
    return <>This feature is available with our {plan} plan.</>
  }
  return <>This feature is available with our {plan} plan.</>
}

const Paywall: FC<PaywallType> = ({ children, feature }) => {
  const permission = Utils.getPlansPermission(feature)
  const minimumPlan = Utils.getMinimumPlan(feature)
  if (!permission) {
    return (
      <div>
        <div className='text-center'>
          <MinimumPlan plan={minimumPlan} />
        </div>
      </div>
    )
  }
  return <>{children}</>
}

export default Paywall
