import React, { FC, useEffect } from 'react'
import Constants from 'common/constants'
import Utils from 'common/utils/utils'
import InfoMessage from 'components/InfoMessage'
import BlockedOrgInfo from 'components/BlockedOrgInfo'
import { Organisation } from 'common/types/responses'
import { PricingToggle } from './PricingToggle'
import { PricingPanel } from './PricingPanel'
import { startupFeatures, enterpriseFeatures } from './pricingFeatures'
import {
  CHARGEBEE_SCRIPT_URL,
  CONTACT_US_URL,
  ON_PREMISE_HOSTING_URL,
  SUPPORT_EMAIL,
  SUPPORT_EMAIL_URL,
} from './constants'
import { useScript } from 'common/hooks/useScript'
import { usePaymentState } from './hooks'
import { initChargebee } from './chargebee'

export type PaymentProps = {
  isDisableAccountText?: string
  organisation: Organisation
}

export const Payment: FC<PaymentProps> = ({
  isDisableAccountText,
  organisation,
}) => {
  const { error, ready } = useScript(CHARGEBEE_SCRIPT_URL)
  const { hasActiveSubscription, isAWS, plan, setYearly, yearly } =
    usePaymentState({ organisation })

  useEffect(() => {
    API.trackPage(Constants.modals.PAYMENT)
  }, [])

  useEffect(() => {
    if (ready && !error) {
      initChargebee({
        paymentsEnabled: Utils.getFlagsmithHasFeature('payments_enabled'),
      })
    }
  }, [ready, error])

  if (isAWS) {
    return (
      <div className='col-md-8'>
        <InfoMessage collapseId='aws-marketplace'>
          Customers with AWS Marketplace subscriptions will need to{' '}
          <a href={CONTACT_US_URL} target='_blank' rel='noreferrer'>
            contact us
          </a>
        </InfoMessage>
      </div>
    )
  }

  if (!ready) {
    return (
      <div className='text-center'>
        <Loader />
      </div>
    )
  }

  return (
    <div>
      <div className='col-md-12'>
        <Row space className='mb-4'>
          {isDisableAccountText && (
            <div className='d-lg-flex flex-lg-row align-items-end justify-content-between w-100 gap-4'>
              <div>
                <h4>
                  {isDisableAccountText}{' '}
                  <a target='_blank' href={SUPPORT_EMAIL_URL} rel='noreferrer'>
                    {SUPPORT_EMAIL}
                  </a>
                </h4>
              </div>
              <div>
                <BlockedOrgInfo />
              </div>
            </div>
          )}
        </Row>

        <PricingToggle isYearly={yearly} onChange={setYearly} />

        <Row className='pricing-container align-start'>
          <PricingPanel
            title='Start-Up'
            priceYearly='40'
            priceMonthly='45'
            isYearly={yearly}
            chargebeePlanId={
              yearly
                ? Project.plans?.startup?.annual
                : Project.plans?.startup?.monthly
            }
            isPurchased={plan.includes('startup')}
            isDisableAccount={isDisableAccountText}
            features={startupFeatures}
            hasActiveSubscription={hasActiveSubscription}
            organisationId={organisation.id}
          />

          <PricingPanel
            title='Enterprise'
            isYearly={yearly}
            isEnterprise
            features={enterpriseFeatures}
            hasActiveSubscription={hasActiveSubscription}
            organisationId={organisation.id}
            headerContent={
              <>
                Optional{' '}
                <a
                  className='text-primary fw-bold'
                  target='_blank'
                  href={ON_PREMISE_HOSTING_URL}
                  rel='noreferrer'
                >
                  On Premise
                </a>{' '}
                or{' '}
                <a
                  className='text-primary fw-bold'
                  target='_blank'
                  href={ON_PREMISE_HOSTING_URL}
                  rel='noreferrer'
                >
                  Private Cloud
                </a>{' '}
                Install
              </>
            }
          />
        </Row>
        <div className='text-center mt-4'>
          *Need something in-between our Enterprise plan for users or API
          limits?
          <div>
            <a href={CONTACT_US_URL}>Reach out</a> to us and we'll help you out
          </div>
        </div>
      </div>
    </div>
  )
}
