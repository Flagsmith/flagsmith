import React, { ReactNode } from 'react'
import classNames from 'classnames'
import Icon, { IconName } from 'components/Icon'
import Button from 'components/base/forms/Button'
import { PricingFeaturesList } from './PricingFeaturesList'
import { PaymentButton } from './PaymentButton'
import { openChat } from 'common/loadChat'
import { PricingFeature } from './types'

export type PricingPanelProps = {
  title: string
  icon?: string
  iconFill?: string
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
  onContactSales?: () => void
}

export const PricingPanel = ({
  chargebeePlanId,
  features,
  headerContent,
  icon = 'flash',
  iconFill,
  isDisableAccount,
  isEnterprise,
  isPurchased,
  isYearly,
  onContactSales,
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
        <div
          className='panel-content p-3 pt-4'
          style={{
            backgroundColor: 'rgba(39, 171, 149, 0.08)',
            minHeight: '320px',
          }}
        >
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              height: '100%',
              minHeight: '200px',
            }}
          >
            <div style={{ flex: '0 0 auto' }}>
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
                  name={icon as IconName}
                  width={32}
                  fill={iconFill || undefined}
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
                    <h5 className='fs-lg mb-0'>/mo</h5>
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

            <div style={{ flex: '1 1 auto' }} />

            <div style={{ flex: '0 0 auto' }}>
              {!viewOnly && !isEnterprise && chargebeePlanId && (
                <>
                  <PaymentButton
                    data-cb-plan-id={chargebeePlanId}
                    className={classNames(
                      'btn btn-primary btn-lg full-width mt-3',
                    )}
                    isDisableAccount={isDisableAccount}
                  >
                    {isPurchased ? 'Purchased' : '14 Day Free Trial'}
                  </PaymentButton>
                </>
              )}

              {!viewOnly && isEnterprise && (
                <Button
                  onClick={() => {
                    if (onContactSales) {
                      onContactSales()
                    } else {
                      openChat()
                    }
                  }}
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
