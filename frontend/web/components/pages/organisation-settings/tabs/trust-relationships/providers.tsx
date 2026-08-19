import React, { ReactNode } from 'react'
import { colorIconDefault } from 'common/theme/tokens'
import { GithubIcon } from 'components/icons/GithubIcon'
import Icon from 'components/icons/Icon'
import { GITHUB_ISSUER, GITHUB_LABEL } from './github'

export type TrustRelationshipProviderKey = 'github' | 'other'

// The providers the create flow offers, and the badges the list view shows.
// Add an entry here to introduce a preset (GitLab CI, Kubernetes, ...).
export type TrustRelationshipProvider = {
  key: TrustRelationshipProviderKey
  label: string
  description: string
  // The list view badges an issuer it recognises; a freeform provider has none.
  issuer?: string
  badge?: string
  // Sized by the caller: the list badge is small, the create flow's card is not.
  icon: (size: number) => ReactNode
}

export const TRUST_RELATIONSHIP_PROVIDERS: TrustRelationshipProvider[] = [
  {
    badge: 'Recommended',
    description:
      'Let workflows in a GitHub repository authenticate with their OIDC job token. Recommended if your CI runs on GitHub Actions.',
    icon: (size) => (
      <GithubIcon width={size} height={size} fill={colorIconDefault} />
    ),
    issuer: GITHUB_ISSUER,
    key: 'github',
    label: GITHUB_LABEL,
  },
  {
    description:
      'Configure a custom issuer, audience and claim matching rules for any OIDC identity provider, such as GitLab CI or Kubernetes.',
    icon: (size) => (
      <Icon name='shield' width={size} height={size} fill={colorIconDefault} />
    ),
    key: 'other',
    label: 'Other OIDC provider',
  },
]

export const providerForIssuer = (
  issuer: string,
): TrustRelationshipProvider | undefined =>
  TRUST_RELATIONSHIP_PROVIDERS.find((provider) => provider.issuer === issuer)
