import React, { FC, ReactNode } from 'react'
import Utils, { PaidFeature } from 'common/utils/utils'
import Button from './base/forms/Button'
import Constants from 'common/constants'
import { IonIcon } from '@ionic/react'
import { checkmarkCircle, documents, lockClosed } from 'ionicons/icons'
import classNames from 'classnames'

type PlanBasedBannerType = {
  className?: string
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
    docs: 'https://docs.flagsmith.com/advanced-use/change-requests',
    title: 'Change Requests',
  },

  'AUDIT': {
    description:
      'View all activity that occurred across the project and specific environments.',
    docs: 'https://docs.flagsmith.com/system-administration/audit-logs',
    title: 'Audit Log',
  },
  'AUTO_SEATS': {
    description: 'Invite additional members.',
    title: 'Invite additional members',
  },
  'CREATE_ADDITIONAL_PROJECT': {
    description: 'View and manage multiple projects in your organisation',
    title: 'Create additional projects',
  },
  'FLAG_OWNERS': {
    description:
      'Assign your team members and groups as owners of individual flags.',
    title: 'Flag Owners',
  },
  'FORCE_2FA': {
    description: 'Ensure your team are using 2-factor authentication.',
    title: 'Enforce Two-Factor Authentication',
  },
  'RBAC': {
    description:
      'Configure fine-grained permissions and roles to manage access across organisations, projects and environments.',
    title: 'Role-based access control',
  },
  'REALTIME': {
    description: 'Add real time detection of feature flag changes in your SDK.',
    docs: 'https://docs.flagsmith.com/advanced-use/real-time-flags',
    title: 'Realtime Updates',
  },
  'SCHEDULE_FLAGS': {
    description:
      'Manage feature state changes that have been scheduled to go live.',
    title: 'Scheduled Flags',
  },
  'STALE_FLAGS': {
    description: 'Automatic tagging of old flags.',
    title: 'Stale Flag Detection',
  },
}

const PlanBasedBanner: FC<PlanBasedBannerType> = ({
  children,
  className,
  feature,
  theme,
}) => {
  const hasPlan = Utils.getPlansPermission(feature)
  const planUrl = Constants.getUpgradeUrl()
  const ctas = (
    <div className='d-flex gap-2 align-items-center text-nowrap'>
      {!Utils.isSaas() && (
        <a
          className='btn text-white d-flex align-items-center gap-1 btn-xsm btn-secondary'
          href='https://docs.flagsmith.com/deployment/configuration/enterprise-edition'
          target={'_blank'}
          rel='noreferrer'
        >
          <IonIcon icon={documents} />
          View Docs
        </a>
      )}
      {Utils.isSaas() ? (
        <a href={Constants.getUpgradeUrl()}>
          <Button theme='tertiary' size='xSmall'>
            Start Free Trial
          </Button>
        </a>
      ) : (
        <Button theme='tertiary' size='xSmall' href={planUrl} target='_blank'>
          Contact Us
        </Button>
      )}
    </div>
  )

  if (theme === 'badge') {
    return (
      <div>
        <a
          href={planUrl}
          target={Utils.isSaas() ? undefined : '_blank'}
          className='chip cursor-pointer chip--xs d-flex align-items-center font-weight-medium text-white bg-primary800'
          rel='noreferrer'
        >
          {
            <IonIcon
              className='me-1'
              icon={hasPlan ? checkmarkCircle : lockClosed}
            />
          }
          {Utils.getPlanName(Utils.getRequiredPlan(feature))}
        </a>
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
      <div
        style={{ maxWidth: 600 }}
        className={classNames(
          'p-2 rounded bg-primary800 text-white',
          className,
        )}
      >
        <div className='d-flex gap-2 justify-content-between font-weight-medium align-items-center'>
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
    <div className={className}>
      <h4 className='d-flex align-items-center gap-2'>
        <span>{featureDescriptions[feature].title}</span>
        <PlanBasedBanner feature={feature} theme={'badge'} />
      </h4>
      <PlanBasedBanner feature={feature} theme={'description'} />
    </div>
  )
}

export default PlanBasedBanner

export const getPlanBasedOption = function (
  data: { label: string; value: any },
  feature: PaidFeature,
) {
  return {
    ...data,
    label: (
      <div className='d-flex gap-2'>
        {data.label}
        <PlanBasedBanner feature={feature} theme={'badge'} />
      </div>
    ),
  }
}
