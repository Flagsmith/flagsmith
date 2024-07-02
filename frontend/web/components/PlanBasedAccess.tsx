import React, { FC, ReactNode } from 'react'
import Utils, { PaidFeature } from 'common/utils/utils'
import Button from './base/forms/Button'
import { Link } from 'react-router-dom'
import Constants from 'common/constants'
import { IonIcon } from '@ionic/react'
import { checkmarkCircle, lockClosed, lockOpen, rocket } from 'ionicons/icons'
import classNames from 'classnames'
import PageTitle from './PageTitle'

type PlanBasedBannerType = {
  feature: keyof typeof featureDescriptions
  theme: 'page' | 'badge' | 'description'
  children?: ReactNode
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
      'View all activity that occurred across the project and specific environments.',
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

const PlanBasedBanner: FC<PlanBasedBannerType> = ({
  children,
  feature,
  theme,
}) => {
  const hasPlan = Utils.getPlansPermission(feature)
  const planUrl = Utils.isSaas()
    ? Constants.upgradeURL
    : 'https://www.flagsmith.com/on-premises-and-private-cloud-hosting#contact'
  const ctas = (
    <div className='d-flex gap-4'>
      {Utils.isSaas() ? (
        <Link to={Constants.upgradeURL}>
          <Button size='xSmall'>Start Free Trial</Button>
        </Link>
      ) : (
        <Button size='xSmall' href={planUrl} target='_blank'>
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

  const BadgeTag = Utils.isSaas() ? Link : 'a'
  if (theme === 'badge') {
    return (
      <div>
        <BadgeTag
          to={planUrl}
          href={planUrl}
          target={Utils.isSaas() ? undefined : '_blank'}
          className='chip cursor-pointer chip--xs d-flex align-items-center font-weight-medium text-white bg-primary'
        >
          {
            <IonIcon
              className='me-1'
              icon={hasPlan ? checkmarkCircle : lockClosed}
            />
          }
          {Utils.getPlanName(Utils.getRequiredPlan(feature))}
        </BadgeTag>
      </div>
    )
  } else if (theme === 'description') {
    if (hasPlan) {
      return (
        <p className={classNames('fs-small lh-sm')}>
          {featureDescriptions[feature].description}
        </p>
      )
    }
    return (
      <div className='p-2 rounded bg-primary bg-opacity-10'>
        <div className='d-flex gap-2 justify-content-between align-items-center'>
          <div>{featureDescriptions[feature].description}</div>
          {ctas}
        </div>
      </div>
    )
  }
  if (hasPlan) {
    return <>{children}</>
  }
  return (
    <div>
      <h4 className='d-flex align-items-center gap-2'>
        <span>{featureDescriptions[feature].title}</span>
        <PlanBasedBanner feature={feature} theme={'badge'} />
      </h4>
      <PlanBasedBanner feature={feature} theme={'description'} />
    </div>
  )
}

export default PlanBasedBanner
