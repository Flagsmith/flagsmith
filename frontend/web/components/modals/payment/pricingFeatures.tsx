import { PricingFeature } from './types'
import { ENTERPRISE_ICON_COLOR } from './constants'

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
    iconFill: ENTERPRISE_ICON_COLOR,
    text: (
      <>
        <strong> 5,000,000+</strong> requests per month
      </>
    ),
  },
  {
    iconFill: ENTERPRISE_ICON_COLOR,
    text: (
      <>
        <strong>20+</strong> Team members
      </>
    ),
  },
  {
    iconFill: ENTERPRISE_ICON_COLOR,
    text: 'Advanced hosting options',
  },
  {
    iconFill: ENTERPRISE_ICON_COLOR,
    text: 'Priority real time technical support with the engineering team over Slack or Discord',
  },
  {
    iconFill: ENTERPRISE_ICON_COLOR,
    text: 'Governance features – roles, permissions, change requests, audit logs',
  },
  {
    iconFill: ENTERPRISE_ICON_COLOR,
    text: 'Features for maximum security',
  },
  {
    iconFill: ENTERPRISE_ICON_COLOR,
    text: 'Optional on premises installation',
  },
  {
    iconFill: ENTERPRISE_ICON_COLOR,
    text: 'Onboarding & training',
  },
]
