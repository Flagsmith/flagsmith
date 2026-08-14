import React, { ReactNode } from 'react'
import { GithubIcon } from 'components/icons/GithubIcon'
import { GITHUB_ISSUER } from './github'

// Known OIDC providers, keyed by issuer. Add an entry here to give a future
// preset (GitLab CI, Kubernetes, ...) its own badge in the list view.
export type TrustRelationshipProvider = {
  issuer: string
  label: string
  icon: ReactNode
}

export const TRUST_RELATIONSHIP_PROVIDERS: TrustRelationshipProvider[] = [
  {
    icon: <GithubIcon width={16} height={16} />,
    issuer: GITHUB_ISSUER,
    label: 'GitHub Actions',
  },
]

export const providerForIssuer = (
  issuer: string,
): TrustRelationshipProvider | undefined =>
  TRUST_RELATIONSHIP_PROVIDERS.find((provider) => provider.issuer === issuer)
