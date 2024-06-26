import { FC } from 'react'
import Utils, { PaidFeature } from 'common/utils/utils'
import Button from './base/forms/Button'
import { Link } from 'react-router-dom'
import Constants from 'common/constants'

type UpsellType = {
  feature: keyof typeof featureDescriptions
}

const featureDescriptions: Record<PaidFeature, any> = {
  'VERSIONING': "View your feature's entire version history",
}

const UpsellBanner: FC<UpsellType> = ({ feature }) => {
  return (
    <div className='border-1 bg-primaryAlfa8'>
      <h5>
        {featureDescriptions[feature]}{' '}
        <div className='chip'>
          {Utils.getPlanName(Utils.getRequiredPlan(feature))}
        </div>
      </h5>
      {Utils.isSaas() ? (
        <p>
          Start a free, 14 day trial to access this feature along with many
          others.
        </p>
      ) : (
        <p></p>
      )}
      <div className='d-flex gap-4'>
        {Utils.isSaas() ? (
          <Link to={Constants.upgradeURL}>
            <Button>View our Plans</Button>
          </Link>
        ) : (
          <Button
            href='https://www.flagsmith.com/on-premises-and-private-cloud-hosting#contact'
            target='_blank'
          >
            Contact Us
          </Button>
        )}
        {!Utils.isSaas() && (
          <a
            href='https://docs.flagsmith.com/deployment/configuration/enterprise-edition'
            target={'_blank'}
            rel='noreferrer'
          >
            Find out more
          </a>
        )}
      </div>
    </div>
  )
}

export default UpsellBanner
