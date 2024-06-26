import React, { FC } from 'react'
import Utils, { PaidFeature } from 'common/utils/utils'
import Button from './base/forms/Button'
import { Link } from 'react-router-dom'
import Constants from 'common/constants'
import { IonIcon } from '@ionic/react'
import { lockClosed } from 'ionicons/icons'

type PlanBasedBannerType = {
  feature: keyof typeof featureDescriptions
  theme: 'banner' | 'badge' | 'description'
}

export const featureDescriptions: Record<PaidFeature, any> = {
  '2FA': {
    description: 'Add Two-Factor authentication for extra security.',
    title: 'Two-Factor Authentication',
  },
  '4_EYES': {
    description:
      'Add a 4-eyes approval mechanism to your feature changes with change requests.',
    title: 'Change Requests',
  },

  'AUDIT': {
    description:
      'Keep track of every action taken within the Flagsmith administration application.',
    title: 'Audit Log',
  },
  'CREATE_ADDITIONAL_PROJECT': {
    description: 'Create additional projects.',
    title: 'Create additional projects.',
  },
  'FLAG_OWNERS': {
    description: 'Assign your team and groups as owners of individual flags.',
    title: 'Flag Owners',
  },
  'FORCE_2FA': {
    description: 'Ensure your team are using 2-factor authentication.',
    title: 'Enforce Two-Factor Authentication',
  },
  'RBAC': {
    descrption:
      'Configure fine-grained permissions and roles to manage access across organisations, projects and environments.',
    title: 'Role-based access control',
  },
  'REALTIME': {
    description: 'Add real time detection of feature flag changes in your SDK.',
    title: 'Realtime Updates',
  },
  'SCHEDULE_FLAGS': {
    description: 'Schedule when your flags change.',
    title: 'Scheduled Flags',
  },
  'STALE_FLAGS': {
    description: 'Automatic tagging of old flags.',
    title: 'Stale Flag Detection',
  },
  'VERSIONING': {
    description: "View your feature's entire version history.",
    title: 'Feature Versioning',
  },
}

const PlanBasedBanner: FC<PlanBasedBannerType> = ({ feature, theme }) => {
  const hasPlan = Utils.getPlansPermission(feature)
  const ctas = (
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
  )
  if (hasPlan) {
    return null
  }
  if (theme === 'badge') {
    return (
      <div>
        <div className='chip chip--xs font-weight-medium text-white bg-primary'>
          <IonIcon className='me-1' icon={lockClosed} />{' '}
          {Utils.getPlanName(Utils.getRequiredPlan(feature))}
        </div>
      </div>
    )
  } else if(theme === 'description') {

  }
  return (
    <div className='border-1 bg-primaryAlfa8'>
      <h5>
        {featureDescriptions[feature]}{' '}
        <div className='chip chip--xs bg-primary'>
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
      {ctas}
    </div>
  )
}

export default PlanBasedBanner
