import React, { FC, useState } from 'react'
import GithubTrustRelationshipForm from './GithubTrustRelationshipForm'
import TrustRelationshipModal from './TrustRelationshipModal'

type Provider = 'github' | 'other'

type NewTrustRelationshipModalProps = {
  organisationId: number
  existingAudiences: string[]
}

const NewTrustRelationshipModal: FC<NewTrustRelationshipModalProps> = ({
  existingAudiences,
  organisationId,
}) => {
  const [provider, setProvider] = useState<Provider | null>(null)

  if (provider === 'github') {
    return (
      <GithubTrustRelationshipForm
        organisationId={organisationId}
        existingAudiences={existingAudiences}
      />
    )
  }
  if (provider === 'other') {
    return <TrustRelationshipModal organisationId={organisationId} />
  }

  return (
    <div className='p-4'>
      <div
        className='panel--grey p-3 mb-3 clickable'
        data-test='provider-github'
        onClick={() => setProvider('github')}
      >
        <h6 className='mb-1'>GitHub Actions</h6>
        <div className='text-muted fs-small'>
          Let workflows in a GitHub repository authenticate with their OIDC job
          token. Recommended if your CI runs on GitHub Actions.
        </div>
      </div>
      <div
        className='panel--grey p-3 clickable'
        data-test='provider-other'
        onClick={() => setProvider('other')}
      >
        <h6 className='mb-1'>Other OIDC provider</h6>
        <div className='text-muted fs-small'>
          Configure a custom issuer, audience and claim matching rules for any
          OIDC identity provider, such as GitLab CI or Kubernetes.
        </div>
      </div>
    </div>
  )
}

export default NewTrustRelationshipModal
