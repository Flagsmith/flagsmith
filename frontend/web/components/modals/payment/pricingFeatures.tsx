import { PricingFeature } from './types'

const ENTERPRISE_ICON_CLASS = 'text-secondary'

export const startupFeatures: PricingFeature[] = [
  {
    text: (
      <>
        Up to
        <strong> 1,000,000</strong> Requests per month
      </>
    ),
  },
  {
    text: (
      <>
        <strong>3</strong> Team members
      </>
    ),
  },
  {
    text: 'Unlimited projects',
  },
  {
    text: 'Email technical support',
  },
  {
    text: 'Scheduled flags',
  },
  {
    text: 'Two-factor authentication (2FA)',
  },
]

export const enterpriseFeatures: PricingFeature[] = [
  {
    iconClass: ENTERPRISE_ICON_CLASS,
    text: (
      <>
        <strong> 5,000,000+</strong> requests per month
      </>
    ),
  },
  {
    iconClass: ENTERPRISE_ICON_CLASS,
    text: (
      <>
        <strong>20+</strong> Team members
      </>
    ),
  },
  {
    iconClass: ENTERPRISE_ICON_CLASS,
    text: 'Advanced hosting options',
  },
  {
    iconClass: ENTERPRISE_ICON_CLASS,
    text: 'Priority real time technical support with the engineering team over Slack or Discord',
  },
  {
    iconClass: ENTERPRISE_ICON_CLASS,
    text: 'Governance features – roles, permissions, change requests, audit logs',
  },
  {
    iconClass: ENTERPRISE_ICON_CLASS,
    text: 'Features for maximum security',
  },
  {
    iconClass: ENTERPRISE_ICON_CLASS,
    text: 'Optional on premises installation',
  },
  {
    iconClass: ENTERPRISE_ICON_CLASS,
    text: 'Onboarding & training',
  },
]
