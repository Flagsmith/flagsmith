import React, { ReactNode } from 'react'
import classNames from 'classnames'
import Icon from 'components/icons/Icon'
import Button from 'components/base/forms/Button'
import { PricingFeaturesList } from './PricingFeaturesList'
import { PaymentButton } from './PaymentButton'
import { openChat } from 'common/loadChat'
import { PricingFeature } from './types'
import Text from 'components/base/Text'

export type PricingPanelProps = {
  title: string
  priceMonthly?: string
  priceYearly?: string
  includesFrom: string
  isYearly: boolean
  chargebeePlanId?: string
  isPurchased?: boolean
  isEnterprise?: boolean
  isDisableAccount?: string
  features: PricingFeature[]
  headerContent?: ReactNode
  hasActiveSubscription: boolean
  organisationId: number
}

export const PricingPanel = ({
  chargebeePlanId,
  features,
  hasActiveSubscription,
  headerContent,
  includesFrom,
  isDisableAccount,
  isEnterprise,
  isPurchased,
  isYearly,
  organisationId,
  priceMonthly,
  priceYearly,
  title,
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
                    'text-default': !isEnterprise,
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
                <Text
                  variant='h4'
                  level={2}
                  className={classNames('mb-0 ml-2', {
                    'text-white': isEnterprise,
                  })}
                >
                  {title}
                </Text>
              </Row>

              {priceYearly && priceMonthly && (
                <Row className='pt-3 justify-content-center'>
                  <Text
                    variant='h5'
                    as='span'
                    className='mb-0 align-self-start'
                  >
                    $
                  </Text>
                  <Text
                    variant='h1'
                    as='span'
                    className='mb-0 d-flex align-items-end'
                  >
                    {isYearly ? priceYearly : priceMonthly}{' '}
                    <span className='fs-lg mb-0'>/mo</span>
                  </Text>
                </Row>
              )}

              {isEnterprise && (
                <Row className='pt-3 justify-content-center'>
                  <div className='pricing-type pricing-accent'>
                    Maximum security and control
                  </div>
                </Row>
              )}
            </div>

            <div className='pricing-panel-spacer' />

            <div>
              {!isEnterprise && chargebeePlanId && (
                <PaymentButton
                  key={chargebeePlanId}
                  data-cb-plan-id={chargebeePlanId}
                  className='btn btn-primary btn-lg full-width mt-3'
                  isDisableAccount={isDisableAccount}
                  hasActiveSubscription={hasActiveSubscription}
                  organisationId={organisationId}
                >
                  {isPurchased ? 'Purchased' : '14 Day Free Trial'}
                </PaymentButton>
              )}

              {isEnterprise && (
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
          <Text
            variant='h5'
            level={2}
            className={classNames('m-2 mb-4', {
              'text-white': isEnterprise,
            })}
          >
            All from{' '}
            <span className={isEnterprise ? 'pricing-accent' : 'text-action'}>
              {includesFrom},
            </span>{' '}
            plus
          </Text>
          <PricingFeaturesList
            features={features}
            iconClass={isEnterprise ? 'pricing-accent' : undefined}
          />
        </div>
      </div>
    </Flex>
  )
}
