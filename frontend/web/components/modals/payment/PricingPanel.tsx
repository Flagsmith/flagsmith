import React, { ReactNode } from 'react'
import classNames from 'classnames'
import Icon from 'components/Icon'
import Button from 'components/base/forms/Button'
import { PricingFeaturesList } from './PricingFeaturesList'
import { PaymentButton } from './PaymentButton'
import { openChat } from 'common/loadChat'
import { PricingFeature } from './types'

export type PricingPanelProps = {
  title: string
  priceMonthly?: string
  priceYearly?: string
  isYearly: boolean
  viewOnly?: boolean
  chargebeePlanId?: string
  isPurchased?: boolean
  isEnterprise?: boolean
  isDisableAccount?: string
  features: PricingFeature[]
  headerContent?: ReactNode
}

export const PricingPanel = ({
  chargebeePlanId,
  features,
  headerContent,
  isDisableAccount,
  isEnterprise,
  isPurchased,
  isYearly,
  priceMonthly,
  priceYearly,
  title,
  viewOnly,
}: PricingPanelProps) => {
  return (
    <Flex
      className={classNames('pricing-panel p-2', {
        'bg-primary900 text-white': isEnterprise,
      })}
    >
      <div className='panel panel-default'>
        <div className='p-3 pt-4 pricing-panel-content'>
          <div className='pricing-panel-layout'>
            <div>
              {headerContent && (
                <span
                  className={classNames('featured', {
                    'text-body': !isEnterprise,
                    'text-white': isEnterprise,
                  })}
                >
                  {headerContent}
                </span>
              )}
              <Row className='pt-4 justify-content-center'>
                <Icon
                  name='flash'
                  width={32}
                  fill={isEnterprise ? 'white' : undefined}
                />
                <h4
                  className={classNames('mb-0 ml-2', {
                    'text-white': isEnterprise,
                  })}
                >
                  {title}
                </h4>
              </Row>

              {priceYearly && priceMonthly && (
                <Row className='pt-3 justify-content-center'>
                  <h5 className='mb-0 align-self-start'>$</h5>
                  <h1 className='mb-0 d-flex align-items-end'>
                    {isYearly ? priceYearly : priceMonthly}{' '}
                    <span className='fs-lg mb-0'>/mo</span>
                  </h1>
                </Row>
              )}

              {isEnterprise && (
                <Row className='pt-3 justify-content-center'>
                  <div className='pricing-type text-secondary'>
                    Maximum security and control
                  </div>
                </Row>
              )}
            </div>

            <div className='pricing-panel-spacer' />

            <div>
              {!viewOnly && !isEnterprise && chargebeePlanId && (
                <PaymentButton
                  data-cb-plan-id={chargebeePlanId}
                  className='btn btn-primary btn-lg full-width mt-3'
                  isDisableAccount={isDisableAccount}
                >
                  {isPurchased ? 'Purchased' : '14 Day Free Trial'}
                </PaymentButton>
              )}

              {!viewOnly && isEnterprise && (
                <Button
                  onClick={() => openChat()}
                  className='full-width btn-lg btn-tertiary mt-3'
                >
                  Contact Sales
                </Button>
              )}
            </div>
          </div>
        </div>

        <div className='panel-footer mt-3'>
          <h5
            className={classNames('m-2 mb-4', {
              'text-white': isEnterprise,
            })}
          >
            All from{' '}
            <span className={isEnterprise ? 'text-secondary' : 'text-primary'}>
              {isEnterprise ? 'Start-Up,' : 'Free,'}
            </span>{' '}
            plus
          </h5>
          <PricingFeaturesList features={features} />
        </div>
      </div>
    </Flex>
  )
}
