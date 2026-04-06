import { PricingFeature } from './types'

export const STARTUP_FEATURES: PricingFeature[] = [
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

export const ENTERPRISE_FEATURES: PricingFeature[] = [
  {
    text: (
      <>
        <strong> 5,000,000+</strong> requests per month
      </>
    ),
  },
  {
    text: (
      <>
        <strong>20+</strong> Team members
      </>
    ),
  },
  {
    text: 'Advanced hosting options',
  },
  {
    text: 'Priority real time technical support with the engineering team over Slack or Discord',
  },
  {
    text: 'Governance features – roles, permissions, change requests, audit logs',
  },
  {
    text: 'Features for maximum security',
  },
  {
    text: 'Optional on premises installation',
  },
  {
    text: 'Onboarding & training',
  },
]
