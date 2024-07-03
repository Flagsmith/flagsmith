import React, { FC, ReactNode } from 'react'
import Utils, { PaidFeature } from 'common/utils/utils'
import Button from './base/forms/Button'
import Constants from 'common/constants'
import { IonIcon } from '@ionic/react'
import { checkmarkCircle, documents, lockClosed } from 'ionicons/icons'
import classNames from 'classnames'
import Tooltip from './Tooltip'
import GifComponent from './Gif'

type PlanBasedBannerType = {
  className?: string
  feature: keyof typeof featureDescriptions
  theme: 'page' | 'badge' | 'description'
  children?: ReactNode
  withoutTooltip?: boolean
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
    preview: 'change-requests.gif',
    title: 'Change Requests',
  },

  'AUDIT': {
    description:
      'View all activity that occurred across the project and specific environments.',
    docs: 'https://docs.flagsmith.com/system-administration/audit-logs',
    preview: 'audit-log.gif',
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
    preview: 'flag-owners.gif',
    title: 'Flag Owners',
  },
  'FORCE_2FA': {
    description: 'Ensure your team are using 2-factor authentication.',
    title: 'Enforce Two-Factor Authentication',
  },
  'RBAC': {
    description:
      'Configure fine-grained permissions and roles to manage access across organisations, projects and environments.',
    preview: 'rbac.gif',
    title: 'Role-based access control',
  },
  'REALTIME': {
    description: 'Add real time detection of feature flag changes in your SDK.',
    docs: 'https://docs.flagsmith.com/advanced-use/real-time-flags',
    preview: 'realtime.gif',
    title: 'Realtime Updates',
  },
  'SCHEDULE_FLAGS': {
    description:
      'Manage feature state changes that have been scheduled to go live.',
    preview: 'scheduled-flags.gif',
    title: 'Scheduled Flags',
  },
  'STALE_FLAGS': {
    description:
      'Add automatic stale flag detection, prompting your team to clean up old flags.',
    preview: 'stale-flags.gif',
    title: 'Stale Flag Detection',
  },
}

const PlanBasedBanner: FC<PlanBasedBannerType> = ({
  children,
  className,
  feature,
  theme,
  withoutTooltip,
}) => {
  const hasPlan = Utils.getPlansPermission(feature)
  const planUrl = Constants.getUpgradeUrl()
  const docs = featureDescriptions[feature]?.docs
  const previewImage = withoutTooltip
    ? null
    : featureDescriptions[feature]?.preview
    ? `/static/images/features/${featureDescriptions[feature]?.preview}`
    : null
  const ctas = (
    <div className='d-flex gap-2 align-items-center text-nowrap'>
      {!Utils.isSaas() ||
        (docs && (
          <a
            className='btn text-white d-flex align-items-center gap-1 btn-xsm btn-secondary'
            href={
              docs ||
              'https://docs.flagsmith.com/deployment/configuration/enterprise-edition'
            }
            target={'_blank'}
            rel='noreferrer'
          >
            <IonIcon icon={documents} />
            View Docs
          </a>
        ))}
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

  const renderWithTooltip = (content) => {
    return (
      <Tooltip tooltipClassName='tooltip-lg p-0' title={content}>
        {previewImage
          ? `<img width='547px;' class='rounded' src='${previewImage}'/>`
          : null}
      </Tooltip>
    )
  }
  if (theme === 'badge') {
    return renderWithTooltip(
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
      </div>,
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
        style={{ maxWidth: 650 }}
        className={classNames(
          'p-2 rounded bg-primary800 text-white',
          className,
        )}
      >
        <div className='d-flex gap-2 justify-content-between font-weight-medium align-items-center'>
          <div>
            {renderWithTooltip(featureDescriptions[feature].description)}
          </div>
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
        <PlanBasedBanner withoutTooltip feature={feature} theme={'badge'} />
      </h4>
      <PlanBasedBanner withoutTooltip feature={feature} theme={'description'} />
      {!!previewImage && (
        <GifComponent className={'rounded img-fluid mt-4'} src={previewImage} />
      )}
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
