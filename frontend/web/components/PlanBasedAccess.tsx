import React, { FC, ReactNode } from 'react'
import Utils, { PaidFeature } from 'common/utils/utils'
import Button from './base/forms/Button'
import Constants from 'common/constants'
import { IonIcon } from '@ionic/react'
import { documents, lockClosed } from 'ionicons/icons'
import classNames from 'classnames'
import API from 'project/api'

type PlanBasedBannerType = {
  className?: string
  feature: keyof typeof featureDescriptions
  theme: 'page' | 'badge' | 'description'
  children?: ReactNode
  title?: ReactNode
  force?: boolean
}

export const featureDescriptions: Record<PaidFeature, any> = {
  '2FA': {
    description: 'Add Two-Factor authentication for extra security.',
    title: 'Two-Factor Authentication',
  },
  '4_EYES': {
    description: 'Add a 4-eyes approval mechanism to your feature changes.',
    docs: 'https://docs.flagsmith.com/advanced-use/change-requests',
    title: 'Change Requests',
  },
  'AUDIT': {
    description:
      'View and search through a history of all changes made in your Flagsmith organisation.',
    docs: 'https://docs.flagsmith.com/system-administration/audit-logs',
    title: 'Audit Log',
  },

  'AUTO_SEATS': {
    description: 'Invite additional members.',
    title: 'Invite additional members',
  },
  'CREATE_ADDITIONAL_PROJECT': {
    description: 'Free organisations are limited to one Flagsmith project',
    title: 'Create additional projects',
  },
  'FLAG_OWNERS': {
    description:
      'Assign your team members and groups as owners of individual flags.',
    title: 'Flag Owners',
  },
  'FORCE_2FA': {
    description: 'Improve security compliance across your organisation.',
    title: 'Enforce Two-Factor Authentication',
  },
  'METADATA': {
    description:
      'Define custom fields that are shown when creating or modifying flags, segments or environments.',
    docs: 'https://docs.flagsmith.com/advanced-use/custom-fields',
    title: 'Custom Fields',
  },
  'RBAC': {
    description:
      'Configure fine-grained permissions and roles to manage access across organisations, projects and environments.',
    docs: 'https://docs.flagsmith.com/system-administration/rbac',
    title: 'Role-based access control',
  },
  'REALTIME': {
    description: 'Add real time detection of feature flag changes in your SDK.',
    docs: 'https://docs.flagsmith.com/advanced-use/real-time-flags',
    title: 'Realtime Updates',
  },
  'SAML': {
    description: 'Configure 2FA, SAML, Okta, ADFS and LDAP.',
    docs: 'https://docs.flagsmith.com/system-administration/authentication/',
    title: 'Enterprise single sign-on',
  },
  'SCHEDULE_FLAGS': {
    description:
      'Manage feature state changes that have been scheduled to go live.',
    docs: 'https://docs.flagsmith.com/advanced-use/scheduled-flags',
    title: 'Scheduled Flags',
  },
  'STALE_FLAGS': {
    description:
      'Add automatic stale flag detection, prompting your team to clean up old flags.',
    title: 'Stale Flag Detection',
  },
  'VERSIONING': {
    description: 'Access all of your feature versions.',
    title: 'Version History',
  },
}

const PlanBasedBanner: FC<PlanBasedBannerType> = ({ children, ...props }) => {
  const { className, feature, force, theme, title } = props
  const trackFeature = () =>
    API.trackEvent(Constants.events.VIEW_LOCKED_FEATURE(feature))
  const hasPlan = !force && Utils.getPlansPermission(feature)
  const planUrl = Constants.getUpgradeUrl(feature)
  const docs = `${featureDescriptions[feature]?.docs}?utm_source=plan_based_access`

  const ctas = (
    <div className='d-flex gap-2 align-items-center text-nowrap'>
      {!Utils.isSaas() ||
        (docs && (
          <a
            onClick={trackFeature}
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
        <a
          onClick={trackFeature}
          target='_blank'
          href={Constants.getUpgradeUrl(feature)}
          rel='noreferrer'
        >
          <Button theme='tertiary' size='xSmall'>
            Start Free Trial
          </Button>
        </a>
      ) : (
        <Button
          onClick={trackFeature}
          theme='tertiary'
          size='xSmall'
          href={planUrl}
          target='_blank'
        >
          Contact Us
        </Button>
      )}
    </div>
  )

  if (theme === 'badge') {
    if (hasPlan) {
      return null
    }
    return (
      <div>
        <a
          href={planUrl}
          target={Utils.isSaas() ? undefined : '_blank'}
          className='chip cursor-pointer chip--xs d-flex align-items-center font-weight-medium text-white bg-primary800'
          rel='noreferrer'
        >
          {<IonIcon className='me-1' icon={lockClosed} />}
          {force
            ? Utils.getNextPlan()
            : Utils.getPlanName(Utils.getRequiredPlan(feature))}
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
        style={{ maxWidth: 650 }}
        className={classNames(
          'p-2 rounded bg-primary800 text-white',
          className,
        )}
      >
        <div className='d-flex gap-2 justify-content-between font-weight-medium align-items-center'>
          <div>{title || featureDescriptions[feature].description}</div>
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
        <PlanBasedBanner {...props} theme={'badge'} />
      </h4>
      <PlanBasedBanner {...props} theme={'description'} />
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
    isDisabled: !Utils.getPlansPermission(feature),
    label: (
      <div className='d-flex gap-2'>
        {data.label}
        <PlanBasedBanner feature={feature} theme={'badge'} />
      </div>
    ),
  }
}
